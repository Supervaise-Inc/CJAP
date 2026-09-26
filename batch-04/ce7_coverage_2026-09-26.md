# CE-7 · steps 4–5 — coverage against the prior-art taxonomy

**Date** 2026-09-26 · **Scope:** the 35 prior-art topics (34 centroids; `msme_and_entrepreneurship` and `prosperity_fund_msme` share one merged centroid) measured over the 1,290-document corpus. Prior art is *diagnosed*, not adopted: it was generated from 79 documents (64 columns, 15 speeches) and has never seen a book or a biography chapter.

Definitions are the project's own: matcher = `build_topic_map._doc_haystack` + `score_topic`, membership = score > 0; centroid = unit-normalised mean of **all chunks** of the member documents (`build_centroids_fullcorpus.py`); document affinity = **best-chunk cosine** (max over the document's chunks, `merge_tag_topics.py`). Knobs from `config.py`: `TOPIC_ASSIGN_MIN_COSINE`=0.68, `TOPIC_MERGE_COSINE`=0.95.

## Sampling hazard (applies to everything below)

| format | docs | doc % | chunks | chunk % | skew (chunk% / doc%) |
|---|---:|---:|---:|---:|---:|
| columns | 803 | 62.2% | 6129 | 45.2% | 0.73× |
| books | 299 | 23.2% | 5599 | 41.3% | 1.78× |
| speeches | 153 | 11.9% | 1430 | 10.6% | 0.89× |
| biography | 35 | 2.7% | 391 | 2.9% | 1.06× |

## Step 4 — the v1 matchers over 1,290 documents

### 4a. Per-topic document count at 1,290, beside the count at 79

| topic | tier | docs @79 (v1) | docs @1,290 | % of corpus | docs by format (col / book / spe / bio) | % of each format's own docs |
|---|---|---:|---:|---:|---:|---:|
| constitutional_doctrine | core | 28 | 611 | 47.4% | 436 / 139 / 33 / 3 | 54.3 / 46.5 / 21.6 / 8.6 |
| supreme_court_history | core | 33 | 406 | 31.5% | 239 / 128 / 35 / 4 | 29.8 / 42.8 / 22.9 / 11.4 |
| faith_journey | core | 20 | 298 | 23.1% | 128 / 93 / 53 / 24 | 15.9 / 31.1 / 34.6 / 68.6 |
| family_and_marriage | core | 22 | 272 | 21.1% | 139 / 53 / 64 / 16 | 17.3 / 17.7 / 41.8 / 45.7 |
| philippine_political_landscape | subordinate | 16 | 238 | 18.4% | 166 / 45 / 24 / 3 | 20.7 / 15.1 / 15.7 / 8.6 |
| twin_beacons_doctrine | anchor | 27 | 213 | 16.5% | 108 / 44 / 57 / 4 | 13.4 / 14.7 / 37.3 / 11.4 |
| rule_of_law | anchor | 30 | 211 | 16.4% | 134 / 40 / 31 / 6 | 16.7 / 13.4 / 20.3 / 17.1 |
| with_due_respect_persona | anchor | 10 | 197 | 15.3% | 108 / 79 / 9 / 1 | 13.4 / 26.4 / 5.9 / 2.9 |
| impeachment_accountability | subordinate | 5 | 171 | 13.3% | 122 / 42 / 5 / 2 | 15.2 / 14.0 / 3.3 / 5.7 |
| icc_and_duterte | subordinate | 16 | 156 | 12.1% | 145 / 2 / 9 / 0 | 18.1 / 0.7 / 5.9 / 0.0 |
| mentors_and_legal_lineage | core | 16 | 156 | 12.1% | 71 / 36 / 39 / 10 | 8.8 / 12.0 / 25.5 / 28.6 |
| due_process | core | 8 | 145 | 11.2% | 95 / 43 / 6 / 1 | 11.8 / 14.4 / 3.9 / 2.9 |
| flp_donors_and_partners | subordinate | 19 | 143 | 11.1% | 78 / 20 / 42 / 3 | 9.7 / 6.7 / 27.5 / 8.6 |
| foundation_for_liberty_and_prosperity | anchor | 25 | 136 | 10.5% | 91 / 0 / 43 / 2 | 11.3 / 0.0 / 28.1 / 5.7 |
| bar_exam_and_legal_education | subordinate | 20 | 132 | 10.2% | 57 / 31 / 39 / 5 | 7.1 / 10.4 / 25.5 / 14.3 |
| jbc_discernment_and_appointment | subordinate | 5 | 110 | 8.5% | 54 / 34 / 13 / 9 | 6.7 / 11.4 / 8.5 / 25.7 |
| eulogies_and_passing | subordinate | 15 | 109 | 8.4% | 65 / 16 / 24 / 4 | 8.1 / 5.4 / 15.7 / 11.4 |
| flp_scholarship_programs | core | 19 | 109 | 8.4% | 55 / 11 / 34 / 9 | 6.8 / 3.7 / 22.2 / 25.7 |
| judicial_reform | core | 6 | 106 | 8.2% | 31 / 51 / 24 / 0 | 3.9 / 17.1 / 15.7 / 0.0 |
| ai_and_technology | subordinate | 11 | 99 | 7.7% | 59 / 27 / 13 / 0 | 7.3 / 9.0 / 8.5 / 0.0 |
| early_life_sampaloc | subordinate | 14 | 87 | 6.7% | 32 / 13 / 30 / 12 | 4.0 / 4.3 / 19.6 / 34.3 |
| global_geopolitics | subordinate | 10 | 83 | 6.4% | 78 / 2 / 3 / 0 | 9.7 / 0.7 / 2.0 / 0.0 |
| international_law_disputes | core | 15 | 78 | 6.0% | 68 / 1 / 8 / 1 | 8.5 / 0.3 / 5.2 / 2.9 |
| judicial_activism_and_political_question | subordinate | 5 | 78 | 6.0% | 40 / 21 / 15 / 2 | 5.0 / 7.0 / 9.8 / 5.7 |
| friendships_and_civic_circles | subordinate | 12 | 76 | 5.9% | 30 / 16 / 21 / 9 | 3.7 / 5.4 / 13.7 / 25.7 |
| msme_and_entrepreneurship | core | 11 | 47 | 3.6% | 22 / 8 / 15 / 2 | 2.7 / 2.7 / 9.8 / 5.7 |
| lawyer_ethics_initiative | subordinate | 4 | 47 | 3.6% | 26 / 15 / 5 / 1 | 3.2 / 5.0 / 3.3 / 2.9 |
| economic_governance_and_business_law | core | 7 | 43 | 3.3% | 16 / 10 / 17 / 0 | 2.0 / 3.3 / 11.1 / 0.0 |
| asean_law_association | subordinate | 4 | 39 | 3.0% | 21 / 4 / 14 / 0 | 2.6 / 1.3 / 9.2 / 0.0 |
| death_penalty_and_echegaray | subordinate | 1 | 30 | 2.3% | 10 / 17 / 1 / 2 | 1.2 / 5.7 / 0.7 / 5.7 |
| eez_resource_sovereignty | subordinate | 7 | 29 | 2.2% | 17 / 9 / 3 / 0 | 2.1 / 3.0 / 2.0 / 0.0 |
| honors_received | subordinate | 2 | 24 | 1.9% | 7 / 10 / 5 / 2 | 0.9 / 3.3 / 3.3 / 5.7 |
| museum_for_liberty_and_prosperity | core | 10 | 20 | 1.6% | 11 / 0 / 8 / 1 | 1.4 / 0.0 / 5.2 / 2.9 |
| prosperity_fund_msme | core | 5 | 13 | 1.0% | 7 / 0 / 6 / 0 | 0.9 / 0.0 / 3.9 / 0.0 |
| robot_identity_meta | meta | 0 | 0 | 0.0% | 0 / 0 / 0 / 0 | 0.0 / 0.0 / 0.0 / 0.0 |

Topics claiming more than 25% of the corpus (`TOPIC_OVER_BROAD_FRAC`): **2** — constitutional_doctrine, supreme_court_history.

### 4b. Documents that score zero against every topic

| format | docs | score zero | % of format's docs |
|---|---:|---:|---:|
| columns | 803 | 25 | 3.1% |
| books | 299 | 13 | 4.3% |
| speeches | 153 | 7 | 4.6% |
| biography | 35 | 1 | 2.9% |
| **all** | 1290 | 46 | 3.6% |

**Restricted to the two formats these matchers have never seen:** book chapters 13 of 299 (4.3%); biography chapters 1 of 35 (2.9%); together 14 of 334 (4.2%).

**How weak is the zero test?** Distribution of each document's *best* matcher score (a single incidental keyword hit is enough to be “covered”):

| best matcher score | columns | books | speeches | biography |
|---|---:|---:|---:|---:|
| 0 (orphan by this test) | 3.1% | 4.3% | 4.6% | 2.9% |
| 1 (one keyword hit) | 15.6% | 18.1% | 6.5% | 14.3% |
| 2 | 32.8% | 37.8% | 21.6% | 20.0% |
| 3 or more | 48.6% | 39.8% | 67.3% | 62.9% |

**Is the enrichment prose the reason?** A natural guess is that the haystack's long prose fields (`one_paragraph_summary`, `primary_topics`, `sub_topics`) hand every document an incidental hit. Tested directly by re-scoring every document with those fields removed (`ce7_00_haystack_counterfactual.py`):

| haystack | documents scoring zero | of which (col / book / spe / bio) | documents with best score ≤ 1 |
|---|---:|---:|---:|
| full haystack (as the matchers actually run) | 46 (3.6%) | 25 / 13 / 7 / 1 | 240 |
| minus one_paragraph_summary | 52 (4.0%) | 31 / 13 / 7 / 1 | 246 |
| minus primary_topics + sub_topics | 49 (3.8%) | 25 / 15 / 8 / 1 | 256 |
| minus all three prose fields | 66 (5.1%) | 39 / 16 / 9 / 2 | 298 |

**The guess is wrong.** Removing all three prose fields moves the zero-score count only from 46 to 66 (5.1% of the corpus). The prose is not why so few documents score zero. The matchers are simply broad: one hit on any of 300 matcher terms (word-boundary, anywhere in title, keywords, entities, register markers or prose) is enough to count a document as covered.

**The zero test is therefore an insensitive orphan detector.** The embedding-based curves in step 5 are the better read of coverage, and Line 1 clusters both the strict zero set and two broader populations.

## Step 5 — provisional centroids for the 34 prior-art topics, over the new corpus

Recipe = production recipe (unit-normalised mean of every chunk of every member document). Zero-member topics fall back to the global mean vector and are flagged.

| topic | docs | chunks | fallback | thin (docs) | thin (chunks) |
|---|---:|---:|---|---|---|
| robot_identity_meta | 0 | 0 | **gmean fallback** | **< 10 docs** | **< 3 chunks** |
| museum_for_liberty_and_prosperity | 20 | 196 |  |  |  |
| honors_received | 24 | 377 |  |  |  |
| eez_resource_sovereignty | 29 | 460 |  |  |  |
| death_penalty_and_echegaray | 30 | 821 |  |  |  |
| asean_law_association | 39 | 354 |  |  |  |
| economic_governance_and_business_law | 43 | 541 |  |  |  |
| msme_and_entrepreneurship+prosperity_fund_msme | 47 | 541 |  |  |  |
| lawyer_ethics_initiative | 47 | 511 |  |  |  |
| friendships_and_civic_circles | 76 | 823 |  |  |  |
| international_law_disputes | 78 | 634 |  |  |  |
| judicial_activism_and_political_question | 78 | 1075 |  |  |  |
| global_geopolitics | 83 | 689 |  |  |  |
| early_life_sampaloc | 87 | 901 |  |  |  |
| ai_and_technology | 99 | 1324 |  |  |  |
| judicial_reform | 106 | 1312 |  |  |  |
| eulogies_and_passing | 109 | 1186 |  |  |  |
| flp_scholarship_programs | 109 | 1107 |  |  |  |
| jbc_discernment_and_appointment | 110 | 1196 |  |  |  |
| bar_exam_and_legal_education | 132 | 1509 |  |  |  |
| foundation_for_liberty_and_prosperity | 136 | 1243 |  |  |  |
| flp_donors_and_partners | 143 | 1533 |  |  |  |
| due_process | 145 | 2063 |  |  |  |
| icc_and_duterte | 156 | 1188 |  |  |  |
| mentors_and_legal_lineage | 156 | 1946 |  |  |  |
| impeachment_accountability | 171 | 2079 |  |  |  |
| with_due_respect_persona | 197 | 1672 |  |  |  |
| rule_of_law | 211 | 2146 |  |  |  |
| twin_beacons_doctrine | 213 | 2175 |  |  |  |
| philippine_political_landscape | 238 | 2225 |  |  |  |
| family_and_marriage | 272 | 2823 |  |  |  |
| faith_journey | 298 | 3552 |  |  |  |
| supreme_court_history | 406 | 5416 |  |  |  |
| constitutional_doctrine | 611 | 6587 |  |  |  |

**Under 10 documents or under 3 chunks at 1,290 scale: 1 topic(s)** — robot_identity_meta.

### 5a. Provisional vs the stored v1 centroids (same topic, same recipe, corpus grown 1,104 → 1,290 docs)

cosine(stored v1 centroid, provisional centroid) per topic: min 0.8322, median 0.9720, max 0.9987. Lowest five: death_penalty_and_echegaray 0.8322, judicial_reform 0.9228, lawyer_ethics_initiative 0.9375, ai_and_technology 0.9437, jbc_discernment_and_appointment 0.9455.

### 5b. Pairwise cosine between the provisional centroids

*Excluded from the pair statistics:* **robot_identity_meta** has no member documents, so its “centroid” is the global mean vector. Its cosine to the other topics (0.928–0.996) only measures how far each topic lies from the corpus mean.

Raw cosine over the 528 pairs of the 33 non-fallback topics: mean **0.9649**, median 0.9694, min 0.8614, max 0.9978 (the stored v1 centroids over the same topics: mean 0.9325; the v1 meta records 0.9334 for its 34).

**Pairs above `TOPIC_MERGE_COSINE` = 0.95 (raw): 417 of 528.**

| cosine (raw) | topic A | topic B |
|---:|---|---|
| 0.9978 | constitutional_doctrine | supreme_court_history |
| 0.9965 | due_process | supreme_court_history |
| 0.9959 | constitutional_doctrine | impeachment_accountability |
| 0.9959 | foundation_for_liberty_and_prosperity | flp_donors_and_partners |
| 0.9957 | family_and_marriage | eulogies_and_passing |
| 0.9957 | family_and_marriage | faith_journey |
| 0.9956 | mentors_and_legal_lineage | eulogies_and_passing |
| 0.9953 | constitutional_doctrine | judicial_activism_and_political_question |
| 0.9952 | twin_beacons_doctrine | flp_donors_and_partners |
| 0.9948 | twin_beacons_doctrine | msme_and_entrepreneurship+prosperity_fund_msme |
| 0.9947 | constitutional_doctrine | due_process |
| 0.9946 | mentors_and_legal_lineage | faith_journey |
| 0.9945 | supreme_court_history | impeachment_accountability |
| 0.9941 | supreme_court_history | judicial_activism_and_political_question |
| 0.9941 | bar_exam_and_legal_education | eulogies_and_passing |

(the 15 highest of 417 shown; the full list is in `ce7_analysis/cache/ce7_cov.json`.)

Applying the project's union-find merge at 0.95 on raw cosine would collapse the 33 non-fallback provisional centroids to **1** topic(s). (In Phase 5 the independence check is an explicit stop criterion if it does this.)

**What does a raw cosine of 0.95 mean in this space?** Centroids are means over many chunks, so they all lean toward the corpus-wide mean direction. Baseline: cosine between the centroids of two *independent random* document groups (60 draws each), raw and centered:

| docs per random group | raw: mean cosine of two random groups | raw min | raw 95th pct | raw: mean cosine to the global mean | centered: mean | centered: 95th pct | centered: max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.9550 | 0.9182 | 0.9705 | 0.9787 | -0.040 | 0.206 | 0.450 |
| 30 | 0.9846 | 0.9674 | 0.9891 | 0.9925 | 0.019 | 0.282 | 0.369 |
| 100 | 0.9954 | 0.9925 | 0.9969 | 0.9977 | 0.020 | 0.322 | 0.420 |

Two independent random 30-document groups sit at raw mean 0.985; the prior-art topic pairs sit at raw mean 0.965. A raw cosine above 0.95 is therefore what *unrelated* document groups produce, and cannot mark a rephrase. After the corpus mean is removed, unrelated groups fall to a centered mean of 0.019 (95th percentile 0.282) — that is the scale on which a duplicate becomes visible.

**Centered cosine, prior-art pairs:** mean 0.0896, median 0.0722, max 0.9525; pairs above 0.95 centered: **1**. Highest ten by centered cosine:

| centered cosine | raw cosine | topic A | topic B |
|---:|---:|---|---|
| 0.9525 | 0.9959 | foundation_for_liberty_and_prosperity | flp_donors_and_partners |
| 0.9333 | 0.9931 | twin_beacons_doctrine | foundation_for_liberty_and_prosperity |
| 0.9296 | 0.9933 | flp_scholarship_programs | flp_donors_and_partners |
| 0.9285 | 0.9855 | foundation_for_liberty_and_prosperity | museum_for_liberty_and_prosperity |
| 0.9257 | 0.9870 | early_life_sampaloc | eulogies_and_passing |
| 0.9064 | 0.9781 | msme_and_entrepreneurship+prosperity_fund_msme | museum_for_liberty_and_prosperity |
| 0.9051 | 0.9933 | foundation_for_liberty_and_prosperity | flp_scholarship_programs |
| 0.8976 | 0.9856 | family_and_marriage | early_life_sampaloc |
| 0.8917 | 0.9931 | foundation_for_liberty_and_prosperity | msme_and_entrepreneurship+prosperity_fund_msme |
| 0.8853 | 0.9750 | museum_for_liberty_and_prosperity | flp_donors_and_partners |


### 5c. Effect of the chunk skew on the centroids themselves

The production recipe weights every *chunk* equally, so a topic with many book members is pulled toward book prose. Re-computing each centroid with every *document* weighted equally and comparing to the production one: cosine min 0.9917, median 0.9988. Topics most shifted by the weighting: honors_received (0.9917, 24 docs), eez_resource_sovereignty (0.9928, 29 docs), death_penalty_and_echegaray (0.9939, 30 docs), ai_and_technology (0.9964, 99 docs), impeachment_accountability (0.9976, 171 docs), msme_and_entrepreneurship+prosperity_fund_msme (0.9978, 47 docs).

### 5d. Orphan-rate curve — share of documents below the floor, 0.55 → 0.80 in 0.01 steps

Three definitions, because they disagree, and the disagreement is itself the skew hazard:
* **A — best-chunk (the project's definition).** A document is an orphan when *no* chunk reaches the floor for *any* topic. A document with 18 chunks has 18 chances to clear it; one with 7 has 7.
* **B — document mean vector.** Cosine of the document's mean chunk vector to each centroid. Length-neutral.
* **C — chunk level.** Share of *chunks* below the floor (carries the 1.78× book skew in its denominator).

**A_best_chunk (project definition)**

| floor | all | columns | books | speeches | biography |
|---:|---:|---:|---:|---:|---:|
| 0.55 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.56 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.57 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.58 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.59 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.60 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.61 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.62 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.63 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.64 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.65 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.66 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.67 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.68 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.69 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.70 | 0.3% | 0.5% | 0.0% | 0.0% | 0.0% |
| 0.71 | 0.4% | 0.6% | 0.0% | 0.0% | 0.0% |
| 0.72 | 0.5% | 0.7% | 0.0% | 0.0% | 0.0% |
| 0.73 | 1.1% | 1.7% | 0.0% | 0.0% | 0.0% |
| 0.74 | 1.5% | 2.1% | 0.3% | 0.7% | 0.0% |
| 0.75 | 2.5% | 3.5% | 0.7% | 1.3% | 0.0% |
| 0.76 | 4.0% | 5.9% | 0.7% | 1.3% | 0.0% |
| 0.77 | 6.0% | 8.6% | 1.7% | 2.6% | 0.0% |
| 0.78 | 10.3% | 13.6% | 3.3% | 7.2% | 8.6% |
| 0.79 | 15.3% | 19.4% | 5.4% | 12.4% | 20.0% |
| 0.80 | 22.4% | 28.6% | 7.4% | 16.3% | 34.3% |

**B_doc_mean_vector (length-neutral)**

| floor | all | columns | books | speeches | biography |
|---:|---:|---:|---:|---:|---:|
| 0.55 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.56 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.57 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.58 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.59 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.60 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.61 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.62 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.63 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.64 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.65 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.66 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.67 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.68 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.69 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.70 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.71 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.72 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.73 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.74 | 0.2% | 0.4% | 0.0% | 0.0% | 0.0% |
| 0.75 | 0.2% | 0.4% | 0.0% | 0.0% | 0.0% |
| 0.76 | 0.4% | 0.6% | 0.0% | 0.0% | 0.0% |
| 0.77 | 0.6% | 1.0% | 0.0% | 0.0% | 0.0% |
| 0.78 | 1.1% | 1.6% | 0.0% | 0.7% | 0.0% |
| 0.79 | 1.6% | 2.2% | 0.0% | 1.3% | 0.0% |
| 0.80 | 2.5% | 3.4% | 0.3% | 2.6% | 0.0% |

**C_chunk_level**

| floor | all | columns | books | speeches | biography |
|---:|---:|---:|---:|---:|---:|
| 0.55 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.56 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.57 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.58 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.59 | 0.0% | 0.1% | 0.0% | 0.0% | 0.0% |
| 0.60 | 0.1% | 0.1% | 0.1% | 0.0% | 0.0% |
| 0.61 | 0.2% | 0.2% | 0.2% | 0.0% | 0.5% |
| 0.62 | 0.3% | 0.4% | 0.3% | 0.1% | 0.8% |
| 0.63 | 0.4% | 0.6% | 0.4% | 0.1% | 0.8% |
| 0.64 | 0.7% | 0.8% | 0.6% | 0.4% | 1.0% |
| 0.65 | 1.0% | 1.0% | 1.0% | 0.7% | 1.3% |
| 0.66 | 1.5% | 1.6% | 1.4% | 1.0% | 1.8% |
| 0.67 | 2.1% | 2.3% | 1.9% | 1.9% | 2.0% |
| 0.68 | 2.9% | 3.4% | 2.4% | 2.5% | 3.3% |
| 0.69 | 4.3% | 4.9% | 3.6% | 3.8% | 5.9% |
| 0.70 | 6.0% | 6.9% | 4.9% | 5.3% | 9.2% |
| 0.71 | 8.1% | 9.4% | 6.5% | 7.5% | 13.0% |
| 0.72 | 11.1% | 12.8% | 8.9% | 10.2% | 17.6% |
| 0.73 | 15.0% | 17.8% | 11.6% | 13.9% | 24.6% |
| 0.74 | 19.9% | 23.3% | 15.8% | 17.7% | 34.5% |
| 0.75 | 25.7% | 29.6% | 21.0% | 22.7% | 44.0% |
| 0.76 | 32.5% | 37.2% | 27.0% | 29.0% | 52.9% |
| 0.77 | 40.7% | 45.5% | 34.9% | 37.5% | 61.6% |
| 0.78 | 49.5% | 54.9% | 43.4% | 45.2% | 68.3% |
| 0.79 | 58.8% | 63.8% | 53.2% | 53.8% | 77.0% |
| 0.80 | 68.0% | 73.0% | 62.7% | 62.9% | 84.1% |

**Supplementary sweep above 0.80** (the prescribed range ends at 0.80; shown so the whole shape of each curve is visible, every second step):

*A_best_chunk (project definition)*

| floor | all | columns | books | speeches | biography |
|---:|---:|---:|---:|---:|---:|
| 0.81 | 31.8% | 39.9% | 12.7% | 21.6% | 54.3% |
| 0.83 | 56.0% | 66.6% | 29.8% | 45.8% | 82.9% |
| 0.85 | 81.9% | 89.8% | 64.9% | 71.2% | 94.3% |
| 0.87 | 96.2% | 98.6% | 94.0% | 86.9% | 100.0% |
| 0.89 | 99.7% | 100.0% | 99.3% | 98.7% | 100.0% |
| 0.91 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.93 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.95 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

*B_doc_mean_vector (length-neutral)*

| floor | all | columns | books | speeches | biography |
|---:|---:|---:|---:|---:|---:|
| 0.81 | 3.8% | 5.1% | 0.3% | 3.9% | 2.9% |
| 0.83 | 8.7% | 10.2% | 3.0% | 8.5% | 22.9% |
| 0.85 | 19.5% | 22.5% | 8.7% | 19.6% | 40.0% |
| 0.87 | 37.1% | 44.3% | 20.4% | 27.5% | 57.1% |
| 0.89 | 59.8% | 68.4% | 39.8% | 51.0% | 74.3% |
| 0.91 | 82.8% | 90.0% | 66.2% | 75.2% | 91.4% |
| 0.93 | 93.7% | 98.9% | 81.3% | 89.5% | 100.0% |
| 0.95 | 97.6% | 100.0% | 90.6% | 98.0% | 100.0% |

### 5e. Re-deriving the floor

Two independent readings. (1) **Where the curve leaves zero / its knee** (kneedle over the full 0.55–0.96 sweep). (2) **Agreement with the matchers as weak labels**: documents scoring zero on every matcher are treated as orphans and documents with best score ≥ 2 as covered; for each floor, Youden's J = TPR − FPR. The labels are noisy (the matchers are the weak instrument this rebuild is replacing), and per-format positives are tiny, so treat (2) as a cross-check on (1), not as ground truth.

| definition | scope | weak-orphans (zero score) | weak-covered (score ≥ 2) | Youden-optimal floor | J | orphans caught | covered wrongly orphaned |
|---|---|---:|---:|---:|---:|---:|---:|
| A best-chunk | all | 46 | 1050 | 0.780 | 0.25 | 33% | 8% |
| A best-chunk | columns | 25 | 653 | 0.780 | 0.46 | 56% | 10% |
| A best-chunk | books | 13 | 232 | 0.860 | 0.04 | 85% | 80% |
| A best-chunk | speeches | 7 | 136 | 0.820 | 0.68 | 100% | 32% |
| A best-chunk | biography | 1 | 29 | too few | - | - | - |
| B doc-mean | all | 46 | 1050 | 0.885 | 0.39 | 87% | 48% |
| B doc-mean | columns | 25 | 653 | 0.845 | 0.45 | 60% | 15% |
| B doc-mean | books | 13 | 232 | 0.880 | 0.52 | 77% | 25% |
| B doc-mean | speeches | 7 | 136 | 0.880 | 0.67 | 100% | 33% |
| B doc-mean | biography | 1 | 29 | too few | - | - | - |

Knee of each curve (kneedle, full sweep):

| definition | scope | knee floor |
|---|---|---:|
| A_best_chunk (project definition) | all | 0.77 |
| A_best_chunk (project definition) | columns | 0.76 |
| A_best_chunk (project definition) | books | 0.80 |
| A_best_chunk (project definition) | speeches | 0.77 |
| A_best_chunk (project definition) | biography | 0.77 |
| B_doc_mean_vector (length-neutral) | all | 0.82 |
| B_doc_mean_vector (length-neutral) | columns | 0.82 |
| B_doc_mean_vector (length-neutral) | books | 0.84 |
| B_doc_mean_vector (length-neutral) | speeches | 0.82 |
| B_doc_mean_vector (length-neutral) | biography | 0.80 |

Floor at which each curve first exceeds a given orphan share:

| definition | scope | > 1% orphaned | > 5% | > 25% | > 50% |
|---|---|---:|---:|---:|---:|
| A best-chunk | all | 0.73 | 0.77 | 0.81 | 0.83 |
| A best-chunk | columns | 0.73 | 0.76 | 0.80 | 0.82 |
| A best-chunk | books | 0.77 | 0.79 | 0.83 | 0.85 |
| A best-chunk | speeches | 0.75 | 0.78 | 0.82 | 0.84 |
| A best-chunk | biography | 0.78 | 0.78 | 0.80 | 0.81 |
| B doc-mean | all | 0.78 | 0.82 | 0.86 | 0.89 |
| B doc-mean | columns | 0.78 | 0.81 | 0.86 | 0.88 |
| B doc-mean | books | 0.82 | 0.85 | 0.88 | 0.90 |
| B doc-mean | speeches | 0.79 | 0.82 | 0.86 | 0.89 |
| B doc-mean | biography | 0.81 | 0.82 | 0.84 | 0.86 |

**Known-orphan validation** (the v1 meta's own check: GC006 and CA330 should fall below a working floor):

| doc | title | nearest (A, best-chunk) | nearest (B, doc-mean) | nearest topic | best matcher score |
|---|---|---:|---:|---|---:|
| GC006 | Independence by Design | 0.7929 | 0.8297 | early_life_sampaloc | 1 |
| CA330 | Overdue process? | 0.8193 | 0.8728 | due_process | 5 |

### 5f. Where documents actually sit

| definition | scope | q01 | q05 | q25 | q50 | q75 | q95 |
|---|---|---:|---:|---:|---:|---:|---:|
| A best-chunk | all | 0.730 | 0.767 | 0.803 | 0.824 | 0.844 | 0.866 |
| A best-chunk | columns | 0.726 | 0.757 | 0.796 | 0.818 | 0.837 | 0.856 |
| A best-chunk | books | 0.766 | 0.789 | 0.824 | 0.841 | 0.855 | 0.871 |
| A best-chunk | speeches | 0.754 | 0.775 | 0.812 | 0.835 | 0.854 | 0.881 |
| A best-chunk | biography | 0.771 | 0.773 | 0.795 | 0.808 | 0.821 | 0.848 |
| B doc-mean | all | 0.779 | 0.815 | 0.858 | 0.882 | 0.902 | 0.937 |
| B doc-mean | columns | 0.771 | 0.809 | 0.854 | 0.875 | 0.895 | 0.920 |
| B doc-mean | books | 0.822 | 0.843 | 0.875 | 0.898 | 0.922 | 0.960 |
| B doc-mean | speeches | 0.790 | 0.817 | 0.858 | 0.890 | 0.908 | 0.939 |
| B doc-mean | biography | 0.807 | 0.812 | 0.839 | 0.858 | 0.890 | 0.917 |

Read against the 0.68 floor: it orphans **0.0%** of documents under definition A and **0.0%** under B (per format A / B: columns 0.0% / 0.0%; books 0.0% / 0.0%; speeches 0.0% / 0.0%; biography 0.0% / 0.0%). The known-orphan table above shows where v1's own reference orphans sit relative to it.

### 5g. Recommended floor — derived from the curves above (for the current provisional centroids)

Rule: take the **knee** of each orphan-rate curve (where the share of orphaned documents starts to climb steeply) as the floor, then cross-check it against the weak-label optimum. The floor is a property of the centroid set it was measured against, so this is the floor for *these 34 provisional centroids*; it must be re-derived against the v2 centroids in Phase 5.

| scope | A best-chunk: knee | A: weak-label optimum | share orphaned at the A knee | B doc-mean: knee | B: weak-label optimum | share orphaned at the B knee |
|---|---:|---:|---:|---:|---:|---:|
| all | 0.77 | 0.78 | 6.0% | 0.82 | 0.89 | 6.0% |
| columns | 0.76 | 0.78 | 5.9% | 0.82 | 0.84 | 7.5% |
| books | 0.80 | 0.86 | 7.4% | 0.84 | 0.88 | 4.7% |
| speeches | 0.77 | 0.82 | 2.6% | 0.82 | 0.88 | 5.9% |
| biography | 0.77 | n/a | 0.0% | 0.80 | n/a | 0.0% |

**Recommendation.** The inherited floor of 0.68 orphans 0.0% (A) and 0.0% (B) of documents — it is inert and should not be carried forward. On the project's own best-chunk definition (A) the curve turns at **0.77** overall (columns 0.76, books 0.80, speeches 0.77, biography 0.77); on the length-neutral document-mean definition (B) it turns at **0.82** overall (columns 0.82, books 0.84, speeches 0.82, biography 0.80). Books need a floor about 0.04 (A) / 0.02 (B) higher than columns to be orphaned at the same rate, so **a single global floor is format-biased**: it flags columns first. A per-format floor, or a floor expressed as a within-format percentile, removes that bias; the choice is Phase 4's. Weak-label cross-check: all disagrees on B (knee 0.82 vs optimum 0.89); columns agrees on B (knee 0.82 vs optimum 0.84); books agrees on B (knee 0.84 vs optimum 0.88); speeches disagrees on B (knee 0.82 vs optimum 0.88); too few weak-label positives to test: biography. The optimum runs higher than the knee wherever it can be computed, so it corroborates the direction, not the exact value.

