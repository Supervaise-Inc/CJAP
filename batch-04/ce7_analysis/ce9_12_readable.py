"""CE-9 step 12: READABLE matchers by greedy selection over readable candidate terms, judged on the deliverable's own metrics.
Candidate pool per dimension = cluster TF-IDF top-80 terms + curated keywords lifted in the cluster + the cluster's top-40 entity names (+ the induction run's terms, filtered).
Readability filters (mechanical, no per-term judgement): >=4 characters (or a whitelisted acronym), no digits, not a stop-word phrase edge, catches >= 5 documents (nothing memorised from 3-4 documents).
Precision filter per term: share of its caught docs inside the dimension's derived cluster >= 0.45, OR share >= 0.30 with P@3 >= 0.75 (P@3 = caught docs that have the dimension among their 3 nearest, leave-one-out).
Greedy: pick the term with the best (new in-cluster docs - 0.35 * new out-of-cluster docs); stop at gain < 2, 14 terms, or recall 0.85.
Then a per-format top-up (a format with >= 3 cluster docs and < 25% recall gets its own pass). Acceptance: caught <= 2x cluster docs and P@3 >= 0.60.
Writes cache/ce9_readable_m20.json. Read-only on the repo. Centred scale only."""
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
ind = json.load(open(CACHE / "ce9_matchers2_m20.json"))["final"]
ACRONYMS = {"ala", "asean", "unclos", "eez", "scs", "icc", "icj", "jbc", "pcgg", "saln", "dap", "pdaf", "flp", "feu", "ata", "bbl", "milf", "pcos", "vcms", "amla", "amlc", "nlrc", "comelec", "sbn", "doj", "lto", "apjr", "scotus", "ppcrv", "omb", "ici", "moa-ad", "cha-cha", "con-ass", "con-con", "dna", "rvr", "csr", "rcm", "lct", "gma"}
JUNK_EDGE = set("the a an of and to in on for with by as at from is are was were be his her their our its this that these those".split())
MIN_DF, SH_A, SH_B, P3_B, LAM, MAXT = 5, 0.45, 0.30, 0.75, 0.35, 14
ent = defaultdict(Counter)
for i, d in enumerate(C.doc_ids):
    e = C.docs[d].get("entities") or {}
    for k in ("people", "institutions", "cases", "laws_treaties", "events"):
        for it in e.get(k, []) or []:
            if isinstance(it, str): ent[i][re.sub(r"\s*\([^)]*\)", "", it).strip().lower()] += 1
hitc = {}
def hits(t):
    if t not in hitc: hitc[t] = ix.engine_hits([t])
    return hitc[t]
def readable(t):
    w = t.split()
    if not w or w[0] in JUNK_EDGE or w[-1] in JUNK_EDGE: return False
    if any(ch.isdigit() for ch in t): return False
    if len(t) < 4 and t not in ACRONYMS: return False
    return True

def pool(j, c, seeds):
    idx = np.where(seeds)[0]; cand = {}
    tm = np.asarray(X[idx].mean(axis=0)).ravel()
    for t in [vocab[k] for k in np.argsort(-tm)[:80]]: cand[t] = 1
    for k, docs in kwd.items():
        if len(set(docs) & set(idx.tolist())) >= 3: cand[k.lower()] = 1
    cnt = Counter()
    for i in idx: cnt.update(ent[i].keys())
    for t, _ in cnt.most_common(40): cand[t] = 1
    for t in ind[str(c)]["terms"]: cand[t] = 1
    out = []
    for t in cand:
        if not readable(t): continue
        h = hits(t); df = int(h.sum())
        if df < MIN_DF: continue
        inn = int((h & seeds).sum())
        if inn < 3: continue
        sh = inn / df; p3 = float((rank[h, j] <= 3).mean())
        if sh >= SH_A or (sh >= SH_B and p3 >= P3_B): out.append((t, df, inn, sh, p3))
    return out

def greedy(cands, seeds, want, covered0=None):
    """want: docs to cover (bool N); returns chosen terms"""
    chosen = []; covered = np.zeros(N, dtype=bool) if covered0 is None else covered0.copy(); caught = covered.copy()
    tot_want = max(1, int(want.sum()))
    while len(chosen) < MAXT:
        best = None
        for t, df, inn, sh, p3 in cands:
            if t in chosen: continue
            h = hits(t)
            new_in = int((h & want & ~covered).sum()); new_out = int((h & ~seeds & ~caught).sum())
            g = new_in - LAM * new_out
            if best is None or g > best[0]: best = (g, t, new_in)
        if best is None or best[0] < 2 or best[2] < 2: break
        chosen.append(best[1]); h = hits(best[1]); covered |= h & want; caught |= h
        if (covered & want).sum() / tot_want >= 0.85: break
    return chosen

res = {}
print(f"{'cl':>3s} {'n':>4s} {'terms':>5s} {'caught':>6s} {'ratio':>5s} {'recall':>6s} {'in-dim':>6s} {'P@1':>5s} {'P@3':>5s} {'P@5':>5s} ok   recall by format col/book/spe/bio")
for j, c in enumerate(ids):
    seeds = lab == c; n = int(seeds.sum()); cands = pool(j, c, seeds)
    terms = greedy(cands, seeds, seeds)
    hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    for f in FMT_ORDER:
        sf = seeds & (fmt == f)
        if sf.sum() >= 3 and (hit & sf).sum() / sf.sum() < 0.25:
            extra = greedy([x for x in cands if x[0] not in terms], seeds, sf & ~hit, covered0=hit & seeds)
            terms += [t for t in extra if t not in terms]; hit = ix.engine_hits(terms) if terms else hit
    terms = prune_subsumed(terms); hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    ca = int(hit.sum()); P = {r: float((rank[hit, j] <= r).mean()) if ca else float("nan") for r in (1, 3, 5)}
    ok = bool(ca and ca <= 2 * n and P[3] >= 0.60)
    byf = {f: (float((hit & seeds & (fmt == f)).sum() / (seeds & (fmt == f)).sum()) if (seeds & (fmt == f)).sum() else None) for f in FMT_ORDER}
    res[int(c)] = dict(n=n, terms=terms, caught=ca, ratio=ca / n, recall=float((hit & seeds).sum() / n), in_dim=float((hit & seeds).sum() / max(1, ca)), P1=P[1], P3=P[3], P5=P[5], ok=ok, recall_by_format=byf,
                       caught_by_format={f: int((hit & (fmt == f)).sum()) for f in FMT_ORDER}, n_candidates=len(cands))
    print(f"{c:3d} {n:4d} {len(terms):5d} {ca:6d} {ca/n:5.2f} {res[int(c)]['recall']:6.2f} {res[int(c)]['in_dim']:6.2f} {P[1]:5.2f} {P[3]:5.2f} {P[5]:5.2f} {'Y' if ok else 'n'}    "
          + "/".join("-" if v is None else f"{v:.2f}" for v in byf.values()) + "\n      " + ", ".join(terms), flush=True)
json.dump(res, open(CACHE / "ce9_readable_m20.json", "w"), indent=1, default=float)
