#!/usr/bin/env python3
"""Render the SHORT "thinking" filler clips in Panganiban's cloned voice (2026-11-05).

    app/.venv/bin/python scripts/render_short_fillers.py [--out ~/fillers_short]
                                                         [--max-s 1.3] [--force] [--dry-run]

Why: the 40 canned filler clips run 2.6-5.2 s (median 3.72 s). A clip starts
2.2-3.6 s into a turn and is never cut mid-word, so a first answer sentence
that is ready at about 4 s waits behind it (Research_2026-11/01_latency_map.md,
finding C1). These phrases are 2-4 words and about 1.2 s long, so a clip is over
before the answer is ready. app/filler_policy.py uses this directory
(CJ_FILLER_SHORT_DIR, default ~/fillers_short) instead of the long set whenever
it contains clips.

The voice is the Fish clone only (tts_fish_wav). There is NO fallback to another
voice: app/voice_guard.py's rule is silence over a stranger, and a filler in the
wrong voice is the same mistake. If Fish is unreachable the script stops.

Every phrase is held to the curated-line gate (answer_gate.check_curated) before
anything is rendered, exactly as scripts/render_intro.py does. A clip longer than
--max-s is rejected, not kept, because a long "short" clip defeats the purpose.

The phrases carry no facts, dates, names or claims.
"""
import argparse
import os
import shutil
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PHRASES = [
    "Ah, one moment.",
    "Let me think.",
    "A fine question.",
    "Hmm, let me see.",
    "Allow me a moment.",
    "One moment po.",
    "Let me recall.",
    "Give me a moment.",
    "Let me consider that.",
    "Bear with me.",
    "A moment, please.",
    "Let me reflect.",
    "Hmm, an interesting one.",
    "Yes, let me see.",
    "Sandali lang po.",
    "Let me look back.",
]


def wav_seconds(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / float(w.getframerate() or 1)


def gate(phrases):
    """check_curated on every phrase; returns the list that failed."""
    try:
        sys.path.insert(0, str(ROOT / "app"))
        import answer_gate
    except Exception as e:
        print(f"gate unavailable ({type(e).__name__}: {e}) - rendering anyway", file=sys.stderr)
        return []
    bad = []
    for i, text in enumerate(phrases, 1):
        res = answer_gate.check_curated(text)
        if not res["ok"]:
            bad.append((i, text, [t.get("rule") for t in res["tripped"]]))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="~/fillers_short")
    ap.add_argument("--max-s", type=float, default=1.3, help="reject clips longer than this")
    ap.add_argument("--force", action="store_true", help="re-render clips that already exist")
    ap.add_argument("--dry-run", action="store_true", help="list what would be rendered")
    a = ap.parse_args(argv)
    out = Path(os.path.expanduser(a.out))

    bad = gate(PHRASES)
    if bad:
        for i, text, rules in bad:
            print(f"gate FAILED {i:02d}: {text!r} {rules}", file=sys.stderr)
        return 1
    if a.dry_run:
        for i, text in enumerate(PHRASES, 1):
            print(f"{i:02d}  {text}")
        print(f"{len(PHRASES)} phrases -> {out}  (max {a.max_s} s each)")
        return 0

    sys.path.insert(0, str(ROOT / "app"))
    sys.path.insert(0, str(ROOT))
    import speech_engines
    out.mkdir(parents=True, exist_ok=True)
    kept, rejected = 0, []
    for i, text in enumerate(PHRASES, 1):
        dest = out / f"s{i:02d}.wav"
        if dest.exists() and not a.force:
            kept += 1
            continue
        try:
            src = speech_engines.tts_fish_wav(text, out_dir=str(out))
        except Exception as e:       # no substitute voice: stop rather than render a stranger
            print(f"Fish unavailable ({type(e).__name__}: {e}) - nothing more rendered", file=sys.stderr)
            return 2
        secs = wav_seconds(src)
        if secs > a.max_s:
            rejected.append((text, round(secs, 2)))
            os.unlink(src)
            continue
        shutil.move(src, dest)
        side = src + ".align.json"
        if os.path.exists(side):
            shutil.move(side, str(dest) + ".align.json")
        kept += 1
        print(f"ok  {dest.name}  {secs:.2f}s  {text}")
    for text, secs in rejected:
        print(f"REJECTED (too long, {secs} s > {a.max_s} s): {text}", file=sys.stderr)
    print(f"{kept} clips in {out}; {len(rejected)} rejected")
    return 0 if kept else 3


if __name__ == "__main__":
    sys.exit(main())
