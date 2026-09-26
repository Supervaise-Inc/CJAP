"""CE-9 shared library: haystacks, an inverted n-gram index, matcher induction with train/test separation, engine-based evaluation.
Reuses ce7_common. Read-only on the repo. The v1 matching ENGINE (build_topic_map._doc_haystack + score_topic) is the ground truth for every
reported number: induction uses a fast normalised n-gram index to PROPOSE terms, then every reported count is recomputed with the real engine."""
from __future__ import annotations
import re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *

TOKEN = re.compile(r"[a-z][a-z0-9'\-]*")
STOP = set("""a an and are as at be but by for from has have he her his i if in into is it its of on or our she so that the their them then there these they this those to was we were what when which who whom will with would you your
also can may must not no yes all any both each few more most other some such only own same than too very just about above after again against before below between during off over under until up down out further here how nor once
one two three first second new said says say mr ms jr sr sen atty ponencia section sec art vs cjp panganiban chapter column author argues argue writes wrote""".split())

def norm_text(s: str) -> str:
    return " ".join(TOKEN.findall(s.lower()))

def ngrams(tokens, nmax=4):
    out = set()
    L = len(tokens)
    for n in range(1, nmax + 1):
        for i in range(L - n + 1):
            g = tokens[i:i + n]
            if g[0] in STOP or g[-1] in STOP:
                continue
            if n == 1 and (len(g[0]) < 3 or g[0].isdigit()):
                continue
            if any(t.isdigit() and len(t) == 4 for t in g) and n == 1:
                continue
            out.add(" ".join(g))
    return out

class Index:
    """haystacks (the v1 engine's own), normalised n-gram sets, inverted index."""
    def __init__(self, C: Corpus):
        self.C = C; self.P = prior_art(); self.m = self.P["module"]
        self.hay = [self.m._doc_haystack(C.docs[d]) for d in C.doc_ids]
        self.tok = [TOKEN.findall(h) for h in self.hay]
        self.grams = [ngrams(t) for t in self.tok]
        inv = defaultdict(list)
        for i, gs in enumerate(self.grams):
            for g in gs: inv[g].append(i)
        self.inv = {g: np.array(v, dtype=np.int32) for g, v in inv.items() if len(v) >= 3}
        self.N = len(C.doc_ids)
        import scipy.sparse as sp
        self.terms = np.array(sorted(self.inv))
        col = {t: j for j, t in enumerate(self.terms)}
        rows, cols = [], []
        for t, docs in self.inv.items():
            j = col[t]; rows.extend(docs.tolist()); cols.extend([j] * len(docs))
        self.B = sp.csc_matrix((np.ones(len(rows), dtype=np.int8), (rows, cols)), shape=(self.N, len(self.terms)))
        self.Br = self.B.tocsr()
        # entity strings (for splitting proposed terms into the 'entities' bucket)
        ent = set()
        for d in C.doc_ids:
            e = C.docs[d].get("entities") or {}
            for k in ("people", "institutions", "cases", "laws_treaties", "events"):
                for it in e.get(k, []) or []:
                    if isinstance(it, str):
                        t = norm_text(re.sub(r"\([^)]*\)", "", it))
                        if t: ent.add(t)
        self.entity_terms = ent

    def engine_hits(self, terms) -> np.ndarray:
        """boolean [N] : documents the REAL engine catches with these terms (score > 0)."""
        pats = [self.m._kw_pattern(t) for t in terms]
        return np.array([any(p.search(h) for p in pats) for h in self.hay], dtype=bool)

    def engine_score(self, terms) -> np.ndarray:
        pats = [self.m._kw_pattern(t) for t in terms]
        return np.array([sum(1 for p in pats if p.search(h)) for h in self.hay], dtype=np.int32)

def induce(ix: Index, seeds: np.ndarray, train: np.ndarray, p_min=0.6, s_min_frac=0.06, s_min_abs=3, max_terms=30, target=0.9, min_gain=2):
    """Learn a matcher for one dimension from documents in `train` only (vectorised).
    seeds : boolean [N] (the dimension's documents); train : boolean [N] (documents the induction may look at).
    A term is admissible if it occurs in >= max(s_min_abs, s_min_frac*|train seeds|) train seeds and >= p_min of the train documents containing it are seeds.
    Greedy set cover over train seeds."""
    S = seeds & train
    nS = int(S.sum())
    if nS < 3: return []
    need = max(s_min_abs, int(np.ceil(s_min_frac * nS)))
    s_cnt = np.asarray(ix.B[S].sum(axis=0)).ravel()
    d_cnt = np.asarray(ix.B[train].sum(axis=0)).ravel()
    ok = (s_cnt >= need) & (d_cnt > 0) & (s_cnt >= p_min * d_cnt)
    cols = np.where(ok)[0]
    if len(cols) == 0: return []
    Sidx = np.where(S)[0]
    Bs = ix.Br[Sidx][:, cols].toarray().astype(bool)          # [train seeds x candidates]
    prec = s_cnt[cols] / d_cnt[cols]
    covered = np.zeros(len(Sidx), dtype=bool); chosen = []
    used = np.zeros(len(cols), dtype=bool)
    while len(chosen) < max_terms and covered.sum() < target * nS:
        gain = (Bs & ~covered[:, None]).sum(axis=0); gain[used] = -1
        best = int(np.argmax(gain + 1e-3 * prec - 1e-6 * np.array([len(ix.terms[c]) for c in cols])))
        if gain[best] < min_gain: break
        chosen.append(ix.terms[cols[best]]); covered |= Bs[:, best]; used[best] = True
    return chosen

def prune_subsumed(terms):
    """drop a term if a chosen shorter term is a whole-word component of it (e.g. keep 'ballots', drop 'ballots pcos')"""
    keep = []
    for t in sorted(terms, key=lambda x: (len(x.split()), len(x))):
        if any((" " + k + " ") in (" " + t + " ") for k in keep): continue
        keep.append(t)
    return keep

def voronoi_neighbourhoods(C: Corpus, Xc: np.ndarray, lab: np.ndarray):
    """leave-one-out nearest-centroid (centered document-mean vectors). returns ids, S[N,K] similarities, cens."""
    ids = sorted(set(lab.tolist())); K = len(ids)
    sums = np.stack([Xc[lab == c].sum(axis=0) for c in ids])
    S = np.zeros((len(lab), K))
    idpos = {c: j for j, c in enumerate(ids)}
    for i in range(len(lab)):
        cen = sums.copy(); j = idpos[lab[i]]; cen[j] = cen[j] - Xc[i]
        S[i] = unit(cen) @ Xc[i]
    return ids, S, unit(sums)

def centered_doc_vectors(C: Corpus):
    mu = C.mat.mean(axis=0)
    dm = np.stack([C.mat[C.rows_of[d]].mean(axis=0) for d in C.doc_ids])
    return unit(dm - mu).astype(np.float64), mu


def bottom_up(Xc: np.ndarray, lab0: np.ndarray, m: int, tau: float = 0.70):
    """Start from a fine partition. Repeatedly (1) merge the closest pair if its CENTERED centroid cosine >= tau (a duplicate),
    else (2) merge the smallest cluster with fewer than m documents into its nearest neighbour. Stops when neither applies.
    Returns (labels 1..K, merge_log)."""
    groups = {int(c): list(np.where(lab0 == c)[0]) for c in sorted(set(lab0.tolist()))}
    log = []
    while len(groups) > 1:
        keys = list(groups); cen = np.stack([unit(Xc[groups[k]].mean(axis=0)) for k in keys]); G = cen @ cen.T
        np.fill_diagonal(G, -2); i, j = np.unravel_index(np.argmax(G), G.shape)
        if G[i, j] >= tau:
            a, b = keys[i], keys[j]
            if len(groups[a]) > len(groups[b]): a, b = b, a
            log.append(("duplicate", float(G[i, j]), len(groups[a]), len(groups[b]))); groups[b] += groups.pop(a); continue
        small = [k for k in keys if len(groups[k]) < m]
        if not small: break
        a = min(small, key=lambda k: len(groups[k])); ai = keys.index(a); j = int(np.argmax(G[ai])); b = keys[j]
        log.append(("undersize", float(G[ai, j]), len(groups[a]), len(groups[b]))); groups[b] += groups.pop(a)
    lab = np.zeros(len(lab0), dtype=int)
    for n, k in enumerate(sorted(groups, key=lambda k: -len(groups[k])), start=1):
        lab[groups[k]] = n
    return lab, log


def bottom_up_capped(Xc: np.ndarray, lab0: np.ndarray, m: int, tau: float = 0.70, cap: int = 100, floor_keep: int = 10):
    """bottom_up with a MAXIMUM cluster size. (1) merge duplicate pairs (centered cosine >= tau) regardless of size;
    (2) merge the smallest cluster with < m documents into its nearest neighbour whose union stays <= cap; if no neighbour has room, keep it
    when it has >= floor_keep documents (it is then marginal), else merge it into its nearest neighbour anyway."""
    groups = {int(c): list(np.where(lab0 == c)[0]) for c in sorted(set(lab0.tolist()))}
    log = []; frozen = set()
    while len(groups) > 1:
        keys = list(groups); cen = np.stack([unit(Xc[groups[k]].mean(axis=0)) for k in keys]); G = cen @ cen.T
        np.fill_diagonal(G, -2); i, j = np.unravel_index(np.argmax(G), G.shape)
        if G[i, j] >= tau:
            a, b = keys[i], keys[j]
            if len(groups[a]) > len(groups[b]): a, b = b, a
            log.append(("duplicate", float(G[i, j]), len(groups[a]), len(groups[b]))); groups[b] += groups.pop(a); frozen.discard(a); continue
        small = [k for k in keys if len(groups[k]) < m and k not in frozen]
        if not small: break
        a = min(small, key=lambda k: len(groups[k])); ai = keys.index(a)
        order = np.argsort(-G[ai]); done = False
        for jj in order:
            b = keys[jj]
            if b == a: continue
            if len(groups[a]) + len(groups[b]) <= cap:
                log.append(("undersize", float(G[ai, jj]), len(groups[a]), len(groups[b]))); groups[b] += groups.pop(a); done = True; break
        if not done:
            if len(groups[a]) >= floor_keep: frozen.add(a)          # keep as a marginal cluster
            else:
                b = keys[int(order[0]) if keys[int(order[0])] != a else int(order[1])]
                log.append(("undersize-forced", float(G[ai, keys.index(b)]), len(groups[a]), len(groups[b]))); groups[b] += groups.pop(a)
    lab = np.zeros(len(lab0), dtype=int)
    for n, k in enumerate(sorted(groups, key=lambda k: -len(groups[k])), start=1):
        lab[groups[k]] = n
    return lab, log


class Topical:
    """topical candidate sources: cluster TF-IDF terms, curated keywords, entity names (all restricted to what the metadata haystack can match)."""
    def __init__(self, C: Corpus, ix: Index):
        import pickle, scipy.sparse as sp
        self.C, self.ix = C, ix
        self.X = sp.load_npz(CACHE / "tfidf_doc.npz").tocsr()
        self.vocab = pickle.load(open(CACHE / "tfidf_vocab.pkl", "rb"))["vocab"]
        self.col = {t: j for j, t in enumerate(ix.terms)}
        kw = set()
        for d in C.doc_ids:
            for k in C.docs[d].get("keywords") or []:
                if isinstance(k, str):
                    t = norm_text(re.sub(r"\([^)]*\)", "", k))
                    if t and t in self.col: kw.add(t)
        self.kw_cols = np.array(sorted(self.col[t] for t in kw), dtype=int)
        self.ent_cols = np.array(sorted(self.col[t] for t in ix.entity_terms if t in self.col), dtype=int)

    def candidate_cols(self, seeds: np.ndarray, train: np.ndarray, k_tfidf=100, lift_min=3.0, need=3):
        ix = self.ix; S = seeds & train; Sidx = np.where(S)[0]
        if len(Sidx) < 3: return np.array([], dtype=int)
        cm = np.asarray(self.X[Sidx].mean(axis=0)).ravel(); om = np.asarray(self.X[np.where(train)[0]].mean(axis=0)).ravel()
        score = cm * (cm / (om + 1e-9))
        top = np.argsort(-score)[:k_tfidf]
        cols = {self.col[self.vocab[j]] for j in top if self.vocab[j] in self.col}
        s_cnt = np.asarray(ix.B[S].sum(axis=0)).ravel(); d_cnt = np.asarray(ix.B[train].sum(axis=0)).ravel()
        share_s = s_cnt / max(1, len(Sidx)); share_all = d_cnt / max(1, int(train.sum()))
        for arr in (self.kw_cols, self.ent_cols):
            ok = arr[(s_cnt[arr] >= need) & (share_s[arr] >= lift_min * np.maximum(share_all[arr], 1e-9))]
            cols.update(ok.tolist())
        return np.array(sorted(cols), dtype=int)

def induce_topical(ix: Index, tp: Topical, seeds, train, p_min=0.5, s_min_frac=0.03, s_min_abs=3, max_terms=20, target=0.95, min_gain=1, k_tfidf=100, cover=None, s_min_cover=2):
    """precision is always measured against the whole cluster (`seeds`); `cover` (default = seeds) is the subset the greedy step tries to cover."""
    S = seeds & train; nS = int(S.sum())
    if nS < 3: return []
    CV = (cover & train) if cover is not None else S
    nC = int(CV.sum())
    if nC < 1: return []
    need = max(s_min_abs, int(np.ceil(s_min_frac * nS)))
    cand = tp.candidate_cols(seeds, train, k_tfidf=k_tfidf, need=s_min_abs)
    if len(cand) == 0: return []
    s_cnt = np.asarray(ix.B[S].sum(axis=0)).ravel(); d_cnt = np.asarray(ix.B[train].sum(axis=0)).ravel()
    ok = (s_cnt[cand] >= need) & (d_cnt[cand] > 0) & (s_cnt[cand] >= p_min * d_cnt[cand])
    cols = cand[ok]
    if len(cols) == 0: return []
    Sidx = np.where(CV)[0]; Bs = ix.Br[Sidx][:, cols].toarray().astype(bool); prec = s_cnt[cols] / d_cnt[cols]
    covered = np.zeros(len(Sidx), dtype=bool); chosen = []; used = np.zeros(len(cols), dtype=bool)
    while len(chosen) < max_terms and covered.sum() < target * nC:
        gain = (Bs & ~covered[:, None]).sum(axis=0); gain[used] = -1
        best = int(np.argmax(gain + 1e-3 * prec - 1e-6 * np.array([len(ix.terms[c]) for c in cols])))
        if gain[best] < min_gain: break
        chosen.append(ix.terms[cols[best]]); covered |= Bs[:, best]; used[best] = True
    return chosen


def rank_matrix(Xc: np.ndarray, lab: np.ndarray, ids, use: np.ndarray):
    """rank[i, j] = rank of dimension j among all dimensions for document i (1 = nearest), centered document-mean vectors.
    Centroids are built ONLY from documents where use[i] is True; a used document is left out of its own centroid (leave-one-out)."""
    pos = {c: j for j, c in enumerate(ids)}; K = len(ids); n = len(lab)
    sums = np.stack([Xc[(lab == c) & use].sum(axis=0) for c in ids])
    S = np.zeros((n, K))
    for i in range(n):
        cen = sums.copy()
        if use[i] and lab[i] in pos: cen[pos[lab[i]]] = cen[pos[lab[i]]] - Xc[i]
        S[i] = unit(cen) @ Xc[i]
    return S, (-S).argsort(axis=1).argsort(axis=1) + 1

def induce_topical2(ix: Index, tp: Topical, seeds, train, near, ps_min=0.3, p3_min=0.65, s_min_frac=0.03, s_min_abs=3, max_terms=20, target=0.95,
                    min_gain=1, k_tfidf=150, min_body_share=0.25, cover=None):
    """topical matcher induction judged by the deliverable's own metrics.
    near : boolean [N], documents that have THIS dimension among their 3 nearest (the embedding neighbourhood).
    A candidate term must (a) come from a topical source, (b) occur in >= min_body_share of the cluster's documents' body text (TF-IDF matrix),
    (c) occur in the metadata of >= need train seeds, (d) have >= ps_min of the train documents it catches inside the cluster,
    (e) have >= p3_min of the train documents it catches inside the neighbourhood."""
    S = seeds & train; nS = int(S.sum())
    if nS < 3: return []
    CV = (cover & train) if cover is not None else S
    if CV.sum() < 1: return []
    need = max(s_min_abs, int(np.ceil(s_min_frac * nS)))
    Sidx = np.where(S)[0]
    cm = np.asarray(tp.X[Sidx].mean(axis=0)).ravel(); om = np.asarray(tp.X[np.where(train)[0]].mean(axis=0)).ravel()
    body_share = np.asarray((tp.X[Sidx] > 0).mean(axis=0)).ravel()
    score = cm * (cm / (om + 1e-9)); score[body_share < min_body_share] = 0
    top = np.argsort(-score)[:k_tfidf]
    cols = {tp.col[tp.vocab[j]] for j in top if score[j] > 0 and tp.vocab[j] in tp.col}
    s_cnt = np.asarray(ix.B[S].sum(axis=0)).ravel(); d_cnt = np.asarray(ix.B[train].sum(axis=0)).ravel()
    share_s = s_cnt / max(1, len(Sidx)); share_all = d_cnt / max(1, int(train.sum()))
    for arr in (tp.kw_cols, tp.ent_cols):
        ok = arr[(s_cnt[arr] >= need) & (share_s[arr] >= 3.0 * np.maximum(share_all[arr], 1e-9))]
        cols.update(ok.tolist())
    cand = np.array(sorted(cols), dtype=int)
    if len(cand) == 0: return []
    n3_cnt = np.asarray(ix.B[near & train].sum(axis=0)).ravel()
    ok = (s_cnt[cand] >= need) & (d_cnt[cand] > 0) & (s_cnt[cand] >= ps_min * d_cnt[cand]) & (n3_cnt[cand] >= p3_min * d_cnt[cand])
    cols = cand[ok]
    if len(cols) == 0: return []
    Cidx = np.where(CV)[0]; Bs = ix.Br[Cidx][:, cols].toarray().astype(bool); prec = n3_cnt[cols] / d_cnt[cols]
    covered = np.zeros(len(Cidx), dtype=bool); chosen = []; used = np.zeros(len(cols), dtype=bool)
    while len(chosen) < max_terms and covered.sum() < target * len(Cidx):
        gain = (Bs & ~covered[:, None]).sum(axis=0); gain[used] = -1
        best = int(np.argmax(gain + 1e-3 * prec - 1e-6 * np.array([len(ix.terms[c]) for c in cols])))
        if gain[best] < min_gain: break
        chosen.append(ix.terms[cols[best]]); covered |= Bs[:, best]; used[best] = True
    return chosen
