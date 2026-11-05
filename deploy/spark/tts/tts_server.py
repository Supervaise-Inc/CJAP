"""cjap-tts — Panganiban's local voice: Qwen3-TTS (faster-qwen3-tts) on the DGX Spark.

The CJAP robot app calls this through voice/qwen.py (engine "spark"):

    GET  /health  -> {"ok": true, "model": "...", "ref": "<sha256[:12]>", ...}
    POST /v1/tts  {"text": str, "speed": float|null} -> audio/wav, mono PCM_16
                  at the model rate (24 kHz). Headers X-Synth-S, X-Audio-S.

One sentence per request, the whole sentence at once (no streaming): CJAP
synthesizes one sentence ahead of playback, and the full-text prefill
(non_streaming_mode=True) is the setting the faster-qwen3-tts Spark author
gave as the fix for timbre drift on long utterances.

`speed` is accepted and ignored: Qwen3-TTS has no speed control, and CJAP's own
tempo smoothing (speech_tempo / WSOLA) already adjusts pace after synthesis.

Settings (environment, see docker-compose.yml):
    TTS_MODEL        local model dir (offline), default /models/Qwen3-TTS-12Hz-1.7B-Base
    TTS_REF_WAV      reference clip, default /voices/ref.wav
    TTS_REF_TXT      its exact transcript, default /voices/ref.txt
    TTS_LANGUAGE     default English
    TTS_XVEC_ONLY    1 = speaker embedding only (no transcript needed), default 0
    TTS_TEMPERATURE / TTS_TOP_K / TTS_TOP_P   default 0.7 / 50 / 0.85
    TTS_SEED         fixed seed per request (same text -> same take), default 4242; 0 = off
    TTS_MAX_CHARS    longest accepted sentence, default 600
"""
from __future__ import annotations

import hashlib
import io
import os
import threading
import time

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from faster_qwen3_tts import FasterQwen3TTS

MODEL = os.environ.get("TTS_MODEL", "/models/Qwen3-TTS-12Hz-1.7B-Base")
REF_WAV = os.environ.get("TTS_REF_WAV", "/voices/ref.wav")
REF_TXT = os.environ.get("TTS_REF_TXT", "/voices/ref.txt")
LANGUAGE = os.environ.get("TTS_LANGUAGE", "English")
XVEC_ONLY = os.environ.get("TTS_XVEC_ONLY", "0") == "1"
TEMPERATURE = float(os.environ.get("TTS_TEMPERATURE", "0.7"))
TOP_K = int(os.environ.get("TTS_TOP_K", "50"))
TOP_P = float(os.environ.get("TTS_TOP_P", "0.85"))
SEED = int(os.environ.get("TTS_SEED", "4242"))
MAX_CHARS = int(os.environ.get("TTS_MAX_CHARS", "600"))

app = FastAPI(title="cjap-tts")
_lock = threading.Lock()          # one generation at a time: CUDA graphs are not re-entrant
_state = {"model": None, "ref_text": "", "ref": "", "loaded_s": None,
          "warm_s": None, "count": 0, "last_synth_s": None, "error": None}


def _ref_hash() -> str:
    h = hashlib.sha256()
    with open(REF_WAV, "rb") as f:
        h.update(f.read())
    h.update(_state["ref_text"].encode("utf-8"))
    h.update(f"{LANGUAGE}|{XVEC_ONLY}".encode())
    return h.hexdigest()[:12]


def _generate(text: str) -> tuple[np.ndarray, int]:
    m = _state["model"]
    if SEED:
        torch.manual_seed(SEED)
    wavs, sr = m.generate_voice_clone(
        text=text,
        language=LANGUAGE,
        ref_audio=REF_WAV,
        ref_text="" if XVEC_ONLY else _state["ref_text"],
        xvec_only=XVEC_ONLY,
        non_streaming_mode=True,
        temperature=TEMPERATURE,
        top_k=TOP_K,
        top_p=TOP_P,
    )
    parts = [np.asarray(w, dtype=np.float32).reshape(-1) for w in wavs]
    audio = np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
    return audio, int(sr)


@app.on_event("startup")
def _load() -> None:
    t0 = time.monotonic()
    if not XVEC_ONLY:
        with open(REF_TXT, encoding="utf-8") as f:
            _state["ref_text"] = " ".join(f.read().split())
    _state["ref"] = _ref_hash()
    _state["model"] = FasterQwen3TTS.from_pretrained(
        MODEL, device="cuda", dtype=torch.bfloat16, local_files_only=True)
    _state["loaded_s"] = round(time.monotonic() - t0, 1)
    t1 = time.monotonic()
    _state["model"].warmup(prefill_len=100)          # captures the CUDA graphs
    with _lock:                                      # caches this voice's prompt
        _generate("Good afternoon. Thank you for coming.")
    _state["warm_s"] = round(time.monotonic() - t1, 1)
    print(f"[cjap-tts] ready: model {MODEL} loaded in {_state['loaded_s']} s, "
          f"warm in {_state['warm_s']} s, ref {_state['ref']}", flush=True)


class TTSRequest(BaseModel):
    text: str
    speed: float | None = None


@app.get("/health")
def health():
    ok = _state["model"] is not None and _state["warm_s"] is not None
    body = {"ok": ok, "model": os.path.basename(MODEL.rstrip("/")), "ref": _state["ref"],
            "language": LANGUAGE, "xvec_only": XVEC_ONLY, "loaded_s": _state["loaded_s"],
            "warm_s": _state["warm_s"], "count": _state["count"],
            "last_synth_s": _state["last_synth_s"], "error": _state["error"]}
    return JSONResponse(body, status_code=200 if ok else 503)


@app.post("/v1/tts")
def tts(req: TTSRequest):
    text = " ".join((req.text or "").split())
    if not text:
        raise HTTPException(400, "empty text")
    if len(text) > MAX_CHARS:
        raise HTTPException(413, f"text longer than {MAX_CHARS} characters")
    if _state["model"] is None:
        raise HTTPException(503, "model not loaded yet")
    t0 = time.monotonic()
    try:
        with _lock:
            audio, sr = _generate(text)
    except Exception as e:                            # report, never crash the server
        _state["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        raise HTTPException(500, _state["error"])
    synth_s = time.monotonic() - t0
    if audio.size == 0:
        raise HTTPException(500, "model returned no audio")
    peak = float(np.max(np.abs(audio)))
    if peak > 1.0:
        audio = audio / peak
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
    _state["count"] += 1
    _state["last_synth_s"] = round(synth_s, 3)
    _state["error"] = None
    return Response(buf.getvalue(), media_type="audio/wav",
                    headers={"X-Synth-S": f"{synth_s:.3f}",
                             "X-Audio-S": f"{audio.size / sr:.3f}"})
