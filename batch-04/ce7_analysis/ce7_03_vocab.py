"""CE-7 step 7 (Line 2): enrichment vocabulary. Per-document counts only, so it is immune to the chunk skew.
Writes batch-04/ce7_enrichment_vocabulary_2026-09-26.csv and cache/vocab_candidates.json; prints a summary that
ce7_report_vocab.py-style prose in the other reports draws on. Read-only on the repo.

FINDING that shapes this step: `primary_topics` and `sub_topics` are one-sentence PROSE items, not tags. Exact-value counting
(the literal spec) yields no value in >= 3 documents. So three analyses are run and kept separate:
  A  exact values of primary_topics / sub_topics  (the literal spec)
  B  `keywords` (the Keyword/s column): the curators' short-tag vocabulary
  C  phrases extracted from the primary_topics + sub_topics prose (document frequency of 1-3-grams)
"""
import csv, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

t0 = time.time()
C = Corpus(); P = prior_art(); S = score_all_docs(C)
N = len(C.doc_ids); FM = FMT_ORDER
m = P["module"]; tax = P["taxonomy"]
maxs = np.array([max(S[d].values()) for d in C.doc_ids])
MIN_DF = 15

def catches(value):
    """prior-art topics whose matcher fires on the value string itself (word-boundary, same engine as the taxonomy)."""
    hs = value.lower()
    return [tid for tid, t in tax.items() if m.score_topic(t, hs) > 0]

def spread(doc_idx):
    c = Counter(C.doc_fmt[i] for i in doc_idx)
    return c, {f: c[f] / C.fmt_docs[f] for f in FM}

def exemplars(doc_idx, n=3):
    V = C.doc_vec[list(doc_idx)]; cen = unit(V.mean(axis=0)); order = np.argsort(-(V @ cen))[:n]
    return [C.doc_ids[list(doc_idx)[i]] for i in order]

def row_for(source, value, doc_idx):
    c, sh = spread(doc_idx); cov = catches(value)
    bk = {C.work[C.doc_ids[i]] for i in doc_idx if C.doc_ids[i][0] == "B"}
    ex = exemplars(doc_idx)
    di = np.array(sorted(doc_idx))
    return {"source": source, "value": value, "doc_count": len(di),
            **{f"docs_{f}": c[f] for f in FM}, **{f"pct_of_{f}": round(100 * sh[f], 1) for f in FM},
            "n_book_works": len(bk), "formats_with_>=3_docs": sum(1 for f in FM if c[f] >= 3),
            "exemplar_1": ex[0], "exemplar_2": ex[1] if len(ex) > 1 else "", "exemplar_3": ex[2] if len(ex) > 2 else "",
            "covered_by_prior_art": "y" if cov else "n", "covering_topics": ";".join(cov[:4]),
            "share_docs_best_score_le1": round(float((maxs[di] <= 1).mean()), 3), "share_docs_score_zero": round(float((maxs[di] == 0).mean()), 3),
            "clears_15_docs": "y" if len(di) >= MIN_DF else "n",
            "dominant_format_by_share": max(FM, key=lambda f: sh[f]),
            "book_to_column_share_ratio": round(sh["books"] / sh["columns"], 2) if sh["columns"] > 0 else "inf"}

rows_out = []
summary = {}

# ------------------------------------------------------------------ A. exact values (the literal spec)
A = {}
for field in ("primary_topics", "sub_topics"):
    df = defaultdict(set)
    for i, d in enumerate(C.doc_ids):
        for x in C.docs[d].get(field) or []:
            if isinstance(x, str) and x.strip():
                df[norm_value(x)].add(i)
    lens = [len(v) for v in df]
    A[field] = {"distinct_values": len(df), "max_docs_for_one_value": max(len(s) for s in df.values()),
                **{f"values_in_>={t}_docs": sum(1 for s in df.values() if len(s) >= t) for t in (2, 3, 5, 10, 15)},
                "median_value_length_chars": int(np.median([len(v) for v in df])), "p90_value_length_chars": int(np.percentile([len(v) for v in df], 90))}
    for v, s in df.items():
        if len(s) >= 2:
            rows_out.append(row_for(f"A_exact_{field}", v, s))
summary["A_exact"] = A

# ------------------------------------------------------------------ B. keywords (curated short tags)
dfk = defaultdict(set)
for i, d in enumerate(C.doc_ids):
    for x in C.docs[d].get("keywords") or []:
        if isinstance(x, str) and x.strip():
            dfk[norm_value(x)].add(i)
B = {"distinct_values": len(dfk), **{f"values_in_>={t}_docs": sum(1 for s in dfk.values() if len(s) >= t) for t in (2, 3, 5, 10, 15, 25)}}
kw_rows = []
for v, s in dfk.items():
    if len(s) >= 5:
        r = row_for("B_keywords", v, s); rows_out.append(r); kw_rows.append(r)
kw15 = [r for r in kw_rows if r["doc_count"] >= MIN_DF]
B["cleared_15"] = len(kw15); B["cleared_15_uncaught"] = sum(1 for r in kw15 if r["covered_by_prior_art"] == "n")
B["cleared_10"] = sum(1 for r in kw_rows if r["doc_count"] >= 10); B["cleared_10_uncaught"] = sum(1 for r in kw_rows if r["doc_count"] >= 10 and r["covered_by_prior_art"] == "n")
summary["B_keywords"] = B
print("A/B done", round(time.time() - t0), "s", flush=True)

# ------------------------------------------------------------------ C. phrases from the prose fields
BOUNDARY_STOP = set(ENGLISH_STOP_WORDS) | {"cjp", "panganiban", "chapter", "column", "author", "argues", "argue", "writes", "wrote", "says", "said", "also", "new", "one", "two", "three",
                                            "first", "second", "would", "may", "can", "must", "mr", "ms", "jr", "sr", "sen", "atty", "ponencia", "section", "sec", "art", "vs"}
prose = []
for d in C.doc_ids:
    parts = [x for f in ("primary_topics", "sub_topics") for x in (C.docs[d].get(f) or []) if isinstance(x, str)]
    prose.append(" . ".join(parts).lower())
cv = CountVectorizer(ngram_range=(1, 3), lowercase=True, min_df=MIN_DF, max_df=0.25, binary=True, token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-']{1,}\b", dtype=np.int8)
Xp = cv.fit_transform(prose).tocsc()
terms = np.array(cv.get_feature_names_out())
def ok(term):
    toks = term.split()
    if toks[0] in BOUNDARY_STOP or toks[-1] in BOUNDARY_STOP: return False
    if len(toks) == 1 and len(toks[0]) < 4: return False
    return True
keep = [j for j, t in enumerate(terms) if ok(t)]
print("prose n-grams with df in [15, 25%]:", len(terms), "-> after boundary filter", len(keep), round(time.time() - t0), "s", flush=True)
docsets = {j: set(Xp[:, j].nonzero()[0].tolist()) for j in keep}
order = sorted(keep, key=lambda j: (-len(docsets[j]), terms[j]))
c_rows = [row_for("C_prose_ngram", terms[j], docsets[j]) for j in order]
rows_out.extend(c_rows)
print("prose rows built", len(c_rows), round(time.time() - t0), "s", flush=True)
C_un = [r for r in c_rows if r["covered_by_prior_art"] == "n"]
# --- does 'enriched in weakly-covered documents' pick out real dimensions, or is it multiple-comparison noise?
weak = (maxs <= 1).astype(np.float32); base = float(weak.mean())
Xk = Xp[:, [j for j in order]].tocsr().astype(np.float32)
dfv = np.asarray(Xk.sum(axis=0)).ravel()
def hits(wvec, mult=2.0, min_weak=8):
    cnt = np.asarray(Xk.T @ wvec).ravel(); sh = cnt / dfv
    return int(((sh >= mult * base) & (cnt >= min_weak)).sum())
obs = {m_: hits(weak, m_) for m_ in (1.5, 2.0, 2.5)}
prng = np.random.default_rng(20260926)
perm = {m_: [hits(prng.permutation(weak), m_) for _ in range(300)] for m_ in (1.5, 2.0, 2.5)}
enrich = {str(m_): {"observed": obs[m_], "shuffled_mean": float(np.mean(perm[m_])), "shuffled_p95": float(np.percentile(perm[m_], 95)), "shuffled_max": int(np.max(perm[m_]))} for m_ in obs}
summary["C_prose"] = {"ngrams_df15_le25pct_after_filter": len(c_rows), "uncaught_by_matcher_string_test": len(C_un), "weak_coverage_enrichment_vs_shuffled_labels": enrich, "baseline_weak_share": base}

# ------------------------------------------------------------------ write CSV
cols = ["source", "value", "doc_count", "clears_15_docs", "docs_columns", "docs_books", "docs_speeches", "docs_biography",
        "pct_of_columns", "pct_of_books", "pct_of_speeches", "pct_of_biography", "n_book_works", "formats_with_>=3_docs",
        "exemplar_1", "exemplar_2", "exemplar_3", "covered_by_prior_art", "covering_topics",
        "share_docs_best_score_le1", "share_docs_score_zero", "dominant_format_by_share", "book_to_column_share_ratio"]
rows_out.sort(key=lambda r: (r["source"], -r["doc_count"], r["value"]))
with open(B4 / "ce7_enrichment_vocabulary_2026-09-26.csv", "w", encoding="utf-8-sig", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n"); wr.writeheader()
    for r in rows_out: wr.writerow({c: r.get(c, "") for c in cols})
print("csv rows:", len(rows_out), round(time.time() - t0), "s")

# ------------------------------------------------------------------ candidate export for steps 8-9
# Curated keywords only: the prose-phrase route did not yield coherent candidates (see the shuffled-label test above).
cand = [{"source": "B_keywords", "value": r["value"], "docs": [C.doc_ids[i] for i in sorted(dfk[r["value"]])]}
        for r in kw15 if r["covered_by_prior_art"] == "n"]
cand_all15 = [{"source": "B_keywords", "value": r["value"], "docs": [C.doc_ids[i] for i in sorted(dfk[r["value"]])], "covered": r["covered_by_prior_art"]} for r in kw15]
cand10 = [{"source": "B_keywords", "value": r["value"], "docs": [C.doc_ids[i] for i in sorted(dfk[r["value"]])]} for r in kw_rows if r["doc_count"] >= 10 and r["covered_by_prior_art"] == "n"]
json.dump({"candidates": cand, "candidates_ge10_uncaught": cand10, "keywords_ge15_all": cand_all15, "summary": summary,
           "keywords_all_ge5": {r["value"]: sorted(dfk[r["value"]]) for r in kw_rows}}, open(CACHE / "vocab_candidates.json", "w"), default=lambda o: o.tolist() if hasattr(o, "tolist") else int(o))
print(json.dumps(summary, indent=1))
print("candidates exported:", len(cand), "uncaught keywords in >=15 docs;", len(cand10), "in >=10 docs")
print("done", round(time.time() - t0), "s")
