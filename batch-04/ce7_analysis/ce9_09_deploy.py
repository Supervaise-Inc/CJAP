"""CE-9 step 9: what the recommended dimensions look like WHEN DEPLOYED (members = documents their matchers catch, centroid = production recipe on the
CENTRED scale). Produces: matcher metrics, separability, the two thresholds' evidence, per-format orphan rates, v1 baseline under the same definitions.
Read-only on the repo. Centred scale only (raw cosine is below the noise floor in this space and is never used as evidence here).

Definitions
  centred vector   : unit(v - mu),  mu = mean of ALL 13,549 chunk vectors (one stored vector; the code change the proposal asks for)
  deployed centroid: unit(mean of ALL chunks of the member docs - mu)   [build_centroids_fullcorpus recipe, centred]
  affinity         : 'best-chunk' = max over a doc's chunks of centred-chunk . centroid;  'doc-mean' = centred doc-mean . centroid
  neighbourhood    : dimension j is in doc i's neighbourhood when j is among i's 3 nearest dimensions (MAX_TOPIC_TAGS = 3), leave-one-out
  LOO              : a member doc is removed from its own dimension's centroid before its affinity to that dimension is measured
Usage: ce9_09_deploy.py <matchers_json> <out_json>      matchers_json: {"<cluster>": {"keywords": [...], "entities": [...]}, ...}"""
import json, sys, time, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

t0 = time.time()
C = Corpus(); ix = Index(C); N = ix.N
Xc, mu = centered_doc_vectors(C)                       # doc-mean, centred, unit (float64)
mu64 = mu.astype(np.float64)
Zc = unit(C.mat.astype(np.float64) - mu64).astype(np.float32)   # centred chunk vectors
ns = C.n_chunks.astype(np.float64)
DS = np.stack([C.mat[C.rows_of[d]].astype(np.float64).sum(axis=0) for d in C.doc_ids])      # per-doc raw chunk sums
chunk_doc_idx = np.array([C.doc_index[d] for d in C.chunk_doc]); order = np.argsort(chunk_doc_idx, kind="stable")
starts = np.searchsorted(chunk_doc_idx[order], np.arange(N))
fmt = C.doc_fmt

def seg_max(v): return np.maximum.reduceat(v[order], starts)

def affinity(H, loo=True):
    """H[N,K] bool membership -> (best_chunk[N,K], doc_mean[N,K], centroids[K,768])"""
    K = H.shape[1]; BC = np.zeros((N, K)); DM = np.zeros((N, K)); CEN = np.zeros((K, 768))
    for j in range(K):
        mem = np.where(H[:, j])[0]
        if len(mem) == 0: continue
        S = DS[mem].sum(axis=0); n = ns[mem].sum()
        cen = unit(S / n - mu64); CEN[j] = cen
        BC[:, j] = seg_max(Zc @ cen.astype(np.float32)); DM[:, j] = Xc @ cen
        if loo and len(mem) > 1:
            for i in mem:
                c2 = unit((S - DS[i]) / (n - ns[i]) - mu64)
                BC[i, j] = float((Zc[C.rows_of[C.doc_ids[i]]] @ c2.astype(np.float32)).max()); DM[i, j] = float(Xc[i] @ c2)
    return BC, DM, CEN

def neighbourhood_precision(H):
    """doc-mean centroids of the member sets, leave-one-out; P@1/3/5 of member docs under 'own dimension among the doc's top-r'. Also lift vs base and a random-membership control."""
    K = H.shape[1]; sums = np.stack([Xc[H[:, j]].sum(axis=0) for j in range(K)]); S = np.zeros((N, K))
    cenu = unit(sums)
    S = Xc @ cenu.T
    for j in range(K):
        for i in np.where(H[:, j])[0]:
            c2 = unit(sums[j] - Xc[i]); S[i, j] = float(Xc[i] @ c2)
    rank = (-S).argsort(axis=1).argsort(axis=1) + 1
    res = []
    for j in range(K):
        mem = H[:, j]
        res.append({r: (float((rank[mem, j] <= r).mean()) if mem.sum() else float("nan")) for r in (1, 3, 5)} | {"caught": int(mem.sum()), "base3": float((rank[:, j] <= 3).mean())})
    return res, rank

def summarize_pairs(cen):
    G = cen @ cen.T; K = len(cen); np.fill_diagonal(G, -2); iu = np.triu_indices(K, 1)
    return G, G[iu]

if __name__ == "__main__":
    mfile, ofile = sys.argv[1], sys.argv[2]
    M = json.load(open(mfile)); K = len(M)      # partition clusters are ints; extra candidate dimensions are strings
    cl = sorted(((int(c) if c.isdigit() else c) for c in M), key=lambda c: (isinstance(c, str), c))
    lab = np.load(CACHE / "ce9_level_final.npy")
    H = np.zeros((N, K), dtype=bool)
    for j, c in enumerate(cl):
        H[:, j] = ix.engine_hits(list(M[str(c)]["keywords"]) + list(M[str(c)].get("entities", [])))
    print(f"K={K} dimensions; docs matched by >=1: {int(H.any(1).sum())}/{N}; mean tags/doc {H.sum(1).mean():.2f}", flush=True)
    out = {"clusters": cl, "caught": H.sum(0).tolist()}

    # ---------- matcher precision (neighbourhood, deployed membership) + random control
    prec, rank = neighbourhood_precision(H)
    rng = np.random.default_rng(20260926)
    Hr = np.zeros_like(H)
    for j in range(K): Hr[rng.choice(N, size=int(H[:, j].sum()), replace=False), j] = True
    prec_r, _ = neighbourhood_precision(Hr)
    # same, against the derived partition (what the matcher was induced against)
    isc = [isinstance(c, int) for c in cl]
    seeds_in = [float((H[:, j] & (lab == cl[j])).sum() / max(1, H[:, j].sum())) if isc[j] else None for j in range(K)]
    seeds_rec = [float((H[:, j] & (lab == cl[j])).sum() / max(1, (lab == cl[j]).sum())) if isc[j] else None for j in range(K)]
    byf = [{f: int((H[:, j] & (fmt == f)).sum()) for f in FMT_ORDER} for j in range(K)]
    def _rb(j, f):
        if not isc[j]: return None
        base = (lab == cl[j]) & (fmt == f)
        return float((H[:, j] & base).sum() / base.sum()) if base.sum() else None
    rbyf = [{f: _rb(j, f) for f in FMT_ORDER} for j in range(K)]
    out["precision"] = [dict(cluster=cl[j], caught=prec[j]["caught"], P1=prec[j][1], P3=prec[j][3], P5=prec[j][5], base3=prec[j]["base3"], control_P3=prec_r[j][3],
                             in_derived_cluster=seeds_in[j], recall_of_cluster=seeds_rec[j], caught_by_format=byf[j], recall_by_format=rbyf[j]) for j in range(K)]
    print("median P@3 %.2f (random-membership control %.2f, base rate %.2f)" % (np.nanmedian([p[3] for p in prec]), np.nanmedian([p[3] for p in prec_r]), np.nanmedian([p["base3"] for p in prec])), flush=True)

    # ---------- v1 baseline: same definition, same code
    members = json.load(open(CACHE / "prior_members.json")); v1ids = sorted(t for t in members if members[t])
    H1 = np.zeros((N, len(v1ids)), dtype=bool)
    for j, t in enumerate(v1ids):
        for d in members[t]: H1[C.doc_index[d], j] = True
    prec1, _ = neighbourhood_precision(H1)
    out["v1_precision"] = [dict(id=t, caught=prec1[j]["caught"], P1=prec1[j][1], P3=prec1[j][3], P5=prec1[j][5], base3=prec1[j]["base3"]) for j, t in enumerate(v1ids)]
    print("v1: median caught %d, median P@3 %.2f (base rate %.2f)" % (np.median([p["caught"] for p in prec1]), np.nanmedian([p[3] for p in prec1]), np.nanmedian([p["base3"] for p in prec1])), flush=True)

    # ---------- deployed centroids, separability, duplicate-threshold evidence
    BC, DM, CEN = affinity(H, loo=False)
    G, pairs = summarize_pairs(CEN)
    mx = [(float(G[j].max()), cl[int(G[j].argmax())]) for j in range(K)]
    fid = [float(CEN[j] @ unit(Xc[lab == cl[j]].mean(axis=0))) if isc[j] else None for j in range(K)]     # deployed (matcher-built) centroid vs the derived cluster's own centroid
    out["separability"] = [dict(cluster=cl[j], max_cos=mx[j][0], nearest=mx[j][1], fidelity_to_derived_cluster=fid[j]) for j in range(K)]
    out["pair_distribution"] = {"n_pairs": int(len(pairs)), "median": float(np.median(pairs)), "p90": float(np.percentile(pairs, 90)), "p95": float(np.percentile(pairs, 95)), "max": float(pairs.max()),
                                "ge_0.5": int((pairs >= 0.5).sum()), "ge_0.6": int((pairs >= 0.6).sum()), "ge_0.65": int((pairs >= 0.65).sum()), "ge_0.68": int((pairs >= 0.68).sum()), "ge_0.7": int((pairs >= 0.7).sum()), "ge_0.75": int((pairs >= 0.75).sum()), "ge_0.8": int((pairs >= 0.8).sum())}
    top = np.dstack(np.unravel_index(np.argsort(-np.triu(np.where(G > -2, G, -2), 1).ravel())[:12], G.shape))[0]
    out["top_pairs"] = [dict(a=cl[int(a)], b=cl[int(b)], cos=float(G[a, b])) for a, b in top]
    print("deployed pair cosines (centred): median %.2f p90 %.2f p95 %.2f max %.2f | >=.5: %d >=.6: %d >=.7: %d >=.8: %d" % (
        out["pair_distribution"]["median"], out["pair_distribution"]["p90"], out["pair_distribution"]["p95"], out["pair_distribution"]["max"],
        out["pair_distribution"]["ge_0.5"], out["pair_distribution"]["ge_0.6"], out["pair_distribution"]["ge_0.7"], out["pair_distribution"]["ge_0.8"]), flush=True)
    for a, b in top[:8]: print(f"   d{cl[int(a)]} - d{cl[int(b)]}  {G[a, b]:.3f}", flush=True)
    # same-dimension split halves (docs), and null random groups of the same sizes
    def cen_of(mem): return unit(DS[mem].sum(axis=0) / ns[mem].sum() - mu64)
    sh = []
    for j in range(K):
        mem = np.where(H[:, j])[0]
        if len(mem) < 6: continue
        for _ in range(30):
            p = rng.permutation(mem); h = len(p) // 2; sh.append(float(cen_of(p[:h]) @ cen_of(p[h:])))
    sh = np.array(sh)
    nul = []
    sizes = H.sum(0)
    for _ in range(4000):
        a = rng.choice(N, size=int(rng.choice(sizes)), replace=False); rest = np.setdiff1d(np.arange(N), a)
        b = rng.choice(rest, size=int(rng.choice(sizes)), replace=False); nul.append(float(cen_of(a) @ cen_of(b)))
    nul = np.array(nul)
    out["dup_evidence"] = {"same_dim_split_half": {"median": float(np.median(sh)), "p25": float(np.percentile(sh, 25)), "p10": float(np.percentile(sh, 10)), "p05": float(np.percentile(sh, 5)), "min": float(sh.min()), "n": int(len(sh)),
                                                "frac_ge_0.60": float((sh >= 0.60).mean()), "frac_ge_0.70": float((sh >= 0.70).mean()), "frac_ge_0.75": float((sh >= 0.75).mean())},
                           "random_groups": {"mean": float(nul.mean()), "p95": float(np.percentile(nul, 95)), "p99": float(np.percentile(nul, 99)), "max": float(nul.max()), "n": int(len(nul))}}
    print("same-dimension split halves: median %.2f p10 %.2f p05 %.2f min %.2f | random groups: mean %.3f p95 %.3f p99 %.3f max %.3f" % (
        np.median(sh), np.percentile(sh, 10), np.percentile(sh, 5), sh.min(), nul.mean(), np.percentile(nul, 95), np.percentile(nul, 99), nul.max()), flush=True)

    # ---------- floor: affinities with and without LOO, observed vs multiple-comparison null
    BCl, DMl, _ = affinity(H, loo=True)
    def best(A): return A.max(axis=1)
    NULL = {"best_chunk": [], "doc_mean": []}
    REPS = 6
    for r in range(REPS):
        Hn = np.zeros_like(H)
        for j in range(K): Hn[rng.choice(N, size=int(H[:, j].sum()), replace=False), j] = True
        bc, dm, _ = affinity(Hn, loo=True)
        NULL["best_chunk"].append(best(bc)); NULL["doc_mean"].append(best(dm))
        print(f"  null replicate {r+1}/{REPS} [{time.time()-t0:.0f}s]", flush=True)
    fl = {}
    for name, obs, obs_in in (("best_chunk", best(BCl), best(BC)), ("doc_mean", best(DMl), best(DM))):
        nl = np.concatenate(NULL[name])
        nlf = {f: np.concatenate([NULL[name][r][fmt == f] for r in range(REPS)]) for f in FMT_ORDER}
        d = {"observed_LOO_pct": {p: float(np.percentile(obs, p)) for p in (1, 2, 5, 10, 25, 50, 75)}, "null_pct": {p: float(np.percentile(nl, p)) for p in (5, 25, 50, 75, 90, 95, 99)},
             "auc_observed_vs_null": float((np.searchsorted(np.sort(nl), obs, side="left")).mean() / len(nl)),
             "by_format_null_p50": {f: float(np.percentile(nlf[f], 50)) for f in FMT_ORDER}, "by_format_null_p25": {f: float(np.percentile(nlf[f], 25)) for f in FMT_ORDER},
             "by_format_auc": {f: float((np.searchsorted(np.sort(nlf[f]), obs[fmt == f], side="left")).mean() / len(nlf[f])) for f in FMT_ORDER},
             "by_format_observed_LOO_median": {f: float(np.median(obs[fmt == f])) for f in FMT_ORDER}, "by_format_null_p95": {f: float(np.percentile(nlf[f], 95)) for f in FMT_ORDER},
             "by_format_null_p99": {f: float(np.percentile(nlf[f], 99)) for f in FMT_ORDER}, "by_format_observed_LOO_p05": {f: float(np.percentile(obs[fmt == f], 5)) for f in FMT_ORDER}, "grid": {}}
        for f in np.round(np.arange(0.10, 0.80, 0.02), 2):
            d["grid"][str(f)] = {"all_LOO": float((obs < f).mean()), "all_in_sample": float((obs_in < f).mean()), **{fm: float((obs[fmt == fm] < f).mean()) for fm in FMT_ORDER},
                                 "null_all": float((nl < f).mean())}
        fl[name] = d
        print(name, "observed LOO pct", {k: round(v, 3) for k, v in d["observed_LOO_pct"].items()}, "| null pct", {k: round(v, 3) for k, v in d["null_pct"].items()}, flush=True)
    out["floor"] = fl
    np.save(CACHE / (Path(ofile).stem + "_centroids.npy"), CEN.astype(np.float32))
    np.save(CACHE / (Path(ofile).stem + "_H.npy"), H)
    np.save(CACHE / (Path(ofile).stem + "_bc_loo.npy"), BCl); np.save(CACHE / (Path(ofile).stem + "_dm_loo.npy"), DMl)
    json.dump(out, open(ofile, "w"), indent=1, default=float)
    print("done", round(time.time() - t0), "s")
