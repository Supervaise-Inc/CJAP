"""Verify the Fish Audio clone end to end — the step that turns voice/fish.py
from "written to the documented contract" into "seen working".

    app/.venv/bin/python scripts/fish_check.py [--play] ["text to say"]

Checks, in order, stopping at the first that fails:
  1. credentials present (FISH_API_KEY / FISH_MODEL_ID from app/.env)
  2. GET /wallet/self/api-credit   — the balance that 402s when empty
  3. GET /model/<id>               — the clone exists and is trained
  4. POST /v1/tts                  — a real synthesis, written to a wav
  5. the wav decodes at our sample rate and has plausible duration

Written 2026-09-16, when steps 1-3 passed and step 4 returned
**402 Insufficient API credit**: Fish bills API credit SEPARATELY from platform
credit. Top up at https://fish.audio/app/developers and run this again.

Costs one short synthesis (step 4) when the balance is non-zero.
"""
from __future__ import annotations

import functools
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

try:  # credentials live in app/.env on the robot
    from dotenv import load_dotenv
    load_dotenv(ROOT / "app" / ".env")
except Exception:
    pass

from voice import fish  # noqa: E402

print = functools.partial(print, flush=True)   # interleave with voice.fish's logging

TEXT = "Good afternoon. I am Artemio Panganiban, and this is my own voice."
OUT = "/dev/shm/fish_check.wav"


def _get(path, key):
    req = urllib.request.Request("https://api.fish.audio" + path,
                                 headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode(errors="replace")
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def main() -> int:
    argv = [a for a in sys.argv[1:]]
    play = "--play" in argv
    if play:
        argv.remove("--play")
    text = argv[0] if argv else TEXT

    print("1. credentials")
    if not fish.configured():
        print("   ✗ FISH_API_KEY / FISH_MODEL_ID not set in app/.env")
        return 1
    key = fish.api_key()
    print(f"   ✓ key …{key[-4:]}, model {fish.model_id()}")

    print("2. API credit")
    st, d = _get("/wallet/self/api-credit", key)
    if st != 200:
        print(f"   ✗ HTTP {st}: {d}")
        return 1
    raw = d.get("credit") if isinstance(d, dict) else None
    try:  # the API returns it as a decimal STRING, e.g. "0.000000"
        credit = float(raw)
    except (TypeError, ValueError):
        credit = 0.0
    print(f"   {'✓' if credit > 0 else '✗'} balance: {raw}")
    if credit <= 0:
        print("     Fish bills API credit SEPARATELY from platform credit —")
        print("     top up at https://fish.audio/app/developers, then re-run.")
        print("     Until then engine_order() still lists fish first and every")
        print("     sentence falls through to the next clone.")
        return 1

    print("3. the clone")
    st, d = _get(f"/model/{fish.model_id()}", key)
    if st != 200:
        print(f"   ✗ HTTP {st}: {d}")
        return 1
    print(f"   ✓ {d.get('title')!r} state={d.get('state')} "
          f"type={d.get('type')} languages={d.get('languages')}")
    if d.get("state") != "trained":
        print("   ✗ the model is not trained yet")
        return 1

    print("4. synthesis")
    t0 = time.time()
    try:
        pcm = fish.synthesize(text)
    except fish.FishError as e:
        print(f"   ✗ {e.reason}: {e}")
        return 1
    secs = time.time() - t0
    print(f"   ✓ {pcm.size} samples in {secs:.1f}s")

    print("5. the audio")
    import soundfile as sf
    sr = fish.audio.SYNTH_SAMPLE_RATE
    sf.write(OUT, pcm, sr, subtype="PCM_16")
    dur = pcm.size / float(sr)
    chars_per_s = len(text) / dur if dur else 0
    print(f"   ✓ {OUT}: {dur:.1f}s at {sr} Hz ({chars_per_s:.1f} chars/s)")
    if not 1.5 <= chars_per_s <= 30:
        print("   ⚠ that pace looks wrong — listen before trusting it")
    if play:
        import subprocess
        subprocess.run(["aplay", "-q", OUT])
    print("\nFish is working. Re-run this after any change to voice/fish.py — the "
          "docstring's measured facts (format, sample rate, speed, latency) are "
          "what it verifies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
