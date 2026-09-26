"""CE-9 step 1: whole-corpus derivation. Ward tree on CENTERED document vectors; metrics per granularity.
Reuses ce7_common (Corpus loader, definitions). Read-only on the repo. Writes cache/ce9_tree.json + cache/ce9_cuts.npz.
All separability figures are on the CENTERED scale; raw cosine is not used as evidence anywhere."""
import json, sys, time, warnings
from collections import Counter
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score, adjusted_rand_score

t0 = time.time()
C = Corpus(); N = len(C.doc_ids); mu = C.mat.mean(axis=0)
dm = np.stack([C.mat[C.rows_of[d]].mean(axis=0) for d in C.doc_ids])
Xc = unit(dm - mu).astype(np.float64)
rng = np.random.default_rng(20260926)
Z = linkage(Xc, method="ward")
KS = (8, 10, 12, 14, 18, 24, 30, 36, 42, 48, 54)
vocab = json.load(open(CACHE / "vocab_candidates.json"))
pools = {k: v for k, v in vocab["keywords_all_ge5"].items() if len(v) >= 10}      # curated keyword pools with >= 10 documents
fmt = C.doc_fmt

# shuffled-feature null (destroys structure, keeps marginals)
Xn = Xc.copy()
for j in range(Xn.shape[1]): Xn[:, j] = rng.permutation(Xn[:, j])
Xn = unit(Xn); Zn = linkage(Xn, method="ward")

def loo_centroids(lab):
    """centered document-mean centroids, and for each doc its similarity to every cluster's centroid with the doc itself removed from its own cluster."""
    ids = sorted(set(lab)); K = len(ids)
    sums = np.stack([Xc[lab == c].sum(axis=0) for c in ids]); cnt = np.array([(lab == c).sum() for c in ids])
    S = np.zeros((N, K))
    for i in range(N):
        own = ids.index(lab[i])
        cen = sums.copy(); cen[own] = cen[own] - Xc[i]
        cen = unit(cen)
        S[i] = cen @ Xc[i]
    return ids, S, unit(sums), cnt

out = {}
print(f"{'k':>3s} {'sil':>6s} {'null':>6s} {'bootARI':>7s} {'min':>4s} {'10-19':>5s} {'loo top1':>8s} {'nn-cos med/max':>15s} {'split-half med/min':>19s} {'pool fid':>9s} {'orph@5% col/book/spe/bio':>26s}")
for k in KS:
    lab = fcluster(Z, k, "maxclust"); labn = fcluster(Zn, k, "maxclust")
    sz = np.bincount(lab)[1:]
    sil = silhouette_score(Xc, lab, metric="cosine"); siln = silhouette_score(Xn, labn, metric="cosine")
    aris = []
    for r in range(10):
        sub = np.sort(rng.choice(N, size=int(0.8 * N), replace=False))
        lb = fcluster(linkage(Xc[sub], method="ward"), k, "maxclust"); aris.append(adjusted_rand_score(lab[sub], lb))
    ids, S, cens, cnt = loo_centroids(lab)
    own = np.array([ids.index(l) for l in lab])
    top1 = float((S.argmax(axis=1) == own).mean())
    G = cens @ cens.T; np.fill_diagonal(G, -1); nn = G.max(axis=1)
    # split-half centroid stability (centered cosine between centroids of two random halves of each cluster)
    sh = []
    for c in ids:
        idx = np.where(lab == c)[0]
        if len(idx) < 4: continue
        vals = []
        for _ in range(20):
            p = rng.permutation(idx); h = len(p) // 2
            vals.append(float(unit(Xc[p[:h]].mean(axis=0)) @ unit(Xc[p[h:2 * h]].mean(axis=0))))
        sh.append(np.median(vals))
    # keyword-pool fidelity
    fid = []
    for v, idxs in pools.items():
        cc = Counter(lab[i] for i in idxs); fid.append(max(cc.values()) / len(idxs))
    # orphan rate at the floor that orphans 5% overall; per format (LOO doc-mean cosine to nearest cluster)
    near = S.max(axis=1); floor5 = float(np.quantile(near, 0.05))
    orph = {f: float((near[fmt == f] < floor5).mean()) for f in FMT_ORDER}
    out[k] = {"k": k, "sil": float(sil), "null_sil": float(siln), "boot_ari": float(np.mean(aris)), "min_size": int(sz.min()), "sizes": sorted(sz.tolist(), reverse=True),
              "n_marginal_10_19": int(((sz >= 10) & (sz < 20)).sum()), "n_lt10": int((sz < 10).sum()), "loo_top1": top1, "nn_cos_median": float(np.median(nn)), "nn_cos_max": float(nn.max()),
              "split_half_median": float(np.median(sh)), "split_half_min": float(np.min(sh)), "pool_fidelity_median": float(np.median(fid)), "pool_fidelity_ge50": float(np.mean(np.array(fid) >= 0.5)),
              "floor_5pct": floor5, "orphan_at_floor5": orph}
    print(f"{k:3d} {sil:6.3f} {siln:6.3f} {np.mean(aris):7.2f} {sz.min():4d} {int(((sz>=10)&(sz<20)).sum()):5d} {top1:8.2f} {np.median(nn):7.2f}/{nn.max():.2f} {np.median(sh):11.2f}/{np.min(sh):.2f} {np.median(fid):9.2f} "
          f"{' / '.join(f'{100*orph[f]:.0f}%' for f in FMT_ORDER):>26s}", flush=True)
np.savez(CACHE / "ce9_cuts.npz", **{f"k{k}": fcluster(Z, k, "maxclust") for k in KS}, doc_ids=np.array(C.doc_ids))
json.dump(out, open(CACHE / "ce9_tree.json", "w"), indent=1)
print("done", round(time.time() - t0), "s;", len(pools), "keyword pools >= 10 docs")
