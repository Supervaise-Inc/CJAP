"""CE-9 step 7: matcher induction judged by the deliverable's own metric (share of caught documents inside the dimension's embedding neighbourhood).
Held-out estimate (learn on a random half of the documents, centroids built from that half only, score the other half) + random-set control,
then the final matchers on all documents. Writes cache/ce9_matchers2_m{M}.json. Read-only on the repo. Centered scale only.

'embedding neighbourhood' = the documents that have the dimension among their 3 nearest dimensions (MAX_TOPIC_TAGS = 3), leave-one-out, on centered
document-mean vectors. Acceptance ('finished'): caught <= 2x the dimension's documents AND P@3 >= 0.60."""
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
lab = np.load(CACHE / f"ce9_level_m{M}.npy"); ids = sorted(set(lab.tolist())); K = len(ids)
fmt = C.doc_fmt; allm = np.ones(N, dtype=bool)
GRID = [(0.30, 0.65), (0.40, 0.70), (0.50, 0.70), (0.60, 0.75), (0.70, 0.80)]
MAX_RATIO, MIN_P3 = 2.0, 0.60

def build(j, seeds, train, rank, tune=True):
    near = rank[:, j] <= 3
    best = None
    for ps, p3 in (GRID if tune else GRID[:1]):
        terms = prune_subsumed(induce_topical2(ix, tp, seeds, train, near, ps_min=ps, p3_min=p3))
        for f in FMT_ORDER:                                            # per-format top-up so no format is left uncovered
            sf = seeds & (fmt == f) & train
            if sf.sum() < 3: continue
            hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
            if (hit & sf).sum() / sf.sum() >= 0.5: continue
            extra = induce_topical2(ix, tp, seeds, train, near, ps_min=ps, p3_min=p3, cover=sf & ~hit, k_tfidf=250)
            terms = prune_subsumed(list(terms) + list(extra))
        if not terms: continue
        hit = ix.engine_hits(terms) & train
        ca = int(hit.sum()); ns = int((seeds & train).sum())
        p3v = float((rank[hit, j] <= 3).mean()) if ca else 0.0
        rec = float((hit & seeds).sum() / max(1, ns))
        cand = {"terms": terms, "ps": ps, "p3": p3, "ratio": ca / max(1, ns), "P3": p3v, "recall": rec}
        if cand["ratio"] <= MAX_RATIO and p3v >= MIN_P3:
            return cand, True
        if best is None or (p3v, -abs(cand["ratio"] - 1.5)) > (best["P3"], -abs(best["ratio"] - 1.5)): best = cand
    return best, False

# ------------------------------------------------------------------ held-out estimate
rng = np.random.default_rng(20260926); train = rng.random(N) < 0.5; test = ~train
S_tr, rank_tr = rank_matrix(Xc, lab, ids, train)
rec, p3, lf, ratio, fin, ctl, nterms = [], [], [], [], 0, [], []
for j, c in enumerate(ids):
    seeds = lab == c
    cand, ok = build(j, seeds, train, rank_tr)
    if cand is None: rec.append(0.0); nterms.append(0); continue
    fin += int(ok); nterms.append(len(cand["terms"]))
    hit = ix.engine_hits(cand["terms"]); ts = seeds & test; ch = hit & test
    rec.append(float((hit & ts).sum() / max(1, ts.sum())))
    if ch.sum():
        p3.append(float((rank_tr[ch, j] <= 3).mean())); lf.append(p3[-1] / float((rank_tr[test, j] <= 3).mean()))
        ratio.append(float(ch.sum() / max(1, ts.sum())))
    rnd = np.zeros(N, dtype=bool); rnd[rng.choice(N, size=int(seeds.sum()), replace=False)] = True
    rc, _ = build(j, rnd, train, rank_tr, tune=False)
    ctl.append(float((ix.engine_hits(rc["terms"]) & rnd & test).sum() / max(1, (rnd & test).sum())) if rc and rc["terms"] else 0.0)
held = {"recall_median": float(np.median(rec)), "P3_median": float(np.median(p3)), "lift3_median": float(np.median(lf)), "caught_over_seeds_median": float(np.median(ratio)),
        "n_recall_ge_50": int(sum(r >= 0.5 for r in rec)), "n_finished_on_train": fin, "terms_median": int(np.median(nterms)), "control_recall_median": float(np.median(ctl)), "n_dims": K}
print("HELD-OUT: recall median %.2f | P@3 %.2f | lift@3 %.1fx | caught/seeds %.2f | dims recall>=.5: %d/%d | finished(train) %d/%d | terms median %d | random-set control recall %.2f  [%ds]" %
      (held["recall_median"], held["P3_median"], held["lift3_median"], held["caught_over_seeds_median"], held["n_recall_ge_50"], K, fin, K, held["terms_median"], held["control_recall_median"], time.time() - t0), flush=True)

# ------------------------------------------------------------------ final matchers on all documents
S_all, rank_all = rank_matrix(Xc, lab, ids, allm)
out = {}
print(f"{'cl':>3s} {'seeds':>5s} {'terms':>5s} {'caught':>6s} {'ratio':>5s} {'in-seeds':>8s} {'recall':>6s} {'P@1':>5s} {'P@3':>5s} {'P@5':>5s} {'lift@3':>6s} ok  recall by format col/book/spe/bio")
for j, c in enumerate(ids):
    seeds = lab == c
    cand, ok = build(j, seeds, allm, rank_all)
    terms = cand["terms"] if cand else []
    hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    n = int(seeds.sum()); ca = int(hit.sum())
    P = {r: float((rank_all[hit, j] <= r).mean()) if ca else float("nan") for r in (1, 3, 5)}
    base3 = float((rank_all[:, j] <= 3).mean())
    byf = {f: (float((hit & seeds & (fmt == f)).sum() / (seeds & (fmt == f)).sum()) if (seeds & (fmt == f)).sum() else None) for f in FMT_ORDER}
    out[int(c)] = {"n": n, "terms": terms, "caught": ca, "ratio": ca / n, "prec_seeds": float((hit & seeds).sum() / max(1, ca)), "recall": float((hit & seeds).sum() / n), "P1": P[1], "P3": P[3], "P5": P[5],
                   "base3": base3, "recall_by_format": byf, "entity_terms": [t for t in terms if t in ix.entity_terms], "finished": bool(ok), "thresholds": [cand["ps"], cand["p3"]] if cand else None,
                   "caught_by_format": {f: int((hit & (fmt == f)).sum()) for f in FMT_ORDER}}
    print(f"{c:3d} {n:5d} {len(terms):5d} {ca:6d} {ca/n:5.2f} {out[int(c)]['prec_seeds']:8.2f} {out[int(c)]['recall']:6.2f} {P[1]:5.2f} {P[3]:5.2f} {P[5]:5.2f} {P[3]/base3 if base3 else float('nan'):6.1f} {'Y' if ok else 'n'}   "
          + "/".join("-" if v is None else f"{v:.2f}" for v in byf.values()), flush=True)
json.dump({"final": out, "held_out": held, "grid": GRID, "acceptance": {"max_caught_ratio": MAX_RATIO, "min_P3": MIN_P3}}, open(CACHE / f"ce9_matchers2_m{M}.json", "w"), indent=1, default=float)
print("done", round(time.time() - t0), "s")
