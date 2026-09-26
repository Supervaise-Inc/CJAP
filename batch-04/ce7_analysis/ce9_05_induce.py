"""CE-9 step 5: induce a matcher per recommended dimension on ALL documents, evaluate with the real engine.
Writes cache/ce9_induced.json (terms per cluster + metrics). Read-only on the repo. Centered scale only.
Induction settings 'F' (chosen from the held-out grid in ce9 exploration): p_min 0.55, s_min_frac 0.03, min_gain 1, max_terms 25, target 0.95."""
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
C = Corpus(); ix = Index(C); N = ix.N; Xc, mu = centered_doc_vectors(C)
M = int(sys.argv[1]) if len(sys.argv) > 1 else 20
lab = np.load(CACHE / f"ce9_level_m{M}.npy"); ids, S, cens = voronoi_neighbourhoods(C, Xc, lab)
rank = (-S).argsort(axis=1).argsort(axis=1) + 1
allmask = np.ones(N, dtype=bool)
SETTINGS = dict(p_min=0.55, s_min_frac=0.03, s_min_abs=3, min_gain=1, max_terms=25, target=0.95)
out = {}
print(f"{'cl':>3s} {'seeds':>5s} {'terms':>5s} {'caught':>6s} {'in-seeds':>8s} {'recall':>6s} {'P@1':>5s} {'P@3':>5s} {'P@5':>5s} {'lift@3':>6s}  recall by format col/book/spe/bio")
for j, c in enumerate(ids):
    seeds = lab == c
    terms = prune_subsumed(induce(ix, seeds, allmask, **SETTINGS))
    hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    n = int(seeds.sum()); ca = int(hit.sum())
    prec = float((hit & seeds).sum() / max(1, ca)); rec = float((hit & seeds).sum() / n)
    P = {r: float((rank[hit, j] <= r).mean()) if ca else float("nan") for r in (1, 3, 5)}
    base3 = float((rank[:, j] <= 3).mean())
    byf = {f: float((hit & seeds & (C.doc_fmt == f)).sum() / max(1, (seeds & (C.doc_fmt == f)).sum())) if (seeds & (C.doc_fmt == f)).sum() else None for f in FMT_ORDER}
    out[int(c)] = {"n": n, "terms": terms, "caught": ca, "prec_seeds": prec, "recall": rec, "P1": P[1], "P3": P[3], "P5": P[5], "base3": base3, "recall_by_format": byf,
                   "entity_terms": [t for t in terms if t in ix.entity_terms]}
    print(f"{c:3d} {n:5d} {len(terms):5d} {ca:6d} {prec:8.2f} {rec:6.2f} {P[1]:5.2f} {P[3]:5.2f} {P[5]:5.2f} {P[3]/base3 if base3 else float('nan'):6.1f}  "
          + "/".join("-" if v is None else f"{v:.2f}" for v in byf.values()), flush=True)
json.dump(out, open(CACHE / f"ce9_induced_m{M}.json", "w"), indent=1, default=float)
print("done", round(time.time() - t0), "s")
