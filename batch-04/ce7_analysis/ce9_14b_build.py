"""CE-9 step 14b: the document text. Imports everything from ce9_14_assemble.py (data loading, tables) and writes batch-04/taxonomy_v2_PROPOSAL.md.
Usage: ce9_14b_build.py <matchers_json> <deploy_json> [out_md]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ce9_14_assemble import *

COMBINED_P3 = 0.54       # measured with ce9_17_pairs.py: one dimension with libel|cyberlibel|cybercrime|maria ressa|death penalty|echegaray (56 caught)
COMBINED_MAXCOS = 0.48


def sha8(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]
def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def build():
    gran_tbl, blur, frag = section_granularity()
    t1 = table1(); t2, tally = table2()
    np_units, np_pools = not_proposed()
    fo = orphan_facts(); fopt = floor_options()
    stat = Counter(status_of(c) for c in cl)
    tiers = Counter(dim[c]["tier"] for c in cl)
    tier_rows = [[t, tiers[t], ", ".join(f"`{dim[c]['id']}`" for c in cl if dim[c]["tier"] == t) or "—"] for t in ("anchor", "core", "subordinate", "meta")]
    th = Counter(dim[c]["theme"] for c in cl)
    low_theme = [f"`{dim[c]['id']}` ({dim[c]['theme']} {pc(dim[c]['theme_share'])})" for c in cl if dim[c]["theme_share"] < 0.5]
    order_ids = [dim[c]["id"] for c in cl]
    de, pdst = D["dup_evidence"], D["pair_distribution"]
    pmed = float(np.median([p["P3"] for p in D["precision"] if p["P3"] == p["P3"]])); cmed = float(np.median([p["control_P3"] for p in D["precision"]]))
    bmed = float(np.median([p["base3"] for p in D["precision"]])); v1med = float(np.median([p["P3"] for p in D["v1_precision"]])); v1base = float(np.median([p["base3"] for p in D["v1_precision"]]))
    v1caught = int(np.median([p["caught"] for p in D["v1_precision"]]))
    rec = [p["recall_of_cluster"] for p in D["precision"] if p["recall_of_cluster"] is not None]; ind = [p["in_derived_cluster"] for p in D["precision"] if p["in_derived_cluster"] is not None]
    thin = [f"`{dim[c]['id']}` ({dim[c]['caught']})" for c in cl if dim[c]["caught"] < 25]
    fid = [sep[c]["fidelity_to_derived_cluster"] for c in cl if isinstance(c, int)]
    lowfid = [f"`{dim[c]['id']}` ({sep[c]['fidelity_to_derived_cluster']:.2f})" for c in cl if isinstance(c, int) and sep[c]["fidelity_to_derived_cluster"] < 0.85]
    top_pairs = []; seenp = set()
    for x in D["top_pairs"]:
        k = frozenset((x["a"], x["b"]))
        if k in seenp or x["cos"] < 0.5: continue
        seenp.add(k); top_pairs.append(f"`{id_of[x['a']]}` ↔ `{id_of[x['b']]}` **{x['cos']:.2f}**")
    cells_zero = []; cells_n = 0
    for c in cl:
        if not isinstance(c, int): continue
        for f in FMT_ORDER:
            nf = int(((lab == c) & (fmt == f)).sum())
            if nf >= 3:
                cells_n += 1; r_ = prec[c]["recall_by_format"][f]
                if not r_: cells_zero.append(f"`{dim[c]['id']}` × {f} ({nf} docs)")
    fm = C.fmt_docs
    head_git = git("rev-parse", "--short", "HEAD"); branch = git("rev-parse", "--abbrev-ref", "HEAD")
    untouched = {"scripts/build_topic_map.py": git("diff", "--stat", "HEAD", "--", "scripts/build_topic_map.py") == "", "config.py": git("diff", "--stat", "HEAD", "--", "config.py") == "",
                 "corpus/voice/topic_map.json": git("diff", "--stat", "HEAD", "--", "corpus/voice/topic_map.json") == "", "data/index/topic_centroids.npy": sha8(IDX / "topic_centroids.npy") == "71a7c294"}
    sign = f"APPROVED: {', '.join(order_ids)} | TOPIC_MERGE_COSINE={THRESH_MERGE:.2f} | TOPIC_ASSIGN_MIN_COSINE={THRESH_ASSIGN:.2f}"
    fl = D["floor"]["best_chunk"]; fdm = D["floor"]["doc_mean"]
    o_all = bestB < THRESH_ASSIGN; oc = {f: (int(o_all[fmt == f].sum()), int((fmt == f).sum())) for f in FMT_ORDER}
    pw = lambda f: f"{oc[f][0]} of {oc[f][1]}"
    dx = "x:death_penalty"
    unbuilt3 = "; ".join(f"{v['name']} ({v['n']} docs)" for v in UNBUILT.values() if "MERGED" not in v["why"])
    n_partition = L["20"]["N"]
    fid6 = sep[6]["fidelity_to_derived_cluster"]
    fine10 = np.load(CACHE / "ce9_level_m10.npy"); ev = None
    for f_ in set(fine10.tolist()):
        ii = np.where(fine10 == f_)[0]
        if len(ii) == 32 and set(lab20[ii].tolist()) == {6}: ev = ii
    ev_arg = BCL[ev].argmax(1) if ev is not None else np.array([], dtype=int); ev_best = BCL[ev].max(1) if ev is not None else np.array([])
    ev_d2 = int((np.array([cl[a_] for a_ in ev_arg]) == 2).sum()); ev_orph = int((ev_best < THRESH_ASSIGN).sum()); ev_n = len(ev) if ev is not None else 0
    from scipy.stats import fisher_exact
    p_bc = float(fisher_exact([[oc['books'][0], oc['books'][1] - oc['books'][0]], [oc['columns'][0], oc['columns'][1] - oc['columns'][0]]])[1])
    n_no_corr = sum(1 for c in cl if "no Phase 3" in derived_from(c))

    doc = f"""# Taxonomy v2 — proposal (Phase 4 / CE-9)

**Status: PROPOSAL FOR SIGN-OFF. Nothing here is applied.** Branch `{branch}` at `{head_git}` when this was written. `scripts/build_topic_map.py`, `config.py`, `corpus/voice/topic_map.json` and `data/index/topic_centroids.npy` are untouched (verified at write time: {', '.join(f'{k} {"✓" if v else "✗"}' for k, v in untouched.items())}); no document has been tagged. Every number below is written by `batch-04/ce7_analysis/ce9_14b_build.py` (with `ce9_14_assemble.py`) from measurements produced by the `ce9_*` scripts beside it (section 12). Similarity is on the **centred scale** throughout; no raw cosine is offered as evidence.

## 0. What you are asked to sign

**Recommended N = {K}.** Chosen at the *medium* granularity (the tree cut into {n_partition} clusters of at least 20 documents each) and then reduced by tests that only make sense once a dimension is *deployed* — built from the documents its own matcher catches, which is what the production recipe does:

* **−1** the business-leaders-and-philanthropy cluster is merged into the Foundation dimension: on deployed centroids they are 0.74–0.78 apart whatever the matcher (the donors *are* the business leaders). The Foundation dimension is now `{id_of[15]}`.
* **−3** three clusters could not be given a finished matcher and are not proposed: {unbuilt3}. The best readable term set catches 6, 0 and 4 of their documents. They are real in embedding space and invisible to the metadata the matchers read (section 10).
* **+1** `death_penalty_and_echegaray` is carried as a dimension of its own, as the brief said it survives: a 13-document fragment at the fine level, 30 documents by matcher. That forces criminal law's own matcher down to libel and cybercrime (`{id_of[6]}`). Against the 0.60 precision bar used for the others one lands just under and one just over ({pc(prec[dx]['P3'])} and {pc(prec[6]['P3'])}), and both beat the combined one-dimension version ({pc(COMBINED_P3)}) — section 5.

**The two thresholds** (section 7): `TOPIC_MERGE_COSINE = {THRESH_MERGE:.2f}` (centred) and `TOPIC_ASSIGN_MIN_COSINE = {THRESH_ASSIGN:.2f}` (centred, best-chunk, one global value).

**Sign-off is one line.** Copy this, delete any id you do not want, change either value if you disagree:

```
{sign}
```

**Read these before you sign — they are where this proposal is weakest:**

1. **Matchers are seeds, not classifiers.** A dimension's matcher catches a median of {pc(float(np.median(rec)))} of its own cluster, and a median of {pc(float(np.median(ind)))} of what it catches is inside that cluster. Its job is to give the centroid a clean set of members; everything else is tagged by centroid affinity. The figures here are in-sample; on unseen documents recall is lower (section 8). {len(thin)} dimensions rest on fewer than 25 caught documents: {', '.join(thin)}.
2. **Separability has thin margins.** No pair of dimensions reaches 0.70 on deployed centroids, but the three closest sit at 0.68–0.69: {', '.join(top_pairs[:3])}. That is why the recommended merge gate is {THRESH_MERGE:.2f}, not 0.70 (section 7).
3. **Biography is the one format I cannot call finished.** At the recommended floor {pw('biography')} biography chapters are orphaned ({pc(oc['biography'][0] / oc['biography'][1], 1)}) against {pc(float(o_all.mean()), 1)} overall. With n = 35 that is not statistically distinguishable from the rest (Fisher p = {fo['p_bio']:.2f}), but all three are judicial-career chapters of the kind the unbuilt chief-justiceship cluster would hold. Decide whether to ship with those three or hold until biography chapters carry a discriminating tag (section 9).
4. **Two of the brief's expectations came out differently.** `death_penalty_and_echegaray` survives, but only as a marginal dimension (above). The Puno pool that Phase 3 read as "same direction as `supreme_court_history`" is *not* a dimension: its 21 chapters are all books and spread over 11 dimensions (section 5). `robot_identity_meta` moves to the router, as the brief said.
5. **The code has to change with the metric** (section 11): the merge gate and the floor are only meaningful on centred vectors, so `build_centroids_fullcorpus.py`, `merge_tag_topics.py` and — the part most likely to be missed — the runtime `retrieval.route()` all need the corpus mean vector. `build_topic_map.load_docs()` also never reads `corpus/books/`.

## 1. Why the v1 merge gate collapsed the taxonomy (P3.3)

{section_p33()}

## 2. Method

{section_method()}

## 3. Granularity: three levels, one recommendation

The dimension list is a choice along one curve. Same family, three values of *m* (the smallest cluster allowed), measured on the centred scale:

{gran_tbl}

*Keyword matchability* is the earlier automatic induction procedure, learned on half the documents and scored on the other half (centroids from the training half only), so its figures are comparable **across levels**; they are not the final matchers' figures (section 8). Its random-set control recall is 0.00 at every level.

**What the coarse level (N = {L['30']['N']}) blurs** — it merges recommended-level dimensions that a reader would never confuse:

{blur}

**What the fine level (N = {L['10']['N']}) fragments** — {L['10']['n_marginal_10_19']} of its {L['10']['N']} dimensions have 10–19 documents, its closest pair of dimensions is already {L['10']['nn_centered_max']:.2f} apart (at the duplicate line), and {L['10']['n_no_matcher']} have no usable keyword matcher. What it splits out of the medium dimensions:

{frag}

**Recommendation: the medium level** (m = 20, {n_partition} clusters). It is the only one of the three with no marginal dimension and a closest pair ({L['20']['nn_centered_max']:.2f}) clearly under the duplicate line; its held-out keyword recall ({pc(L['20']['recall_median'])}) beats the fine level's ({pc(L['10']['recall_median'])}) — the fine level buys a higher precision ({pc(L['10']['P2_median'])} vs {pc(L['20']['P2_median'])} at P@2) with {L['10']['N'] - L['20']['N']} more dimensions, most of them marginal. It is also the coarsest level that still keeps apart the subjects a visitor would ask about (elections vs the Marcos–Robredo contest vs citizenship; impeachment vs US politics; the sea dispute vs the Bangsamoro peace process). A coarser cut is defensible if the demo does not need those distinctions — the {L['30']['N']}-dimension level is a real alternative, not a strawman. The deployed tests then take the medium level from {n_partition} to **{K}** (section 0).

## 4. Table 1 — the proposed taxonomy ({K} dimensions)

`doc_count` is the number of documents the dimension's matcher catches on the {N:,}-document corpus (the v1 `topic_map.json` convention). `separability` is the highest centred cosine between this dimension's **deployed** centroid and any other's. `status`: **{sum(v for k, v in stat.items() if k.startswith('Dimension holds'))} Dimension holds (two of them marginal) · {stat.get('Same direction, wrong members', 0)} Same direction, wrong members · 0 Not established** — a row that were *Not established* would not be here; the one that was, `honors_received`, is in Table 2. Every dimension's `derived_from` is a Ward-tree cluster of the whole corpus; where a Phase 3 candidate or a curated-keyword pool also names it that is listed, and where none does the row says so — {n_no_corr} of the {K} rest on the tree alone.

{t1}

### Tier distribution and theme anchors

{table(['tier', 'n', 'dimensions'], tier_rows)}

Rule: **anchor** is a policy label, not a size — the Chief Justice's organising philosophy (`twin_beacons_doctrine`) and the Foundation, as in v1; **core** = at least 40 documents caught; **subordinate** = fewer; **meta** is empty because `robot_identity_meta` leaves the taxonomy. Tier is informational in the code (router-prompt preface, tie-break); it is one line to change.

`theme_anchor` is the plurality theme letter of the dimension's derived cluster ({', '.join(f'{k} {v}' for k, v in sorted(th.items()))}). It matters more than it looks: `app/service.py` turns it into a spoken register cue, and the per-topic token budgets in `answer_pipeline.py` were seeded from it. Where the plurality is under half the cluster the anchor is a judgement call: {', '.join(low_theme) or 'none'}.

## 5. The two named verdicts, and the same-direction cases

**`robot_identity_meta` — moves to the router (verdict confirmed).** 0 documents, 0 chunks; its v1 centroid is the corpus-mean fallback. It is already a router intent (`corpus/voice/router_prompt.md`) and a deterministic regex gate (`app/retrieval.py` `input_gate`). What must be kept outside the taxonomy: the intent id, its 120-token budget (`answer_pipeline.py` and `cj_chat.py` line 162), its `META` register cue (`app/service.py` line 68) and the hard-coded identity response (`answer_pipeline.py` line 802). Removing the taxonomy entry without providing those breaks `service._theme_of` for that id.

**`death_penalty_and_echegaray` — survives, as a marginal dimension.** The evidence:

* It is real and narrow: Phase 3 measured cohesion 0.34 against a null 95th percentile of 0.23; 30 documents, 17 of them book chapters; the curated pools “leo echegaray” 5/5 and “people v. echegaray” 5/5 sit inside one cluster; at the fine level it is a 13-document cluster (*death penalty, penalty, appellant, victim, death, rape*).
* At the recommended level it is *not* its own cluster: it is a fragment of the 56-document criminal-law cluster, 0.60 from the rest of that cluster.
* **The trap.** As a matcher-defined dimension it is separable only if no other dimension carries its terms. With `death penalty` in criminal law's matcher the two deployed centroids are **0.96** apart (all 30 of its documents are also in criminal law). With criminal law restricted to libel and cybercrime, its nearest dimension is **{sep[dx]['max_cos']:.2f}** away. So the criminal-law dimension is narrowed to `{id_of[6]}` — which is not the whole 56-document cluster: its centroid is {fid6:.2f} from the cluster's own, and the cluster's 32 evidence-and-procedure documents have no dimension of their own ({ev_d2} of those {ev_n} have `{id_of[2]}` as their best-chunk dimension and {ev_orph} is an orphan).
* **The cost, and why splitting is still the better option.** Neighbourhood precision is {pc(prec[dx]['P3'])} for the death-penalty dimension and {pc(prec[6]['P3'])} for `{id_of[6]}`, against a bar of 60% (random-membership control {pc(prec[dx]['control_P3'])} / {pc(prec[6]['control_P3'])}). The single combined dimension — libel, cybercrime and the death penalty in one matcher — scores {pc(COMBINED_P3)} on 56 documents, lower than either half. If you would rather have one dimension, delete `death_penalty_and_echegaray` from the sign-off line and add `death penalty` and `echegaray` to `{id_of[6]}`'s matcher; the merge gate then never sees the pair.

**The same-direction cases.** `faith_journey` keeps its id and gets a new matcher: its v1 centroid is 0.80 from the scripture-and-prayer dimension while only 22 of its 298 matcher documents are in it. Davide ↔ `judicial_reform` holds: 9 of the 23 Davide chapters land in `{id_of[10]}`, more than in any other dimension, so the v1 topic was right and its matcher missed them. **Puno ↔ `supreme_court_history` does not hold up as a dimension:** the 21 Puno chapters are all books and spread over 11 dimensions (7 in property and contracts — they are decisions he wrote); Phase 3's 0.81 was two diffuse directions agreeing. `supreme_court_history` is dropped (Table 2).

## 6. Table 2 — the fate of the {len(FATE)} v1 topics

(35 topics in the v1 taxonomy; v1's stored centroids had already merged `msme_and_entrepreneurship` and `prosperity_fund_msme` into one, shown as one row.) The document counts are the v1 matchers run on the current {N:,}-document corpus; the stored `topic_map.json` `doc_count` (from the 79-document corpus, before books) is shown beside it.

{t2}

**Counts:** {', '.join(f'{k}: **{v}**' for k, v in sorted(tally.items(), key=lambda kv: -kv[1]))} — {sum(tally.values())} v1 topics in all. Every v1 matcher was rewritten; none was reused unchanged (two — `international_law_disputes`, `asean_law_association` — pass the acceptance test as they stand and were beaten by their replacement). {len([c for c in cl if not v1_target.get(c)])} of the {K} dimensions have no v1 predecessor.

**Id remap for Phase 5** (v1 id → v2 id): {'; '.join(f"`{t}` → `{id_of.get(tg, EXTRA_DIMS.get(tg, {}).get('id', '—'))}`" for t, (w, tg, _) in FATE.items() if tg is not None and (w.startswith('carried') or w.startswith('redefined') or w.startswith('absorbed')))}. Dropped: {', '.join(f'`{t}`' for t, (w, tg, _) in FATE.items() if w == 'dropped')}. Live files keyed by v1 ids: `corpus/voice/{{topic_map.json, router_prompt.md, voice_card.md}}` and at least 9 files under `eval/`; the live corpus JSONs carry no topic tags, so nothing needs retagging in `corpus/`.

## 7. Table 3 — the two thresholds

### `TOPIC_MERGE_COSINE` → **{THRESH_MERGE:.2f}, on the centred scale** (v1: 0.95 on the raw scale)

**The metric changes and the code must change with it** — 0.75 means nothing on raw cosine, where independent random groups score 0.98 (section 1).

{merge_tables()}

* **Above the noise.** Random groups of the dimensions' own sizes reach {de['random_groups']['max']:.2f} at most in {de['random_groups']['n']:,} draws (95th percentile {de['random_groups']['p95']:.2f}; Phase 3's own run of the same idea: mean 0.019, 95th 0.282). Anything under ~0.55 is indistinguishable from unrelated document groups.
* **Above every pair we decided is distinct.** {pdst['n_pairs']} pairs of proposed dimensions; the highest is {pdst['max']:.3f}; {pdst['ge_0.65']} are at 0.65 or above and {pdst['ge_0.7']} at 0.70 or above. A gate at 0.70 would sit {0.70 - pdst['max']:.3f} above the closest pair — one rebuild away from silently merging a pair the sign-off has approved, which is how P3.3 collapsed. At {THRESH_MERGE:.2f} the margin is {THRESH_MERGE - pdst['max']:.3f}.
* **Below a genuine duplicate.** Splitting one dimension's own documents at random into two halves — the best model of "the same subject twice" — gives a median centroid cosine of {de['same_dim_split_half']['median']:.2f}; {pc(de['same_dim_split_half']['frac_ge_0.75'])} of such splits are at or above 0.75, {pc(de['same_dim_split_half']['frac_ge_0.70'])} at or above 0.70, {pc(de['same_dim_split_half']['frac_ge_0.60'])} at or above 0.60. So the gate is a **backstop for accidental duplicates, not a discriminator**: at 0.75 it catches about two of three of them. The separability that matters is enforced by this document (Table 1), not by the gate.
* The Ward family was built with a working duplicate line of 0.70 on *partition* centroids (closest pair {L['20']['nn_centered_max']:.2f}); deployed centroids are noisier than partition centroids (matchers admit some out-of-cluster documents), which is the reason the config value is higher.

### `TOPIC_ASSIGN_MIN_COSINE` → **{THRESH_ASSIGN:.2f}, centred scale, best-chunk, one global value** (v1: 0.68 raw, inert — it orphaned 0.0% under every definition)

*Definition.* Best-chunk (a document's affinity is its best chunk's cosine to the dimension), evaluated **leave-one-out**: a member document is removed from its own dimension's centroid before its affinity is measured, so the number is not inflated by a document matching itself. Best-chunk separates real dimensions from noise better than document-mean (area under the curve of observed best affinity over a random-membership null: **{fl['auc_observed_vs_null']:.3f}** vs **{fdm['auc_observed_vs_null']:.3f}**; by format, best-chunk: {', '.join(f"{f} {v:.2f}" for f, v in fl['by_format_auc'].items())}), and it is what `merge_tag_topics.py` already uses.

*Value.* The null is the same procedure with **random** document sets of the dimensions' own sizes, taking a maximum over all {K} dimensions per document: best-chunk median **{fl['null_pct']['50']:.3f}**, 90th percentile {fl['null_pct']['90']:.3f}, 95th {fl['null_pct']['95']:.3f}. The recommended {THRESH_ASSIGN:.2f} is that median: a document is an orphan when its best dimension is no better than what a random set of documents would typically give it. Observed best-chunk affinity has median {fl['observed_LOO_pct']['50']:.3f} and 5th percentile {fl['observed_LOO_pct']['5']:.3f}.

**What this floor is and is not.** It is a *noise-median floor for flagging orphans*, not a significance test. A floor at the null's 95th percentile ({fo['null_p95']:.3f}) would orphan **{pc(fo['frac_below_null_p95'])} of all documents** — which shows how weak per-document evidence is in this space, and why the top-3 rank and the tagging margin, not the floor, decide what a document is about. At {THRESH_ASSIGN:.2f}: {fo['n_orph']} documents ({pc(float(o_all.mean()), 1)}) are orphans; of the rest, {fo['tags'][3]} keep three tags, {fo['tags'][2]} two and {fo['tags'][1]} one (top three by best-chunk, at or above the floor).

**Global, per-format, or within-format percentile.** Orphan rates (leave-one-out) under each policy:

{fopt}

Per-format floors at each format's own noise median (B) lower the columns rate by about two points and raise the books rate by about one and a half — a couple of points of parity for a config change from one number to four — so I recommend the single global value (A). A within-format percentile (C) forces equal rates by construction and would flag documents in a format that is perfectly covered; it is a policy, not evidence. Document-mean (D) is the weaker separator and orphans columns more. The Phase 3 finding that books need a higher floor than columns holds here too (books' noise median {FB['by_format_null_p50']['books']:.2f} vs columns' {FB['by_format_null_p50']['columns']:.2f}) but is small on this scale.

## 8. Matchers

The taxonomy engine is unchanged (v1 `_doc_haystack` + `score_topic`: word-boundary match over title, summary, topic tags, keywords, register markers and entity names; a document is in the dimension if any term matches). Every term is a plain readable phrase that catches **at least 5 documents**; nothing is a regular expression. Method: candidate terms = the cluster's top TF-IDF terms, the curated keywords and entity names lifted inside it; a greedy pick scoring each term by cluster documents gained minus 0.35× outside documents gained, under a per-term precision filter; a per-format top-up; then defining vocabulary tried in a fixed order and admitted only while the union stays under 1.9× the cluster with at least 65% of caught documents in the dimension's neighbourhood; then the edits printed in `ce9_edits.py` and `ce9_19_freeze.py`, each with the measurement that forced it (`noon`, `fisherman`, `levy` were precise on their clusters and meaningless as subjects).

**Reading the table.** *Share in its own embedding neighbourhood* = of the documents the matcher catches, the share that have this dimension among their 3 nearest (`MAX_TOPIC_TAGS` = 3), leave-one-out, with dimension centroids built from the matcher-caught members. The random-membership control replaces each dimension's members with a random set of the same size (it lands on the base rate, as it should). The cluster columns compare the matcher to the tree's cluster; *fidelity* is the cosine between the centroid built from the caught documents and the cluster's own centroid.

{matcher_table()}

**Result.** Median neighbourhood share **{pc(pmed)}** (random-membership control {pc(cmed)}, base rate {pc(bmed)}); median documents caught {int(np.median([p['caught'] for p in D['precision']]))}. The v1 matchers under the *same* definition: median neighbourhood share **{pc(v1med)}** (base rate {pc(v1base)}) and median documents caught **{v1caught}**; the largest v1 matchers fire on 611, 406 and 298 documents. No new matcher catches more than {max(p['caught'] for p in D['precision'])} documents or more than {max(dim[c]['caught'] / dim[c]['n'] for c in cl if dim[c]['n']):.1f}× its cluster.

**What this does and does not show.**

* **In-sample.** The final lists were chosen on the same {N:,} documents they are scored on, against the deliverable's own metric. The honest generalisation evidence is the earlier automatic procedure of the same family: on unseen documents (learn on a random half, score the other, centroids from the training half only) it recovered **44%** of its clusters' documents at neighbourhood precision **59%** (6.9× the base rate), against a random-set control of 0.00 recall (`ce9_results/ce9_07_heldout.log`). Expect the final lists to do somewhat worse than the table on new documents.
* **Keyword matching is weak in this corpus and cannot be made strong.** The haystack is title, summary, topic tags, keywords and entities. The words that *define* a subject ('impeachment', 'martial law', 'election') are also mentioned across other subjects, so any term precise enough to seed a centroid catches only part of the subject: median cluster recall {pc(float(np.median(rec)))}, and {sum(1 for r in rec if r < 0.5)} of {len(rec)} dimensions are below half. That is acceptable **only because a matcher's job here is to give the centroid clean members**: median fidelity is {float(np.median(fid)):.2f}; below 0.85: {', '.join(lowfid) or 'none'}. Everything else is tagged by affinity, which is what `merge_tag_topics.py` already does.
* **All four formats.** {cells_n - len(cells_zero)} of {cells_n} (dimension × format) cells with at least 3 cluster documents have at least one caught document. The {len(cells_zero)} that do not: {', '.join(cells_zero) or 'none'}.

### v1 matchers under the same definition (baseline)

{v1_table()}

## 9. Per-format orphan rate at the recommended floor and set

At floor {THRESH_ASSIGN:.2f}, best-chunk, leave-one-out, the {K} dimensions above:

{table(['format', 'documents', 'orphans', 'rate'], [[f, oc[f][1], oc[f][0], pc(oc[f][0] / oc[f][1], 1)] for f in FMT_ORDER] + [['**all**', N, int(o_all.sum()), pc(float(o_all.mean()), 1)]], ['l', 'r', 'r', 'r'])}

Sensitivity — the best-chunk floor grid ("held-out" = leave-one-out; "as production would print it" leaves each member document inside its own centroids and so reads lower):

{floor_table('best_chunk', [0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.40])}

* **Columns are orphaned first** ({pc(oc['columns'][0] / oc['columns'][1], 1)} vs books {pc(oc['books'][0] / oc['books'][1], 1)}), the same direction as Phase 3, but the gap is not significant on these counts (Fisher p = {p_bc:.2f}).
* **Biography: {oc['biography'][0]} of {oc['biography'][1]} ({pc(oc['biography'][0] / oc['biography'][1], 1)}) — not finished.** The orphans: {'; '.join(f"`{d}` *{t}* (best affinity {a:.3f}, nearest `{n}`)" for d, t, a, n in fo['bio_orphans'])}. All three belong to the cluster this proposal could not build a matcher for (the chief justiceship and a judicial career). Biography's separation from noise is the weakest of the four formats (AUC {fl['by_format_auc']['biography']:.2f} vs {fl['by_format_auc']['columns']:.2f} for columns). Fisher p = {fo['p_bio']:.2f} against the other formats: three documents cannot prove a pattern and I am not claiming one; I am saying I cannot rule it out, and the three documents are exactly where the missing dimension would be.
* The tag budget: {fo['tags'][3]} documents ({pc(fo['tags'][3] / N)}) keep three tags, {fo['tags'][2]} two, {fo['tags'][1]} one and {fo['tags'][0]} none.

## 10. What I decided not to propose, and why

**Recommended-level clusters that are not dimensions**

{np_units}

**The three unbuilt clusters are not wrong; they are unreachable.** They are the smallest and most vocabulary-diffuse of the {n_partition}. What would unlock them is metadata, not a cleverer matcher: a curator-added tag on the ~20 documents of each, after which each can be tested against the four rules.

**The fine level's extra dimensions.** Section 3 lists the {L['10']['N'] - L['20']['N']} fragments the fine level adds. None is promoted except the death-penalty fragment (section 5). Each is 11–19 documents, sits about 0.69 from its sibling (at the duplicate line) and would need its own matcher and separability test; any can be promoted individually on request.

**Phase 3's viable candidates** — 9 orphan clusters and 14 curated-keyword pools. Where each lands in the recommended partition:

{np_pools}

The pools are words and names — 'supreme court', 'integrity', 'transparency', 'grave abuse of discretion', the names of former justices — that occur across subjects; none is a dimension. A few *corroborate* one (`sandiganbayan` half inside criminal trials, `people power` inside presidential power, `judicial independence` half inside how-the-Court-decides). The orphan clusters mostly land inside a single dimension ({', '.join(f"{c.replace('orphan ', '')} → {id_of.get(r['landing'][0]['dim'], 'd' + str(r['landing'][0]['dim']))} ({pc(r['landing'][0]['share_of_candidate'])})" for c, r in CORR['candidates'].items() if c.startswith('orphan') and r['landing'][0]['share_of_candidate'] >= 0.5)}); one, P0 k=4 · c1 (30 documents), is a residual bag whose best dimension holds only {pc(CORR['candidates']['orphan P0 k=4 · c1']['landing'][0]['share_of_candidate'])} of it.

**Concept dimensions.** `rule_of_law`, `due_process`, `constitutional_doctrine`, `judicial_activism_and_political_question`, `with_due_respect_persona`: concepts and stances mentioned across the corpus have no place in it (Table 2).

## 11. Phase 5 dependencies — code that changes with this proposal (nothing was changed here)

1. **Centring (the metric change).** Store the corpus mean `mu` (768 floats, the mean of all chunk vectors) beside the centroids and record its hash in `topic_centroids_meta.json`. `scripts/build_centroids_fullcorpus.py`: centroid = `unit(mean(member chunks) − mu)`; its zero-member fallback (`gmean`) is no longer needed (every dimension here has at least 11 members; assert it). `scripts/merge_tag_topics.py`: the pair test at lines 42–46 then runs on centred centroids as written, but line 69 `cmat @ final_cen.T` must use centred chunk vectors (`unit(cmat − mu)`), and the floor at line 77 becomes {THRESH_ASSIGN:.2f} with the merge gate {THRESH_MERGE:.2f}.
2. **Runtime routing — the part most likely to be missed.** `app/retrieval.py` line 91, `cos = cen @ qv`, uses raw query vectors against the centroids. If the stored centroids become centred, `qv` must be centred too, and every constant calibrated on raw route scores must be re-derived: `TOPIC_SOFTMAX_TEMPERATURE` (0.7), `OUT_OF_SCOPE_THRESHOLD` (0.15), `THEME_CONF_THRESHOLD` (0.51, derived from frozen route bands) and `TOPIC_MARGIN_THRESHOLD` (0.01). Two ways out, for you to choose: (a) centre only at build time and keep a raw copy of the new centroids for runtime routing (smallest blast radius; runtime routing stays as weakly discriminating as it is today), or (b) centre both and recalibrate. I recommend (a) for Phase 5 and (b) as a measured follow-up.
3. **`build_topic_map.load_docs()` (line 691) reads `columns`, `speeches` and `biography` — never `books`.** The {fm['books']} book chapters ({pc(fm['books'] / N)} of the corpus, {pc(C.fmt_chunks['books'] / C.mat.shape[0])} of the chunks) would not be tagged or counted. Add `books/**`. The stored v1 `topic_map.json` `doc_count`s (e.g. 30 for `rule_of_law`) are stale for that reason and because they predate the {N:,}-document corpus.
4. **Topic-id-keyed tables.** `answer_pipeline.py` / `cj_chat.py` lines 127–163 (per-topic token budgets seeded from `theme_anchor`; an id missing from the table falls back to `TOKEN_BUDGET_DIM_DEFAULT` = 220, so new ids degrade gracefully but silently); `router_prompt.md` (regenerated from the taxonomy); `service.py` lines 96–118; the comment at `config.py` line 617 (names `honors_received`); at least 9 files under `eval/` (found by searching for `faith_journey`; search for every v1 id). The remap is in section 6.
5. **`robot_identity_meta`** keeps an entry outside the taxonomy (section 5).
6. **Verification.** `verify_pin.py` fails until Phase 5 regenerates the chunk/centroid pin, as before; the corpus mean vector must be pinned with it.

## 12. Reproduction and controls

All scripts are in `batch-04/ce7_analysis/` (read-only on the repo; cached intermediates in `cache/`, not committed; `ce9_results/` holds copies of the JSON outputs this document is built from, plus the held-out log): `ce9_00_entry.py` (branch/HEAD/file-hash guards), `ce9_00b_p33.py` (the collapse), `ce9_01_tree.py` / `ce9_03_levels.py` (tree and the three levels), `ce9_08*_*.py` (fate, candidate-side view, corroboration, pools, v1-matcher reuse), `ce9_12_readable.py` → `ce9_13_finalize.py` → `ce9_19_freeze.py` (matchers; `ce9_edits.py` holds the hand edits), `ce9_09_deploy.py` (deployed centroids, separability, both thresholds, orphan rates, v1 baseline), `ce9_17_pairs.py` (separability iteration), `ce9_14_assemble.py` + `ce9_14b_build.py` (this document), `ce9_20_verify_taxonomy_block.py` (proves Appendix A splices into a copy of `build_topic_map.py`, imports, and reproduces Table 1's document counts). Controls run: shuffled-feature null for the tree; random-membership control for every matcher; random-set control for induction; leave-one-out for every affinity; a 6-replicate multiple-comparison null for the floor. Hypotheses tried and **disproved along the way**: that a per-term precision filter alone yields readable matchers (it yields memorised names — `p11`, `kee`, `wdr3` — and was replaced); that a cluster-membership precision test finds a topic's defining words (it excludes them, because they are mentioned elsewhere); that the death-penalty pair is inseparable (on partition centroids it is 0.60; on deployed centroids it is 0.96 only while criminal law's matcher carries its terms).

## Appendix A — the complete `TAXONOMY` list

Replaces the `TAXONOMY` statement in `scripts/build_topic_map.py` **whole** — currently lines 70–645, from `TAXONOMY: list[dict[str, Any]] = [` to its closing `]` inclusive. (The brief cites 69–649; the extra lines are a blank line above and the blank lines and `# -- Matching engine` banner below, which should stay.) {K} entries. Not applied; `ce9_20_verify_taxonomy_block.py` splices this block into a copy, imports it and checks it.

```python
{taxonomy_block()}
```
"""
    return doc


if __name__ == "__main__":
    text = build()
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({len(text.splitlines())} lines, {len(text):,} chars)")
