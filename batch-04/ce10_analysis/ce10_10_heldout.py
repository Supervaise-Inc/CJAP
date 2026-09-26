"""CE-10 Step 5: matcher precision OUT OF SAMPLE, on the built map. Two measurements, because "held-out" means two different things here.

The Phase 4 headline (median 76% in-neighbourhood) was IN-SAMPLE in the sense that matters: the term lists were chosen on all 1,290 documents and
then scored on them. Its held-out estimate was for the AUTOMATIC PROCEDURE (44% recall / 59% precision). So:

 A. BUILT MAP, held-out centroids. The 30 matchers exactly as built (topic_map.json doc_ids). 20 random 50/50 document splits: centroids are built from
    the matcher-caught documents of the TRAIN half only; on the TEST half, of the documents a matcher catches, the share that have that dimension among their
    3 nearest (centred doc-mean cosine). The terms were selected using all documents, so this measures whether a matcher's caught set is coherent for documents
    the CENTROIDS never saw - NOT whether the term lists generalise. Random-membership control alongside.
 B. THE PROCEDURE, split-sample. Re-run the automatic part of the matcher construction (candidate pool from the cluster's TF-IDF / curated keywords / entities;
    readability + precision filters; greedy 'gain - 0.35 x outside') on the TRAIN half only, freeze, and score on the TEST half with train-only centroids: recall of
    the cluster's test documents, and neighbourhood precision. Hand edits and the defining-vocabulary pass are NOT reproduced (they cannot be, blind);
    per-format top-up omitted. Random-set control: the same procedure on a random document set of the same size (expect recall ~ 0).
    The 29 dimensions with a Ward cluster (death_penalty has none). 8 splits.
Read-only on the repo. Centred scale."""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT / "batch-04/ce7_analysis"))
from ce9_lib import *          # Corpus, Index, centered_doc_vectors, norm_text, prune_subsumed, FMT_ORDER ...
from ce9_spec import SPEC
import scipy.sparse as sp

C = Corpus(); ix = Index(C); N = ix.N; Xc, mu = centered_doc_vectors(C); fmt = C.doc_fmt
tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))["topics"]
tids = list(tm.keys()); K = len(tids)
H = np.zeros((N, K), dtype=bool)
for j, t in enumerate(tids):
    for d in tm[t]["doc_ids"]: H[C.doc_index[d], j] = True
lab = np.load(ROOT / "batch-04/ce7_analysis/cache/ce9_level_final.npy")
cl_of = {SPEC[c]["id"]: c for c in SPEC}                                  # topic id -> Ward cluster number (29 of the 30)
rng0 = np.random.default_rng(20260927)

def top3_share(cens, docs_idx, j):
    """share of docs_idx whose 3 nearest centroids (rows of cens, unit) include j"""
    S = Xc[docs_idx] @ cens.T; rank = (-S).argsort(axis=1).argsort(axis=1) + 1
    return float((rank[:, j] <= 3).mean()) if len(docs_idx) else float("nan")

# ------------------------------------------------------------------ A. built map, held-out centroids
A_prec, A_ctl, A_rec = [], [], []
for rep in range(20):
    rng = np.random.default_rng(1000 + rep); train = rng.random(N) < 0.5; test = ~train
    Hr = np.zeros_like(H)
    for j in range(K): Hr[rng.choice(N, size=int(H[:, j].sum()), replace=False), j] = True
    def cens_of(M):
        s = np.stack([Xc[M[:, j] & train].sum(axis=0) if (M[:, j] & train).any() else np.zeros(Xc.shape[1]) for j in range(K)])
        return unit(s)
    ce, cr = cens_of(H), cens_of(Hr)
    for j in range(K):
        idx = np.where(H[:, j] & test)[0]; idr = np.where(Hr[:, j] & test)[0]
        if len(idx) >= 3: A_prec.append((tids[j], top3_share(ce, idx, j)))
        if len(idr) >= 3: A_ctl.append(top3_share(cr, idr, j))
per_t = {t: float(np.median([v for tt, v in A_prec if tt == t])) for t in tids if any(tt == t for tt, _ in A_prec)}
print(f"A. BUILT MAP, held-out centroids (20 splits): median neighbourhood precision {100 * np.median(list(per_t.values())):.0f}%  [per-dimension medians min {100 * min(per_t.values()):.0f}% / max {100 * max(per_t.values()):.0f}%; "
      f"{sum(v >= 0.6 for v in per_t.values())}/{len(per_t)} dimensions >= 60%]  random-membership control {100 * np.median(A_ctl):.0f}%  (base rate {100 * 3 / K:.0f}%)")

# ------------------------------------------------------------------ B. the procedure, split-sample
X = sp.load_npz(ROOT / "batch-04/ce7_analysis/cache/tfidf_doc.npz").tocsr(); vocab = pickle.load(open(ROOT / "batch-04/ce7_analysis/cache/tfidf_vocab.pkl", "rb"))["vocab"]
ACR = {"ala", "asean", "unclos", "eez", "scs", "icc", "icj", "jbc", "pcgg", "saln", "dap", "pdaf", "flp", "feu", "ata", "bbl", "milf", "pcos", "vcms", "amla", "amlc", "nlrc", "comelec", "sbn", "doj", "lto", "apjr", "scotus", "ppcrv", "omb", "ici", "moa-ad", "cha-cha", "con-ass", "con-con", "dna", "rvr", "csr", "rcm", "lct", "gma"}
EDGE = set("the a an of and to in on for with by as at from is are was were be his her their our its this that these those".split())
def readable(t):
    w = t.split(); return bool(w) and w[0] not in EDGE and w[-1] not in EDGE and not any(ch.isdigit() for ch in t) and (len(t) >= 4 or t in ACR)
def fast(t):
    a = ix.inv.get(norm_text(t))
    if a is None: return None
    h = np.zeros(N, dtype=bool); h[a] = True; return h
ent = defaultdict(Counter)
for i, d in enumerate(C.doc_ids):
    e = C.docs[d].get("entities") or {}
    for k in ("people", "institutions", "cases", "laws_treaties", "events"):
        for it in e.get(k, []) or []:
            if isinstance(it, str): ent[i][re.sub(r"\s*\([^)]*\)", "", it).strip().lower()] += 1
kwd = json.load(open(ROOT / "batch-04/ce7_analysis/cache/vocab_candidates.json"))["keywords_all_ge5"]
kw_docs = {k.lower(): set(C.doc_index[d] if isinstance(d, str) else int(d) for d in v) for k, v in kwd.items()}
ids29 = [t for t in tids if t in cl_of]
def procedure(seeds_full, train, ranks, j):
    """learn matcher terms for one dimension from TRAIN docs only; returns terms"""
    st = seeds_full & train; idx = np.where(st)[0]
    if len(idx) < 4: return []
    cand = {}
    tmv = np.asarray(X[idx].mean(axis=0)).ravel()
    for t in [vocab[k] for k in np.argsort(-tmv)[:80]]: cand[t] = 1
    idxs = set(idx.tolist())
    for k, docs in kw_docs.items():
        if len(docs & idxs) >= 2: cand[k] = 1
    cnt = Counter()
    for i in idx: cnt.update(ent[i].keys())
    for t, _ in cnt.most_common(40): cand[t] = 1
    pool = []
    for t in cand:
        if not readable(t): continue
        h = fast(t)
        if h is None: continue
        ht = h & train; df = int(ht.sum()); inn = int((ht & st).sum())
        if df < 3 or inn < 2: continue
        sh = inn / df; p3 = float((ranks[ht, j] <= 3).mean())
        if sh >= 0.45 or (sh >= 0.30 and p3 >= 0.75): pool.append((t, h & train))
    chosen, covered, caught = [], np.zeros(N, dtype=bool), np.zeros(N, dtype=bool)
    while len(chosen) < 14:
        best = None
        for t, h in pool:
            if t in chosen: continue
            new_in = int((h & st & ~covered).sum()); new_out = int((h & ~st & ~caught).sum()); g = new_in - 0.35 * new_out
            if best is None or g > best[0]: best = (g, t, new_in, h)
        if best is None or best[0] < 2 or best[2] < 2: break
        chosen.append(best[1]); covered |= best[3] & st; caught |= best[3]
        if covered.sum() / max(1, st.sum()) >= 0.85: break
    return prune_subsumed(chosen)

B = {"recall": [], "prec": [], "ctl_recall": [], "ctl_prec": [], "n_terms": []}
per_dim = defaultdict(lambda: {"recall": [], "prec": []})
for rep in range(8):
    rng = np.random.default_rng(2000 + rep); train = rng.random(N) < 0.5; test = ~train
    ids_c = sorted({cl_of[t] for t in ids29}); S, rank_all = rank_matrix(Xc, lab, ids_c, train)     # train-only partition centroids (LOO for train docs)
    pos = {c: k for k, c in enumerate(ids_c)}
    terms_by = {}; caught_by = {}
    for t in ids29:
        c = cl_of[t]; j = pos[c]; seeds = lab == c
        terms = procedure(seeds, train, rank_all, j); terms_by[t] = terms
        caught_by[t] = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    Mtr = np.stack([caught_by[t] & train for t in ids29], axis=1)
    cens = unit(np.stack([Xc[Mtr[:, k]].sum(axis=0) if Mtr[:, k].any() else np.zeros(Xc.shape[1]) for k in range(len(ids29))]))
    for k, t in enumerate(ids29):
        seeds = lab == cl_of[t]; te_seeds = seeds & test; ct = caught_by[t] & test
        rec = float((ct & te_seeds).sum() / max(1, te_seeds.sum())); pr = top3_share(cens, np.where(ct)[0], k) if ct.sum() >= 3 else float("nan")
        B["recall"].append(rec); B["n_terms"].append(len(terms_by[t]))
        if not np.isnan(pr): B["prec"].append(pr)
        per_dim[t]["recall"].append(rec)
        if not np.isnan(pr): per_dim[t]["prec"].append(pr)
        # random-set control: same procedure on a random document set the size of the training seeds
        rnd = np.zeros(N, dtype=bool); rnd[rng.choice(N, size=int((seeds & train).sum()), replace=False)] = True
        cr_terms = procedure(rnd, train, rank_all, pos[cl_of[t]])
        crc = (ix.engine_hits(cr_terms) if cr_terms else np.zeros(N, dtype=bool)) & test
        B["ctl_recall"].append(float((crc & rnd & test).sum() / max(1, (rnd & test).sum())))
    print(f"   split {rep + 1}/8 done", flush=True)
mr, mp = np.median([np.median(v["recall"]) for v in per_dim.values()]), np.median([np.median(v["prec"]) for v in per_dim.values() if v["prec"]])
print(f"B. THE PROCEDURE, split-sample (8 splits, 29 dimensions): held-out recall of the cluster's test docs: median {100 * mr:.0f}%; neighbourhood precision of the caught test docs: median {100 * mp:.0f}%; "
      f"dimensions with recall >= 50%: {sum(np.median(v['recall']) >= 0.5 for v in per_dim.values())}/29; median terms per dimension {int(np.median(B['n_terms']))}; random-set control recall {100 * np.median(B['ctl_recall']):.0f}%")
json.dump({"A_built_map_heldout_centroids": {"median_precision": float(np.median(list(per_t.values()))), "per_dimension_median": per_t, "control_median": float(np.median(A_ctl)), "base_rate": 3 / K,
                                              "n_ge_60": int(sum(v >= 0.6 for v in per_t.values()))},
           "B_procedure_split_sample": {"recall_median": float(mr), "precision_median": float(mp), "control_recall_median": float(np.median(B["ctl_recall"])),
                                        "per_dimension": {t: {"recall": float(np.median(v["recall"])), "precision": float(np.median(v["prec"])) if v["prec"] else None} for t, v in per_dim.items()}}},
          open(ROOT / "batch-04/ce10_analysis/cache/heldout.json", "w"), indent=1)
