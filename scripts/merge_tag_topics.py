"""
CE-10 Steps 3.4-3.5 — independence check on the centred centroids, then tag ALL documents.

1. INDEPENDENCE CHECK (was: an in-place union-find merge). Every pair of centroids whose centred cosine exceeds
   TOPIC_MERGE_COSINE is REPORTED. If there is any, this script STOPS (exit 2) and writes nothing: a proposed merge
   changes the signed-off dimension set, so it is a human decision — never something to bypass (P3.3 bypassed the
   gate by running it at 1.01 and then re-merged at raw 0.95, which collapsed 34 -> 3).
2. TAGGING. Every document in the corpus (all formats — not the 95-document pilot subset; that hard-coding is what
   made P3.3 fail its coverage bullet) gets primary + secondary tags: the top MAX_TOPIC_TAGS dimensions by BEST-CHUNK
   centred cosine that are >= TOPIC_ASSIGN_MIN_COSINE; the best is primary, the rest secondary. A document with no
   dimension at or above the floor is an orphan.
   Two affinity readings are written: `in_sample` (what production sees — the document's own chunks are inside its
   dimensions' centroids) and `held_out` (leave-one-out: a member document is removed from its own dimension's centroid
   first — the reading the proposal's orphan rates were measured on). The floor was derived on the held-out reading.

All cosines are on vectors centred on data/index/corpus_mean.npy, loaded through app/centering.py (sha256 checked
against the centroid meta; missing or mismatching => raises, no fallback to raw). Normalisation is after centring.

Writes reports/topic_tags_full_<date>.json and adds the independence/orphan results to the centroid meta.
Usage:  python scripts/merge_tag_topics.py [YYYY-MM-DD]
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT)); sys.path.insert(0, str(PROJECT_ROOT / "app"))
import config  # noqa: E402
import centering  # noqa: E402

REPORTS = PROJECT_ROOT / "reports"
FORMATS = {"C": "columns", "B": "books", "S": "speeches", "G": "biography"}


def main(date_tag: str) -> int:
    meta = json.loads(Path(config.CENTROIDS_META_PATH).read_text(encoding="utf-8"))
    mu = centering.mean_for_meta(meta)                              # raises loudly; never raw
    cen = np.load(config.CENTROIDS_PATH).astype(np.float32)
    ids = meta["topic_ids"]; n = len(ids)
    assert cen.shape[0] == n and meta.get("taxonomy_version") == 2

    # ---- 1. independence check at the approved TOPIC_MERGE_COSINE ------------------------------------------------
    cc = cen @ cen.T; iu = np.triu_indices(n, 1)
    over = [(round(float(cc[i, j]), 4), ids[i], ids[j]) for i, j in zip(*iu) if cc[i, j] > config.TOPIC_MERGE_COSINE]
    top = sorted(((round(float(cc[i, j]), 4), ids[i], ids[j]) for i, j in zip(*iu)), reverse=True)[:8]
    print(f"[independence] TOPIC_MERGE_COSINE={config.TOPIC_MERGE_COSINE} (centred): {len(over)} of {len(iu[0])} pairs above it")
    for t in top:
        print(f"    {t[0]:.4f}  {t[1]}  <->  {t[2]}")
    if over:
        print(f"[independence] STOP: the gate proposes {len(over)} merge(s) of the signed-off set: {over}", file=sys.stderr)
        return 2

    # ---- 2. tag every document ----------------------------------------------------------------------------------------
    cmeta = json.loads(Path(config.CORPUS_DENSE_META_PATH).read_text(encoding="utf-8"))
    cmat = np.load(config.CORPUS_DENSE_PATH).astype(np.float32)
    chunk_ids = cmeta["chunk_ids"]
    assert cmat.shape[0] == meta["corpus_mean"]["n_chunks"] == len(chunk_ids)
    rows_of: dict[str, list[int]] = {}
    for i, cid in enumerate(chunk_ids):
        rows_of.setdefault(cid.split("::")[0], []).append(i)
    docs = sorted(rows_of)
    tmap = json.loads((PROJECT_ROOT / "corpus" / "voice" / "topic_map.json").read_text(encoding="utf-8"))["topics"]
    members = {tid: set(tmap[tid]["doc_ids"]) for tid in ids}
    floor = config.TOPIC_ASSIGN_MIN_COSINE

    Zc = centering.center(cmat, mu)                                  # centred chunk vectors
    sims = Zc @ cen.T                                                # [n_chunks, n_topics]
    best_in = np.stack([sims[rows_of[d]].max(axis=0) for d in docs])   # [n_docs, n_topics] in-sample best-chunk
    # leave-one-out: a member doc is taken out of its own dimension's centroid before its affinity to that dimension
    raw_sum = {tid: cmat[[r for d in sorted(members[tid]) for r in rows_of.get(d, [])]].astype(np.float64).sum(axis=0) for tid in ids}
    n_ch = {tid: sum(len(rows_of.get(d, [])) for d in members[tid]) for tid in ids}
    best_lo = best_in.copy(); di = {d: k for k, d in enumerate(docs)}
    for j, tid in enumerate(ids):
        for d in members[tid]:
            if d not in di: continue
            rows = rows_of[d]; k = di[d]
            c2 = centering.center((raw_sum[tid] - cmat[rows].astype(np.float64).sum(axis=0)) / (n_ch[tid] - len(rows)), mu)
            best_lo[k, j] = float((Zc[rows] @ c2).max())

    def tag(aff_row):
        order = np.argsort(-aff_row)[:config.MAX_TOPIC_TAGS]
        return [(ids[int(k)], round(float(aff_row[k]), 4)) for k in order if aff_row[k] >= floor]

    per_doc, orph_in, orph_lo = {}, [], []
    for d in docs:
        k = di[d]; kept = tag(best_in[k]); kept_lo = tag(best_lo[k])
        rec = {"format": FORMATS[d[0]], "n_tags": len(kept),
               "best": {"topic": ids[int(best_in[k].argmax())], "cos": round(float(best_in[k].max()), 4)}}
        if kept:
            rec.update(primary=kept[0][0], primary_cos=kept[0][1], secondary=[t for t, _ in kept[1:]])
        else:
            rec.update(primary=None, primary_cos=None, secondary=[]); orph_in.append(d)
        rec["held_out_orphan"] = not kept_lo
        if not kept_lo: orph_lo.append(d)
        per_doc[d] = rec

    def by_format(orph):
        out = {}
        for f in FORMATS.values():
            tot = sum(1 for d in docs if FORMATS[d[0]] == f); o = sum(1 for d in orph if FORMATS[d[0]] == f)
            out[f] = {"docs": tot, "orphans": o, "rate": round(o / tot, 4)}
        return out

    tag_dist = {}
    for r in per_doc.values(): tag_dist[str(r["n_tags"])] = tag_dist.get(str(r["n_tags"]), 0) + 1
    primary_counts = {tid: sum(1 for r in per_doc.values() if r["primary"] == tid) for tid in ids}
    tagged = len(docs) - len(orph_in)
    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "taxonomy_version": 2, "scale": "centred",
        "corpus_mean_sha256": meta["corpus_mean"]["sha256"], "n_docs": len(docs),
        "assign_floor": floor, "merge_cosine": config.TOPIC_MERGE_COSINE, "max_topic_tags": config.MAX_TOPIC_TAGS,
        "affinity": "best-chunk centred cosine (max over a document's chunks)",
        "coverage": {"tagged": tagged, "of": len(docs), "orphans_in_sample": len(orph_in), "orphans_held_out": len(orph_lo)},
        "orphan_rate_by_format": {"in_sample": by_format(orph_in), "held_out": by_format(orph_lo)},
        "independence_check": {"threshold": config.TOPIC_MERGE_COSINE, "pairs_above": [], "closest_pairs": top},
        "tags_per_doc": tag_dist, "primary_counts": primary_counts,
        "orphans_in_sample": orph_in, "orphans_held_out": orph_lo, "per_doc": per_doc,
    }
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"topic_tags_full_{date_tag}.json"
    out.write_text(json.dumps(report, ensure_ascii=config.JSON_ENSURE_ASCII, indent=2) + "\n",
                   encoding=config.OUTPUT_ENCODING, newline="\n")
    meta.update({"merge_cosine": config.TOPIC_MERGE_COSINE, "assign_floor": floor, "merged_pairs": [],
                 "independence_check_max_pair": top[0][0], "n_docs_tagged": tagged, "n_docs": len(docs),
                 "orphans_in_sample": len(orph_in), "orphans_held_out": len(orph_lo), "tags_report": out.name,
                 "tagged_date": date_tag})
    Path(config.CENTROIDS_META_PATH).write_text(
        json.dumps(meta, ensure_ascii=config.JSON_ENSURE_ASCII, indent=2) + "\n", encoding=config.OUTPUT_ENCODING, newline="\n")
    print(f"[tag] {tagged} of {len(docs)} documents tagged (primary + secondary); orphans in-sample {len(orph_in)}, held-out {len(orph_lo)}")
    for view in ("in_sample", "held_out"):
        print(f"[orphan/{view}] " + "  ".join(f"{f}: {v['orphans']}/{v['docs']} ({100 * v['rate']:.1f}%)"
                                             for f, v in report["orphan_rate_by_format"][view].items()))
    print(f"[tag] tags per doc {tag_dist}")
    print(f"[write] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()))
