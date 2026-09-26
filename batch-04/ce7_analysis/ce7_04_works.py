"""CE-7 step 8 (Line 3): per-work coverage. Writes batch-04/ce7_per_work_coverage_2026-09-26.md. Read-only on the repo.
Needs cache/prior_members.json (step 4-5), cache/vocab_candidates.json (step 7), cache/orphan_clusters.json (step 6)."""
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
N = len(C.doc_ids); FM = FMT_ORDER
mu = C.mat.mean(axis=0)
members = json.load(open(CACHE / "prior_members.json"))
cen_ids = [t for t in P["centroid_ids"] if members[t]]                       # non-fallback prior-art topics
cen_c = np.stack([unit(C.mat[[r for d in members[t] for r in C.rows_of[d]]].mean(axis=0) - mu) for t in cen_ids]).astype(np.float32)
doc_c = unit(np.stack([C.mat[C.rows_of[d]].mean(axis=0) for d in C.doc_ids]) - mu)       # centered doc-mean vectors
near_cos = (doc_c @ cen_c.T); nearest = near_cos.argmax(axis=1); nearest_cos = near_cos.max(axis=1)
maxs = np.array([max(S[d].values()) for d in C.doc_ids])
is_book = np.array([d[0] == "B" for d in C.doc_ids])
p10_books = float(np.quantile(nearest_cos[is_book], 0.10))
vocab = json.load(open(CACHE / "vocab_candidates.json"))
kw_cands = vocab["candidates"]                                               # uncaught curated keywords in >= 15 docs
kw_of_doc = defaultdict(list)
for c in kw_cands:
    for d in c["docs"]: kw_of_doc[d].append(c["value"])
orph = json.load(open(CACHE / "orphan_clusters.json"))
p0_k = orph["detail"]["P0_kmax"]; p2 = orph["detail"]["P2_cap"]
clus_of = defaultdict(list)
for tag, det in (("P0/k%d" % p0_k["k"], p0_k), ("P2/k%d" % p2["k"], p2)):
    for cl in det["clusters"]:
        for d in cl["docs"]: clus_of[d].append(f"{tag}.c{cl['label']}")
p2docs = set(orph["populations"][[n for n in orph["populations"] if n.startswith("P2")][0]])
NEW_WORKS = ["Battles in the Supreme Court", "Judicial Renaissance", "Leadership by Example: The Davide Standard", "Leveling the Playing Field", "Liberty and Prosperity",
             "Love God, Serve Man", "Reforming the Judiciary", "Transparency, Unanimity & Diversity"]
works = defaultdict(list)
for d in C.doc_ids:
    if d[0] == "B": works[C.work[d]].append(d)
assert len(works) == 12

L = []
def w(s=""): L.append(s)
def table(headers, rows, align=None):
    w("| " + " | ".join(headers) + " |")
    w("|" + "|".join(("---:" if (align and align[i] == "r") else "---") for i in range(len(headers))) + "|")
    for r in rows: w("| " + " | ".join(str(x) for x in r) + " |")
    w()

w("# CE-7 · step 8 — per-work coverage")
w()
w("**Date** 2026-09-26. For each of the twelve works: which dimensions its chapters land on under three independent lenses, and how many chapters have **no home** under any of them. "
  "A work whose chapters have no home is evidence for a missing dimension, not a labelling problem.")
w()
w("## Lenses")
w()
w("1. **Prior-art matchers** (`_doc_haystack` + `score_topic`): a chapter is *matcher-zero* at best score 0 and *weak* at best score ≤ 1. The matchers are broad (step 4), so “landing on” a topic here says little; the counts of *weak* chapters say more.")
w(f"2. **Embedding, centered scale.** Each chapter's mean chunk vector minus the corpus mean, compared with the prior-art centroids (also centered; step 5 showed that raw cosine cannot separate topics in this space). "
  f"A chapter is *embedding-distant* when its nearest prior-art centroid is below the **books' own 10th percentile** ({p10_books:.3f}) — a book-relative cut, so the format shift found in step 5 does not inflate the count.")
w(f"3. **Candidate dimensions from lines 1–2:** the {len(kw_cands)} curated keywords appearing in ≥ 15 documents that no prior-art matcher catches (step 7), and the orphan clusters (step 6: P0 at k={p0_k['k']}, P2 at k={p2['k']}).")
w()
w("**No home** = weak on the matchers (best score ≤ 1) **and** carries none of the uncaught-keyword candidates **and** is embedding-distant. All three conditions, so the count is conservative.")
w()
rows, det = [], {}
for wk in sorted(works, key=lambda k: (k in NEW_WORKS, -len(works[k]))):
    ds = works[wk]; ii = [C.doc_index[d] for d in ds]
    zero = [d for d in ds if maxs[C.doc_index[d]] == 0]
    weak = [d for d in ds if maxs[C.doc_index[d]] <= 1]
    dist = [d for d in ds if nearest_cos[C.doc_index[d]] < p10_books]
    kwh = [d for d in ds if kw_of_doc[d]]
    nohome = [d for d in weak if d in set(dist) and not kw_of_doc[d]]
    inorph = [d for d in ds if d in p2docs or any(x.startswith("P0") for x in clus_of[d])]
    near = Counter(cen_ids[nearest[i]] for i in ii)
    # work-level centroid and its distance from prior art (centered)
    wc = unit(C.mat[[r for d in ds for r in C.rows_of[d]]].mean(axis=0) - mu); wsim = wc @ cen_c.T
    det[wk] = {"docs": ds, "zero": zero, "weak": weak, "distant": dist, "kw": kwh, "nohome": nohome, "near": near, "work_nearest": (cen_ids[int(wsim.argmax())], float(wsim.max())),
               "orph": inorph}
    rows.append([wk + (" **(new)**" if wk in NEW_WORKS else ""), len(ds), sum(len(C.rows_of[d]) for d in ds), len(zero), f"{len(weak)} ({pct(len(weak), len(ds))})", f"{len(dist)} ({pct(len(dist), len(ds))})",
                 f"{len(kwh)} ({pct(len(kwh), len(ds))})", len(nohome), f"{cen_ids[int(wsim.argmax())]} ({wsim.max():.2f})"])
w("## Summary by work")
w()
table(["work", "chapters", "chunks", "matcher-zero", "weak (best score ≤ 1)", "embedding-distant", "carry ≥ 1 uncaught-keyword candidate", "**no home**", "nearest prior-art topic to the whole work (centered cosine)"], rows, "lrrrrrrrl")
new_ch = sum(len(works[k]) for k in NEW_WORKS); old_ch = 299 - new_ch
nh_new = sum(len(det[k]["nohome"]) for k in NEW_WORKS); nh_old = sum(len(det[k]["nohome"]) for k in works if k not in NEW_WORKS)
w(f"**Works with at least one matcher-zero chapter: {sum(1 for k in works if det[k]['zero'])} of 12** ({', '.join(k for k in works if det[k]['zero']) or 'none'}). "
  f"**Works with at least one chapter that has no home under all three lenses: {sum(1 for k in works if det[k]['nohome'])} of 12.** "
  f"Chapters with no home: {nh_new} of {new_ch} in the eight new works, {nh_old} of {old_ch} in the four earlier works. "
  f"Chapters that are weak on the matchers: {sum(len(det[k]['weak']) for k in NEW_WORKS)} of {new_ch} (new) vs {sum(len(det[k]['weak']) for k in works if k not in NEW_WORKS)} of {old_ch} (earlier).")
w()
w("## Where each work's chapters land")
w()
w("Per work: the prior-art topic each chapter is *nearest* to on the centered scale (hard assignment, counts), the uncaught-keyword candidates its chapters carry, and the orphan clusters it contributes to.")
w()
for wk in sorted(works, key=lambda k: (k in NEW_WORKS, -len(works[k]))):
    d = det[wk]; ds = works[wk]
    kwc = Counter(v for x in ds for v in kw_of_doc[x]); orc = Counter(c for x in ds for c in clus_of[x])
    w(f"### {wk}{' (new)' if wk in NEW_WORKS else ''} — {len(ds)} chapters")
    w()
    w(f"* nearest prior-art topic per chapter (centered): " + "; ".join(f"{t} ×{n}" for t, n in d["near"].most_common(5)) + f" — top topic takes {pct(d['near'].most_common(1)[0][1], len(ds))} of chapters")
    w(f"* uncaught-keyword candidates carried (chapters): " + ("; ".join(f"“{v}” ×{n}" for v, n in kwc.most_common(6)) or "none"))
    w(f"* orphan clusters contributed to: " + ("; ".join(f"{c} ×{n}" for c, n in orc.most_common(4)) or "none"))
    w(f"* matcher-zero chapters: " + (", ".join(f"`{x}` {C.title[x].split(' -- ')[-1][:48]}" for x in d["zero"]) or "none"))
    w(f"* **no home** (weak ∧ no keyword ∧ embedding-distant): " + (", ".join(f"`{x}` {C.title[x].split(' -- ')[-1][:48]}" for x in d["nohome"]) or "none"))
    w()
w("## Reading")
w()
w("* The matchers place almost every chapter of every work somewhere, because a single incidental keyword hit is enough; the **weak** column is the honest measure of thin coverage.")
w("* The centered-scale nearest-topic column shows whether a work is spread over the prior-art topics or piles onto one or two. A work whose chapters all share one nearest topic is being *absorbed* into it; that is either correct (the topic is genuinely about the work) or a sign the topic is too coarse — the exemplar titles decide which, and Phase 4 should read them.")
w("* Uncaught-keyword candidates are curator-authored and skew toward the book formats (step 7). They are a mix of doctrinal terms, institutions and *people* (justices and presidents), so a chapter carrying one has a term the prior art does not name and the columns rarely use; whether that term is a *dimension* or just a proper name is a judgement for Phase 4, not something this count settles.")
w()
Path(B4 / "ce7_per_work_coverage_2026-09-26.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
json.dump({k: {kk: (vv if not isinstance(vv, Counter) else dict(vv)) for kk, vv in v.items()} for k, v in det.items()}, open(CACHE / "per_work.json", "w"), indent=1, default=lambda o: list(o) if isinstance(o, tuple) else float(o))
print("wrote per-work report;", len(L), "lines; no-home:", {k: len(v['nohome']) for k, v in det.items()})
