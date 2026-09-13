#!/usr/bin/env python3
"""Measure the gates against adversarial questions — the 09-12 audit, repeatable.

That audit ran 50 adversarial questions through the real pipeline and found the
gates blocked 0 of 277 composed sentences while 37 invented particulars reached
speech. It was done by hand, once. This script makes the number reproducible,
so a change to the gates can be shown to have moved it.

Two modes:

  (default)  offline, free. Runs the premise gate over the question set and
             reports how many unanswerable premises are refused before a
             composer ever runs, plus how many answerable questions would be
             wrongly refused — the error that matters in the other direction.

  --live     spends money. For every question the premise gate lets through, it
             runs the REAL router, context builder and composer, splits the
             answer the way the robot does, and puts each sentence through the
             same gates the live path uses (forbidden patterns, year, full
             date, unverified titles) plus the Haiku fact audit on the
             sentences that trigger it. Writes reports/gate_audit.json.

  python scripts/gate_audit.py
  python scripts/gate_audit.py --live --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "docs" / "test-specs" / "TS-007-premise-gate-questions.json"


def _load(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {"refuse": doc.get("refuse", []), "answer": doc.get("answer", [])}


def offline(qs: dict) -> dict:
    import premise_gate as pg
    out = {"mode": "offline", "horizon": pg.corpus_horizon(),
           "refused": [], "missed": [], "false_positives": [], "passed": []}
    for e in qs["refuse"]:
        v = pg.check(e["q"])
        (out["refused"] if v["refuse"] else out["missed"]).append(
            {"q": e["q"], "expected": e.get("category"), "got": v["category"]})
    for e in qs["answer"]:
        v = pg.check(e["q"])
        (out["false_positives"] if v["refuse"] else out["passed"]).append(
            {"q": e["q"], "got": v["category"]})
    return out


def live(qs: dict, limit: int | None) -> dict:
    """The expensive half: compose real answers and gate every sentence."""
    import answer_gate as ag
    import answer_pipeline as ap
    import premise_gate as pg
    from speech_streaming import _FACT_TRIGGER, split_ready

    client = ap.make_client()
    artifacts = ap.CorpusArtifacts()
    asked = [e["q"] for e in qs["refuse"]] + [e["q"] for e in qs["answer"]]
    if limit:
        asked = asked[:limit]

    out = {"mode": "live", "questions": [], "n_sentences": 0, "n_blocked": 0,
           "n_declined": 0, "n_audited": 0}
    for q in asked:
        rec = {"q": q, "declined": None, "sentences": [], "blocked": []}
        v = pg.check(q)
        if v["refuse"]:
            rec["declined"] = v["category"]
            out["n_declined"] += 1
            out["questions"].append(rec)
            print(f"  DECLINED [{v['category']}] {q}")
            continue
        t0 = time.monotonic()
        routing = ap.route_question(client, q, artifacts)
        topics = [t for t in [routing.get("primary_topic")]
                  + list(routing.get("secondary_topics") or []) if t]
        buf, parts = "", []
        for piece in ap.generate_response_stream(client, q, routing, artifacts, []):
            buf += piece
            ready, buf = split_ready(buf)
            parts += ready
        if buf.strip():
            parts.append(buf.strip())
        ctx = ap.LAST_CONTEXT_TEXT[0]
        for s in parts:
            out["n_sentences"] += 1
            rec["sentences"].append(s)
            g = ag.check_answer(q, s, topic_ids=topics, forbid_only=True, audit=False)
            fc = ag.fact_check(s, ctx, q)
            tripped = list(g["tripped"])
            for kind, vals in (("year", fc["bad_years"]), ("date", fc["bad_dates"])):
                tripped += [{"rule": "fact-gate", "kind": kind, "detail": d} for d in vals]
            if not tripped and _FACT_TRIGGER.search(s):
                out["n_audited"] += 1
                au = ap.sentence_fact_audit(client, s, ctx)
                if not au.get("supported", True):
                    tripped.append({"rule": "fact-audit", "kind": "unsupported",
                                    "detail": au.get("reason", "")})
            if tripped:
                out["n_blocked"] += 1
                rec["blocked"].append({"sentence": s, "tripped": tripped})
                print(f"  BLOCKED  {tripped[0]['kind']}: {s[:70]}")
        rec["compose_s"] = round(time.monotonic() - t0, 1)
        print(f"  answered ({len(parts)} sentences, {rec['compose_s']}s) {q[:60]}")
        out["questions"].append(rec)
    return out


def main() -> int:
    ap_ = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("--live", action="store_true",
                     help="compose real answers and gate every sentence (costs money)")
    ap_.add_argument("--limit", type=int, help="only the first N questions (--live)")
    ap_.add_argument("--questions", type=Path, default=QUESTIONS)
    args = ap_.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "app"))
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "app" / ".env")
    except ImportError:
        pass

    qs = _load(args.questions)
    res = offline(qs)
    n_ref, n_ans = len(qs["refuse"]), len(qs["answer"])
    print(f"premise gate — corpus horizon {res['horizon']}")
    print(f"  unanswerable premises refused : {len(res['refused'])}/{n_ref}")
    for m in res["missed"]:
        print(f"      MISSED  {m['q']}")
    print(f"  answerable questions untouched: {len(res['passed'])}/{n_ans}")
    for f in res["false_positives"]:
        print(f"      REFUSED WRONGLY [{f['got']}]  {f['q']}")

    if args.live:
        print("\nlive composition — this spends API credit")
        res = {"offline": res, **live(qs, args.limit)}
        n = res["n_sentences"]
        print(f"\n  questions declined before composing: {res['n_declined']}")
        print(f"  sentences composed                 : {n}")
        print(f"  sentences audited by Haiku         : {res['n_audited']}")
        print(f"  sentences blocked by a gate        : {res['n_blocked']}"
              + (f" ({100 * res['n_blocked'] / n:.1f}%)" if n else ""))

    dest = ROOT / "reports" / "gate_audit.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"\nwritten: {dest.relative_to(ROOT)}")
    return 1 if (res.get("missed") or res.get("false_positives")
                 or res.get("offline", {}).get("missed")) else 0


if __name__ == "__main__":
    sys.exit(main())
