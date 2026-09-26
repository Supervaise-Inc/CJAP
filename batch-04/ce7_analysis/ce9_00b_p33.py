"""CE-9 step 0b: reproduce the P3.3 collapse (34 -> 3 topics) and show why the raw-cosine merge gate cannot work in this embedding space.
Read-only: loads the STORED v1 centroids (data/index/topic_centroids.npy, untouched) and the archived collapsed run's metadata. Writes cache/ce9_p33.json."""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

C = Corpus(); N = len(C.doc_ids)
cen = np.load(IDX / "topic_centroids.npy").astype(np.float64); ids = json.load(open(IDX / "topic_centroids_meta.json", encoding="utf-8"))["topic_ids"]
arch = json.load(open(IDX / "_archive" / "_collapsed_2026-09-26_topic_centroids_meta.json", encoding="utf-8"))
print("archived collapsed run:", {k: arch[k] for k in ("n_topics", "premerge_n_topics", "merge_cosine") if k in arch}, "merged pairs:", len(arch.get("merged_pairs", [])))
n = len(ids); G = cen @ cen.T; iu = np.triu_indices(n, 1); pv = G[iu]
print(f"stored v1 centroids: {n} topics, {len(pv)} pairs; raw pair cosine mean {pv.mean():.4f} median {np.median(pv):.4f} min {pv.min():.4f} max {pv.max():.4f}")
def groups_at(th):
    parent = list(range(n))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    npairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            if G[i, j] > th: npairs += 1; parent[find(i)] = find(j)
    return len({find(i) for i in range(n)}), npairs
sweep = {}
for th in (0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.01):
    g, p = groups_at(th); sweep[str(th)] = {"topics_left": g, "pairs_above": p}
    print(f"  raw threshold {th:.2f}: {p:3d} of {len(pv)} pairs above -> {g} topics left")
# random document groups: raw vs centred
rng = np.random.default_rng(20260926)
mu = C.mat.mean(axis=0).astype(np.float64)
def cen_of(docs, centred):
    rows = [r for d in docs for r in C.rows_of[C.doc_ids[d]]]; v = C.mat[rows].astype(np.float64).mean(axis=0)
    return unit(v - mu) if centred else unit(v)
raw, cc = [], []
for _ in range(600):
    a = rng.choice(N, 30, replace=False); b = rng.choice(np.setdiff1d(np.arange(N), a), 30, replace=False)
    raw.append(float(cen_of(a, False) @ cen_of(b, False))); cc.append(float(cen_of(a, True) @ cen_of(b, True)))
raw, cc = np.array(raw), np.array(cc)
print(f"600 pairs of independent random 30-doc groups: raw cosine mean {raw.mean():.3f} (min {raw.min():.3f}); centred mean {cc.mean():.3f} p95 {np.percentile(cc, 95):.3f} max {cc.max():.3f}")
json.dump({"archived": {k: arch.get(k) for k in ("n_topics", "premerge_n_topics", "merge_cosine")} | {"merged_pairs": len(arch.get("merged_pairs", []))},
           "stored_v1": {"n_topics": n, "n_pairs": int(len(pv)), "raw_mean": float(pv.mean()), "raw_median": float(np.median(pv)), "raw_min": float(pv.min()), "raw_max": float(pv.max())},
           "sweep": sweep, "random_groups_30": {"n": 600, "raw_mean": float(raw.mean()), "raw_min": float(raw.min()), "centred_mean": float(cc.mean()), "centred_p95": float(np.percentile(cc, 95)), "centred_max": float(cc.max())}},
          open(CACHE / "ce9_p33.json", "w"), indent=1)
