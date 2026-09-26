"""CE-7 step 6 (Line 1): cluster the orphan documents, then cross-check at chunk level.
Writes batch-04/ce7_orphan_clusters_2026-09-26.md and cache/orphan_clusters.json. Read-only on the repo.

Populations (P0 is the one the prompt specifies; P1/P2 exist because 46 documents cannot support k up to 40):
  P0  strict: documents scoring zero on every prior-art matcher
  P1  weak  : documents whose best matcher score is <= 1 (zero, or one incidental keyword hit)
  P2  format-fair embedding orphans: the bottom 10% of each format's OWN doc-mean-vector affinity to the prior-art centroids
"""
import json, os, sys, time, warnings
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score, adjusted_rand_score

t0 = time.time()
C = Corpus(); S = score_all_docs(C)
N = len(C.doc_ids)
maxs = {d: max(S[d].values()) for d in C.doc_ids}
nearB = np.load(CACHE / "nearest_B.npy")
FM = FMT_ORDER
pops = {"P0 strict (zero score)": [d for d in C.doc_ids if maxs[d] == 0],
        "P1 weak (score ≤ 1)": [d for d in C.doc_ids if maxs[d] <= 1]}
p2 = []
for f in FM:
    idx = [i for i, d in enumerate(C.doc_ids) if C.doc_fmt[i] == f]
    cut = np.quantile(nearB[idx], 0.10); p2 += [C.doc_ids[i] for i in idx if nearB[i] <= cut]
pops["P2 embedding orphans (bottom 10% per format)"] = sorted(p2)
PN = list(pops)
KMAX = 40
rng = np.random.default_rng(20260926)
L = []; out = {}
def w(s=""): L.append(s)
def table(headers, rows, align=None):
    w("| " + " | ".join(headers) + " |")
    w("|" + "|".join(("---:" if (align and align[i] == "r") else "---") for i in range(len(headers))) + "|")
    for r in rows: w("| " + " | ".join(str(x) for x in r) + " |")
    w()

# ---------------------------------------------------------------- TF-IDF over ALL 1,290 documents (IDF from the whole corpus)
STOP = {"summary", "notable", "anecdotes", "anecdote", "chapter", "ch", "vol", "cjp", "panganiban", "chief", "justice", "philippines", "philippine", "said", "mr", "ms"}
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
tf = TfidfVectorizer(ngram_range=(1, 2), stop_words=sorted(ENGLISH_STOP_WORDS | STOP), min_df=3, max_df=0.4, sublinear_tf=True,
                     token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-']{2,}\b", dtype=np.float32)
import scipy.sparse as sp, pickle
_xf, _vf = CACHE / "tfidf_doc.npz", CACHE / "tfidf_vocab.pkl"
if _xf.exists() and _vf.exists():
    Xdoc = sp.load_npz(_xf).tocsr(); tf_state = pickle.load(open(_vf, "rb")); vocab = tf_state["vocab"]; tf.vocabulary_ = tf_state["vocabulary_"]; tf.idf_ = tf_state["idf_"]
    tf._tfidf.idf_ = tf_state["idf_"]
else:
    Xdoc = tf.fit_transform([C.doc_text(d) for d in C.doc_ids])
    vocab = np.array(tf.get_feature_names_out())
    sp.save_npz(_xf, Xdoc.tocsr()); pickle.dump({"vocab": vocab, "vocabulary_": tf.vocabulary_, "idf_": tf.idf_}, open(_vf, "wb"))
print("tfidf fitted", Xdoc.shape, round(time.time() - t0), "s", flush=True)

def top_terms(doc_ids, n=15):
    idx = [C.doc_index[d] for d in doc_ids]
    m = np.asarray(Xdoc[idx].mean(axis=0)).ravel()
    return [vocab[i] for i in np.argsort(-m)[:n]]
def top_terms_chunks(rows, n=10):
    Xc = tf.transform([C.chunk_text[r] for r in rows]); m = np.asarray(Xc.mean(axis=0)).ravel()
    return [vocab[i] for i in np.argsort(-m)[:n]]

# ---------------------------------------------------------------- doc-level curves
def km_fit(X, k, n_init=10, seed=0, weights=None):
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(X, sample_weight=weights)
def sil_curve(X, kmax=KMAX, n_init=10):
    res = {}
    for k in range(2, min(kmax, len(X) - 1) + 1):
        km = km_fit(X, k, n_init); res[k] = (float(silhouette_score(X, km.labels_, metric="cosine")), float(km.inertia_))
    return res
curves, nulls = {}, {}
REUSE = os.environ.get("CE7_REUSE_CURVES") == "1" and (CACHE / "orphan_clusters.json").exists()
PREV = json.load(open(CACHE / "orphan_clusters.json")) if REUSE else None
for name in PN:
    if REUSE:
        dc = PREV["doc_curves"][name]
        curves[name] = {int(k): (v["sil"], v["inertia"]) for k, v in dc.items()}; nulls[name] = {int(k): v["null"] for k, v in dc.items()}
        print("curve reused", name, flush=True); continue
    docs = pops[name]; X = C.doc_vec[[C.doc_index[d] for d in docs]]
    curves[name] = sil_curve(X, n_init=(5 if name.startswith('P1') else 10))
    nl = [sil_curve(C.doc_vec[rng.choice(N, size=len(docs), replace=False)], n_init=4) for _ in range(3)]
    nulls[name] = {k: float(np.mean([n[k][0] for n in nl])) for k in curves[name]}
    print("curve done", name, len(docs), round(time.time() - t0), "s", flush=True)
out["doc_curves"] = {n: {k: {"sil": v[0], "inertia": v[1], "null": nulls[n][k]} for k, v in curves[n].items()} for n in PN}

def knee_inertia(cv):
    ks = np.array(sorted(cv)); y = np.array([cv[k][1] for k in ks]); xn = (ks - ks.min()) / (ks.max() - ks.min()); yn = (y - y.min()) / (y.max() - y.min())
    return int(ks[np.argmax((1 - yn) - xn)])   # kneedle for a decreasing convex curve
def analysis_knees(name):
    cv = curves[name]; ks = sorted(cv); n = len(pops[name])
    gmax = max(ks, key=lambda k: cv[k][0])
    adj = {k: cv[k][0] - nulls[name][k] for k in ks}
    amax = max(ks, key=lambda k: adj[k])
    cap = max(2, n // 10)
    capk = max([k for k in ks if k <= cap], key=lambda k: adj[k])
    sm = np.array([cv[k][0] for k in ks]); top = sm.max()
    plateau = [k for k in ks if cv[k][0] >= top - 0.02]
    return {"n": n, "global_max_k": gmax, "global_max_sil": cv[gmax][0], "null_adjusted_max_k": amax, "null_adjusted_excess": adj[amax],
            "inertia_elbow_k": knee_inertia(cv), "cap_k(N/10)": cap, "best_k_under_cap": capk, "plateau_k_within_0.02_of_max": [min(plateau), max(plateau)],
            "mean_excess_over_null": float(np.mean(list(adj.values())))}
knees = {n: analysis_knees(n) for n in PN}
out["knees"] = knees

# ---------------------------------------------------------------- report header
w("# CE-7 · step 6 — orphan clustering (document level, then chunk level)")
w()
w("**Date** 2026-09-26. Population, method and every caveat first; clusters after.")
w()
w("## Populations")
w()
w("The prompt specifies the documents scoring **zero** on every prior-art matcher (P0). That set is **46 documents** — too few to support k up to 40, and step 4 already showed the zero test is insensitive. "
  "Two broader populations are therefore clustered alongside it, and labelled as additions:")
w()
rows = []
for n in PN:
    d = pops[n]; c = Counter(fmt_of(x) for x in d)
    rows.append([n, len(d), " / ".join(str(c[f]) for f in FM), sum(len(C.rows_of[x]) for x in d)])
table(["population", "docs", "by format (col / book / spe / bio)", "chunks"], rows, "lrrr")
w("Each document is represented by the **mean of its chunk vectors** (unit-normalised), so a long book chapter and a short column are one point each. "
  "k-means (`n_init` 10, fixed seed), silhouette on cosine distance, k = 2…40 (capped at N−1). **Null**: the same procedure on the same number of *randomly drawn documents* from the whole corpus (3 draws averaged) — a silhouette only counts as structure to the extent it beats that.")
w()
w("## Document-level silhouette curves, k = 2…40")
w()
hdr = ["k"]
for n in PN: hdr += [n.split(" ")[0] + " silhouette", n.split(" ")[0] + " null"]
rows = []
for k in range(2, KMAX + 1):
    r = [k]
    for n in PN:
        r += [f"{curves[n][k][0]:.3f}" if k in curves[n] else "–", f"{nulls[n][k]:.3f}" if k in nulls[n] else "–"]
    rows.append(r)
table(hdr, rows, "r" * len(hdr))
w("### Knees")
w()
rows = []
for n in PN:
    kk = knees[n]
    rows.append([n, kk["n"], f"k={kk['global_max_k']} ({kk['global_max_sil']:.3f})", f"k={kk['null_adjusted_max_k']} (+{kk['null_adjusted_excess']:.3f})", f"k={kk['inertia_elbow_k']}",
                 f"{kk['plateau_k_within_0.02_of_max'][0]}–{kk['plateau_k_within_0.02_of_max'][1]}", f"k={kk['best_k_under_cap']} (cap {kk['cap_k(N/10)']})", f"{kk['mean_excess_over_null']:+.3f}"])
table(["population", "N", "silhouette maximum", "max excess over null", "inertia elbow (kneedle)", "k range within 0.02 of the maximum", "best k with average cluster ≥ 10 docs", "mean excess over null (all k)"], rows, "lrrrrrrr")
w("**Reading the curves.** "
  + " ".join(f"{n.split(' ')[0]}: mean silhouette excess over null {knees[n]['mean_excess_over_null']:+.3f}, maximum {knees[n]['global_max_sil']:.3f}." for n in PN)
  + " A silhouette below ~0.25 is conventionally weak structure; none of these curves leaves that band.")
w()

# ---------------------------------------------------------------- cluster description
def describe(name, k, tag):
    docs = pops[name]; idx = [C.doc_index[d] for d in docs]; X = C.doc_vec[idx]
    km = km_fit(X, k); lab = km.labels_
    sil = silhouette_score(X, lab, metric="cosine")
    # bootstrap stability: 20 resamples of 80% of docs, ARI vs the full fit on the shared docs
    aris = []
    for r in range(20):
        sub = np.sort(rng.choice(len(docs), size=int(0.8 * len(docs)), replace=False))
        kb = km_fit(X[sub], k, n_init=4, seed=r); aris.append(adjusted_rand_score(lab[sub], kb.labels_))
    res = {"population": name, "k": k, "silhouette": float(sil), "bootstrap_ARI_mean": float(np.mean(aris)), "bootstrap_ARI_min": float(np.min(aris)), "clusters": []}
    fmt_pop = Counter(fmt_of(d) for d in docs)
    w(f"### {tag}: {name} at k = {k}")
    w()
    w(f"silhouette {sil:.3f} · bootstrap stability (ARI of 20 × 80% resamples vs the full fit): mean {np.mean(aris):.2f}, worst {np.min(aris):.2f} · cluster sizes (docs): {sorted(Counter(lab.tolist()).values(), reverse=True)}")
    w()
    order = sorted(range(k), key=lambda c: -int((lab == c).sum()))
    for c in order:
        members = [docs[i] for i in range(len(docs)) if lab[i] == c]
        cen = unit(X[lab == c].mean(axis=0)); sims = X[lab == c] @ cen
        ex = [members[i] for i in np.argsort(-sims)[:5]]
        chunks = sum(len(C.rows_of[d]) for d in members); fc = Counter(fmt_of(d) for d in members)
        mix = " · ".join(f"{f[:3]} {fc[f]} ({pct(fc[f], fmt_pop[f])} of pop. / {pct(fc[f], C.fmt_docs[f])} of corpus)" for f in FM if fc[f])
        works = Counter(C.work[d] for d in members if d[0] == "B")
        w(f"**Cluster {c + 1}** — **{len(members)} distinct docs**, {chunks} raw chunks ({chunks / len(members):.1f} chunks/doc)")
        w(f"* format mix, each as a share of that format's own docs — {mix}")
        if works: w(f"* books by work: " + "; ".join(f"{a} ×{b}" for a, b in works.most_common()))
        w(f"* top-15 TF-IDF terms: {', '.join(top_terms(members))}")
        w("* exemplars (nearest the cluster centre): " + "; ".join(f"`{d}` {C.title[d][:70]}" for d in ex))
        w()
        res["clusters"].append({"label": c + 1, "docs": members, "n_docs": len(members), "n_chunks": chunks, "format_docs": dict(fc), "exemplars": ex, "terms": top_terms(members),
                                "works": dict(works)})
    return res, lab

detail = {}
kk0 = knees[PN[0]]
w("## Cluster detail — P0 (the prompt's population)")
w()
w(f"Two views: **k = {kk0['global_max_k']}**, the silhouette maximum (the prompt's “chosen k”, the knee of the full curve), and **k = {kk0['best_k_under_cap']}**, the coarsest scale at which clusters average ≥ 10 documents "
  "(the smallest size this phase treats as a viable dimension). At the first, clusters are small; that is reported, not hidden.")
w()
detail["P0_kmax"], lab_p0 = describe(PN[0], kk0["global_max_k"], "P0 view 1")
detail["P0_cap"], lab_p0c = describe(PN[0], kk0["best_k_under_cap"], "P0 view 2")
kk2 = knees[PN[2]]
w("## Cluster detail — P2 (format-fair embedding orphans; addition)")
w()
w(f"Described at **k = {kk2['best_k_under_cap']}** (best null-adjusted silhouette with an average cluster of ≥ 10 documents; the silhouette maximum is at k={kk2['global_max_k']} but there clusters average {len(pops[PN[2]]) / kk2['global_max_k']:.1f} documents).")
w()
detail["P2_cap"], lab_p2 = describe(PN[2], kk2["best_k_under_cap"], "P2")
kk1 = knees[PN[1]]
w("## P1 (weak coverage; addition) — no cluster detail")
w()
w(f"Mean silhouette excess over the random-document null is {kk1['mean_excess_over_null']:+.3f} and the maximum is {kk1['global_max_sil']:.3f} (null at that k: {nulls[PN[1]][kk1['global_max_k']]:.3f}). "
  "**The 240 weakly-covered documents do not form clusters any more than 240 random documents do.** They are documents whose metadata happened to match few matcher terms, not a missing topic; clustering them further would describe noise.")
w()

# ---------------------------------------------------------------- chunk-level cross-check
w("## Chunk-level cross-check")
w()
w("Population chunks are all the chunks of the population's documents. Two runs each, because book chapters contribute 18 chunks against a column's 7: "
  "**unweighted** (every chunk counts once — carries the book skew) and **document-weighted** (every chunk weighted 1 / its document's chunk count, so each document counts once). "
  "Silhouette is computed unweighted in both (scikit-learn has no weighted silhouette); only the k-means fit differs.")
w()
chunk_out = {}
def chunk_curve(rows, weights, kmax=KMAX):
    Xc = C.mat[rows]; res = {}
    for k in range(2, min(kmax, len(Xc) - 1) + 1):
        km = km_fit(Xc, k, n_init=5, weights=weights)
        res[k] = float(silhouette_score(Xc, km.labels_, metric="cosine"))
    return res
def chunk_study(name, doc_lab, doc_k, tag):
    docs = pops[name]; rows = [r for d in docs for r in C.rows_of[d]]
    wts = np.array([1.0 / len(C.rows_of[C.chunk_doc[r]]) for r in rows]); wts = wts / wts.mean()
    if REUSE and name in PREV["chunk"]:
        cu = {int(k): v for k, v in PREV["chunk"][name]["curve_unweighted"].items()}; cw = {int(k): v for k, v in PREV["chunk"][name]["curve_weighted"].items()}
    else:
        cu = chunk_curve(rows, None); cw = chunk_curve(rows, wts)
    ks = sorted(cu)
    w(f"### {tag}: {name} — {len(rows)} chunks from {len(docs)} documents")
    w()
    table(["k", "unweighted", "doc-weighted"], [[k, f"{cu[k]:.3f}", f"{cw[k]:.3f}"] for k in ks if k <= 12 or k % 4 == 0], "rrr")
    bu = max(ks, key=lambda k: cu[k]); bw = max(ks, key=lambda k: cw[k])
    w(f"Silhouette maximum: unweighted k={bu} ({cu[bu]:.3f}); document-weighted k={bw} ({cw[bw]:.3f}). Document-level knee for this population: k={doc_k}.")
    w()
    kc = doc_k   # describe the chunk clustering at the SAME k as the document-level view, so the two are directly comparable
    Xc = C.mat[rows]
    res = {}
    for wname, ww in (("unweighted", None), ("doc-weighted", wts)):
        km = km_fit(Xc, kc, n_init=10, weights=ww); cl = km.labels_
        doc_of = np.array([C.chunk_doc[r] for r in rows])
        info = []
        for c in range(kc):
            m = cl == c
            if not m.any(): continue
            dcount = Counter(doc_of[m]); nd = len(dcount); top3 = sum(v for _, v in dcount.most_common(3)) / m.sum()
            coh = np.mean([dcount[d] / len(C.rows_of[d]) for d in dcount])          # avg share of a member doc's chunks that sit in this cluster
            fc = Counter(fmt_of(d) for d in doc_of[m])
            info.append({"c": c + 1, "chunks": int(m.sum()), "docs": nd, "top3_share": float(top3), "cohesion": float(coh), "fmt_chunks": dict(fc)})
        info.sort(key=lambda r: -r["chunks"])
        res[wname] = {"labels": cl, "info": info}
        w(f"**{wname} k-means, k = {kc}** — per cluster: raw chunks, distinct documents, share of the cluster's chunks that come from its 3 biggest documents (high ⇒ a few documents), "
          "*cohesion* = average share of each member document's own chunks that also sit in this cluster (high ⇒ whole documents, low ⇒ passages from many documents), format mix as a share of each format's chunks in the population.")
        w()
        fcp = Counter(fmt_of(C.chunk_doc[r]) for r in rows)
        table(["cluster", "chunks", "distinct docs", "top-3 doc share", "cohesion", "format mix (share of that format's population chunks)", "shape"],
              [[r["c"], r["chunks"], r["docs"], f"{100 * r['top3_share']:.0f}%", f"{r['cohesion']:.2f}",
                " · ".join(f"{f[:3]} {pct(r['fmt_chunks'].get(f, 0), fcp[f])}" for f in FM if r["fmt_chunks"].get(f)),
                "**≤ 3 docs (skew artefact)**" if r["docs"] <= 3 else ("document-shaped" if r["cohesion"] >= 0.5 else "passage-shaped")] for r in info], "rrrrrlr")
        few = [r for r in info if r["docs"] <= 3]
        w(f"*Clusters drawn from ≤ 3 documents: **{len(few)} of {len(info)}**, holding {sum(r['chunks'] for r in few)} of {sum(r['chunks'] for r in info)} chunks ({100 * sum(r['chunks'] for r in few) / sum(r['chunks'] for r in info):.0f}%). "
          "A long book chapter can fill a chunk cluster by itself; that is a property of chapter length, not evidence of a dimension of the corpus.*")
        w()
        res[wname]["few_doc_clusters"] = len(few); res[wname]["n_clusters"] = len(info)
    # agreement between the two levels
    Xd = C.doc_vec[[C.doc_index[d] for d in docs]]
    modal = []
    for j, d in enumerate(docs):
        rr = [i for i, r in enumerate(rows) if C.chunk_doc[r] == d]
        modal.append(Counter(res["unweighted"]["labels"][rr]).most_common(1)[0][0])
    ari_u = adjusted_rand_score(doc_lab, modal)
    modal_w = []
    for j, d in enumerate(docs):
        rr = [i for i, r in enumerate(rows) if C.chunk_doc[r] == d]
        modal_w.append(Counter(res["doc-weighted"]["labels"][rr]).most_common(1)[0][0])
    ari_w = adjusted_rand_score(doc_lab, modal_w)
    # how dispersed are a doc's chunks across chunk clusters
    disp = []
    for j, d in enumerate(docs):
        rr = [i for i, r in enumerate(rows) if C.chunk_doc[r] == d]
        cnt = Counter(res["unweighted"]["labels"][rr]); disp.append(cnt.most_common(1)[0][1] / len(rr))
    w(f"**Agreement between the levels (k = {kc} at both).** Adjusted Rand index between the document-level clusters and each document's *modal* chunk cluster: unweighted **{ari_u:.2f}**, document-weighted **{ari_w:.2f}** "
      f"(1 = identical partitions, 0 = chance). On average {100 * np.mean(disp):.0f}% of a document's chunks fall in its single most common chunk cluster.")
    w()
    # doc-level cluster -> chunk-cluster spread
    rows_x = []
    for c in sorted(set(doc_lab)):
        mem = [j for j in range(len(docs)) if doc_lab[j] == c]
        fr = [max(Counter(res["unweighted"]["labels"][[i for i, r in enumerate(rows) if C.chunk_doc[r] == docs[j]]]).values()) / len(C.rows_of[docs[j]]) for j in mem]
        tgt = Counter(modal[j] for j in mem)
        rows_x.append([c + 1, len(mem), f"{100 * np.mean(fr):.0f}%", ", ".join(f"chunk-cl {a + 1}×{b}" for a, b in tgt.most_common(3))])
    table(["doc-level cluster", "docs", "avg share of a doc's chunks in its modal chunk cluster", "modal chunk clusters of its docs"], rows_x, "rrrl")
    chunk_out[name] = {"few_doc": {wn: res[wn].get("few_doc_clusters") for wn in res}, "n_clusters": {wn: res[wn].get("n_clusters") for wn in res}, "k": kc, "ari_unweighted": float(ari_u), "ari_weighted": float(ari_w), "curve_unweighted": cu, "curve_weighted": cw, "max_unweighted": [bu, cu[bu]], "max_weighted": [bw, cw[bw]]}
    return res

w("*(Chunk clusters are numbered independently of document clusters; the cross-table below shows the correspondence.)*"); w()
chunk_study(PN[0], lab_p0, kk0["global_max_k"], "P0")
chunk_study(PN[2], lab_p2, kk2["best_k_under_cap"], "P2")
out["chunk"] = chunk_out

# ---------------------------------------------------------------- where the levels disagree
w("## Where document-level and chunk-level evidence disagree")
w()
for n in (PN[0], PN[2]):
    co = chunk_out[n]
    w(f"* **{n}.** Document-level silhouette maximum k={knees[n]['global_max_k']} ({knees[n]['global_max_sil']:.3f}); chunk-level maximum k={co['max_unweighted'][0]} ({co['max_unweighted'][1]:.3f}) unweighted, "
      f"k={co['max_weighted'][0]} ({co['max_weighted'][1]:.3f}) document-weighted; partition agreement (ARI, unweighted / document-weighted) {co['ari_unweighted']:.2f} / {co['ari_weighted']:.2f}. "
      "Where the unweighted and document-weighted chunk runs pick different k or produce different clusters, the difference is the book skew (a book chapter's 18 chunks outvote a column's 7).")
w()
for n in (PN[0], PN[2]):
    co = chunk_out[n]
    if "few_doc" in co:
        w(f"* **Skew, measured ({n.split(' ')[0]}):** at the document-level k, chunk clusters drawn from ≤ 3 documents number {co['few_doc']['unweighted']} of {co['n_clusters']['unweighted']} in the unweighted run and {co['few_doc']['doc-weighted']} of {co['n_clusters']['doc-weighted']} once every document counts once. The difference is the book skew.")
w()
w("**Rule used to read the tables above.** A cluster with high *cohesion* (whole documents land together) and a document-level counterpart is **document-shaped** — a candidate dimension of the corpus. A cluster with low cohesion drawn from many documents, each contributing a few passages, is **passage-shaped** — "
  "a recurring passage-level motif (a quotation, a story, a structural section) that does not describe what any document is *about*; it should not become a topic on its own.")
w()

Path(B4 / "ce7_orphan_clusters_2026-09-26.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
out["detail"] = {k: {kk: vv for kk, vv in v.items()} for k, v in detail.items()}
out["populations"] = {n: pops[n] for n in PN}
json.dump(out, open(CACHE / "orphan_clusters.json", "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
print("done", round(time.time() - t0), "s;", len(L), "lines")
