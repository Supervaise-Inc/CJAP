"""
CE-11 diagnostic — retrieval-only grading of the 14 batch-03 gold additions. $0.

Why a separate script
---------------------
run_ops2_c1.py / run_ops2_c2.py read the frozen 40-query set and
gold_reference_set.csv by hard-coded path, and grade against the v4 gold. The
CE-11 rows are a different question with no baseline: they test what batch-03
actually changed. This reads

    eval/results/ce11_queries_2026-09-26.json          (queries; frozen: false)
    eval/results/gold_additions_batch03_2026-09-26.csv (the grading reference)

and grades retrieval only. No composer, no API call, no token spend. Neither
run_ops2_c1.py nor run_ops2_c2.py is touched.

The universe guard
------------------
Every one of the nine CE-11 gold documents is a book chapter, and NONE of them
is in the 95-document v4 pilot allowlist. Run against that universe and every
grounding row scores zero by construction -- a meaningless result that looks
like catastrophic failure. So this script REFUSES to run unless every expected
grounding document is present in the live runtime universe, and names the
missing ones. Restore the full-corpus runtime index first:

    python scripts/make_runtime_dense_index.py --force      (no --allowlist)

What it grades
--------------
  grounding rows : hit@1 / @3 / @5 / @10 over the selected chunks' doc_ids
  RETIRED rows   : PASS when no retired doc_id appears in the selection
  OOS rows       : reports route top_cosine against OUT_OF_SCOPE_THRESHOLD and
                   in_scope; reported, NOT hard-graded -- the real out-of-scope
                   behaviour is a composer decline, which costs tokens and is a
                   separate decision.

Writes eval/results/ce11_diag_<label>.json. Verifies before it writes; on any
error it removes whatever it wrote.

Usage:  python scripts/run_ce11_diag.py <label>
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

RES = ROOT / "eval" / "results"
QUERIES = RES / "ce11_queries_2026-09-26.json"
GOLD = RES / "gold_additions_batch03_2026-09-26.csv"
SENTINELS = {"RETIRED", "OOS", "META", "NONE"}


def main(label: str) -> int:
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")   # type: ignore[union-attr]
        except Exception:                      # noqa: BLE001
            pass

    import config            # noqa: E402
    import embeddings        # noqa: E402
    # Model first, before any numpy/pickle work: on this environment torch model
    # construction after BLAS work access-violates (the exit-139 family). Same
    # ordering run_ops2_c1.py uses, and for the same reason.
    embeddings.get_model()
    import retrieval         # noqa: E402

    for p in (QUERIES, GOLD):
        if not p.exists():
            print(f"[ce11] MISSING {p}. STOP.", file=sys.stderr)
            return 2

    qdoc = json.loads(QUERIES.read_text(encoding="utf-8"))
    queries = qdoc["queries"]
    gold = {r["qid"]: r for r in csv.DictReader(open(GOLD, encoding="utf-8-sig"))}

    qids = [q["id"] for q in queries]
    missing_gold = [q for q in qids if q not in gold]
    if missing_gold:
        print(f"[ce11] qids in the query set with no gold row: {missing_gold}. STOP.", file=sys.stderr)
        return 2

    # ---- the universe, and the guard that makes this run meaningful ----------
    pmeta = json.loads(Path(config.DENSE_INDEX_META_PATH).read_text(encoding="utf-8"))
    universe = set(pmeta["doc_ids"])
    print(f"[ce11] runtime universe: {len(universe)} documents / {pmeta['n_chunks']} chunks "
          f"({pmeta.get('allowlist_version')})")

    needed = {d for q in queries for d in (q.get("expected_grounding_doc_ids") or [])}
    absent = sorted(needed - universe)
    if absent:
        print(f"[ce11] {len(absent)} expected grounding document(s) are NOT in the runtime universe: "
              f"{absent}\n[ce11] Grading against this universe would score them zero by construction. "
              "Restore the full-corpus runtime index first:\n"
              "[ce11]   python scripts/make_runtime_dense_index.py --force   (no --allowlist)\n"
              "[ce11] STOP.", file=sys.stderr)
        return 3

    retired_csv = ROOT / "data" / "csv" / "retired_doc_ids.csv"
    retired = set()
    if retired_csv.exists():
        with open(retired_csv, encoding="utf-8-sig", newline="") as fh:
            retired = {r["doc_id"].strip() for r in csv.DictReader(fh) if r.get("doc_id")}

    rows, leaks = [], []
    for q in queries:
        qid = q["id"]
        g = gold[qid]
        res = retrieval.run(q["query"], universe)
        sel = res["retrieval"]["selected"]
        seen, order = set(), []
        for cid, _score, _diag in sel:
            d = cid.split("::")[0]
            if d not in seen:
                seen.add(d); order.append(d)
        route = res["route"]
        rec = {
            "qid": qid, "qtype": q.get("type"), "theme": q.get("theme"), "query": q["query"],
            "routed_topic": route["top_topic"], "route_cosine": route["top_cosine"],
            "in_scope": bool(route["in_scope"]),
            "n_chunks_selected": len(sel),
            "retrieved_doc_ids": order,
            "top_chunk_ids": [c for c, _, _ in sel][:10],
            "universe_size": res["retrieval"]["universe_size"],
            "fallback_global": res["retrieval"]["fallback_global"],
        }
        leak = sorted(retired & set(order))
        if leak:
            leaks.append({"qid": qid, "retired": leak})
        rec["retired_leak"] = leak

        sentinel = (g.get("gold_source_docs") or "").strip().upper()
        expected = q.get("expected_grounding_doc_ids") or []
        if sentinel == "RETIRED":
            rec["mode"] = "retired_probe"
            rec["verdict"] = "PASS" if not leak else "FAIL"
            rec["criterion"] = "no retired doc_id may appear in the selection"
        elif sentinel == "OOS":
            rec["mode"] = "oos_probe"
            rec["verdict"] = "REPORTED"
            rec["criterion"] = (f"route cosine vs OUT_OF_SCOPE_THRESHOLD "
                                f"{config.OUT_OF_SCOPE_THRESHOLD}; the real test is a composer "
                                "decline, which is not run here")
        else:
            rec["mode"] = "grounding"
            rec["expected_docs"] = expected
            for k in (1, 3, 5, 10):
                rec[f"hit@{k}"] = bool(set(order[:k]) & set(expected))
            rec["hit@selected"] = bool(set(order) & set(expected))
            rec["rank_of_first_gold"] = next(
                (i + 1 for i, d in enumerate(order) if d in expected), None)
            rec["verdict"] = "PASS" if rec["hit@selected"] else "FAIL"
            rec["criterion"] = "at least one expected grounding document in the selection"
        rows.append(rec)

    grounding = [r for r in rows if r["mode"] == "grounding"]
    n = len(grounding)
    summary = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "universe": {"n_docs": pmeta["n_docs"], "n_chunks": pmeta["n_chunks"],
                     "allowlist_version": pmeta.get("allowlist_version")},
        "queries_file": QUERIES.name,
        "queries_sha256_of_queries": qdoc.get("meta", {}).get("sha256_of_queries"),
        "grading_reference": GOLD.name,
        "n_queries": len(rows),
        "n_grounding": n,
        "grounding_recall": {
            f"@{k}": round(sum(1 for r in grounding if r[f"hit@{k}"]) / n, 3) for k in (1, 3, 5, 10)
        } if n else {},
        "grounding_recall_at_selected": round(
            sum(1 for r in grounding if r["hit@selected"]) / n, 3) if n else None,
        "retired_probes_pass": all(r["verdict"] == "PASS" for r in rows if r["mode"] == "retired_probe"),
        "retired_leaks_anywhere": leaks,
        "llm_calls": 0,
        "cost_usd": 0.0,
    }

    out = RES / f"ce11_diag_{label}.json"
    written = None
    try:
        out.write_text(json.dumps({"summary": summary, "per_query": rows},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written = out
    except Exception as e:                      # noqa: BLE001
        if written:
            try:
                written.unlink()
            except OSError:
                pass
        print(f"[ce11] FAILED, wrote nothing: {e}", file=sys.stderr)
        return 1

    print(f"[ce11] {label}: {len(rows)} queries, {n} grounding")
    if n:
        print(f"[ce11] grounding recall @1/@3/@5/@10 = "
              + "/".join(str(summary['grounding_recall'][f'@{k}']) for k in (1, 3, 5, 10))
              + f" | at-selected {summary['grounding_recall_at_selected']}")
    print(f"[ce11] retired probes pass: {summary['retired_probes_pass']} | "
          f"retired leaks anywhere: {leaks if leaks else 'none'}")
    for r in rows:
        extra = (f"rank_first_gold={r.get('rank_of_first_gold')}" if r["mode"] == "grounding"
                 else r["mode"])
        print(f"   {r['qid']:>4}  {r['verdict']:<8} {r['routed_topic']:<42} "
              f"n={r['n_chunks_selected']:<3} {extra}")
    print(f"[ce11] wrote {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python scripts/run_ce11_diag.py <label>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
