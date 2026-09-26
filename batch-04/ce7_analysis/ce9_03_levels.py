"""CE-9 step 3: evaluate the granularity family. Base = Ward k=54 on centered document vectors; bottom-up merging with
(duplicate: centered cosine >= 0.70) and (undersize: < m documents). One partition per m. Centered scale only.
Writes cache/ce9_levels.json and cache/ce9_level_m{m}.npy. Read-only on the repo."""
import json, sys, time, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *
from sklearn.metrics import silhouette_score

t0 = time.time()
C = Corpus(); ix = Index(C); N = ix.N
Xc, mu = centered_doc_vectors(C)
cuts = np.load(CACHE / "ce9_cuts.npz")
rng = np.random.default_rng(20260926)
train = rng.random(N) < 0.5; test = ~train
vocab = json.load(open(CACHE / "vocab_candidates.json"))
pools = {k: v for k, v in vocab["keywords_all_ge5"].items() if len(v) >= 10}
fmt = C.doc_fmt
Xn = Xc.copy()
for j in range(Xn.shape[1]): Xn[:, j] = rng.permutation(Xn[:, j])
Xn = unit(Xn)

def level_metrics(m):
    lab, log = bottom_up(Xc, cuts["k54"], m)
    np.save(CACHE / f"ce9_level_m{m}.npy", lab)
    ids, S, cens = voronoi_neighbourhoods(C, Xc, lab)
    K = len(ids); sz = np.array([(lab == c).sum() for c in ids])
    idpos = {c: j for j, c in enumerate(ids)}; own = np.array([idpos[c] for c in lab])
    rank = (-S).argsort(axis=1).argsort(axis=1) + 1
    top1 = float((rank[np.arange(N), own] == 1).mean()); top5 = float((rank[np.arange(N), own] <= 5).mean())
    G = cens @ cens.T; np.fill_diagonal(G, -2); nn = G.max(axis=1)
    sh = []
    for c in ids:
        idx = np.where(lab == c)[0]; vals = []
        for _ in range(20):
            p = rng.permutation(idx); h = len(p) // 2
            vals.append(float(unit(Xc[p[:h]].mean(axis=0)) @ unit(Xc[p[h:2 * h]].mean(axis=0))))
        sh.append(np.median(vals))
    fid = [max(Counter(lab[i] for i in idxs).values()) / len(idxs) for idxs in pools.values()]
    near = S.max(axis=1); floor5 = float(np.quantile(near, 0.05))
    orph = {f: float((near[fmt == f] < floor5).mean()) for f in FMT_ORDER}
    sil = float(silhouette_score(Xc, lab, metric="cosine")); nl = np.array(lab.copy()); rng.shuffle(nl); siln = float(silhouette_score(Xn, lab, metric="cosine"))
    # held-out matchability + random control
    rows, ctl = [], []
    for j, c in enumerate(ids):
        seeds = lab == c
        terms = prune_subsumed(induce(ix, seeds, train)); r = {"n": int(seeds.sum()), "n_terms": len(terms)}
        if terms:
            hit = ix.engine_hits(terms); ts = seeds & test; ch = hit & test
            r["recall"] = float((hit & ts).sum() / max(1, ts.sum())); r["prec_cluster"] = float((hit & ts).sum() / max(1, ch.sum())); r["caught"] = int(ch.sum())
            r["P2"] = float((rank[ch, j] <= 2).mean()) if ch.sum() else float("nan"); r["base2"] = float((rank[:, j] <= 2).mean())
            r["P5"] = float((rank[ch, j] <= 5).mean()) if ch.sum() else float("nan")
        else:
            r.update({"recall": 0.0, "prec_cluster": float("nan"), "caught": 0, "P2": float("nan"), "base2": float((rank[:, j] <= 2).mean()), "P5": float("nan")})
        rows.append(r)
        rnd = np.zeros(N, dtype=bool); rnd[rng.choice(N, size=int(seeds.sum()), replace=False)] = True
        rt = prune_subsumed(induce(ix, rnd, train)); cr = {"n_terms": len(rt), "recall": 0.0}
        if rt:
            hit = ix.engine_hits(rt); ts = rnd & test; cr["recall"] = float((hit & ts).sum() / max(1, ts.sum()))
        ctl.append(cr)
    med = lambda xs: float(np.nanmedian([x for x in xs if x == x])) if any(x == x for x in xs) else float("nan")
    return {"m": m, "N": K, "sizes": sorted(sz.tolist(), reverse=True), "min": int(sz.min()), "max": int(sz.max()), "max_share": float(sz.max() / N),
            "n_marginal_10_19": int(((sz >= 10) & (sz < 20)).sum()), "silhouette": sil, "silhouette_null_shuffled_features": siln,
            "loo_top1": top1, "loo_top5": top5, "nn_centered_median": float(np.median(nn)), "nn_centered_max": float(nn.max()),
            "split_half_median": float(np.median(sh)), "split_half_min": float(np.min(sh)),
            "pool_fidelity_median": float(np.median(fid)), "orphan_at_floor5": orph, "orphan_bio_over_col": float(orph["biography"] / max(orph["columns"], 1e-9)),
            "recall_median": med([r["recall"] for r in rows]), "prec_cluster_median": med([r["prec_cluster"] for r in rows]), "P2_median": med([r["P2"] for r in rows]),
            "P5_median": med([r["P5"] for r in rows]), "lift2_median": med([r["P2"] / r["base2"] if r["base2"] else float("nan") for r in rows]),
            "n_recall_ge_50": int(sum(1 for r in rows if r["recall"] >= 0.5)), "n_no_matcher": int(sum(1 for r in rows if r["n_terms"] == 0)),
            "control_recall_median": med([c["recall"] for c in ctl]), "dims": rows}

out = {}
print(f"{'m':>3s} {'N':>3s} {'min':>4s} {'max%':>5s} {'marg':>4s} {'sil/null':>11s} {'top1':>5s} {'top5':>5s} {'nn max':>6s} {'sh med/min':>11s} {'fid':>5s} {'orph col/bk/sp/bio @5%':>24s} {'recall':>6s} {'P@2':>5s} {'P@5':>5s} {'lift2':>5s} {'r>=.5':>6s} {'none':>4s} {'ctl':>4s}")
for m in (10, 15, 20, 25, 30, 40):
    x = level_metrics(m); out[m] = x
    o = x["orphan_at_floor5"]
    print(f"{m:3d} {x['N']:3d} {x['min']:4d} {100*x['max_share']:4.1f}% {x['n_marginal_10_19']:4d} {x['silhouette']:5.3f}/{x['silhouette_null_shuffled_features']:5.3f} {x['loo_top1']:5.2f} {x['loo_top5']:5.2f} {x['nn_centered_max']:6.2f} "
          f"{x['split_half_median']:5.2f}/{x['split_half_min']:.2f} {x['pool_fidelity_median']:5.2f} {' / '.join(f'{100*o[f]:.0f}%' for f in FMT_ORDER):>24s} {x['recall_median']:6.2f} {x['P2_median']:5.2f} {x['P5_median']:5.2f} {x['lift2_median']:5.1f} "
          f"{x['n_recall_ge_50']:>3d}/{x['N']:<2d} {x['n_no_matcher']:4d} {x['control_recall_median']:4.2f}", flush=True)
json.dump({str(k): v for k, v in out.items()}, open(CACHE / "ce9_levels.json", "w"), indent=1, default=float)
print("done", round(time.time() - t0), "s")
