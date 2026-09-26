"""Phase 4 (CE-9) entry check — Python, never grep. Read-only. Exit nonzero on any mismatch."""
import glob, hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
os.chdir(ROOT)
fail = []
def check(label, got, want):
    ok = got == want
    print(f"  [{'OK ' if ok else 'BAD'}] {label}: {got}" + ("" if ok else f"   (expected {want})"))
    if not ok: fail.append(label)
sha8 = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]   # the prompt calls these "sha16" but quotes 8 hex characters

print("== git ==")
check("branch", subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip(), "deliverable/2026-09")
check("HEAD", subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()[:7], "c8e58cc")
print("== Phase 3 outputs present ==")
for f in ("ce7_coverage_2026-09-26.md", "ce7_orphan_clusters_2026-09-26.md", "ce7_enrichment_vocabulary_2026-09-26.csv",
          "ce7_per_work_coverage_2026-09-26.md", "ce7_candidate_separation_2026-09-26.md"):
    check(f"batch-04/{f}", os.path.exists(f"batch-04/{f}"), True)
for f in ("ce7_common.py", "ce7_00_haystack_counterfactual.py", "ce7_01_coverage.py", "ce7_02_orphans.py", "ce7_03_vocab.py", "ce7_04_works.py", "ce7_05_separation.py"):
    check(f"batch-04/ce7_analysis/{f}", os.path.exists(f"batch-04/ce7_analysis/{f}"), True)
for f in ("prior_members.json", "vocab_candidates.json", "orphan_clusters.json", "ce7_cov.json", "separation.json", "per_work.json", "tfidf_doc.npz"):
    check(f"cache/{f}", os.path.exists(f"batch-04/ce7_analysis/cache/{f}"), True)
print("== corpus / index ==")
ci = json.load(open("corpus/index/chunk_index.json", encoding="utf-8"))
check("docs", len(ci["by_doc"]), 1290); check("chunks", ci["stats"]["n_chunks"], 13549)
check("chunk_index.json sha (first 8 hex)", sha8("corpus/index/chunk_index.json"), "f89071b9")
check("corpus_dense.npy bytes", os.path.getsize("data/index/corpus_dense.npy"), 13549 * 768 * 4 + 128)
print("== v1 must be untouched ==")
check("topic_map.json sha (first 8 hex)", sha8("corpus/voice/topic_map.json"), "da34048f")
check("topic_centroids.npy sha (first 8 hex)", sha8("data/index/topic_centroids.npy"), "71a7c294")
blob = subprocess.check_output(["git", "cat-file", "blob", "HEAD:corpus/voice/topic_map.json"])
check("topic_map.json == HEAD blob", open("corpus/voice/topic_map.json", "rb").read() == blob, True)
check("topic_centroids shape", np.load("data/index/topic_centroids.npy").shape, (34, 768))
print()
print("ENTRY STATE:", "ALL CHECKS PASSED" if not fail else f"FAILED -> {fail}")
sys.exit(1 if fail else 0)
