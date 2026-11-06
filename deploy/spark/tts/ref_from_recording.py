#!/usr/bin/env python3
"""Make the cjap-tts voice reference from a REAL recording of Justice Panganiban.

    app/.venv/bin/python deploy/spark/tts/ref_from_recording.py REC OUT_DIR
    app/.venv/bin/python deploy/spark/tts/ref_from_recording.py REC OUT_DIR --pick 2
    app/.venv/bin/python deploy/spark/tts/ref_from_recording.py REC OUT_DIR --start 41.2 --end 54.0

REC is any file ffmpeg reads (e.g. Recording_four.aac, the 3 min 16 s recording the
Fish Audio "CJAP" model was trained on). Run it with CJAP's venv from the checkout:
it reads OPENAI_BASE_URL / OPENAI_API_KEY from app/.env and transcribes through the
Spark's own Whisper (LiteLLM model `whisper`), so the recording never leaves the box.

1. Transcribes the whole recording with timestamps (OUT_DIR/source_transcript.json).
2. Finds continuous stretches of 10-15 s (whole Whisper segments, pauses under
   0.7 s, no near-silent segment) and ranks them by Whisper's confidence. Prints
   the best five; the first is used unless --pick N or --start/--end is given.
3. Cuts that stretch to OUT_DIR/ref.wav (24 kHz mono PCM_16, no other processing)
   and transcribes the CUT again, writing the text to OUT_DIR/ref.txt.

Then LISTEN to ref.wav and correct ref.txt by hand where Whisper misheard: the
clone needs the transcript to match the audio word for word.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LO_S, HI_S, MAX_GAP_S = 10.0, 15.0, 0.7


def load_env() -> None:
    env = ROOT / "app" / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def ffmpeg_bin() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def cut(rec: str, start: float, end: float, out_wav: Path) -> None:
    subprocess.run([ffmpeg_bin(), "-y", "-loglevel", "error", "-ss", f"{start:.3f}",
                    "-to", f"{end:.3f}", "-i", rec, "-ac", "1", "-ar", "24000",
                    "-c:a", "pcm_s16le", str(out_wav)], check=True)


def as_dict(resp):
    if isinstance(resp, (dict, list)):
        return resp
    if isinstance(resp, str):
        return json.loads(resp)
    if hasattr(resp, "model_dump"):
        return resp.model_dump()
    return json.loads(str(resp))


def transcribe(path: str, verbose: bool):
    from openai import OpenAI
    base, key = os.environ.get("OPENAI_BASE_URL", ""), os.environ.get("OPENAI_API_KEY", "")
    if not base or not key:
        sys.exit("OPENAI_BASE_URL / OPENAI_API_KEY are not set in app/.env (runbook step 6)")
    client = OpenAI(base_url=base, api_key=key, timeout=600)
    with open(path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model=os.environ.get("OPENAI_STT_MODEL", "whisper"), file=f, language="en",
            response_format="verbose_json" if verbose else "text")
    if not verbose:
        text = resp if isinstance(resp, str) else getattr(resp, "text", str(resp))
        text = text.strip()
        if text.startswith("{"):
            text = str(json.loads(text).get("text", "")).strip()
        return " ".join(text.split())
    return as_dict(resp)


def windows(segs: list) -> list:
    """Continuous runs of whole segments lasting LO_S..HI_S, best first."""
    out = []
    for i in range(len(segs)):
        for j in range(i, len(segs)):
            if j > i and segs[j]["start"] - segs[j - 1]["end"] > MAX_GAP_S:
                break
            if segs[j].get("no_speech_prob", 0) > 0.3:
                break
            dur = segs[j]["end"] - segs[i]["start"]
            if dur > HI_S:
                break
            if dur >= LO_S:
                run = segs[i:j + 1]
                score = sum(s.get("avg_logprob", -1.0) for s in run) / len(run)
                out.append({"start": segs[i]["start"], "end": segs[j]["end"], "score": score,
                            "text": " ".join(s["text"].strip() for s in run)})
    out.sort(key=lambda w: w["score"], reverse=True)
    picked = []
    for w in out:                                   # non-overlapping, best first
        if all(w["end"] <= p["start"] or w["start"] >= p["end"] for p in picked):
            picked.append(w)
    return picked[:5]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rec")
    ap.add_argument("out_dir")
    ap.add_argument("--pick", type=int, default=1, help="use candidate N (1 = best)")
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    a = ap.parse_args()
    load_env()
    out = Path(a.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    if a.start is None or a.end is None:
        print("transcribing the whole recording with timestamps (a minute or two)...", flush=True)
        full = transcribe(a.rec, verbose=True)
        (out / "source_transcript.json").write_text(json.dumps(full, indent=1), encoding="utf-8")
        segs = [s for s in full.get("segments", []) if s.get("end", 0) > s.get("start", 0)]
        if not segs:
            sys.exit("Whisper returned no segments with timestamps; use --start/--end instead "
                     "(times from listening), see source_transcript.json for the text")
        cands = windows(segs)
        if not cands:
            sys.exit("no continuous 10-15 s stretch found; pick one by ear with --start/--end")
        for n, w in enumerate(cands, 1):
            print(f"{n}. {w['start']:7.2f}-{w['end']:7.2f} s ({w['end'] - w['start']:4.1f} s, "
                  f"confidence {w['score']:.2f}): {w['text'][:110]}")
        if not 1 <= a.pick <= len(cands):
            sys.exit(f"--pick must be 1..{len(cands)}")
        start, end = cands[a.pick - 1]["start"], cands[a.pick - 1]["end"]
    else:
        start, end = a.start, a.end

    wav = out / "ref.wav"
    cut(a.rec, max(0.0, start - 0.05), end + 0.15, wav)
    text = transcribe(str(wav), verbose=False)
    (out / "ref.txt").write_text(text + "\n", encoding="utf-8")
    print(f"\nref.wav: {start:.2f}-{end:.2f} s of {a.rec}")
    print(f"ref.txt: {text}")
    print("Now LISTEN to ref.wav and fix ref.txt where it differs from what is said.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
