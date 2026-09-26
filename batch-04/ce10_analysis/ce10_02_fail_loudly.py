"""CE-10 Step 1 proof: the three cosine sites never fall back to raw. Negative cases (always) + positive case (once v2 centroids exist)."""
import json, os, sys, traceback
from pathlib import Path
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
import numpy as np, config, centering
res = []
def expect_raise(name, fn):
    try: fn(); res.append((name, "DID NOT RAISE  <-- BAD"))
    except centering.CorpusMeanError as e: res.append((name, "raises CorpusMeanError: " + str(e)[:110]))
expect_raise("mean file missing", lambda: centering.load_corpus_mean("0" * 64, path=ROOT / "data/index/does_not_exist.npy"))
expect_raise("sha256 mismatch", lambda: centering.load_corpus_mean("0" * 64))
expect_raise("meta lacks recorded sha", lambda: centering.load_corpus_mean(None))
expect_raise("raw (v1-style) meta", lambda: centering.mean_for_meta({"n_topics": 34, "topic_ids": []}))
expect_raise("meta says centred but no sha", lambda: centering.mean_for_meta({"scale": "centred"}))
# the runtime loader on whatever centroid files are on disk right now
import retrieval
try:
    cen, meta = retrieval._load_centroids(); res.append(("retrieval._load_centroids() on disk", f"loaded {cen.shape}, scale={meta.get('scale')}, taxonomy_version={meta.get('taxonomy_version')}"))
except centering.CorpusMeanError as e: res.append(("retrieval._load_centroids() on disk", "raises CorpusMeanError (expected until v2 centroids exist): " + str(e)[:110]))
for n, r in res: print(f"  {n:38s} {r}")
sys.exit(1 if any("BAD" in r for _, r in res) else 0)
