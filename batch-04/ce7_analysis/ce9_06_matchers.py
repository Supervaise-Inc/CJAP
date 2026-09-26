"""CE-9 step 6: topical matcher induction on ALL documents + per-format top-up, evaluated with the real v1 engine.
Candidates are restricted to topical sources (cluster TF-IDF terms, curated keywords, entity names). Writes cache/ce9_matchers_m{M}.json.
Also runs a 2-fold held-out estimate of the same procedure (learn on one half, score on the other) and a random-set control."""
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
C = Corpus(); ix = Index(C); tp = Topical(C, ix); N = ix.N; Xc, mu = centered_doc_vectors(C)
M = int(sys.argv[1]) if len(sys.argv) > 1 else 20
lab = np.load(CACHE / f"ce9_level_m{M}.npy"); ids, S, cens = voronoi_neighbourhoods(C, Xc, lab)
rank = (-S).argsort(axis=1).argsort(axis=1) + 1
fmt = C.doc_fmt
allm = np.ones(N, dtype=bool)
P_MIN = 0.5

def build(seeds, train, cover_formats=True):
    terms = prune_subsumed(induce_topical(ix, tp, seeds, train, p_min=P_MIN))
    if cover_formats:
        for f in FMT_ORDER:
            sf = seeds & (fmt == f) & train
            if sf.sum() < 3: continue
            hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
            if (hit & sf).sum() / sf.sum() >= 0.5: continue
            extra = induce_topical(ix, tp, seeds, train, p_min=P_MIN, cover=sf & ~hit, k_tfidf=200)
            terms = prune_subsumed(list(terms) + list(extra))
    return terms

# ---- final matchers (all documents)
out = {}
print(f"{'cl':>3s} {'seeds':>5s} {'terms':>5s} {'caught':>6s} {'in-seeds':>8s} {'recall':>6s} {'P@1':>5s} {'P@3':>5s} {'P@5':>5s} {'lift@3':>6s}  recall by format col/book/spe/bio")
for j, c in enumerate(ids):
    seeds = lab == c
    terms = build(seeds, allm)
    hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    n = int(seeds.sum()); ca = int(hit.sum())
    P = {r: float((rank[hit, j] <= r).mean()) if ca else float("nan") for r in (1, 3, 5)}
    base3 = float((rank[:, j] <= 3).mean())
    byf = {f: (float((hit & seeds & (fmt == f)).sum() / (seeds & (fmt == f)).sum()) if (seeds & (fmt == f)).sum() else None) for f in FMT_ORDER}
    out[int(c)] = {"n": n, "terms": terms, "caught": ca, "prec_seeds": float((hit & seeds).sum() / max(1, ca)), "recall": float((hit & seeds).sum() / n), "P1": P[1], "P3": P[3], "P5": P[5], "base3": base3,
                   "recall_by_format": byf, "entity_terms": [t for t in terms if t in ix.entity_terms], "caught_by_format": {f: int((hit & (fmt == f)).sum()) for f in FMT_ORDER}}
    print(f"{c:3d} {n:5d} {len(terms):5d} {ca:6d} {out[int(c)]['prec_seeds']:8.2f} {out[int(c)]['recall']:6.2f} {P[1]:5.2f} {P[3]:5.2f} {P[5]:5.2f} {P[3]/base3 if base3 else float('nan'):6.1f}  "
          + "/".join("-" if v is None else f"{v:.2f}" for v in byf.values()), flush=True)

# ---- held-out estimate of the same procedure + random control
rng = np.random.default_rng(20260926); train = rng.random(N) < 0.5; test = ~train
rec, p3, lf, ctl = [], [], [], []
for j, c in enumerate(ids):
    seeds = lab == c; terms = build(seeds, train)
    if terms:
        hit = ix.engine_hits(terms); ts = seeds & test; ch = hit & test
        rec.append((hit & ts).sum() / max(1, ts.sum()))
        if ch.sum(): p3.append((rank[ch, j] <= 3).mean()); lf.append((rank[ch, j] <= 3).mean() / (rank[:, j] <= 3).mean())
    else: rec.append(0.0)
    rnd = np.zeros(N, dtype=bool); rnd[rng.choice(N, size=int(seeds.sum()), replace=False)] = True
    rt = build(rnd, train, cover_formats=False)
    ctl.append(float(((ix.engine_hits(rt) & rnd & test).sum() / max(1, (rnd & test).sum())) if rt else 0.0))
held = {"recall_median": float(np.median(rec)), "P3_median": float(np.median(p3)), "lift3_median": float(np.median(lf)), "n_recall_ge_50": int(sum(r >= 0.5 for r in rec)), "control_recall_median": float(np.median(ctl))}
print("HELD-OUT (procedure incl. per-format top-up): recall median %.2f | P@3 %.2f | lift@3 %.1fx | dims recall>=.5: %d/%d | random-set control recall %.2f" %
      (held["recall_median"], held["P3_median"], held["lift3_median"], held["n_recall_ge_50"], len(ids), held["control_recall_median"]))
json.dump({"final": out, "held_out": held, "p_min": P_MIN}, open(CACHE / f"ce9_matchers_m{M}.json", "w"), indent=1, default=float)
print("done", round(time.time() - t0), "s")
