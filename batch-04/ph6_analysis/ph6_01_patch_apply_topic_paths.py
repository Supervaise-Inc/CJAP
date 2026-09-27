"""Phase 6 Step 1 (code side): scripts/apply_topic_paths.py learns route_source.
  matcher  - the keyword matcher caught the document (derive_topic_paths, unchanged): primary/secondary lists, route_source "matcher"
  affinity - no matcher caught it; best-chunk CENTRED affinity to the closest dimension clears TOPIC_ASSIGN_MIN_COSINE: primary [top tag],
             secondary [the next tags at or above the floor, up to MAX_TOPIC_TAGS-1]; route_source "affinity"
  orphan   - no matcher and no dimension at or above the floor: primary null, secondary [], route_source "orphan" (explicit, never blank)
Affinities come from reports/topic_tags_full_<date>.json (merge_tag_topics.py, all 1,290 documents); the script REFUSES a report that was not
built on the current corpus mean / floor / taxonomy. The file is CRLF in git; edited in LF space, written back CRLF."""
from pathlib import Path
P = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder/scripts/apply_topic_paths.py")
raw = P.read_bytes(); assert raw.count(b"\r\n") == raw.count(b"\n")
s = raw.decode("utf-8").replace("\r\n", "\n")
NL = chr(92) + "n"
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)

sub('''Run after build_topic_map.py whenever the taxonomy changes''', '''Phase 6: every document's `topic_paths` also carries `route_source`:
  "matcher"  - a keyword matcher caught it (primary/secondary lists);
  "affinity" - no matcher did, but its best-chunk centred cosine to a dimension clears TOPIC_ASSIGN_MIN_COSINE (filled from
               reports/topic_tags_full_<date>.json);
  "orphan"   - neither: `"primary": null`, `"secondary": []` - explicit, never silently blank.

Run after build_topic_map.py whenever the taxonomy changes''')
sub('''import json
from pathlib import Path
''', '''import hashlib
import json
import sys
from pathlib import Path
''')
sub('''    score_topic,
)
''', '''    score_topic,
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
''')
sub('''def main() -> int:
    paths = sorted(''', '''def main() -> int:
    tags_path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((PROJECT_ROOT_REPORTS).glob("topic_tags_full_*.json"))[-1]
    tags = load_tags(tags_path)
    print(f"[apply] affinity source: {tags_path.name} (floor {tags['assign_floor']}, {tags['n_docs']} docs, centred)")
    paths = sorted(''')
sub('''    updated = 0
    empty_primary = 0
    for p, doc in docs:
        tp = derive_topic_paths(doc["id"], doc_scores)
        if doc.get("topic_paths") != tp:''', '''    updated = 0
    counts = {"matcher": 0, "affinity": 0, "orphan": 0}
    orphans: list[str] = []
    assert len(docs) == tags["n_docs"], (len(docs), tags["n_docs"])
    for p, doc in docs:
        tp = route_for(doc["id"], derive_topic_paths(doc["id"], doc_scores), tags)
        counts[tp["route_source"]] += 1
        if tp["route_source"] == "orphan":
            orphans.append(doc["id"])
        if doc.get("topic_paths") != tp:''')
sub('''        if not tp["primary"]:
            empty_primary += 1
            print(f"  [warn] no primary topic for {doc['id']}")
    print(f"[apply] {updated} files updated of {len(docs)}; "
          f"{empty_primary} with empty primary path")''', '''    print(f"[apply] {updated} files updated of {len(docs)}")
    print(f"[apply] route_source: matcher {counts['matcher']} + affinity {counts['affinity']} + orphan {counts['orphan']} = {sum(counts.values())}")
    for fmt in "CBSG":
        print(f"        orphans in {fmt}: {sum(1 for o in orphans if o[0] == fmt)}")
    print(f"[apply] orphans: {orphans}")''')
sub('''from build_topic_map import (  # type: ignore[import-not-found]
    CORPUS_ROOT,''', '''from build_topic_map import (  # type: ignore[import-not-found]
    CORPUS_ROOT,
    REPORTS_DIR as PROJECT_ROOT_REPORTS,''')
import ast; ast.parse(s)
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("patched apply_topic_paths.py (CRLF preserved)")
