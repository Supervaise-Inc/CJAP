"""CE-7 steps 9-10 (Line 4): candidate centroids, viability minima, separation, and the degenerate prior-art topics.
Writes batch-04/ce7_candidate_separation_2026-09-26.md. Read-only on the repo. Does NOT choose a topic count."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *

C = Corpus(); P = prior_art(); S = score_all_docs(C)
tax = P["taxonomy"]
N = len(C.doc_ids); FM = FMT_ORDER
mu = C.mat.mean(axis=0)
rng = np.random.default_rng(20260926)
members = json.load(open(CACHE / "prior_members.json"))
vocab = json.load(open(CACHE / "vocab_candidates.json"))
orph = json.load(open(CACHE / "orphan_clusters.json"))
cov = json.load(open(CACHE / "ce7_cov.json"))
MIN_DOCS, MIN_CHUNKS = 10, 3       # step 5's own thin-topic minima; justified empirically below

def cents(docs):
    rows = [r for d in docs for r in C.rows_of[d]]
    if not rows: return None, None, 0
    m = C.mat[rows].mean(axis=0)
    return unit(m).astype(np.float32), unit(m - mu).astype(np.float32), len(rows)

L = []
def w(s=""): L.append(s)
def table(headers, rows, align=None):
    w("| " + " | ".join(headers) + " |")
    w("|" + "|".join(("---:" if (align and align[i] == "r") else "---") for i in range(len(headers))) + "|")
    for r in rows: w("| " + " | ".join(str(x) for x in r) + " |")
    w()

# ---------------------------------------------------------------- prior art (non-fallback)
pa_ids = [t for t in P["centroid_ids"] if members[t]]
pa_raw, pa_ctr = {}, {}
for t in pa_ids:
    r_, c_, _ = cents(members[t]); pa_raw[t] = r_; pa_ctr[t] = c_
PA_R = np.stack([pa_raw[t] for t in pa_ids]); PA_C = np.stack([pa_ctr[t] for t in pa_ids])
fb = [t for t in P["centroid_ids"] if not members[t]]

# ---------------------------------------------------------------- candidates
cands = []
p0, p2 = orph["detail"]["P0_kmax"], orph["detail"]["P2_cap"]
p0c = orph["detail"]["P0_cap"]
for tag, det in ((f"orphan P0 k={p0['k']}", p0), (f"orphan P0 k={p0c['k']}", p0c), (f"orphan P2 k={p2['k']}", p2)):
    for cl in det["clusters"]:
        cands.append({"id": f"{tag} · c{cl['label']}", "line": "1 orphan cluster", "docs": cl["docs"], "terms": ", ".join(cl["terms"][:5])})
for c in vocab["candidates"]:
    cands.append({"id": f"kw · {c['value']}", "line": "2 keyword (≥15 docs, uncaught)", "docs": c["docs"], "terms": ""})
extra10 = [c for c in vocab.get("candidates_ge10_uncaught", []) if c["value"] not in {x["value"] for x in vocab["candidates"]}]
for c in cands:
    r_, c_, nch = cents(c["docs"]); c["raw"], c["ctr"], c["chunks"] = r_, c_, nch
    c["n_docs"] = len(c["docs"]); c["fmt"] = Counter(fmt_of(d) for d in c["docs"])
    c["viable"] = c["n_docs"] >= MIN_DOCS and c["chunks"] >= MIN_CHUNKS

w("# CE-7 · steps 9–10 — candidate separation, viability, and the degenerate prior-art topics")
w()
w("**Date** 2026-09-26. **This report does not choose a topic count.** It states what each candidate is, whether it is viable, and what it duplicates.")
w()
w("## Candidate set")
w()
w(f"* **Line 1 — orphan clusters** (step 6): P0 (strict zero set) at k={p0['k']} and k={p0c['k']}; P2 (format-fair embedding orphans) at k={p2['k']}. P1 is not used: it is indistinguishable from random documents.")
w(f"* **Line 2 — curated keywords** (step 7): the {len(vocab['candidates'])} values in ≥ 15 documents that no prior-art matcher catches. (Sensitivity: {len(extra10)} further values reach 10–14 documents; listed at the end, not used.) "
  "The literal `primary_topics`/`sub_topics` route produced no candidates (they are prose), and prose phrases produced only chance-level enrichment, so neither contributes.")
w("* **Line 3 — per-work coverage** (step 8) is evidence about the candidates above, not a separate source: see `ce7_per_work_coverage_2026-09-26.md`.")
w(f"* **Comparators:** the {len(pa_ids)} non-fallback prior-art centroids, rebuilt over the 1,290-document corpus (step 5). {', '.join(fb)} has no members and is excluded from every comparison.")
w()

# ---------------------------------------------------------------- Step 7 evidence (Line 2), rendered from the CSV + summary
import csv as _csv
vs = vocab["summary"]
w("## Line 2 evidence — enrichment vocabulary (step 7)")
w()
w("Full data: `ce7_enrichment_vocabulary_2026-09-26.csv`. Per-document counts only, so this evidence is **immune to the chunk skew**. The prompt gives this line the most weight because the curators wrote it by hand, document by document.")
w()
w("**What the prompt asked for returns nothing, and why.** `primary_topics` and `sub_topics` hold one-sentence prose items, not tags:")
w()
a = vs["A_exact"]
table(["field", "distinct values", "median length (chars)", "most documents sharing one value", "values in ≥ 2 docs", "≥ 5", "≥ 10", "**≥ 15**"],
      [[f, a[f]["distinct_values"], a[f]["median_value_length_chars"], a[f]["max_docs_for_one_value"], a[f]["values_in_>=2_docs"], a[f]["values_in_>=5_docs"], a[f]["values_in_>=10_docs"], f"**{a[f]['values_in_>=15_docs']}**"] for f in ("primary_topics", "sub_topics")], "lrrrrrrr")
w("**Zero values reach 15 documents.** Counting exact values in these two fields cannot produce a vocabulary. Two adaptations follow, kept separate and labelled:")
w()
b = vs["B_keywords"]
w(f"**B — the `keywords` field (the `Keyword/s` column), the curators' short-tag vocabulary.** {b['distinct_values']:,} distinct values; **{b['values_in_>=15_docs']} appear in ≥ 15 documents** ({b['values_in_>=10_docs']} in ≥ 10; {b['values_in_>=5_docs']} in ≥ 5). "
  f"**{b['cleared_15_uncaught']} of the {b['cleared_15']} are not caught by any prior-art matcher** (the matcher fires on the value string itself). All {b['cleared_15']}, with the per-format share of *that format's own documents*:")
w()
kwrows = [r for r in _csv.DictReader(open(B4 / "ce7_enrichment_vocabulary_2026-09-26.csv", encoding="utf-8-sig")) if r["source"] == "B_keywords" and r["clears_15_docs"] == "y"]
kwrows.sort(key=lambda r: -int(r["doc_count"]))
table(["value", "docs", "docs col / book / spe / bio", "% of each format's own docs (col / book / spe / bio)", "book works", "caught by prior art?", "share of its docs weakly covered", "3 exemplars"],
      [[r["value"], r["doc_count"], f"{r['docs_columns']} / {r['docs_books']} / {r['docs_speeches']} / {r['docs_biography']}",
        f"{r['pct_of_columns']} / {r['pct_of_books']} / {r['pct_of_speeches']} / {r['pct_of_biography']}", r["n_book_works"],
        ("yes — " + r["covering_topics"].split(";")[0]) if r["covered_by_prior_art"] == "y" else "**no**", f"{100*float(r['share_docs_best_score_le1']):.0f}%",
        ", ".join(f"`{r[k]}`" for k in ("exemplar_1", "exemplar_2", "exemplar_3"))] for r in kwrows], "lrrrrlrl")
bk = [r for r in kwrows if float(r["pct_of_books"]) >= 3 * max(float(r["pct_of_columns"]), 0.1)]
NEW_WORKS_ = {"Battles in the Supreme Court", "Judicial Renaissance", "Leadership by Example: The Davide Standard", "Leveling the Playing Field", "Liberty and Prosperity",
              "Love God, Serve Man", "Reforming the Judiciary", "Transparency, Unanimity & Diversity"}
def new_share(value):
    bdocs = [C.doc_ids[i] for i in vocab["keywords_all_ge5"][value] if C.doc_ids[i][0] == "B"]
    return (sum(1 for d in bdocs if C.work[d] in NEW_WORKS_) / len(bdocs)) if bdocs else None
bk_new = [r["value"] for r in bk if (new_share(r["value"]) or 0) >= 0.5]
w(f"**Format shape.** {len(bk)} of the {len(kwrows)} values are at least 3× more prevalent (as a share of documents) among book chapters than among columns; "
  f"{sum(1 for r in kwrows if int(r['docs_columns']) == 0)} occur in no column at all. Of the {len(bk)} book-skewed values, {len(bk_new)} have most of their book chapters in the eight works new to this batch and {len(bk) - len(bk_new)} in the four earlier works. "
  "This is a *document-level* fact, not a chunk-count artefact.")
w()
c = vs["C_prose"]; e = c["weak_coverage_enrichment_vs_shuffled_labels"]
w(f"**C — phrases extracted from the two prose fields** ({c['ngrams_df15_le25pct_after_filter']:,} one-to-three-word phrases in 15 or more documents but no more than a quarter of the corpus). Two findings, both against using them as candidates:")
w()
w(f"1. The matcher string test does not discriminate: {c['uncaught_by_matcher_string_test']:,} of {c['ngrams_df15_le25pct_after_filter']:,} phrases are “uncaught”, because a matcher term is a multi-word phrase and rarely sits inside another short phrase. It cannot be the filter.")
w(f"2. A better filter — phrases whose documents are *disproportionately weakly covered* (best matcher score ≤ 1; baseline share {100 * c['baseline_weak_share']:.1f}%) — is indistinguishable from chance. "
  "Each row compares the number of phrases passing the filter with the number that pass when the weak-coverage labels are **shuffled across documents** (300 shuffles):")
w()
table(["filter (weak share ≥ m × baseline, ≥ 8 weak docs)", "phrases passing (observed)", "passing under shuffled labels: mean", "95th percentile", "max"],
      [[f"m = {m}", e[m]["observed"], f"{e[m]['shuffled_mean']:.1f}", f"{e[m]['shuffled_p95']:.1f}", e[m]["shuffled_max"]] for m in ("1.5", "2.0", "2.5")], "lrrrr")
w("The observed counts sit at or below what shuffled labels produce, and the phrases that do pass are incoherent single words (“manual”, “voter”, “damages”, “perfect”, “massive”). **Prose phrases contribute no candidate dimensions.** They remain in the CSV, flagged, for anyone who wants to look.")
w()

# ---------------------------------------------------------------- minima with empirical justification
w("## Minimum size — and why")
w()
w(f"**Minima: {MIN_DOCS} distinct documents and {MIN_CHUNKS} chunks** — the same thresholds step 5 uses to flag a prior-art topic as thin. Justification, measured rather than asserted: "
  "draw two *disjoint* random subsets of n documents from a coherent pool and compare their centered centroids. If a group of n documents has a stable direction, two such groups from the same pool agree far more than two groups from unrelated pools.")
w()
pools_pa = {t: members[t] for t in pa_ids if len(members[t]) >= 60}
pool_names = sorted(pools_pa, key=lambda t: -len(pools_pa[t]))[:8]
kwmap = vocab["keywords_all_ge5"]
pools_kw = {k: [C.doc_ids[i] for i in v] for k, v in kwmap.items() if len(v) >= 40}
POOLS = {"matcher-defined prior-art topics (broad)": {t: pools_pa[t] for t in pool_names}, "curated-keyword groups (coherent by construction)": pools_kw}
def ctr_of(ds): return cents(ds)[1]
NS = (3, 5, 8, 10, 15, 20, 30)
null_by_n = {}
for n in NS:
    nullv = []
    for _ in range(150):
        idx = rng.permutation(N); a_ = [C.doc_ids[i] for i in idx[:n]]; b_ = [C.doc_ids[i] for i in idx[n:2 * n]]
        nullv.append(float(ctr_of(a_) @ ctr_of(b_)))
    null_by_n[n] = nullv
rows, floor_med, floor_p10 = [], {}, {}
for pname, pools in POOLS.items():
    for n in NS:
        topical = []
        for t, pool in pools.items():
            if len(pool) < 2 * n: continue
            for _ in range(12):
                idx = rng.permutation(len(pool)); a_ = [pool[i] for i in idx[:n]]; b_ = [pool[i] for i in idx[n:2 * n]]
                topical.append(float(ctr_of(a_) @ ctr_of(b_)))
        if not topical: continue
        nv = null_by_n[n]; med_ok = np.median(topical) > np.percentile(nv, 95); p10_ok = np.percentile(topical, 10) > np.percentile(nv, 95)
        rows.append([pname.split(" (")[0], n, len(pools) if True else 0, len(topical), f"{np.median(topical):.3f}", f"{np.percentile(topical, 10):.3f}", f"{np.median(nv):.3f}", f"{np.percentile(nv, 95):.3f}", "yes" if med_ok else "no", "yes" if p10_ok else "no"])
        if med_ok and pname not in floor_med: floor_med[pname] = n
        if p10_ok and pname not in floor_p10: floor_p10[pname] = n
table(["pool type", "docs per subset (n)", "pools", "pairs drawn", "same-pool agreement: median (centered cosine)", "same-pool: 10th pct", "unrelated: median", "unrelated: 95th pct", "median beats unrelated 95th pct?", "10th pct beats it?"], rows, "lrrrrrrrll")
chosen = max(floor_med.values()) if len(floor_med) == len(POOLS) else None
w(f"**Reading.** Criterion 1 — the *median* same-pool pair agrees more than the 95th percentile of unrelated pairs — is first met at n = "
  + "; ".join(f"{v} ({k.split(' (')[0]})" for k, v in floor_med.items()) + ". "
  + ("Criterion 2 — even the weak 10th-percentile pair beats that bar — is first met at n = " + "; ".join(f"{v} ({k.split(' (')[0]})" for k, v in floor_p10.items()) + "." if floor_p10 else "Criterion 2 (even the 10th-percentile pair beats the bar) is not met by n = 30 for the matcher-defined pools, whose membership is broad and individually incoherent — which is itself a finding about the prior-art topics, not about the minimum.")
  + f" The prompt-derived minimum of {MIN_DOCS} documents is therefore {'supported' if chosen is not None and MIN_DOCS >= chosen else 'NOT supported'} on criterion 1 (conservative reading: the larger of the two pool types, n = {chosen}); "
  "below 10, groups drawn from broad pools have no stable direction of their own (curated groups already do at 5, so 10 is the smallest size that holds for both). For the stricter tail criterion 20–30 documents are needed, so **a candidate with 10–19 documents is viable but marginal** and is marked so below. The 3-chunk minimum is a floor on the centroid's raw material (a centroid from fewer than 3 chunks is one passage) and is never binding once 10 documents are present.")
w()

# ---------------------------------------------------------------- viability
w("## Viability")
w()
rows = []
for c in cands:
    rows.append([c["id"], c["line"], c["n_docs"], c["chunks"], " / ".join(str(c["fmt"].get(f, 0)) for f in FM), ("**keep** (marginal: 10–19 docs)" if c["n_docs"] < 20 else "**keep**") if c["viable"] else f"drop (< {MIN_DOCS} docs)" if c["n_docs"] < MIN_DOCS else f"drop (< {MIN_CHUNKS} chunks)"])
table(["candidate", "source", "docs", "chunks", "docs by format (col / book / spe / bio)", "viability"], rows, "llrrrl")
viable = [c for c in cands if c["viable"]]
w(f"**{len(viable)} of {len(cands)} candidates meet the minima; {len(cands) - len(viable)} are dropped.** "
  f"Dropped by source: " + "; ".join(f"{s} {sum(1 for c in cands if c['line'] == s and not c['viable'])}" for s in sorted({c['line'] for c in cands})) + ".")
w()

# ---------------------------------------------------------------- separation
w("## Separation")
w()
w(f"Two scales, because they answer different questions. **Raw cosine** is the project's own scale and the one `TOPIC_MERGE_COSINE` = {MERGE} is defined on; step 5 showed that unrelated random document groups already reach 0.955–0.995 on it, "
  "so a raw score above the threshold is *not* evidence of a rephrase. **Centered cosine** (corpus mean removed) is the scale on which unrelated groups sit near 0 (95th percentile ≈ 0.3, maximum 0.45 across 60 draws), so it is the scale on which a duplicate is visible. "
  "**Document overlap** (Jaccard of the two member sets) is an independent third check that does not depend on the embedding at all.")
w()
nullc = cov["null"]
w("A candidate is called a **rephrase** here only when *both* hold: centered cosine ≥ 0.80 (well above every unrelated-group draw) and document overlap Jaccard ≥ 0.30. "
  "Anything above `TOPIC_MERGE_COSINE` on raw cosine is reported separately, as the prompt requires, but see the note above on what that flag means in this space.")
w()
CAND_C = np.stack([c["ctr"] for c in cands]); CAND_R = np.stack([c["raw"] for c in cands])
cc_pa = CAND_C @ PA_C.T; cr_pa = CAND_R @ PA_R.T
cc_cc = CAND_C @ CAND_C.T; cr_cc = CAND_R @ CAND_R.T
def jac(a, b):
    a, b = set(a), set(b); return len(a & b) / len(a | b)
rows_v, res = [], []
for i, c in enumerate(cands):
    if not c["viable"]: continue
    j = int(cc_pa[i].argmax()); k = int(cr_pa[i].argmax())
    nraw_pa = int((cr_pa[i] > MERGE).sum())
    ov = jac(c["docs"], members[pa_ids[j]])
    # nearest OTHER viable candidate on the centered scale
    others = [(cc_cc[i, m], m) for m, o in enumerate(cands) if m != i and o["viable"]]
    bo = max(others) if others else (float("nan"), None)
    ovc = jac(c["docs"], cands[bo[1]]["docs"]) if bo[1] is not None else float("nan")
    reph_pa = cc_pa[i, j] >= 0.80 and ov >= 0.30
    same_pa = cc_pa[i, j] >= 0.80 and ov < 0.30            # same direction, different documents
    reph_c = bo[1] is not None and bo[0] >= 0.80 and ovc >= 0.30
    same_c = bo[1] is not None and bo[0] >= 0.80 and ovc < 0.30
    res.append({"id": c["id"], "nearest_pa_centered": pa_ids[j], "cc": float(cc_pa[i, j]), "overlap": ov, "nearest_pa_raw": pa_ids[k], "cr": float(cr_pa[i, k]), "n_raw_gt_merge": nraw_pa,
                "nearest_cand": (cands[bo[1]]["id"] if bo[1] is not None else None), "cc_cand": float(bo[0]), "overlap_cand": ovc, "rephrase_pa": bool(reph_pa), "same_dir_pa": bool(same_pa), "rephrase_cand": bool(reph_c), "same_dir_cand": bool(same_c)})
    rows_v.append([c["id"], c["n_docs"], f"{pa_ids[j]} ({cc_pa[i, j]:.2f} / J {ov:.2f})", f"{pa_ids[k]} ({cr_pa[i, k]:.3f})", nraw_pa,
                   ("**rephrase of " + pa_ids[j] + "**") if reph_pa else (f"**same direction as {pa_ids[j]}, different documents**" if same_pa else "distinct"),
                   (f"{cands[bo[1]]['id'][:40]} ({bo[0]:.2f} / J {ovc:.2f})" if bo[1] is not None else "—"),
                   "**rephrase**" if reph_c else ("**same direction, different documents**" if same_c else "distinct")])
w("### Viable candidates against the 33 prior-art centroids and against each other")
w()
table(["candidate", "docs", "nearest prior-art topic, centered (cosine / doc-overlap J)", "nearest prior-art topic, raw (cosine)", "prior-art topics above raw " + str(MERGE),
       "relation to the nearest prior-art topic", "nearest other candidate, centered (cosine / J)", "relation to it"], rows_v, "lllrllll")
n_pa_reph = sum(1 for r in res if r["rephrase_pa"]); n_c_reph = sum(1 for r in res if r["rephrase_cand"])
n_pa_same = sum(1 for r in res if r["same_dir_pa"]); n_c_same = sum(1 for r in res if r["same_dir_cand"])
n_raw = sum(1 for r in res if r["n_raw_gt_merge"] > 0)
w(f"**Summary.** Of {len(res)} viable candidates: **{n_pa_reph}** are rephrases of a prior-art topic (centered ≥ 0.80 *and* document overlap ≥ 0.30); **{n_pa_same}** point in the *same direction* as a prior-art topic but with different documents "
  f"(centered ≥ 0.80, overlap < 0.30: " + (", ".join(f"{r['id']} → {r['nearest_pa_centered']} ({r['cc']:.2f}, J {r['overlap']:.2f})" for r in res if r["same_dir_pa"]) or "none") + "). "
  "That second category matters: the prior-art *topic* may be right while its *matcher* misses the documents, which is a coverage failure, not a duplicate. "
  f"Among the candidates themselves, {n_c_reph} are rephrases of another candidate and {n_c_same} have a same-direction, different-document neighbour. "
  f"**{n_raw}** exceed raw {MERGE} against at least one prior-art centroid (the prompt's literal test) — median number of prior-art topics above raw {MERGE} per candidate: {int(np.median([r['n_raw_gt_merge'] for r in res]))} of {len(pa_ids)}, which is why the raw test cannot be used to decide.")
w()
# distribution of candidate->prior art centered cosines
allcc = np.array([r["cc"] for r in res])
w(f"Nearest-prior-art centered cosine over the viable candidates: min {allcc.min():.2f}, median {np.median(allcc):.2f}, max {allcc.max():.2f}. Candidates with nearest centered cosine below 0.5 have no close prior-art neighbour: "
  + (", ".join(r["id"] for r in res if r["cc"] < 0.5) or "none") + ".")
w()
# candidate-candidate pairs above thresholds (viable only)
vi = [i for i, c in enumerate(cands) if c["viable"]]
pairs = sorted(((float(cc_cc[a, b]), cands[a]["id"], cands[b]["id"], jac(cands[a]["docs"], cands[b]["docs"])) for x, a in enumerate(vi) for b in vi[x + 1:]), reverse=True)
w("### Closest candidate pairs (centered scale)")
w()
table(["centered cosine", "doc-overlap J", "candidate A", "candidate B"], [[f"{c:.3f}", f"{j:.2f}", a, b] for c, a, b, j in pairs[:12]], "rrll")

# ---------------------------------------------------------------- prior art vs prior art on the centered scale (for the 'what survives' question)
pp = PA_C @ PA_C.T
ppairs = sorted(((float(pp[i, j]), pa_ids[i], pa_ids[j], jac(members[pa_ids[i]], members[pa_ids[j]])) for i in range(len(pa_ids)) for j in range(i + 1, len(pa_ids))), reverse=True)
w("### For reference: the prior-art topics against each other on the same scales")
w()
table(["centered cosine", "doc-overlap J", "topic A", "topic B"], [[f"{c:.3f}", f"{j:.2f}", a, b] for c, a, b, j in ppairs[:12]], "rrll")
both = [p for p in ppairs if p[0] >= 0.80 and p[3] >= 0.30]
w(f"On the centered scale {sum(1 for p in ppairs if p[0] >= 0.80)} prior-art pairs reach 0.80, and {len(both)} of those also overlap ≥ 0.30 in documents — the prior-art rephrases by the same two-part test: "
  + "; ".join(f"{a} ~ {b} ({c:.2f}, J {j:.2f})" for c, a, b, j in both) + ".")
w()

# ---------------------------------------------------------------- step 10: the degenerate topics
w("## Step 10 — the three degenerate prior-art topics")
w()
w("Evidence at 1,290 documents (matcher membership, production centroid recipe), against the 79-document counts the topic map was generated from. "
  "Three separate questions, because passing one does not answer the others: (1) do the members share a *direction*? (2) does that direction have anything to do with the topic's *label*? (3) *why* did the matcher select them?")
w()
def coherence(docs):
    dv = unit(np.stack([C.mat[C.rows_of[d]].mean(axis=0) for d in docs]) - mu); cen = unit(dv.mean(axis=0)); return float((dv @ cen).mean())
def coh_null(n):
    vals = []
    for _ in range(80):
        ds = [C.doc_ids[i] for i in rng.choice(N, size=n, replace=False)]; vals.append(coherence(ds))
    return float(np.mean(vals)), float(np.percentile(vals, 95))
m_ = P["module"]
def term_profile(t, ds):
    """which matcher terms fire on the member documents (word-boundary, same engine)"""
    terms = list(tax[t]["matchers"]["keywords"]) + list(tax[t]["matchers"].get("entities", []))
    cnt = Counter(); single = 0
    for d in ds:
        hs = m_._doc_haystack(C.docs[d]); hit = [x for x in terms if m_._kw_pattern(x).search(hs)]
        cnt.update(hit); single += (len(hit) == 1)
    return cnt, single
LABEL_WORDS = {"robot_identity_meta": ("robot", "artificial intelligence", "chatbot", "real cjp"),
               "honors_received": ("honor", "honour", "award", "medal", "recogni", "doctor of", "laureate", "tribute", "hall of fame", "conferred"),
               "death_penalty_and_echegaray": ("death penalty", "echegaray", "capital punishment", "lethal injection", "death row", "life and death", "execution")}
deg = ["robot_identity_meta", "honors_received", "death_penalty_and_echegaray"]
rows, degd = [], {}
for t in deg:
    ds = members[t] if members.get(t) else [d for d in C.doc_ids if S[d][t] > 0]
    n = len(ds); v1 = P["v1_doc_count"].get(t)
    if n < 3:
        rows.append([t, v1, n, 0, "0 / 0 / 0 / 0", "-", "-", "-", "-"]); degd[t] = {"n": n, "chunks": 0}; continue
    coh = coherence(ds); nm, n95 = coh_null(n)
    r_, c_, nch = cents(ds); sims = (c_ @ PA_C.T); order = np.argsort(-sims)
    nn = [(pa_ids[i], float(sims[i])) for i in order if pa_ids[i] != t][:3]
    byf = Counter(fmt_of(d) for d in ds); works = Counter(C.work[d] for d in ds if d[0] == "B")
    dvv = unit(np.stack([C.mat[C.rows_of[d]].mean(axis=0) for d in ds]) - mu)
    ex = [ds[i] for i in np.argsort(-(dvv @ c_))[:5]]
    prof, single = term_profile(t, ds)
    lw = LABEL_WORDS[t]
    on_label = [d for d in ds if any(x in (C.title[d] + " " + " ".join(C.docs[d].get("keywords") or [])).lower() for x in lw)]
    degd[t] = {"n": n, "chunks": nch, "coh": coh, "null_mean": nm, "null_p95": n95, "nn": nn, "byf": dict(byf), "works": dict(works), "ex": ex, "prof": prof.most_common(6), "single": single,
               "on_label": len(on_label), "coh_ok": bool(coh > n95)}
    rows.append([t, v1, n, nch, " / ".join(str(byf.get(f, 0)) for f in FM), f"{coh:.3f} vs {nm:.3f} (p95 {n95:.3f})", f"{100*single/n:.0f}%", f"{len(on_label)} of {n} ({100*len(on_label)/n:.0f}%)",
                 "; ".join(f"{a} {b:.2f}" for a, b in nn)])
table(["topic", "docs @79", "docs @1,290", "chunks", "docs by format (col / book / spe / bio)", "(1) coherence: members vs same-size random groups", "(3) members selected by ONE matcher term", "(2) members whose title or keywords mention the topic's subject", "nearest prior-art topics, centered"], rows, "lrrrrrrrl")
w("*Coherence* asks whether the members share a direction beyond chance. It does **not** say the direction is the topic: a set of documents can be coherent because they are all about the judiciary while the matcher picked them for an unrelated word. Column (2) counts members whose own title or curated keywords mention the topic's subject; column (3) is the share of members the matcher selected on a single term.")
w()
for t in deg:
    d = degd[t]
    w(f"### `{t}`")
    w()
    if d["n"] < 3:
        rob = [dd for dd in C.doc_ids if any(x in (C.title[dd] + " " + " ".join(C.docs[dd].get("keywords") or [])).lower() for x in LABEL_WORDS[t])]
        kwr = [(k, len(v)) for k, v in vocab["keywords_all_ge5"].items() if "robot" in k or "artificial intelligence" in k]
        w("* **0 member documents and 0 chunks at 1,290 scale** (also 0 at 79). Its centroid is the global mean vector, the same fallback used for any memberless topic, so a routing cosine against it measures how ordinary a query is, not how close it is to a subject.")
        w(f"* Tier `{tax[t]['tier']}`: {tax[t]['definition'][:210]}")
        w(f"* Corpus evidence that looks *related*: {len(rob)} document(s) mention robots or AI in the title or keywords" + (": " + "; ".join(f"`{x}` {C.title[x][:50]}" for x in rob[:6]) if rob else "") + ". Curated-keyword values (>= 5 docs) containing 'robot' or 'artificial intelligence': " + ("; ".join(f"'{k}' x{n}" for k, n in kwr) or "none") + ". "
          "Read their titles: they are columns about robotics and AI as a subject, not the persona speaking about its own identity, which is what this topic's definition covers. That is a routing intent, not a corpus dimension.")
        w()
        continue
    w(f"* **(1) Direction.** {d['n']} member documents, {d['chunks']} chunks; formats (col / book / spe / bio) {' / '.join(str(d['byf'].get(f, 0)) for f in FM)}" + (f"; books by work: " + "; ".join(f"{a} x{b}" for a, b in Counter(d['works']).most_common(5)) if d["works"] else "") + f". Coherence {d['coh']:.3f} vs {d['null_mean']:.3f} for random groups of {d['n']} (95th percentile {d['null_p95']:.3f}): " + ("**more coherent than chance**." if d["coh_ok"] else "**not distinguishable from random documents**."))
    w(f"* **(2) Label.** {d['on_label']} of {d['n']} members ({100*d['on_label']/d['n']:.0f}%) mention the topic's subject in their own title or keywords. Nearest prior-art topics (centered): " + "; ".join(f"{a} {b:.2f}" for a, b in d["nn"]) + ".")
    w(f"* **(3) Why the matcher selected them.** Matcher terms that fire (documents): " + "; ".join(f"'{a}' x{b}" for a, b in d["prof"]) + f". {d['single']} of {d['n']} members ({100*d['single']/d['n']:.0f}%) were selected on a single term.")
    w("* Exemplars (nearest the members' centre): " + "; ".join(f"`{x}` {C.title[x][:60]}" for x in d["ex"]))
    if d["coh_ok"] and d["on_label"] / d["n"] >= 0.5:
        w("* **Read:** the members share a direction *and* most mention the subject: a real, if narrow, dimension of the corpus.")
    elif d["coh_ok"]:
        w("* **Read:** the members share a direction, but **that direction is not the topic's label**: fewer than half mention it. The matcher is selecting documents for incidental terms, and the coherence found is that of some other theme they have in common. Real content at this scale is *not* established for this label.")
    else:
        w("* **Read:** no shared direction beyond chance: a keyword accident.")
    w()
honors = degd["honors_received"]; robot = degd["robot_identity_meta"]; dp = degd["death_penalty_and_echegaray"]
w("### The byte-identical pair: `honors_received` and `robot_identity_meta`")
w()
w("At 79 documents both had no usable members, so both centroids fell back to the same global mean vector and were byte-identical: every query was *equally close* to both, and both leaked into secondary tags as if they were topics. What the measurements at 1,290 support:")
w()
w(f"* **`robot_identity_meta`**: still {robot['n']} documents and 0 chunks. Nothing in the corpus supports it as a corpus dimension. Its centroid is the global mean.")
w(f"* **`honors_received`**: now {honors['n']} documents and {honors['chunks']} chunks, so the byte-identical fallback no longer applies to it. But only {honors['on_label']} of its {honors['n']} members mention honors in their title or keywords, and the matcher terms that select them are: "
  + "; ".join(f"'{a}' x{b}" for a, b in honors['prof'][:4]) + ". The topic is no longer degenerate in the numeric sense, and its semantic content is " + ("established." if honors["coh_ok"] and honors["on_label"] / honors["n"] >= 0.5 else "**not established**."))
w("* **What the evidence supports:** (a) the two must never again share a centroid, and a memberless topic must not receive a fallback vector that competes in routing; (b) `robot_identity_meta` has no corpus content and belongs in the router's intent layer, outside the centroid set; "
  "(c) `honors_received` was not independently re-found by any of the three derivation lines (no orphan cluster, no curated keyword clears the threshold), so it should enter v2 only if a purpose-built matcher shows genuine honors content. Whether either survives is Phase 4's call.")
w(f"* **`death_penalty_and_echegaray`**: now {dp['n']} documents / {dp['chunks']} chunks (1 document at 79), and {dp['on_label']} of {dp['n']} members ({100*dp['on_label']/dp['n']:.0f}%) mention its subject. It is " + ("real and narrow" if dp["coh_ok"] and dp["on_label"] / dp["n"] >= 0.5 else "not established as a topic") + f", and **book-dominated** ({dp['byf'].get('books', 0)} of {dp['n']} members are book chapters); "
  "the curated keywords 'death penalty', 'leo echegaray' and 'people v. echegaray' each appear in only 5 documents, below the 15-document threshold, so the vocabulary line alone would not have surfaced it.")
w()
w("## Sensitivity: candidates below the prompt's 15-document threshold")
w()
w(f"{len(extra10)} further uncaught curated keywords reach 10–14 documents: " + ", ".join(f"“{c['value']}” ({len(c['docs'])})" for c in sorted(extra10, key=lambda c: -len(c['docs']))[:26]) + ". Not used as candidates; listed so the threshold's effect is visible.")
w()
Path(B4 / "ce7_candidate_separation_2026-09-26.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
json.dump({"results": res, "viable": [c["id"] for c in viable], "dropped": [c["id"] for c in cands if not c["viable"]], "min_n_chosen": chosen, "degenerate": degd}, open(CACHE / "separation.json", "w"), indent=1, default=lambda o: float(o))
print("wrote separation report;", len(L), "lines | viable", len(viable), "of", len(cands), "| rephrase of prior art:", n_pa_reph, "| of candidate:", n_c_reph, "| min n:", chosen)
