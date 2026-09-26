"""CE-9 step 11: readable candidate matcher terms per recommended dimension, with the numbers needed to choose them by hand.
Sources: cluster TF-IDF top terms, curated keywords and entity names lifted in the cluster, and the terms the induction run proposed.
Every term is evaluated with the real v1 engine (word-boundary match over the metadata haystack): df = documents it catches,
in = how many of those are in the dimension's derived cluster, share = in/df, P3 = share of the caught documents that have this dimension among their 3 nearest (leave-one-out).
Usage: ce9_11_terms.py <first_cluster> <last_cluster> [min_in=4] [min_share=0.30]"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *
import scipy.sparse as sp

C = Corpus(); ix = Index(C); N = ix.N; Xc, mu = centered_doc_vectors(C)
lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist()))
S, rank = rank_matrix(Xc, lab, ids, np.ones(N, dtype=bool))
X = sp.load_npz(CACHE / "tfidf_doc.npz").tocsr(); vocab = pickle.load(open(CACHE / "tfidf_vocab.pkl", "rb"))["vocab"]
kwd = json.load(open(CACHE / "vocab_candidates.json"))["keywords_all_ge5"]
ind = json.load(open(CACHE / "ce9_matchers2_m20.json"))["final"]
lo, hi = int(sys.argv[1]), int(sys.argv[2]); MIN_IN = int(sys.argv[3]) if len(sys.argv) > 3 else 4; MIN_SH = float(sys.argv[4]) if len(sys.argv) > 4 else 0.30
cache = {}
def stats(term, j, seeds):
    if term not in cache: cache[term] = ix.engine_hits([term])
    h = cache[term]; df = int(h.sum())
    if df == 0: return None
    inn = int((h & seeds).sum())
    return df, inn, inn / df, float((rank[h, j] <= 3).mean())
ent = defaultdict(Counter)
for i, d in enumerate(C.doc_ids):
    e = C.docs[d].get("entities") or {}
    for k in ("people", "institutions", "cases", "laws_treaties", "events"):
        for it in e.get(k, []) or []:
            if isinstance(it, str): ent[i][re.sub(r"\s*\([^)]*\)", "", it).strip().lower()] += 1
for j, c in enumerate(ids):
    if not (lo <= c <= hi): continue
    seeds = lab == c; idx = np.where(seeds)[0]; n = len(idx)
    cand = {}
    tm = np.asarray(X[idx].mean(axis=0)).ravel()
    for t in [vocab[k] for k in np.argsort(-tm)[:80]]: cand.setdefault(t, "tfidf")
    for k, docs in kwd.items():
        if len(set(docs) & set(idx.tolist())) >= 3: cand.setdefault(k.lower(), "kw")
    cnt = Counter()
    for i in idx: cnt.update(ent[i].keys())
    for t, k in cnt.most_common(40): cand.setdefault(t, "ent")
    for t in ind[str(c)]["terms"]: cand.setdefault(t, "induced")
    rows = []
    for t, src in cand.items():
        if len(t) < 3: continue
        s = stats(t, j, seeds)
        if s is None: continue
        df, inn, sh, p3 = s
        if inn >= MIN_IN and sh >= MIN_SH: rows.append((inn, sh, df, p3, t, src))
    rows.sort(key=lambda r: (-r[0], -r[1]))
    print(f"\n### d{c} n={n}  (kept {len(rows)} candidate terms with in>={MIN_IN}, share>={MIN_SH})")
    for inn, sh, df, p3, t, src in rows[:32]:
        print(f"   {t:38s} df={df:3d} in={inn:3d} ({100*inn/n:3.0f}% of dim) share={sh:.2f} P3={p3:.2f} [{src}]")
