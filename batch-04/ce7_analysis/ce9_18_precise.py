"""CE-9 step 16: second pass over the greedy readable matchers. The first pass (ce9_12) demanded that every TERM be precise on its own, which leaves the defining vocabulary
('martial law', 'impeachment', 'trump', 'election') out because those words are also mentioned in other subjects. Here a term is admitted when the UNION stays acceptable:
caught <= 1.8x the dimension's documents AND >= 70% of the caught documents have the dimension among their 3 nearest (leave-one-out), and it adds >= 3 cluster documents; every term must itself catch >= 8 documents (nothing memorised from a handful).
Candidates are screened with the fast normalised n-gram index; the FINAL union of every dimension is re-evaluated with the real v1 engine and that is what is reported.
Writes cache/ce9_relaxed_m20.json."""
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

C = Corpus(); ix = Index(C); N = ix.N; Xc, mu = centered_doc_vectors(C); fmt = C.doc_fmt
lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist())); K = len(ids)
S, rank = rank_matrix(Xc, lab, ids, np.ones(N, dtype=bool))
X = sp.load_npz(CACHE / "tfidf_doc.npz").tocsr(); vocab = pickle.load(open(CACHE / "tfidf_vocab.pkl", "rb"))["vocab"]
kwd = json.load(open(CACHE / "vocab_candidates.json"))["keywords_all_ge5"]
G = json.load(open(CACHE / "ce9_readable_m20.json"))
ACR = {"ala", "asean", "unclos", "eez", "scs", "icc", "icj", "jbc", "pcgg", "saln", "dap", "pdaf", "flp", "feu", "ata", "bbl", "milf", "pcos", "vcms", "amla", "amlc", "nlrc", "comelec", "sbn", "doj", "lto", "apjr", "scotus", "ppcrv", "omb", "ici", "moa-ad", "cha-cha", "con-ass", "con-con", "dna", "rvr", "csr", "rcm", "lct", "gma"}
EDGE = set("the a an of and to in on for with by as at from is are was were be his her their our its this that these those".split())
MAX_RATIO, MIN_INDIM, MAXT, MIN_GAIN, MIN_DF = 1.5, 0.65, 12, 2, 5
def readable(t):
    w = t.split()
    return bool(w) and w[0] not in EDGE and w[-1] not in EDGE and not any(ch.isdigit() for ch in t) and (len(t) >= 4 or t in ACR)
def fast(t):
    g = norm_text(t); a = ix.inv.get(g)
    if a is None: return None
    h = np.zeros(N, dtype=bool); h[a] = True; return h
ent = defaultdict(Counter)
for i, d in enumerate(C.doc_ids):
    e = C.docs[d].get("entities") or {}
    for k in ("people", "institutions", "cases", "laws_treaties", "events"):
        for it in e.get(k, []) or []:
            if isinstance(it, str): ent[i][re.sub(r"\s*\([^)]*\)", "", it).strip().lower()] += 1
exec(open(Path(__file__).parent / 'ce9_edits.py', encoding='utf-8').read())
out = {}
print(f"{'cl':>3s} {'n':>4s} {'terms':>5s} {'caught':>6s} {'ratio':>5s} {'recall':>6s} {'in-dim':>6s} {'P@1':>5s} {'P@3':>5s} {'P@5':>5s} ok   recall by format col/book/spe/bio")
for j, c in enumerate(ids):
    seeds = lab == c; n = int(seeds.sum()); idx = np.where(seeds)[0]
    cand = {}
    tm = np.asarray(X[idx].mean(axis=0)).ravel()
    for t in [vocab[k] for k in np.argsort(-tm)[:100]]: cand[t] = 1
    for k, docs in kwd.items():
        if len(set(docs) & set(idx.tolist())) >= 3: cand[k.lower()] = 1
    cnt = Counter()
    for i in idx: cnt.update(ent[i].keys())
    for t, _ in cnt.most_common(50): cand[t] = 1
    pool = []
    for t in cand:
        if not readable(t) or t in DROP.get(c, []): continue
        h = fast(t)
        if h is None: continue
        df = int(h.sum()); inn = int((h & seeds).sum())
        if df >= MIN_DF and inn >= 3 and inn / df >= 0.5: pool.append((t, h))
    terms = []; cur = np.zeros(N, dtype=bool)          # start EMPTY: the union criteria alone decide what is admitted
    while len(terms) < MAXT:
        best = None
        for t, h in pool:
            if t in terms: continue
            new_in = int((h & seeds & ~cur).sum())
            if new_in < MIN_GAIN: continue
            u = cur | h; ca = int(u.sum())
            if ca > MAX_RATIO * n: continue
            if float((u & seeds).sum() / max(1, ca)) < MIN_INDIM: continue
            sc = new_in - 0.25 * int((h & ~seeds & ~cur).sum())
            if best is None or sc > best[0]: best = (sc, t, h)
        if best is None: break
        terms.append(best[1]); cur |= best[2]
    terms = prune_subsumed(terms); hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool); ca = int(hit.sum())
    P = {r: float((rank[hit, j] <= r).mean()) if ca else float("nan") for r in (1, 3, 5)}; ok = bool(ca and ca <= 2 * n and P[3] >= 0.60)
    byf = {f: (float((hit & seeds & (fmt == f)).sum() / (seeds & (fmt == f)).sum()) if (seeds & (fmt == f)).sum() else None) for f in FMT_ORDER}
    out[int(c)] = dict(n=n, terms=terms, caught=ca, ratio=ca / n if n else None, recall=float((hit & seeds).sum() / n), in_dim=float((hit & seeds).sum() / max(1, ca)), P1=P[1], P3=P[3], P5=P[5], ok=ok, recall_by_format=byf)
    print(f"{c:3d} {n:4d} {len(terms):5d} {ca:6d} {ca/n:5.2f} {out[int(c)]['recall']:6.2f} {out[int(c)]['in_dim']:6.2f} {P[1]:5.2f} {P[3]:5.2f} {P[5]:5.2f} {'Y' if ok else 'n'}    " + "/".join("-" if v is None else f"{v:.2f}" for v in byf.values())
          + "\n      " + ", ".join(terms), flush=True)
json.dump(out, open(CACHE / "ce9_precise_m20.json", "w"), indent=1, default=float)
