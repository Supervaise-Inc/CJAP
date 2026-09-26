"""CE-9 step 2: how matchable are dimensions at each granularity? Train/test split by document + random-set control.
For each Ward cut: induce a matcher on the TRAIN half only, score on the TEST half with the real v1 engine.
Writes cache/ce9_matchability.json. Read-only on the repo. Centered scale only."""
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
Xc, mu = centered_doc_vectors(C)
print("index built", ix.B.shape, round(time.time() - t0), "s", flush=True)
rng = np.random.default_rng(20260926)
train = rng.random(N) < 0.5; test = ~train
cuts = np.load(CACHE / "ce9_cuts.npz")
KS = (12, 30, 42)
res = {}
for k in KS:
    lab = cuts[f"k{k}"]; ids, S, cens = voronoi_neighbourhoods(C, Xc, lab)
    rank = (-S).argsort(axis=1).argsort(axis=1) + 1        # rank of each cluster for each doc (1 = nearest)
    rows, crow = [], []
    for j, c in enumerate(ids):
        seeds = lab == c
        terms = prune_subsumed(induce(ix, seeds, train))
        real = {"cluster": int(c), "n": int(seeds.sum()), "n_terms": len(terms), "terms": terms[:12]}
        if terms:
            hit = ix.engine_hits(terms)
            ts = seeds & test; ch = hit & test
            real["recall_test"] = float((hit & ts).sum() / max(1, ts.sum()))
            real["prec_cluster_test"] = float((hit & ts).sum() / max(1, ch.sum()))
            real["caught_test"] = int(ch.sum())
            for r in (1, 2, 5):
                real[f"P@{r}"] = float((rank[ch, j] <= r).mean()) if ch.sum() else float("nan")
                real[f"base@{r}"] = float((rank[:, j] <= r).mean())
        else:
            real.update({"recall_test": 0.0, "prec_cluster_test": float("nan"), "caught_test": 0})
        # control: a random document set of the same size, same procedure
        rnd = np.zeros(N, dtype=bool); rnd[rng.choice(N, size=int(seeds.sum()), replace=False)] = True
        rt = prune_subsumed(induce(ix, rnd, train))
        ctl = {"n_terms": len(rt)}
        if rt:
            hit = ix.engine_hits(rt); ts = rnd & test; ch = hit & test
            ctl["recall_test"] = float((hit & ts).sum() / max(1, ts.sum())); ctl["prec_test"] = float((hit & ts).sum() / max(1, ch.sum())); ctl["caught_test"] = int(ch.sum())
        else:
            ctl.update({"recall_test": 0.0, "prec_test": float("nan"), "caught_test": 0})
        rows.append(real); crow.append(ctl)
    med = lambda xs: float(np.nanmedian([x for x in xs if x == x])) if any(x == x for x in xs) else float("nan")
    res[k] = {"dims": rows, "control": crow,
              "median_recall_test": med([r["recall_test"] for r in rows]), "median_prec_cluster_test": med([r["prec_cluster_test"] for r in rows]),
              "median_P@1": med([r.get("P@1", float("nan")) for r in rows]), "median_P@2": med([r.get("P@2", float("nan")) for r in rows]), "median_P@5": med([r.get("P@5", float("nan")) for r in rows]),
              "median_lift@2": med([r.get("P@2", float("nan")) / r["base@2"] if r.get("base@2") else float("nan") for r in rows]),
              "n_dims_recall_ge_50": int(sum(1 for r in rows if r["recall_test"] >= 0.5)),
              "n_dims_no_matcher": int(sum(1 for r in rows if r["n_terms"] == 0)),
              "control_median_recall_test": med([c["recall_test"] for c in crow]), "control_median_prec_test": med([c["prec_test"] for c in crow])}
    x = res[k]
    print(f"k={k:2d}: held-out recall median {x['median_recall_test']:.2f} | cluster-precision median {x['median_prec_cluster_test']:.2f} | P@1 {x['median_P@1']:.2f} P@2 {x['median_P@2']:.2f} P@5 {x['median_P@5']:.2f} "
          f"| lift@2 {x['median_lift@2']:.1f}x | dims with recall>=0.5: {x['n_dims_recall_ge_50']}/{len(rows)} | no matcher: {x['n_dims_no_matcher']} "
          f"|| CONTROL (random sets) recall {x['control_median_recall_test']:.2f} precision {x['control_median_prec_test']:.2f}", flush=True)
json.dump({str(k): v for k, v in res.items()}, open(CACHE / "ce9_matchability.json", "w"), indent=1, default=float)
print("done", round(time.time() - t0), "s")
