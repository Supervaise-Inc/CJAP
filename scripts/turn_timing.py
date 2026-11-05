#!/usr/bin/env python3
"""Per-stage turn timing from the robot's own `[trace]` journal lines (2026-11-05).

The robot already prints one line per answered turn (main_voice_robot.py,
_trace_turn):

    [trace] path=streamed | stt_s=1.31s | compose_s=6.80s | first_audio_s=3.90s |
            on_air_s=5.20s | audio_s=14.10s | words=58 | topic=... | interrupted=False

This script turns those lines into a per-stage table and a summary (n, median,
mean, p90, min, max), writes JSON/CSV for the paper, and compares two robots.

Collect on a robot (one line per turn, with timestamps):

    journalctl -u supervaise -o short-iso --no-pager -g '\\[trace\\]' > alpha_trace.txt

Use:

    python scripts/turn_timing.py alpha_trace.txt --label alpha --json alpha.json
    python scripts/turn_timing.py beta_trace.txt  --label beta  --json beta.json
    python scripts/turn_timing.py --compare alpha.json beta.json

What each stage means (all seconds):

    stt_s          speech-to-text call, from the end of the recording
    first_audio_s  from the end of STT until the first answer sentence is
                   synthesised and ready
    on_air_s       from the end of STT until that sentence actually starts
                   playing (it waits for the "thinking" filler clip to finish)
    filler_wait_s  on_air_s - first_audio_s: time the finished answer sat
                   waiting behind a filler clip
    heard_to_sound_s  stt_s + on_air_s + --endpoint-s: an estimate of what the
                   visitor perceives, from the last word spoken to the first
                   answer sound

NOT in the trace, so not in the table: the silence the recorder waits for after
the visitor stops talking (1.2 s in the direct profile, 4 s code default), the
VAD / speaker-lock gates, and the wake phrase. Pass --endpoint-s to add the
silence timeout to the estimate. A manual stopwatch count of "about 12 s" should
be compared with heard_to_sound_s, not with on_air_s alone.
"""
import argparse
import csv
import json
import re
import statistics
import sys

TRACE_RE = re.compile(r"^(?P<when>.*?)\s*\[trace\]\s+(?P<body>.*)$")
NUM_RE = re.compile(r"^-?\d+(\.\d+)?s?$")

STAGES = ["stt_s", "first_audio_s", "on_air_s", "filler_wait_s", "heard_to_sound_s", "compose_s"]


def _value(v):
    v = v.strip()
    if v == "-":
        return None
    if NUM_RE.match(v):
        return float(v.rstrip("s"))
    if v in ("True", "False"):
        return v == "True"
    return v


def parse_line(line):
    """One [trace] line -> dict, or None when it is not one."""
    m = TRACE_RE.match(line.rstrip("\n"))
    if not m:
        return None
    rec = {"when": m.group("when").strip()}
    for part in m.group("body").split(" | "):
        if "=" in part:
            k, v = part.split("=", 1)
            rec[k.strip()] = _value(v)
    return rec if "path" in rec else None


def parse_lines(lines):
    return [r for r in (parse_line(l) for l in lines) if r]


def derive(rec, endpoint_s=0.0):
    """Add filler_wait_s and heard_to_sound_s where the inputs exist."""
    out = dict(rec)
    fa, oa, stt = rec.get("first_audio_s"), rec.get("on_air_s"), rec.get("stt_s")
    if fa is not None and oa is not None:
        out["filler_wait_s"] = round(max(0.0, oa - fa), 2)
    if stt is not None and oa is not None:
        out["heard_to_sound_s"] = round(stt + oa + endpoint_s, 2)
    return out


def _pct(vals, q):
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def summarize(turns):
    """{stage: {n, median, mean, p90, min, max}} over the turns that have it."""
    out = {}
    for st in STAGES:
        vals = [t[st] for t in turns if isinstance(t.get(st), (int, float))]
        if not vals:
            continue
        out[st] = {"n": len(vals), "median": round(statistics.median(vals), 2),
                   "mean": round(statistics.fmean(vals), 2), "p90": round(_pct(vals, 0.9), 2),
                   "min": round(min(vals), 2), "max": round(max(vals), 2)}
    return out


def build(lines, label="", endpoint_s=0.0, path="streamed"):
    recs = parse_lines(lines)
    turns = [derive(r, endpoint_s) for r in recs if path == "all" or r.get("path") == path]
    return {"label": label, "path": path, "endpoint_s": endpoint_s,
            "lines_seen": len(recs), "n": len(turns), "turns": turns,
            "summary": summarize(turns)}


def format_report(rep):
    out = [f"{rep['label'] or 'turns'}: {rep['n']} turn(s) on path '{rep['path']}' "
           f"({rep['lines_seen']} [trace] lines seen, endpoint {rep['endpoint_s']} s)"]
    if not rep["summary"]:
        out.append("  no turns with timing fields")
        return "\n".join(out)
    out.append(f"  {'stage':<18}{'n':>4}{'median':>9}{'mean':>8}{'p90':>8}{'min':>8}{'max':>8}")
    for st, s in rep["summary"].items():
        out.append(f"  {st:<18}{s['n']:>4}{s['median']:>9.2f}{s['mean']:>8.2f}"
                   f"{s['p90']:>8.2f}{s['min']:>8.2f}{s['max']:>8.2f}")
    return "\n".join(out)


def compare(a, b):
    """Side-by-side medians and p90 of two reports (the two robots)."""
    la, lb = a.get("label") or "A", b.get("label") or "B"
    out = [f"{'stage':<18}{la + ' med':>12}{lb + ' med':>12}{'delta':>9}{la + ' p90':>12}{lb + ' p90':>12}"]
    for st in STAGES:
        sa, sb = a["summary"].get(st), b["summary"].get(st)
        if not sa or not sb:
            continue
        out.append(f"{st:<18}{sa['median']:>12.2f}{sb['median']:>12.2f}"
                   f"{sb['median'] - sa['median']:>+9.2f}{sa['p90']:>12.2f}{sb['p90']:>12.2f}")
    out.append(f"n: {la}={a['n']}  {lb}={b['n']}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*", help="journal text files, or - for stdin")
    ap.add_argument("--label", default="")
    ap.add_argument("--path", default="streamed",
                    help="trace path to keep: streamed (default), all, or e.g. canned")
    ap.add_argument("--endpoint-s", type=float, default=0.0,
                    help="silence timeout the recorder waits after the visitor stops "
                         "(1.2 direct profile); added to heard_to_sound_s")
    ap.add_argument("--json", help="write the report (turns + summary) to this file")
    ap.add_argument("--csv", help="write one row per turn to this file")
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"),
                    help="compare two reports written by --json")
    a = ap.parse_args(argv)

    if a.compare:
        reps = [json.load(open(p, encoding="utf-8")) for p in a.compare]
        print(compare(*reps))
        return 0
    if not a.files:
        ap.error("give a journal file, - for stdin, or --compare")
    lines = []
    for f in a.files:
        lines += (sys.stdin if f == "-" else open(f, encoding="utf-8", errors="replace")).readlines()
    rep = build(lines, a.label, a.endpoint_s, a.path)
    print(format_report(rep))
    if a.json:
        json.dump(rep, open(a.json, "w", encoding="utf-8"), indent=1)
    if a.csv and rep["turns"]:
        cols = sorted({k for t in rep["turns"] for k in t})
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rep["turns"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
