"""CE-7 steps 4-5: diagnosis against prior art (matchers), provisional centroids, separation, orphan-rate curves.
Writes batch-04/ce7_coverage_2026-09-26.md and cache/ce7_cov.json. Read-only on the repo."""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *

rng = np.random.default_rng(20260926)
C = Corpus(); P = prior_art(); S = score_all_docs(C)
N = len(C.doc_ids)
tax_ids = P["order"]; cen_ids = P["centroid_ids"]
FM = FMT_ORDER
tot_docs = C.fmt_docs; tot_chunks = C.fmt_chunks

out = {}
L = []                                    # markdown lines
def w(s=""): L.append(s)
def table(headers, rows, align=None):
    w("| " + " | ".join(headers) + " |")
    w("|" + "|".join(("---:" if (align and align[i] == "r") else "---") for i in range(len(headers))) + "|")
    for r in rows: w("| " + " | ".join(str(x) for x in r) + " |")
    w()

# ------------------------------------------------------------------ step 4
member = {t: [d for d in C.doc_ids if S[d][t] > 0] for t in tax_ids}
maxscore = {d: max(S[d].values()) for d in C.doc_ids}
zero = [d for d in C.doc_ids if maxscore[d] == 0]
out["zero_docs"] = zero
out["maxscore_dist"] = {f: dict(Counter(min(maxscore[d], 3) for d in C.doc_ids if fmt_of(d) == f)) for f in FM}

w("# CE-7 · steps 4–5 — coverage against the prior-art taxonomy")
w()
w("**Date** 2026-09-26 · **Scope:** the 35 prior-art topics (34 centroids; `msme_and_entrepreneurship` and `prosperity_fund_msme` share one merged centroid) "
  "measured over the 1,290-document corpus. Prior art is *diagnosed*, not adopted: it was generated from 79 documents (64 columns, 15 speeches) and has never seen a book or a biography chapter.")
w()
w("Definitions are the project's own: matcher = `build_topic_map._doc_haystack` + `score_topic`, membership = score > 0; centroid = unit-normalised mean of **all chunks** of the member documents "
  "(`build_centroids_fullcorpus.py`); document affinity = **best-chunk cosine** (max over the document's chunks, `merge_tag_topics.py`). "
  f"Knobs from `config.py`: `TOPIC_ASSIGN_MIN_COSINE`={FLOOR}, `TOPIC_MERGE_COSINE`={MERGE}.")
w()
w("## Sampling hazard (applies to everything below)")
w()
table(["format", "docs", "doc %", "chunks", "chunk %", "skew (chunk% / doc%)"],
      [[f, tot_docs[f], pct(tot_docs[f], N), tot_chunks[f], pct(tot_chunks[f], 13549),
        f"{(tot_chunks[f] / 13549) / (tot_docs[f] / N):.2f}×"] for f in FM], "lrrrrr")

w("## Step 4 — the v1 matchers over 1,290 documents")
w()
w("### 4a. Per-topic document count at 1,290, beside the count at 79")
w()
rows = []
for t in tax_ids:
    m = member[t]; byf = Counter(fmt_of(d) for d in m)
    v1 = P["v1_doc_count"].get(t)
    rows.append([t, P["taxonomy"][t]["tier"], v1, len(m), pct(len(m), N),
                 " / ".join(f"{byf[f]}" for f in FM),
                 " / ".join(pct(byf[f], tot_docs[f]).replace("%", "") for f in FM)])
rows.sort(key=lambda r: -r[3])
table(["topic", "tier", "docs @79 (v1)", "docs @1,290", "% of corpus", "docs by format (col / book / spe / bio)", "% of each format's own docs"], rows, "llrrrrr")
out["topic_doc_counts"] = {r[0]: {"v1": r[2], "now": r[3]} for r in rows}
over = [r[0] for r in rows if r[3] > config.TOPIC_OVER_BROAD_FRAC * N]
w(f"Topics claiming more than {int(100*config.TOPIC_OVER_BROAD_FRAC)}% of the corpus (`TOPIC_OVER_BROAD_FRAC`): **{len(over)}** — {', '.join(over) or 'none'}.")
w()
w("### 4b. Documents that score zero against every topic")
w()
zb = Counter(fmt_of(d) for d in zero)
table(["format", "docs", "score zero", "% of format's docs"], [[f, tot_docs[f], zb[f], pct(zb[f], tot_docs[f])] for f in FM] + [["**all**", N, len(zero), pct(len(zero), N)]], "lrrr")
w(f"**Restricted to the two formats these matchers have never seen:** book chapters {zb['books']} of {tot_docs['books']} ({pct(zb['books'], tot_docs['books'])}); "
  f"biography chapters {zb['biography']} of {tot_docs['biography']} ({pct(zb['biography'], tot_docs['biography'])}); together {zb['books'] + zb['biography']} of {tot_docs['books'] + tot_docs['biography']} "
  f"({pct(zb['books'] + zb['biography'], tot_docs['books'] + tot_docs['biography'])}).")
w()
w("**How weak is the zero test?** Distribution of each document's *best* matcher score (a single incidental keyword hit is enough to be “covered”):")
w()
table(["best matcher score", *FM], [[lab, *[pct(sum(1 for d in C.doc_ids if fmt_of(d) == f and (maxscore[d] == k if k < 3 else maxscore[d] >= 3)), tot_docs[f]) for f in FM]]
                                   for lab, k in (("0 (orphan by this test)", 0), ("1 (one keyword hit)", 1), ("2", 2), ("3 or more", 3))], "lrrrr")
_cf_path = CACHE / "haystack_cf.json"
n_terms = sum(len(t["matchers"]["keywords"]) + len(t["matchers"].get("entities", [])) for t in P["taxonomy"].values())
if _cf_path.exists():
    cf = json.load(open(_cf_path))
    w("**Is the enrichment prose the reason?** A natural guess is that the haystack's long prose fields (`one_paragraph_summary`, `primary_topics`, `sub_topics`) hand every document an incidental hit. "
      "Tested directly by re-scoring every document with those fields removed (`ce7_00_haystack_counterfactual.py`):")
    w()
    table(["haystack", "documents scoring zero", "of which (col / book / spe / bio)", "documents with best score ≤ 1"],
          [[c["variant"], f"{c['zero']} ({pct(c['zero'], N)})", " / ".join(str(c["zero_by_format"].get(f, 0)) for f in FM), c["le1"]] for c in cf], "lrrr")
    full, stripped = cf[0]["zero"], cf[-1]["zero"]
    w(f"**The guess is wrong.** Removing all three prose fields moves the zero-score count only from {full} to {stripped} ({pct(stripped, N)} of the corpus). The prose is not why so few documents score zero. "
      f"The matchers are simply broad: one hit on any of {n_terms} matcher terms (word-boundary, anywhere in title, keywords, entities, register markers or prose) is enough to count a document as covered.")
else:
    w("(Haystack counterfactual not available: run `ce7_00_haystack_counterfactual.py` first.)")
w()
w("**The zero test is therefore an insensitive orphan detector.** The embedding-based curves in step 5 are the better read of coverage, and Line 1 clusters both the strict zero set and two broader populations.")
w()
out["fmt_zero"] = dict(zb)

# ------------------------------------------------------------------ step 5
mu = C.mat.mean(axis=0)
cen_raw, cen_dw, cen_ctr, info = [], [], [], []
for tid in cen_ids:
    docs = set()
    for sub in tid.split("+"):
        docs |= set(member.get(sub, []))
    docs = sorted(docs)
    rows_ = [r for d in docs for r in C.rows_of[d]]
    if rows_:
        m = C.mat[rows_].mean(axis=0)
        cen_raw.append(unit(m)); cen_ctr.append(unit(m - mu))
        cen_dw.append(centroid_from_docs(C, docs, "doc")[0])
    else:
        cen_raw.append(C.gmean); cen_ctr.append(np.zeros(768, dtype=np.float32)); cen_dw.append(C.gmean)
    info.append({"id": tid, "docs": len(docs), "chunks": len(rows_), "fallback": not rows_, "doc_ids": docs})
cen_raw = np.stack(cen_raw).astype(np.float32); cen_dw = np.stack(cen_dw).astype(np.float32); cen_ctr = np.stack(cen_ctr).astype(np.float32)
np.save(CACHE / "prior_centroids_prov.npy", cen_raw)
out["prior_info"] = [{k: v for k, v in i.items() if k != "doc_ids"} for i in info]
json.dump({i["id"]: i["doc_ids"] for i in info}, open(CACHE / "prior_members.json", "w"))

w("## Step 5 — provisional centroids for the 34 prior-art topics, over the new corpus")
w()
w("Recipe = production recipe (unit-normalised mean of every chunk of every member document). Zero-member topics fall back to the global mean vector and are flagged.")
w()
thin = [i for i in info if i["docs"] < 10 or i["chunks"] < 3]
rows = [[i["id"], i["docs"], i["chunks"], "**gmean fallback**" if i["fallback"] else "", "**< 10 docs**" if i["docs"] < 10 else "", "**< 3 chunks**" if i["chunks"] < 3 else ""] for i in sorted(info, key=lambda i: i["docs"])]
table(["topic", "docs", "chunks", "fallback", "thin (docs)", "thin (chunks)"], rows, "lrrlll")
w(f"**Under 10 documents or under 3 chunks at 1,290 scale: {len(thin)} topic(s)** — {', '.join(i['id'] for i in thin) or 'none'}.")
w()
out["thin"] = [i["id"] for i in thin]

# --- v1 stored vs provisional
v1c = P["v1_centroids"]; drift = np.einsum("ij,ij->i", v1c, cen_raw)
w("### 5a. Provisional vs the stored v1 centroids (same topic, same recipe, corpus grown 1,104 → 1,290 docs)")
w()
w(f"cosine(stored v1 centroid, provisional centroid) per topic: min {drift.min():.4f}, median {np.median(drift):.4f}, max {drift.max():.4f}. "
  f"Lowest five: " + ", ".join(f"{cen_ids[i]} {drift[i]:.4f}" for i in np.argsort(drift)[:5]) + ".")
w()

# --- pairwise. NON-FALLBACK topics only: a gmean-fallback "centroid" is the corpus mean, not a topic.
non_fb = [i for i, x in enumerate(info) if not x["fallback"]]
fb_ids = [cen_ids[i] for i, x in enumerate(info) if x["fallback"]]
nf_ids = [cen_ids[i] for i in non_fb]
S_raw = cen_raw @ cen_raw.T
S_ctr = cen_ctr @ cen_ctr.T
ii, jj = np.triu_indices(len(non_fb), 1)
raw_p = np.array([S_raw[non_fb[a], non_fb[b]] for a, b in zip(ii, jj)])
ctr_p = np.array([S_ctr[non_fb[a], non_fb[b]] for a, b in zip(ii, jj)])
pairs = sorted(((float(S_raw[non_fb[a], non_fb[b]]), nf_ids[a], nf_ids[b]) for a, b in zip(ii, jj)), reverse=True)
cpairs = sorted(((float(S_ctr[non_fb[a], non_fb[b]]), nf_ids[a], nf_ids[b], float(S_raw[non_fb[a], non_fb[b]])) for a, b in zip(ii, jj)), reverse=True)
above = [p for p in pairs if p[0] > MERGE]
cabove = [p for p in cpairs if p[0] > MERGE]
v1c_nf = v1c[non_fb]; v1_pairs = (v1c_nf @ v1c_nf.T)[np.triu_indices(len(non_fb), 1)]
w("### 5b. Pairwise cosine between the provisional centroids")
w()
for f in fb_ids:
    i = cen_ids.index(f); rng_ = S_raw[i, non_fb]
    w(f"*Excluded from the pair statistics:* **{f}** has no member documents, so its “centroid” is the global mean vector. Its cosine to the other topics ({rng_.min():.3f}–{rng_.max():.3f}) only measures how far each topic lies from the corpus mean.")
    w()
w(f"Raw cosine over the {len(pairs)} pairs of the {len(non_fb)} non-fallback topics: mean **{raw_p.mean():.4f}**, median {np.median(raw_p):.4f}, min {raw_p.min():.4f}, max {raw_p.max():.4f} "
  f"(the stored v1 centroids over the same topics: mean {v1_pairs.mean():.4f}; the v1 meta records 0.9334 for its 34).")
w()
w(f"**Pairs above `TOPIC_MERGE_COSINE` = {MERGE} (raw): {len(above)} of {len(pairs)}.**")
w()
table(["cosine (raw)", "topic A", "topic B"], [[f"{c:.4f}", a, b] for c, a, b in above[:15]], "rll")
w(f"(the 15 highest of {len(above)} shown; the full list is in `ce7_analysis/cache/ce7_cov.json`.)")
w()
parent = list(range(len(nf_ids)))
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for c, a, b in above: parent[find(nf_ids.index(a))] = find(nf_ids.index(b))
groups = len({find(i) for i in range(len(nf_ids))})
w(f"Applying the project's union-find merge at {MERGE} on raw cosine would collapse the {len(nf_ids)} non-fallback provisional centroids to **{groups}** topic(s). (In Phase 5 the independence check is an explicit stop criterion if it does this.)")
w()
# null distribution: what does a raw cosine of 0.95 mean here?
def random_group_centroid(n_docs):
    """returns (raw centroid, centered centroid) computed exactly as for the topics: unit(mean), unit(mean - corpus mean)."""
    idx = rng.choice(N, size=n_docs, replace=False)
    rows_ = [r for i in idx for r in C.rows_of[C.doc_ids[i]]]
    m = C.mat[rows_].mean(axis=0)
    return unit(m), unit(m - mu)
null = {}
for n in (10, 30, 100):
    ga = [random_group_centroid(n) for _ in range(60)]; gb = [random_group_centroid(n) for _ in range(60)]
    a = np.stack([x[0] for x in ga]); b = np.stack([x[0] for x in gb]); ca = np.stack([x[1] for x in ga]); cb = np.stack([x[1] for x in gb])
    cs = np.einsum("ij,ij->i", a, b); cg = a @ C.gmean; ccs = np.einsum("ij,ij->i", ca, cb)
    null[n] = {"pair_mean": float(cs.mean()), "pair_min": float(cs.min()), "pair_p95": float(np.percentile(cs, 95)), "vs_gmean_mean": float(cg.mean()),
               "centered_pair_mean": float(ccs.mean()), "centered_pair_p95": float(np.percentile(ccs, 95)), "centered_pair_max": float(ccs.max())}
w("**What does a raw cosine of 0.95 mean in this space?** Centroids are means over many chunks, so they all lean toward the corpus-wide mean direction. Baseline: cosine between the centroids of two *independent random* document groups (60 draws each), raw and centered:")
w()
table(["docs per random group", "raw: mean cosine of two random groups", "raw min", "raw 95th pct", "raw: mean cosine to the global mean", "centered: mean", "centered: 95th pct", "centered: max"],
      [[n, f"{v['pair_mean']:.4f}", f"{v['pair_min']:.4f}", f"{v['pair_p95']:.4f}", f"{v['vs_gmean_mean']:.4f}", f"{v['centered_pair_mean']:.3f}", f"{v['centered_pair_p95']:.3f}", f"{v['centered_pair_max']:.3f}"] for n, v in null.items()], "rrrrrrrr")
w(f"Two independent random 30-document groups sit at raw mean {null[30]['pair_mean']:.3f}; the prior-art topic pairs sit at raw mean {raw_p.mean():.3f}. A raw cosine above {MERGE} is therefore what *unrelated* document groups produce, and cannot mark a rephrase. "
  f"After the corpus mean is removed, unrelated groups fall to a centered mean of {null[30]['centered_pair_mean']:.3f} (95th percentile {null[30]['centered_pair_p95']:.3f}) — that is the scale on which a duplicate becomes visible.")
w()
w(f"**Centered cosine, prior-art pairs:** mean {ctr_p.mean():.4f}, median {np.median(ctr_p):.4f}, max {ctr_p.max():.4f}; pairs above {MERGE} centered: **{len(cabove)}**. Highest ten by centered cosine:")
w()
table(["centered cosine", "raw cosine", "topic A", "topic B"], [[f"{c:.4f}", f"{r:.4f}", a, b] for c, a, b, r in cpairs[:10]], "rrll")
w()
out["pairs_above_merge"] = [[round(c, 4), a, b] for c, a, b in above]
out["centered_top"] = [[round(c, 4), a, b, round(r, 4)] for c, a, b, r in cpairs[:25]]
out["pair_stats"] = {"n_nonfallback": len(nf_ids), "mean": float(raw_p.mean()), "median": float(np.median(raw_p)), "max": float(raw_p.max()), "n_pairs": len(pairs), "n_above": len(above), "collapse_groups": groups,
                     "centered_mean": float(ctr_p.mean()), "centered_max": float(ctr_p.max()), "centered_above": len(cabove), "fallback": fb_ids}
out["null"] = null

# --- weighting effect on centroids (skew)
wd = np.einsum("ij,ij->i", cen_raw, cen_dw)
w("### 5c. Effect of the chunk skew on the centroids themselves")
w()
w(f"The production recipe weights every *chunk* equally, so a topic with many book members is pulled toward book prose. Re-computing each centroid with every *document* weighted equally and comparing to the production one: "
  f"cosine min {wd[[i for i in non_fb]].min():.4f}, median {np.median(wd[non_fb]):.4f}. Topics most shifted by the weighting: "
  + ", ".join(f"{cen_ids[i]} ({wd[i]:.4f}, {info[i]['docs']} docs)" for i in sorted(non_fb, key=lambda i: wd[i])[:6]) + ".")
w()

# --- orphan-rate curves
sims = C.mat @ cen_raw.T                                            # [chunks, 34]
best_chunk = np.stack([sims[C.rows_of[d]].max(axis=0) for d in C.doc_ids])   # [docs,34]
nearest_A = best_chunk[:, [i for i in range(len(cen_ids))]].max(axis=1)      # project definition: best chunk
nearest_B = (C.doc_vec @ cen_raw.T).max(axis=1)                              # doc mean vector
chunk_nearest = sims.max(axis=1)
chunk_fmt = np.array([fmt_of(d) for d in C.chunk_doc])
floors = np.round(np.arange(0.55, 0.8001, 0.01), 2)
ext = np.round(np.arange(0.81, 0.9601, 0.01), 2)
def curve(values, mask_fmt, grid):
    v = values[mask_fmt]
    return [float((v < f).mean()) for f in grid]
curves = {}
for defname, vals, fm in (("A_best_chunk (project definition)", nearest_A, C.doc_fmt), ("B_doc_mean_vector (length-neutral)", nearest_B, C.doc_fmt), ("C_chunk_level", chunk_nearest, chunk_fmt)):
    curves[defname] = {"all": curve(vals, np.ones(len(vals), bool), floors)}
    for f in FM: curves[defname][f] = curve(vals, fm == f, floors)
    curves[defname]["ext_all"] = curve(vals, np.ones(len(vals), bool), ext)
    for f in FM: curves[defname]["ext_" + f] = curve(vals, fm == f, ext)
out["orphan_curves"] = {"floors": floors.tolist(), "ext_floors": ext.tolist(), "curves": curves}

w("### 5d. Orphan-rate curve — share of documents below the floor, 0.55 → 0.80 in 0.01 steps")
w()
w("Three definitions, because they disagree, and the disagreement is itself the skew hazard:")
w("* **A — best-chunk (the project's definition).** A document is an orphan when *no* chunk reaches the floor for *any* topic. A document with 18 chunks has 18 chances to clear it; one with 7 has 7.")
w("* **B — document mean vector.** Cosine of the document's mean chunk vector to each centroid. Length-neutral.")
w("* **C — chunk level.** Share of *chunks* below the floor (carries the 1.78× book skew in its denominator).")
w()
for defname in curves:
    w(f"**{defname}**"); w()
    hdr = ["floor", "all", *FM]
    rows = [[f"{fl:.2f}", *[f"{100*curves[defname][k][i]:.1f}%" for k in ["all", *FM]]] for i, fl in enumerate(floors)]
    table(hdr, rows, "rrrrrr")
w("**Supplementary sweep above 0.80** (the prescribed range ends at 0.80; shown so the whole shape of each curve is visible, every second step):")
w()
for defname in list(curves)[:2]:
    w(f"*{defname}*"); w()
    rows = [[f"{fl:.2f}", *[f"{100*curves[defname]['ext_' + k][i]:.1f}%" if k != "all" else f"{100*curves[defname]['ext_all'][i]:.1f}%" for k in ["all", *FM]]] for i, fl in enumerate(ext) if i % 2 == 0]
    table(["floor", "all", *FM], rows, "rrrrrr")

# --- where do the curves move? knees + weak-label separation
def knee(grid, y):
    y = np.asarray(y); x = np.asarray(grid)
    if y.max() - y.min() < 1e-9: return None
    xn = (x - x.min()) / (x.max() - x.min()); yn = (y - y.min()) / (y.max() - y.min())
    return float(x[np.argmax(xn - yn)])       # kneedle for an increasing convex curve: largest gap below the diagonal
full_grid = np.concatenate([floors, ext])
kn = {}
for defname in list(curves)[:2]:
    for k in ["all", *FM]:
        y = curves[defname][k] + curves[defname]["ext_" + k if k != "all" else "ext_all"]
        kn[f"{defname}|{k}"] = knee(full_grid, y)
zero_mask = np.array([d in set(zero) for d in C.doc_ids]); cov_mask = np.array([maxscore[d] >= 2 for d in C.doc_ids])
w("### 5e. Re-deriving the floor")
w()
w("Two independent readings. (1) **Where the curve leaves zero / its knee** (kneedle over the full 0.55–0.96 sweep). (2) **Agreement with the matchers as weak labels**: documents scoring zero on every matcher are treated as orphans and documents with best score ≥ 2 as covered; for each floor, Youden's J = TPR − FPR. "
  "The labels are noisy (the matchers are the weak instrument this rebuild is replacing), and per-format positives are tiny, so treat (2) as a cross-check on (1), not as ground truth.")
w()
rows = []
best_floor = {}
grid = np.round(np.arange(0.55, 0.9601, 0.005), 3)
for defname, vals in (("A best-chunk", nearest_A), ("B doc-mean", nearest_B)):
    for k in ["all", *FM]:
        msk = np.ones(N, bool) if k == "all" else (C.doc_fmt == k)
        pos = zero_mask & msk; neg = cov_mask & msk
        if pos.sum() < 3 or neg.sum() < 3:
            rows.append([defname, k, int(pos.sum()), int(neg.sum()), "too few", "-", "-", "-"]); continue
        J = [((vals[pos] < f).mean() - (vals[neg] < f).mean()) for f in grid]
        bi = int(np.argmax(J)); best_floor[f"{defname}|{k}"] = {"floor": float(grid[bi]), "J": float(J[bi]), "tpr": float((vals[pos] < grid[bi]).mean()), "fpr": float((vals[neg] < grid[bi]).mean())}
        rows.append([defname, k, int(pos.sum()), int(neg.sum()), f"{grid[bi]:.3f}", f"{J[bi]:.2f}", f"{100*(vals[pos] < grid[bi]).mean():.0f}%", f"{100*(vals[neg] < grid[bi]).mean():.0f}%"])
table(["definition", "scope", "weak-orphans (zero score)", "weak-covered (score ≥ 2)", "Youden-optimal floor", "J", "orphans caught", "covered wrongly orphaned"], rows, "llrrrrrr")
w("Knee of each curve (kneedle, full sweep):")
w()
table(["definition", "scope", "knee floor"], [[k.split("|")[0], k.split("|")[1], "flat" if v is None else f"{v:.2f}"] for k, v in kn.items()], "llr")
out["knees"] = kn; out["best_floor"] = best_floor
# where does the curve reach 1%, 5%, 25%, 50%
w("Floor at which each curve first exceeds a given orphan share:")
w()
def first_above(vals, msk, share):
    v = vals[msk]
    for f in full_grid:
        if (v < f).mean() > share: return float(f)
    return None
rows = []
for defname, vals in (("A best-chunk", nearest_A), ("B doc-mean", nearest_B)):
    for k in ["all", *FM]:
        msk = np.ones(N, bool) if k == "all" else (C.doc_fmt == k)
        rows.append([defname, k, *[("-" if (x := first_above(vals, msk, s)) is None else f"{x:.2f}") for s in (0.01, 0.05, 0.25, 0.50)]])
table(["definition", "scope", "> 1% orphaned", "> 5%", "> 25%", "> 50%"], rows, "llrrrr")
w("**Known-orphan validation** (the v1 meta's own check: GC006 and CA330 should fall below a working floor):")
w()
kv = []
for d in ("GC006", "CA330"):
    i = C.doc_index[d]
    kv.append([d, C.title[d][:60], f"{nearest_A[i]:.4f}", f"{nearest_B[i]:.4f}", cen_ids[int(best_chunk[i].argmax())], maxscore[d]])
table(["doc", "title", "nearest (A, best-chunk)", "nearest (B, doc-mean)", "nearest topic", "best matcher score"], kv, "llrrlr")
out["known_orphans"] = {r[0]: {"A": r[2], "B": r[3], "nearest_topic": r[4], "matcher_max": r[5]} for r in kv}
np.save(CACHE / "nearest_A.npy", nearest_A); np.save(CACHE / "nearest_B.npy", nearest_B)

# --- distribution facts that frame the floor
w("### 5f. Where documents actually sit")
w()
qs = (0.01, 0.05, 0.25, 0.5, 0.75, 0.95)
rows = []
for defname, vals in (("A best-chunk", nearest_A), ("B doc-mean", nearest_B)):
    for k in ["all", *FM]:
        v = vals if k == "all" else vals[C.doc_fmt == k]
        rows.append([defname, k, *[f"{np.quantile(v, q):.3f}" for q in qs]])
table(["definition", "scope", *[f"q{int(100*q):02d}" for q in qs]], rows, "llrrrrrr")
o68A = float((nearest_A < FLOOR).mean()); o68B = float((nearest_B < FLOOR).mean())
o68f = {f: (float((nearest_A[C.doc_fmt == f] < FLOOR).mean()), float((nearest_B[C.doc_fmt == f] < FLOOR).mean())) for f in FM}
w(f"Read against the {FLOOR} floor: it orphans **{100*o68A:.1f}%** of documents under definition A and **{100*o68B:.1f}%** under B "
  f"(per format A / B: " + "; ".join(f"{f} {100*o68f[f][0]:.1f}% / {100*o68f[f][1]:.1f}%" for f in FM) + "). "
  "The known-orphan table above shows where v1's own reference orphans sit relative to it.")
w()
out["orphan_at_floor"] = {"A": o68A, "B": o68B, "per_format": o68f}
# --- 5g. recommended floor
w("### 5g. Recommended floor — derived from the curves above (for the current provisional centroids)")
w()
w("Rule: take the **knee** of each orphan-rate curve (where the share of orphaned documents starts to climb steeply) as the floor, then cross-check it against the weak-label optimum. "
  "The floor is a property of the centroid set it was measured against, so this is the floor for *these 34 provisional centroids*; it must be re-derived against the v2 centroids in Phase 5.")
w()
rows = []
rec = {}
for k in ["all", *FM]:
    m_ = np.ones(N, bool) if k == "all" else (C.doc_fmt == k)
    kA = kn.get(f"A_best_chunk (project definition)|{k}"); kB = kn.get(f"B_doc_mean_vector (length-neutral)|{k}")
    yA = best_floor.get(f"A best-chunk|{k}"); yB = best_floor.get(f"B doc-mean|{k}")
    shA = float((nearest_A[m_] < kA).mean()) if kA else float("nan"); shB = float((nearest_B[m_] < kB).mean()) if kB else float("nan")
    rec[k] = {"knee_A": kA, "knee_B": kB, "youden_A": (yA or {}).get("floor"), "youden_B": (yB or {}).get("floor"), "share_at_kneeA": shA, "share_at_kneeB": shB}
    rows.append([k, f"{kA:.2f}" if kA else "-", f"{yA['floor']:.2f}" if yA else "n/a", f"{100*shA:.1f}%", f"{kB:.2f}" if kB else "-", f"{yB['floor']:.2f}" if yB else "n/a", f"{100*shB:.1f}%"])
table(["scope", "A best-chunk: knee", "A: weak-label optimum", "share orphaned at the A knee", "B doc-mean: knee", "B: weak-label optimum", "share orphaned at the B knee"], rows, "lrrrrrr")
kall = rec["all"]
w(f"**Recommendation.** The inherited floor of {FLOOR} orphans {100*o68A:.1f}% (A) and {100*o68B:.1f}% (B) of documents — it is inert and should not be carried forward. "
  f"On the project's own best-chunk definition (A) the curve turns at **{kall['knee_A']:.2f}** overall (columns {rec['columns']['knee_A']:.2f}, books {rec['books']['knee_A']:.2f}, speeches {rec['speeches']['knee_A']:.2f}, biography {rec['biography']['knee_A']:.2f}); "
  f"on the length-neutral document-mean definition (B) it turns at **{kall['knee_B']:.2f}** overall (columns {rec['columns']['knee_B']:.2f}, books {rec['books']['knee_B']:.2f}, speeches {rec['speeches']['knee_B']:.2f}, biography {rec['biography']['knee_B']:.2f}). "
  f"Books need a floor about {rec['books']['knee_A'] - rec['columns']['knee_A']:.2f} (A) / {rec['books']['knee_B'] - rec['columns']['knee_B']:.2f} (B) higher than columns to be orphaned at the same rate, so **a single global floor is format-biased**: it flags columns first. "
  "A per-format floor, or a floor expressed as a within-format percentile, removes that bias; the choice is Phase 4's. "
  + "Weak-label cross-check: " + "; ".join(
      f"{k} {'agrees' if abs(rec[k]['knee_B'] - rec[k]['youden_B']) <= 0.05 else 'disagrees'} on B (knee {rec[k]['knee_B']:.2f} vs optimum {rec[k]['youden_B']:.2f})"
      for k in ["all", *FM] if rec[k]["youden_B"] is not None and rec[k]["knee_B"] is not None)
  + ("; too few weak-label positives to test: " + ", ".join(k for k in FM if rec[k]["youden_B"] is None) if any(rec[k]["youden_B"] is None for k in FM) else "")
  + ". The optimum runs higher than the knee wherever it can be computed, so it corroborates the direction, not the exact value.")
w()
out["recommended_floor"] = rec

Path(B4 / "ce7_coverage_2026-09-26.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
json.dump(out, open(CACHE / "ce7_cov.json", "w"), indent=1, default=float)
print("wrote ce7_coverage_2026-09-26.md;", len(L), "lines")
print("zero docs:", len(zero), dict(zb), "| pairs>0.95:", len(above), "->", groups, "groups | floor q01 A:", round(float(np.quantile(nearest_A, .01)), 3), "B:", round(float(np.quantile(nearest_B, .01)), 3))
