"""voice.fish — Fish Audio synthesis for the PRIMARY clone of the CJ voice.

    from voice.fish import synthesize, FishError, configured, model_id

synthesize(text, speed=…) → float32 PCM at audio.SYNTH_SAMPLE_RATE; raises
FishError, which carries the same ``.reason`` vocabulary as voice.speak's
SynthError (quota | network | error) so app/voice_guard.py reads either
without caring which vendor failed. Never contains the API key.

Why a second vendor at all (2026-09-16): the ElevenLabs account hit
131,000/131,000 characters mid-session, every uncached sentence 401'd, and each
call site quietly fell back to the OpenAI ``echo`` voice — so an answer switched
between Panganiban and a stranger sentence by sentence. app/voice_guard.py
stops the stranger. This module is what speaks instead: Fish model "CJAP" is a
clone of the SAME person, so unlike ``echo`` it is an acceptable stand-in.

Since the user's "prioritize fish.audio voice" (same day) this is the FIRST
clone tried, with ElevenLabs as the fallback behind it — see
speech_engines.engine_order() / ``CJ_TTS_ORDER``.

Credentials come from the environment (app/.env on the robot):
``FISH_API_KEY`` and ``FISH_MODEL_ID``. Absent = this clone is simply not
configured and engine_order() skips it, which is not an error — this file must
never stop a robot booting.

VERIFIED against a live synthesis 2026-09-16 (``scripts/fish_check.py``, which
is the way to re-verify after any change here). What the endpoint actually
returns on this account: **200, ``audio/wav``, a RIFF container, 24 kHz mono**
— it honours ``sample_rate``, so the resample below is a no-op in practice and
stays only as insurance. ``prosody.speed`` works and is monotonic (0.90 →
6.82 s, none → 5.94 s, 1.15 → 5.36 s for the same sentence).

⚠ It is SLOW. Measured on the CM4 against ElevenLabs, same four unseen
sentences: **Fish 1.78 s warm median, ElevenLabs 0.47 s** — roughly 3.8x. Since
synthesis stays well under playback (a ~4 s sentence renders in ~1.8 s) the
one-ahead pipeline keeps up and answers do not gap mid-way; the cost lands
almost entirely on TIME-TO-FIRST-AUDIO, about +1.3 s per turn. The dynamic
filler covers some of it and the clip cache makes every repeat free. If that
becomes the thing to fix, the lever is ``CJ_TTS_ORDER`` (or the /maintain
engine card), not this file.

Before 2026-09-16 the account had zero API credit and every call 402'd. Fish
bills API credit SEPARATELY from platform credit — if synthesis starts failing
with 402 while the Fish dashboard shows a balance, that is why: top up at
https://fish.audio/app/developers.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import time

import numpy as np
import requests

from . import audio

log = logging.getLogger("voice.fish")

API_URL = "https://api.fish.audio/v1/tts"
# The same synthesis as a Server-Sent-Events stream that also carries WORD
# timings (2026-09-16). Without them a Fish sentence reached the captions with
# no `words`, so /audience and /face-display showed the whole sentence at once
# instead of revealing each word as it is spoken. Verified live on this account
# with model s1: raw 24 kHz s16le chunks + cumulative per-chunk_seq snapshots
# of {"segments": [{"text", "start", "end"}]}, punctuation stripped. It was
# also faster than the plain endpoint (2.0 s vs 2.9 s, same sentence, cold).
STREAM_URL = "https://api.fish.audio/v1/tts/stream/with-timestamp"
# 0 = use the plain endpoint and return no word timings (the pre-09-16 path).
WORD_TIMINGS = os.environ.get("FISH_WORD_TIMINGS", "1") != "0"
# Fish's backend speech model, sent as a header (not the cloned voice — that is
# reference_id). "s1" is their current flagship; "speech-1.6" is the fallback
# generation if s1 is ever withdrawn for this account.
SPEECH_MODEL = os.environ.get("FISH_SPEECH_MODEL", "s1")
REQUEST_TIMEOUT_S = float(os.environ.get("FISH_TIMEOUT_S", "15"))
MAX_RETRIES = int(os.environ.get("FISH_MAX_RETRIES", "2"))

# Keep-alive across sentences, exactly as voice.speak does: a fresh TLS
# handshake costs ~0.3-0.7 s each on the CM4.
_session = requests.Session()


class FishError(Exception):
    """Fish Audio synthesis failed. ``.reason`` matches voice.speak.SynthError
    (quota | network | error) so the voice guard reads both the same way.
    Never contains the API key."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(detail or reason)
        self.reason = reason


def api_key() -> str:
    return os.environ.get("FISH_API_KEY", "").strip()


def model_id() -> str:
    return os.environ.get("FISH_MODEL_ID", "").strip()


def configured() -> bool:
    """True when both credentials are present. Which clone is tried FIRST, and
    whether this one is tried at all, is speech_engines.engine_order()
    (``CJ_TTS_ORDER``) — this only says "the credentials exist"."""
    return bool(api_key() and model_id())


def _decode(raw: bytes) -> tuple[np.ndarray, int]:
    """Whatever container Fish returned → (mono float32, sample_rate).

    soundfile handles wav/flac natively. The defensiveness is deliberate: see
    the module docstring — no one has yet seen a 200 from this endpoint on
    this account."""
    import soundfile as sf
    try:
        pcm, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
    except Exception as e:
        raise FishError("error", f"undecodable audio ({type(e).__name__})")
    pcm = np.asarray(pcm, dtype=np.float32)
    if pcm.ndim > 1:                      # stereo → mono
        pcm = pcm.mean(axis=1).astype(np.float32)
    if pcm.size == 0:
        raise FishError("error", "empty audio response")
    return pcm, int(sr)


def _reason_for(status: int) -> str:
    if status == 402:                     # insufficient API credit — the live case
        return "quota"
    if status == 429:
        return "quota"
    if status in (401, 403):
        return "error"
    if 500 <= status < 600:
        return "network"
    return "error"


def _body(text: str, speed: float | None, fmt: str) -> dict:
    body = {
        "text": text,
        "reference_id": model_id(),
        "format": fmt,
        "sample_rate": audio.SYNTH_SAMPLE_RATE,
        "normalize": True,
        "latency": "normal",        # "balanced" is faster and rougher
    }
    if speed is not None:           # Fish takes a multiplier like ElevenLabs
        body["prosody"] = {"speed": round(min(1.2, max(0.7, float(speed))), 3)}
    return body


def _post(url: str, body: dict, stream: bool = False):
    """POST with the retry policy; returns a 200 response or raises FishError."""
    key = api_key()
    headers = {"Authorization": f"Bearer {key}", "model": SPEECH_MODEL,
               "Content-Type": "application/json"}
    last_detail = "unknown"
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = _session.post(url, headers=headers, json=body,
                                 timeout=REQUEST_TIMEOUT_S, stream=stream)
        except (requests.ConnectionError, requests.Timeout) as e:
            last_detail = type(e).__name__
            log.warning("Fish request failed (%s), attempt %d/%d",
                        last_detail, attempt + 1, MAX_RETRIES + 1)
            if attempt < MAX_RETRIES:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise FishError("network", last_detail)

        if resp.status_code == 200:
            return resp

        if 500 <= resp.status_code < 600 and attempt < MAX_RETRIES:
            last_detail = f"server error {resp.status_code}"
            log.warning("Fish %s, attempt %d/%d", last_detail,
                        attempt + 1, MAX_RETRIES + 1)
            time.sleep(1.0 * (2 ** attempt))
            continue

        # Surface the vendor's own machine-readable message; the body carries
        # no secrets, and 402 in particular needs its exact wording in the log
        # because "credit" means two different balances at Fish.
        detail = ""
        try:
            detail = str(resp.json().get("message", ""))[:160]
        except Exception:
            detail = resp.text[:160]
        reason = _reason_for(resp.status_code)
        if resp.status_code == 402:
            log.error("Fish 402: API credit is exhausted. Fish bills API credit "
                      "SEPARATELY from platform credit — top up at "
                      "https://fish.audio/app/developers")
        else:
            log.error("Fish request rejected: HTTP %d %s", resp.status_code, detail)
        err = FishError(reason, f"http {resp.status_code}: {detail}" if detail
                        else f"http {resp.status_code}")
        err.status = resp.status_code
        raise err

    raise FishError("error", last_detail)  # unreachable, defensive


def _read_stream(resp) -> tuple[np.ndarray, list]:
    """SSE body → (float32 PCM at SYNTH_SAMPLE_RATE, [[seg_text, start, end]]
    on the whole clip's timeline)."""
    raw = bytearray()
    snaps: dict = {}              # chunk_seq -> (offset_s, segments), latest wins
    try:
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            try:
                ev = json.loads(line[5:].strip())
            except ValueError:
                continue
            if ev.get("audio_base64"):
                raw += base64.b64decode(ev["audio_base64"])
            al = ev.get("alignment")
            if isinstance(al, dict) and al.get("segments") is not None:
                snaps[ev.get("chunk_seq", 0)] = (
                    float(ev.get("chunk_audio_offset_sec") or 0.0), al["segments"])
    except (requests.RequestException, ValueError) as e:
        raise FishError("network", f"stream broke ({type(e).__name__})")
    finally:
        resp.close()
    if len(raw) < 2:
        raise FishError("error", "empty audio response")
    pcm = np.frombuffer(bytes(raw[: len(raw) // 2 * 2]), dtype="<i2")
    pcm = (pcm.astype(np.float32) / 32768.0)
    segs = []
    for seq in sorted(snaps, key=lambda k: (k is None, k)):
        off, items = snaps[seq]
        for it in items:
            try:
                segs.append([str(it["text"]), round(off + float(it["start"]), 3),
                             round(off + float(it["end"]), 3)])
            except (KeyError, TypeError, ValueError):
                continue
    return pcm, segs


def _key(word: str) -> str:
    return re.sub(r"[\W_]+", "", word.lower())


def _spread(toks: list, t0: float, t1: float) -> list:
    """Place tokens over [t0, t1] by letter count — the estimate for words the
    stream did not time."""
    wt = [max(1, len(_key(t))) for t in toks]
    tot, c, out = float(sum(wt)), 0, []
    for t, w in zip(toks, wt):
        s0 = t0 + (t1 - t0) * c / tot
        c += w
        out.append([t, round(s0, 3), round(t0 + (t1 - t0) * c / tot, 3)])
    return out


def words_from_segments(text: str, segs: list, dur: float | None = None) -> list:
    """Fish segments (punctuation stripped) → [[word, start, end]] over the
    ORIGINAL tokens of `text`, so the captions read "afternoon." with its
    full stop, exactly as the ElevenLabs sidecar does. A token that spans
    several segments ("Court's" → "Court", "s") takes their union; a
    pure-punctuation token ("—") rides on the word before it.

    From the first token the segments cannot account for (text normalisation
    spelled a number out, or the stream simply stopped timing), the remaining
    tokens are spread over the remaining audio — up to `dur`, the clip length —
    so every word of the sentence still appears, and appears no earlier than
    the last word that WAS timed."""
    toks = text.split()
    sk = [_key(s[0]) for s in segs]
    out, j, lead = [], 0, ""
    for i, tok in enumerate(toks):
        k = _key(tok)
        if not k:
            if out:
                out[-1][0] += " " + tok
            else:
                lead += tok + " "
            continue
        while j < len(sk) and not sk[j]:          # a segment with no letters
            j += 1
        joined, end = "", j
        while end < len(sk) and len(joined) < len(k) and k.startswith(joined + sk[end]):
            joined += sk[end]
            end += 1
        if joined != k:
            rest = toks[i:]
            t0 = segs[j][1] if j < len(segs) else (out[-1][2] if out else 0.0)
            t1 = max(t0, float(dur) if dur else (segs[-1][2] if segs else t0))
            if t1 - t0 < 0.05 * len(rest):        # no audio left to spread over
                t1 = t0 + 0.25 * len(rest)
            out += _spread(rest, t0, t1)
            break
        out.append([lead + tok, segs[j][1], segs[end - 1][2]])
        lead, j = "", end
    return out


def synthesize(text: str, speed: float | None = None,
               words_out: list | None = None) -> np.ndarray:
    """One Fish call → float32 PCM at audio.SYNTH_SAMPLE_RATE, post-processed
    for the robot's driver exactly as the ElevenLabs path is, so a sentence
    that falls between the two clones matches the ones around it in level and
    tone. Raises FishError; never leaks the key.

    words_out: pass a list to receive [[word, start_s, end_s], ...] — the same
    shape as the ElevenLabs sidecar. It stays empty if the timestamp endpoint
    is unavailable; the audio is still returned from the plain endpoint.
    audio.process() filters and scales but never trims, so the timings hold."""
    if not api_key() or not model_id():
        raise FishError("error", "FISH_API_KEY or FISH_MODEL_ID not set")

    if words_out is not None and WORD_TIMINGS:
        try:
            pcm, segs = _read_stream(_post(STREAM_URL, _body(text, speed, "pcm"),
                                           stream=True))
            words_out[:] = (words_from_segments(
                text, segs, pcm.size / float(audio.SYNTH_SAMPLE_RATE))
                if segs else [])
            return audio.process(pcm, audio.SYNTH_SAMPLE_RATE)
        except FishError as e:
            # quota and network will fail the plain endpoint the same way; a
            # rejection of THIS endpoint (withdrawn, schema change) will not
            if e.reason != "error" or getattr(e, "status", None) in (401, 403):
                raise
            log.warning("Fish timestamp endpoint unusable (%s) — plain synthesis, "
                        "no word timings", e)

    resp = _post(API_URL, _body(text, speed, "wav"))
    pcm, sr = _decode(resp.content)
    if sr != audio.SYNTH_SAMPLE_RATE:
        pcm = audio.resample(pcm, sr, audio.SYNTH_SAMPLE_RATE)
    return audio.process(pcm, audio.SYNTH_SAMPLE_RATE)
