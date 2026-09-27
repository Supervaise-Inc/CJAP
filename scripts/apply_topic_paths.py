"""
Backfill `topic_paths` in every generated .json file (1,290: columns, books, speeches,
biography) using the curated taxonomy from build_topic_map.py.

Reads each .json under corpus/{columns,books,speeches,biography}/, computes
primary / secondary topic ids by scoring the doc against the taxonomy,
and writes the result back in place (idempotent).

Phase 6: every document's `topic_paths` also carries `route_source`:
  "matcher"  - a keyword matcher caught it (primary/secondary lists);
  "affinity" - no matcher did, but its best-chunk centred cosine to a dimension clears TOPIC_ASSIGN_MIN_COSINE (filled from
               reports/topic_tags_full_<date>.json);
  "orphan"   - neither: `"primary": null`, `"secondary": []` - explicit, never silently blank.

Run after build_topic_map.py whenever the taxonomy changes, and BEFORE the corpus pin is refreshed
(pinning first wiped the backfill on every earlier regeneration).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from build_topic_map import (  # type: ignore[import-not-found]
    CORPUS_ROOT,
    REPORTS_DIR as PROJECT_ROOT_REPORTS,
    TAXONOMY,
    _doc_haystack,
    derive_topic_paths,
    score_topic,
)
import config  # noqa: E402  (build_topic_map put the project root on sys.path)


def load_tags(path: Path) -> dict:
    """The affinity report, refused unless it was built on THIS corpus mean, floor and taxonomy."""
    rep = json.loads(path.read_text(encoding="utf-8"))
    mean_sha = hashlib.sha256(Path(config.CORPUS_MEAN_PATH).read_bytes()).hexdigest()
    meta = json.loads(Path(config.CENTROIDS_META_PATH).read_text(encoding="utf-8"))
    problems = []
    if rep.get("corpus_mean_sha256") != mean_sha:
        problems.append("corpus_mean sha256 differs from data/index/corpus_mean.npy")
    if rep.get("assign_floor") != config.TOPIC_ASSIGN_MIN_COSINE:
        problems.append(f"report floor {rep.get('assign_floor')} != config {config.TOPIC_ASSIGN_MIN_COSINE}")
    if rep.get("scale") != "centred" or rep.get("taxonomy_version") != 2:
        problems.append("report is not centred / taxonomy v2")
    if meta.get("tags_report") != path.name:
        problems.append(f"centroid meta names {meta.get('tags_report')!r} as the tags report, not {path.name!r}")
    ids = {t["id"] for t in TAXONOMY}
    used = {r["primary"] for r in rep["per_doc"].values() if r.get("primary")}
    if not used <= ids:
        problems.append(f"report tags unknown topics: {sorted(used - ids)}")
    if problems:
        raise SystemExit("[apply] refusing the tags report: " + "; ".join(problems))
    return rep


def route_for(doc_id: str, matcher_tp: dict, tags: dict) -> dict:
    """matcher > affinity > orphan, with the provenance recorded beside the route."""
    if matcher_tp["primary"]:
        return {"primary": matcher_tp["primary"], "secondary": matcher_tp["secondary"], "route_source": "matcher"}
    rec = tags["per_doc"][doc_id]
    if rec.get("primary"):
        return {"primary": [rec["primary"]], "secondary": list(rec.get("secondary") or []), "route_source": "affinity"}
    return {"primary": None, "secondary": [], "route_source": "orphan"}


def main() -> int:
    tags_path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((PROJECT_ROOT_REPORTS).glob("topic_tags_full_*.json"))[-1]
    tags = load_tags(tags_path)
    print(f"[apply] affinity source: {tags_path.name} (floor {tags['assign_floor']}, {tags['n_docs']} docs, centred)")
    paths = sorted(
        list(CORPUS_ROOT.glob("columns/**/*.json"))
        + list(CORPUS_ROOT.glob("speeches/**/*.json"))
        + list(CORPUS_ROOT.glob("biography/**/*.json"))
        # CE-10: books/** was never globbed here either (same defect as load_docs): 299 book chapters carried no topic_paths.
        + list(CORPUS_ROOT.glob("books/**/*.json"))
    )
    # First pass: score every doc.
    doc_scores: dict[str, dict[str, int]] = {}
    docs: list[tuple[Path, dict]] = []
    for p in paths:
        doc = json.loads(p.read_text(encoding="utf-8"))
        docs.append((p, doc))
        hs = _doc_haystack(doc)
        doc_scores[doc["id"]] = {t["id"]: score_topic(t, hs) for t in TAXONOMY}
    # Second pass: write topic_paths back.
    updated = 0
    counts = {"matcher": 0, "affinity": 0, "orphan": 0}
    orphans: list[str] = []
    assert len(docs) == tags["n_docs"], (len(docs), tags["n_docs"])
    for p, doc in docs:
        tp = route_for(doc["id"], derive_topic_paths(doc["id"], doc_scores), tags)
        counts[tp["route_source"]] += 1
        if tp["route_source"] == "orphan":
            orphans.append(doc["id"])
        if doc.get("topic_paths") != tp:
            doc["topic_paths"] = tp
            p.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",     # CE-10: LF, not the platform newline (the corpus JSONs are LF in git)
            )
            updated += 1
    print(f"[apply] {updated} files updated of {len(docs)}")
    print(f"[apply] route_source: matcher {counts['matcher']} + affinity {counts['affinity']} + orphan {counts['orphan']} = {sum(counts.values())}")
    for fmt in "CBSG":
        print(f"        orphans in {fmt}: {sum(1 for o in orphans if o[0] == fmt)}")
    print(f"[apply] orphans: {orphans}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
