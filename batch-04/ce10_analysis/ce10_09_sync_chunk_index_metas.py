"""CE-10 Step 5, first bullet — DECISION: refresh chunk_index.json's source_snapshot (re-pinned at 1,295) and make the four metas agree.
Why refresh: chunk_index.json's `source_snapshot` was copied from the PRE-CE-4 pin (1,109 docs, old columns/books xlsx hashes) while the
chunks were built from the CE-4 corpus; leaving it would state false provenance. Why it is safe: chunks.jsonl is BYTE-IDENTICAL (proved below), so
embeddings, BM25 and centroids are unaffected; only the chunk_index.json header changes, and with it the sha256 four data/index metas record.
This script proves the precondition, replaces the old sha256 with the new one byte-for-byte in exactly those four files (formatting untouched),
verifies each meta now equals sha256(chunk_index.json), and writes data/index/chunk_index_refresh_2026-09-27.json as the provenance record."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sha = lambda b: hashlib.sha256(b).hexdigest()
ci, cj = ROOT / "corpus/index/chunk_index.json", ROOT / "corpus/index/chunks.jsonl"
head = lambda p: subprocess.run(["git", "show", f"HEAD:{p}"], cwd=ROOT, capture_output=True).stdout
old_ci, old_cj = head("corpus/index/chunk_index.json"), head("corpus/index/chunks.jsonl")
assert sha(cj.read_bytes()) == sha(old_cj), "chunks.jsonl changed - STOP, restore corpus/index from HEAD"
a, b = json.loads(old_ci.decode("utf-8")), json.loads(ci.read_bytes().decode("utf-8"))
assert a["stats"] == b["stats"] and a["by_doc"] == b["by_doc"], "chunk_index differs beyond source_snapshot - STOP"
snap = json.loads((ROOT / "corpus_snapshot.json").read_text(encoding="utf-8"))
assert b["source_snapshot"]["doc_id_count"] == snap["header"]["doc_id_count"] == 1295
assert b["source_snapshot"]["source_files"] == [{"filename": s["filename"], "sha256": s["sha256"]} for s in snap["source_files"]]
old_sha, new_sha = sha(old_ci), sha(ci.read_bytes())
print(f"chunks.jsonl byte-identical ({sha(cj.read_bytes())[:16]}...); chunk_index differs ONLY in source_snapshot ({a['source_snapshot']['doc_id_count']} -> {b['source_snapshot']['doc_id_count']})")
print(f"chunk_index_sha256 {old_sha[:16]}... -> {new_sha[:16]}...")
metas = ["corpus_dense_meta.json", "pilot_dense_meta.json", "pilot_sparse_meta.json", "topic_centroids_meta.json"]
for m in metas:
    p = ROOT / "data/index" / m; raw = p.read_bytes()
    assert raw.count(old_sha.encode()) == 1, (m, raw.count(old_sha.encode()))
    p.write_bytes(raw.replace(old_sha.encode(), new_sha.encode()))
for m in metas:
    assert (ROOT / "data/index" / m).read_bytes().count(new_sha.encode()) == 1 and (ROOT / "data/index" / m).read_bytes().count(old_sha.encode()) == 0
    print(f"  {m:32s} now records {new_sha[:16]}...")
(ROOT / "data/index/chunk_index_refresh_2026-09-27.json").write_text(json.dumps({
    "reason": "chunk_index.json source_snapshot refreshed to the CE-10 re-pin (1,295 docs); chunks.jsonl byte-identical, so dense/BM25/centroids are unaffected",
    "chunks_jsonl_sha256": sha(cj.read_bytes()), "chunk_index_sha256_before": old_sha, "chunk_index_sha256_after": new_sha,
    "metas_updated": metas, "source_snapshot_before": a["source_snapshot"], "source_snapshot_after": b["source_snapshot"]}, indent=2) + "\n", encoding="utf-8", newline="\n")
print("wrote data/index/chunk_index_refresh_2026-09-27.json")
