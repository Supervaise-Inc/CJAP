"""voice.qwen — the LOCAL clone of the CJ voice: Qwen3-TTS on the DGX Spark.

    from voice.qwen import synthesize, QwenError, configured, model_id

synthesize(text, speed=…) → float32 PCM at audio.SYNTH_SAMPLE_RATE; raises
QwenError, which carries the same ``.reason`` vocabulary as voice.fish's
FishError and voice.speak's SynthError (quota | network | error), so
app/voice_guard.py reads it without caring which engine failed.

Why (2026-11-05): CJAP moved from the robot's Pi onto a DGX Spark with a
Reachy Mini Lite on USB-C, and the voice moved from Fish Audio / ElevenLabs to
a Qwen3-TTS clone served on the Spark's GPU by the ``cjap-tts`` container
(``deploy/spark/compose``, see docs/spark/RUNBOOK.md). It is a clone of
the SAME person, so voice_guard accepts it; ``CJ_TTS_ORDER=spark`` makes it the
only voice, which keeps "silence rather than a different voice" true.

The server contract (cjap-tts, tts_server.py):
    GET  {URL}/health  → {"ok": true, "model": "...", "ref": "<sha256[:12]>"}
    POST {URL}/v1/tts  {"text": str, "speed": float|null} → audio/wav
                       24 kHz mono PCM_16 (any rate/channels are tolerated)

Configuration (app/.env): ``CJ_QWEN_TTS_URL`` (e.g. http://127.0.0.1:8091).
Absent = this clone is simply not configured and engine_order() skips it, which
is not an error — this file must never stop a robot booting.

Word timings: Qwen3-TTS returns none. ``words_out`` is filled by spreading the
sentence's own tokens over the clip by letter count (the same estimate
voice.fish uses for words its stream did not time), so the captions advance
word by word, close to but not exactly on the voice.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import time

import numpy as np
import requests

from . import audio

log = logging.getLogger("voice.qwen")

REQUEST_TIMEOUT_S = float(os.environ.get("CJ_QWEN_TTS_TIMEOUT_S", "20"))
MAX_RETRIES = int(os.environ.get("CJ_QWEN_TTS_RETRIES", "1"))
# The server returns the raw model output; the same robot-driver chain as the
# cloud clones (high-pass, presence, -16 LUFS) runs here, so a Spark sentence
# matches the pre-rendered ElevenLabs fillers around it in level and tone.
POSTPROCESS = os.environ.get("CJ_QWEN_TTS_POSTPROCESS", "1") != "0"


class QwenError(Exception):
    """reason ∈ {quota, network, error} — the voice_guard vocabulary. The local
    server has no quota, so only network and error ever occur."""

    def __init__(self, reason: str, detail: str = "", status: int | None = None):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
        self.status = status


def url() -> str:
    return os.environ.get("CJ_QWEN_TTS_URL", "").strip().rstrip("/")


def configured() -> bool:
    """True when the server URL is set. Whether this clone is tried at all is
    speech_engines.engine_order() (``CJ_TTS_ORDER``)."""
    return bool(url())


_MODEL_TAG = {"tag": None, "ts": 0.0}


def model_id() -> str:
    """'<model>:<reference hash>' from the server's /health, cached for 60 s.
    It is part of the clip-cache key, so a new reference recording (or model)
    never serves sentences cached in the old voice. If the server cannot be
    asked, the last known tag is kept; with none at all, a fixed placeholder is
    used and the synthesis call that follows reports the real failure."""
    now = time.monotonic()
    if _MODEL_TAG["tag"] and now - _MODEL_TAG["ts"] < 60:
        return _MODEL_TAG["tag"]
    try:
        r = requests.get(f"{url()}/health", timeout=3)
        j = r.json() if r.ok else {}
        tag = f"{j.get('model', 'qwen3-tts')}:{j.get('ref', 'noref')}"
        _MODEL_TAG.update(tag=tag, ts=now)
    except Exception:
        if not _MODEL_TAG["tag"]:
            return "qwen3-tts:unknown"
    return _MODEL_TAG["tag"]


def _decode(raw: bytes) -> tuple[np.ndarray, int]:
    import soundfile as sf
    try:
        pcm, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
    except Exception as e:
        raise QwenError("error", f"undecodable audio ({type(e).__name__})")
    pcm = np.asarray(pcm, dtype=np.float32)
    if pcm.ndim > 1:
        pcm = pcm.mean(axis=1).astype(np.float32)
    if pcm.size == 0:
        raise QwenError("error", "empty audio response")
    return pcm, int(sr)


def _post(text: str, speed: float | None) -> bytes:
    if not configured():
        raise QwenError("error", "CJ_QWEN_TTS_URL not set")
    body = {"text": text, "speed": speed}
    last = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(f"{url()}/v1/tts", json=body, timeout=REQUEST_TIMEOUT_S)
        except (requests.ConnectionError, requests.Timeout) as e:
            last = QwenError("network", type(e).__name__)
        else:
            if r.status_code == 200:
                return r.content
            detail = ""
            try:
                detail = str(r.json().get("detail", ""))[:120]
            except ValueError:
                detail = r.text[:120]
            last = QwenError("error" if r.status_code < 500 else "network",
                             f"HTTP {r.status_code} {detail}".strip(), r.status_code)
            if r.status_code < 500:
                break                       # a 4xx will not change on retry
        if attempt < MAX_RETRIES:
            time.sleep(0.3 * (attempt + 1))
    raise last


def _key(word: str) -> str:
    return re.sub(r"[\W_]+", "", word.lower())


def spread_words(text: str, dur: float) -> list:
    """[[word, start_s, end_s], ...] over [0, dur] by letter count; a
    pure-punctuation token rides on the word before it."""
    toks = text.split()
    out, lead = [], ""
    words = []
    for tok in toks:
        if not _key(tok):
            if words:
                words[-1] += " " + tok
            else:
                lead += tok + " "
            continue
        words.append(lead + tok)
        lead = ""
    if not words or dur <= 0:
        return []
    wt = [max(1, len(_key(w))) for w in words]
    tot, c = float(sum(wt)), 0
    for w, n in zip(words, wt):
        s0 = dur * c / tot
        c += n
        out.append([w, round(s0, 3), round(dur * c / tot, 3)])
    return out


def synthesize(text: str, speed: float | None = None,
               words_out: list | None = None) -> np.ndarray:
    """One local call → float32 PCM at audio.SYNTH_SAMPLE_RATE, post-processed
    for the robot's driver like the cloud clones. Raises QwenError."""
    pcm, sr = _decode(_post(text, speed))
    if sr != audio.SYNTH_SAMPLE_RATE:
        pcm = audio.resample(pcm, sr, audio.SYNTH_SAMPLE_RATE)
    if POSTPROCESS:
        pcm = audio.process(pcm, audio.SYNTH_SAMPLE_RATE)
    if words_out is not None:
        words_out[:] = spread_words(text, pcm.size / float(audio.SYNTH_SAMPLE_RATE))
    return pcm
