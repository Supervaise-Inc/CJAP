# CE-7 · steps 9–10 — candidate separation, viability, and the degenerate prior-art topics

**Date** 2026-09-26. **This report does not choose a topic count.** It states what each candidate is, whether it is viable, and what it duplicates.

## Candidate set

* **Line 1 — orphan clusters** (step 6): P0 (strict zero set) at k=11 and k=4; P2 (format-fair embedding orphans) at k=12. P1 is not used: it is indistinguishable from random documents.
* **Line 2 — curated keywords** (step 7): the 14 values in ≥ 15 documents that no prior-art matcher catches. (Sensitivity: 26 further values reach 10–14 documents; listed at the end, not used.) The literal `primary_topics`/`sub_topics` route produced no candidates (they are prose), and prose phrases produced only chance-level enrichment, so neither contributes.
* **Line 3 — per-work coverage** (step 8) is evidence about the candidates above, not a separate source: see `ce7_per_work_coverage_2026-09-26.md`.
* **Comparators:** the 33 non-fallback prior-art centroids, rebuilt over the 1,290-document corpus (step 5). robot_identity_meta has no members and is excluded from every comparison.

## Line 2 evidence — enrichment vocabulary (step 7)

Full data: `ce7_enrichment_vocabulary_2026-09-26.csv`. Per-document counts only, so this evidence is **immune to the chunk skew**. The prompt gives this line the most weight because the curators wrote it by hand, document by document.

**What the prompt asked for returns nothing, and why.** `primary_topics` and `sub_topics` hold one-sentence prose items, not tags:

| field | distinct values | median length (chars) | most documents sharing one value | values in ≥ 2 docs | ≥ 5 | ≥ 10 | **≥ 15** |
|---|---:|---:|---:|---:|---:|---:|---:|
| primary_topics | 6375 | 122 | 1 | 0 | 0 | 0 | **0** |
| sub_topics | 19332 | 106 | 2 | 11 | 0 | 0 | **0** |

**Zero values reach 15 documents.** Counting exact values in these two fields cannot produce a vocabulary. Two adaptations follow, kept separate and labelled:

**B — the `keywords` field (the `Keyword/s` column), the curators' short-tag vocabulary.** 13,086 distinct values; **30 appear in ≥ 15 documents** (63 in ≥ 10; 272 in ≥ 5). **14 of the 30 are not caught by any prior-art matcher** (the matcher fires on the value string itself). All 30, with the per-format share of *that format's own documents*:

| value | docs | docs col / book / spe / bio | % of each format's own docs (col / book / spe / bio) | book works | caught by prior art? | share of its docs weakly covered | 3 exemplars |
|---|---:|---:|---:|---:|---|---:|---|
| supreme court | 75 | 30 / 45 / 0 / 0 | 3.7 / 15.1 / 0.0 / 0.0 | 2 | **no** | 16% | `BA006`, `BA005`, `CA429` |
| rule of law | 57 | 43 / 13 / 1 / 0 | 5.4 / 4.3 / 0.7 / 0.0 | 4 | yes — rule_of_law | 23% | `CA432`, `BB027`, `BA084` |
| 1987 constitution | 55 | 8 / 45 / 2 / 0 | 1.0 / 15.1 / 1.3 / 0.0 | 5 | yes — constitutional_doctrine | 0% | `BD054`, `BA005`, `BA006` |
| grave abuse of discretion | 50 | 6 / 44 / 0 / 0 | 0.7 / 14.7 / 0.0 / 0.0 | 11 | **no** | 16% | `BB027`, `BD059`, `BB028` |
| liberty and prosperity | 40 | 19 / 20 / 1 / 0 | 2.4 / 6.7 / 0.7 / 0.0 | 3 | yes — twin_beacons_doctrine | 10% | `BD056`, `BD059`, `BD060` |
| gloria macapagal-arroyo | 32 | 1 / 31 / 0 / 0 | 0.1 / 10.4 / 0.0 / 0.0 | 3 | yes — philippine_political_landscape | 0% | `BE003`, `BA036`, `BE005` |
| due process | 29 | 17 / 12 / 0 / 0 | 2.1 / 4.0 / 0.0 / 0.0 | 7 | yes — due_process | 28% | `BA032`, `BA041`, `BA037` |
| integrity | 27 | 0 / 27 / 0 / 0 | 0.0 / 9.0 / 0.0 / 0.0 | 5 | **no** | 11% | `BA005`, `BD002`, `BD008` |
| sandiganbayan | 26 | 17 / 9 / 0 / 0 | 2.1 / 3.0 / 0.0 / 0.0 | 6 | **no** | 23% | `CA410`, `BB019`, `CA374` |
| a centenary of justice | 24 | 0 / 24 / 0 / 0 | 0.0 / 8.0 / 0.0 / 0.0 | 2 | yes — supreme_court_history | 17% | `BA032`, `BD045`, `BD013` |
| transparency | 24 | 1 / 23 / 0 / 0 | 0.1 / 7.7 / 0.0 / 0.0 | 7 | **no** | 21% | `BB031`, `BD045`, `BE008` |
| hilario g. davide jr. | 23 | 0 / 23 / 0 / 0 | 0.0 / 7.7 / 0.0 / 0.0 | 7 | **no** | 17% | `BD059`, `BD053`, `BD064` |
| jovito r. salonga | 22 | 0 / 19 / 2 / 1 | 0.0 / 6.4 / 1.3 / 2.9 | 7 | yes — mentors_and_legal_lineage | 0% | `BD054`, `BC045`, `BC039` |
| judicial independence | 22 | 11 / 11 / 0 / 0 | 1.4 / 3.7 / 0.0 / 0.0 | 7 | **no** | 18% | `BB027`, `BA084`, `BD028` |
| reynato s. puno | 21 | 0 / 21 / 0 / 0 | 0.0 / 7.0 / 0.0 / 0.0 | 9 | **no** | 19% | `BA032`, `BA036`, `BB013` |
| fidel v. ramos | 20 | 2 / 17 / 0 / 1 | 0.2 / 5.7 / 0.0 / 2.9 | 8 | **no** | 5% | `BD070`, `BC045`, `BD045` |
| impeachment | 20 | 9 / 11 / 0 / 0 | 1.1 / 3.7 / 0.0 / 0.0 | 3 | yes — impeachment_accountability | 5% | `BA036`, `BA093`, `BA005` |
| separation of powers | 19 | 5 / 13 / 1 / 0 | 0.6 / 4.3 / 0.7 / 0.0 | 6 | yes — constitutional_doctrine | 10% | `BA084`, `BB027`, `BD053` |
| constitution | 18 | 18 / 0 / 0 / 0 | 2.2 / 0.0 / 0.0 / 0.0 | 0 | **no** | 22% | `CA430`, `CA429`, `CA022` |
| vicente v. mendoza | 18 | 1 / 17 / 0 / 0 | 0.1 / 5.7 / 0.0 / 0.0 | 7 | **no** | 11% | `BA032`, `BA080`, `BA091` |
| four ins | 17 | 4 / 12 / 1 / 0 | 0.5 / 4.0 / 0.7 / 0.0 | 2 | yes — judicial_reform | 6% | `BD059`, `BD054`, `BD064` |
| judicial reform | 17 | 8 / 9 / 0 / 0 | 1.0 / 3.0 / 0.0 / 0.0 | 4 | yes — judicial_reform | 41% | `BD013`, `CA432`, `BD004` |
| ombudsman | 17 | 8 / 8 / 1 / 0 | 1.0 / 2.7 / 0.7 / 0.0 | 2 | **no** | 29% | `CA435`, `CA436`, `BE009` |
| people power | 17 | 3 / 14 / 0 / 0 | 0.4 / 4.7 / 0.0 / 0.0 | 5 | **no** | 0% | `BA032`, `BE003`, `BA036` |
| rotary club of manila | 17 | 2 / 11 / 1 / 3 | 0.2 / 3.7 / 0.7 / 8.6 | 3 | yes — friendships_and_civic_circles | 0% | `SC014`, `BC023`, `BC045` |
| tan yan kee foundation | 16 | 11 / 0 / 5 / 0 | 1.4 / 0.0 / 3.3 / 0.0 | 0 | yes — flp_donors_and_partners | 0% | `SD016`, `SD060`, `CB003` |
| action program for judicial reform | 15 | 1 / 13 / 1 / 0 | 0.1 / 4.3 / 0.7 / 0.0 | 5 | yes — judicial_reform | 0% | `BD064`, `BD039`, `BD067` |
| bukas loob sa diyos | 15 | 1 / 9 / 3 / 2 | 0.1 / 3.0 / 2.0 / 5.7 | 5 | yes — faith_journey | 0% | `BC045`, `BC030`, `BC028` |
| congress | 15 | 2 / 13 / 0 / 0 | 0.2 / 4.3 / 0.0 / 0.0 | 1 | **no** | 0% | `BA006`, `BA001`, `BD005` |
| flp | 15 | 14 / 0 / 1 / 0 | 1.7 / 0.0 / 0.7 / 0.0 | 0 | yes — foundation_for_liberty_and_prosperity | 0% | `CD017`, `CA433`, `CB018` |

**Format shape.** 21 of the 30 values are at least 3× more prevalent (as a share of documents) among book chapters than among columns; 5 occur in no column at all. Of the 21 book-skewed values, 10 have most of their book chapters in the eight works new to this batch and 11 in the four earlier works. This is a *document-level* fact, not a chunk-count artefact.

**C — phrases extracted from the two prose fields** (3,688 one-to-three-word phrases in 15 or more documents but no more than a quarter of the corpus). Two findings, both against using them as candidates:

1. The matcher string test does not discriminate: 3,612 of 3,688 phrases are “uncaught”, because a matcher term is a multi-word phrase and rarely sits inside another short phrase. It cannot be the filter.
2. A better filter — phrases whose documents are *disproportionately weakly covered* (best matcher score ≤ 1; baseline share 18.6%) — is indistinguishable from chance. Each row compares the number of phrases passing the filter with the number that pass when the weak-coverage labels are **shuffled across documents** (300 shuffles):

| filter (weak share ≥ m × baseline, ≥ 8 weak docs) | phrases passing (observed) | passing under shuffled labels: mean | 95th percentile | max |
|---|---:|---:|---:|---:|
| m = 1.5 | 108 | 155.9 | 214.1 | 273 |
| m = 2.0 | 24 | 25.7 | 40.1 | 51 |
| m = 2.5 | 5 | 4.7 | 9.0 | 12 |

The observed counts sit at or below what shuffled labels produce, and the phrases that do pass are incoherent single words (“manual”, “voter”, “damages”, “perfect”, “massive”). **Prose phrases contribute no candidate dimensions.** They remain in the CSV, flagged, for anyone who wants to look.

## Minimum size — and why

**Minima: 10 distinct documents and 3 chunks** — the same thresholds step 5 uses to flag a prior-art topic as thin. Justification, measured rather than asserted: draw two *disjoint* random subsets of n documents from a coherent pool and compare their centered centroids. If a group of n documents has a stable direction, two such groups from the same pool agree far more than two groups from unrelated pools.

| pool type | docs per subset (n) | pools | pairs drawn | same-pool agreement: median (centered cosine) | same-pool: 10th pct | unrelated: median | unrelated: 95th pct | median beats unrelated 95th pct? | 10th pct beats it? |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| matcher-defined prior-art topics | 3 | 8 | 96 | 0.067 | -0.130 | -0.011 | 0.243 | no | no |
| matcher-defined prior-art topics | 5 | 8 | 96 | 0.135 | -0.121 | -0.015 | 0.220 | no | no |
| matcher-defined prior-art topics | 8 | 8 | 96 | 0.228 | -0.061 | 0.007 | 0.262 | no | no |
| matcher-defined prior-art topics | 10 | 8 | 96 | 0.288 | -0.038 | 0.008 | 0.259 | yes | no |
| matcher-defined prior-art topics | 15 | 8 | 96 | 0.341 | 0.077 | -0.021 | 0.257 | yes | no |
| matcher-defined prior-art topics | 20 | 8 | 96 | 0.392 | 0.122 | 0.013 | 0.238 | yes | no |
| matcher-defined prior-art topics | 30 | 8 | 96 | 0.533 | 0.293 | -0.010 | 0.226 | yes | yes |
| curated-keyword groups | 3 | 5 | 60 | 0.212 | -0.000 | -0.011 | 0.243 | no | no |
| curated-keyword groups | 5 | 5 | 60 | 0.341 | 0.087 | -0.015 | 0.220 | yes | no |
| curated-keyword groups | 8 | 5 | 60 | 0.410 | 0.015 | 0.007 | 0.262 | yes | no |
| curated-keyword groups | 10 | 5 | 60 | 0.470 | 0.163 | 0.008 | 0.259 | yes | no |
| curated-keyword groups | 15 | 5 | 60 | 0.562 | 0.217 | -0.021 | 0.257 | yes | no |
| curated-keyword groups | 20 | 5 | 60 | 0.570 | 0.369 | 0.013 | 0.238 | yes | yes |
| curated-keyword groups | 30 | 5 | 12 | 0.689 | 0.598 | -0.010 | 0.226 | yes | yes |

**Reading.** Criterion 1 — the *median* same-pool pair agrees more than the 95th percentile of unrelated pairs — is first met at n = 10 (matcher-defined prior-art topics); 5 (curated-keyword groups). Criterion 2 — even the weak 10th-percentile pair beats that bar — is first met at n = 30 (matcher-defined prior-art topics); 20 (curated-keyword groups). The prompt-derived minimum of 10 documents is therefore supported on criterion 1 (conservative reading: the larger of the two pool types, n = 10); below 10, groups drawn from broad pools have no stable direction of their own (curated groups already do at 5, so 10 is the smallest size that holds for both). For the stricter tail criterion 20–30 documents are needed, so **a candidate with 10–19 documents is viable but marginal** and is marked so below. The 3-chunk minimum is a floor on the centroid's raw material (a centroid from fewer than 3 chunks is one passage) and is never binding once 10 documents are present.

## Viability

| candidate | source | docs | chunks | docs by format (col / book / spe / bio) | viability |
|---|---|---:|---:|---:|---|
| orphan P0 k=11 · c4 | 1 orphan cluster | 7 | 50 | 7 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c2 | 1 orphan cluster | 6 | 44 | 5 / 0 / 1 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c3 | 1 orphan cluster | 6 | 58 | 2 / 3 / 0 / 1 | drop (< 10 docs) |
| orphan P0 k=11 · c6 | 1 orphan cluster | 5 | 30 | 1 / 1 / 3 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c10 | 1 orphan cluster | 5 | 145 | 2 / 3 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c9 | 1 orphan cluster | 4 | 93 | 0 / 4 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c11 | 1 orphan cluster | 4 | 76 | 1 / 2 / 1 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c1 | 1 orphan cluster | 3 | 20 | 3 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c5 | 1 orphan cluster | 2 | 18 | 2 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c7 | 1 orphan cluster | 2 | 16 | 0 / 0 / 2 / 0 | drop (< 10 docs) |
| orphan P0 k=11 · c8 | 1 orphan cluster | 2 | 15 | 2 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=4 · c1 | 1 orphan cluster | 30 | 456 | 13 / 12 / 4 / 1 | **keep** |
| orphan P0 k=4 · c2 | 1 orphan cluster | 8 | 58 | 8 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P0 k=4 · c4 | 1 orphan cluster | 5 | 30 | 1 / 1 / 3 / 0 | drop (< 10 docs) |
| orphan P0 k=4 · c3 | 1 orphan cluster | 3 | 21 | 3 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P2 k=12 · c2 | 1 orphan cluster | 22 | 172 | 3 / 12 / 5 / 2 | **keep** |
| orphan P2 k=12 · c4 | 1 orphan cluster | 17 | 126 | 16 / 1 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c1 | 1 orphan cluster | 14 | 140 | 9 / 5 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c7 | 1 orphan cluster | 13 | 90 | 11 / 2 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c8 | 1 orphan cluster | 11 | 88 | 6 / 1 / 3 / 1 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c3 | 1 orphan cluster | 10 | 159 | 6 / 4 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c10 | 1 orphan cluster | 10 | 67 | 6 / 1 / 2 / 1 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c12 | 1 orphan cluster | 10 | 79 | 7 / 3 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| orphan P2 k=12 · c5 | 1 orphan cluster | 9 | 74 | 3 / 0 / 6 / 0 | drop (< 10 docs) |
| orphan P2 k=12 · c9 | 1 orphan cluster | 7 | 59 | 6 / 1 / 0 / 0 | drop (< 10 docs) |
| orphan P2 k=12 · c11 | 1 orphan cluster | 5 | 33 | 5 / 0 / 0 / 0 | drop (< 10 docs) |
| orphan P2 k=12 · c6 | 1 orphan cluster | 3 | 21 | 3 / 0 / 0 / 0 | drop (< 10 docs) |
| kw · supreme court | 2 keyword (≥15 docs, uncaught) | 75 | 565 | 30 / 45 / 0 / 0 | **keep** |
| kw · congress | 2 keyword (≥15 docs, uncaught) | 15 | 115 | 2 / 13 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| kw · grave abuse of discretion | 2 keyword (≥15 docs, uncaught) | 50 | 1080 | 6 / 44 / 0 / 0 | **keep** |
| kw · judicial independence | 2 keyword (≥15 docs, uncaught) | 22 | 243 | 11 / 11 / 0 / 0 | **keep** |
| kw · integrity | 2 keyword (≥15 docs, uncaught) | 27 | 259 | 0 / 27 / 0 / 0 | **keep** |
| kw · reynato s. puno | 2 keyword (≥15 docs, uncaught) | 21 | 624 | 0 / 21 / 0 / 0 | **keep** |
| kw · ombudsman | 2 keyword (≥15 docs, uncaught) | 17 | 146 | 8 / 8 / 1 / 0 | **keep** (marginal: 10–19 docs) |
| kw · sandiganbayan | 2 keyword (≥15 docs, uncaught) | 26 | 347 | 17 / 9 / 0 / 0 | **keep** |
| kw · vicente v. mendoza | 2 keyword (≥15 docs, uncaught) | 18 | 556 | 1 / 17 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| kw · transparency | 2 keyword (≥15 docs, uncaught) | 24 | 313 | 1 / 23 / 0 / 0 | **keep** |
| kw · fidel v. ramos | 2 keyword (≥15 docs, uncaught) | 20 | 296 | 2 / 17 / 0 / 1 | **keep** |
| kw · people power | 2 keyword (≥15 docs, uncaught) | 17 | 320 | 3 / 14 / 0 / 0 | **keep** (marginal: 10–19 docs) |
| kw · hilario g. davide jr. | 2 keyword (≥15 docs, uncaught) | 23 | 488 | 0 / 23 / 0 / 0 | **keep** |
| kw · constitution | 2 keyword (≥15 docs, uncaught) | 18 | 146 | 18 / 0 / 0 / 0 | **keep** (marginal: 10–19 docs) |

**23 of 41 candidates meet the minima; 18 are dropped.** Dropped by source: 1 orphan cluster 18; 2 keyword (≥15 docs, uncaught) 0.

## Separation

Two scales, because they answer different questions. **Raw cosine** is the project's own scale and the one `TOPIC_MERGE_COSINE` = 0.95 is defined on; step 5 showed that unrelated random document groups already reach 0.955–0.995 on it, so a raw score above the threshold is *not* evidence of a rephrase. **Centered cosine** (corpus mean removed) is the scale on which unrelated groups sit near 0 (95th percentile ≈ 0.3, maximum 0.45 across 60 draws), so it is the scale on which a duplicate is visible. **Document overlap** (Jaccard of the two member sets) is an independent third check that does not depend on the embedding at all.

A candidate is called a **rephrase** here only when *both* hold: centered cosine ≥ 0.80 (well above every unrelated-group draw) and document overlap Jaccard ≥ 0.30. Anything above `TOPIC_MERGE_COSINE` on raw cosine is reported separately, as the prompt requires, but see the note above on what that flag means in this space.

### Viable candidates against the 33 prior-art centroids and against each other

| candidate | docs | nearest prior-art topic, centered (cosine / doc-overlap J) | nearest prior-art topic, raw (cosine) | prior-art topics above raw 0.95 | relation to the nearest prior-art topic | nearest other candidate, centered (cosine / J) | relation to it |
|---|---|---|---:|---|---|---|---|
| orphan P0 k=4 · c1 | 30 | death_penalty_and_echegaray (0.47 / J 0.00) | ai_and_technology (0.970) | 13 | distinct | orphan P2 k=12 · c3 (0.83 / J 0.05) | **same direction, different documents** |
| orphan P2 k=12 · c2 | 22 | faith_journey (0.84 / J 0.06) | faith_journey (0.930) | 0 | **same direction as faith_journey, different documents** | kw · fidel v. ramos (0.44 / J 0.00) | distinct |
| orphan P2 k=12 · c4 | 17 | eez_resource_sovereignty (0.25 / J 0.00) | constitutional_doctrine (0.936) | 0 | distinct | orphan P2 k=12 · c8 (0.29 / J 0.00) | distinct |
| orphan P2 k=12 · c1 | 14 | due_process (0.51 / J 0.01) | due_process (0.963) | 4 | distinct | kw · grave abuse of discretion (0.52 / J 0.02) | distinct |
| orphan P2 k=12 · c7 | 13 | with_due_respect_persona (0.44 / J 0.02) | with_due_respect_persona (0.931) | 0 | distinct | kw · supreme court (0.28 / J 0.00) | distinct |
| orphan P2 k=12 · c8 | 11 | friendships_and_civic_circles (0.67 / J 0.01) | friendships_and_civic_circles (0.940) | 0 | distinct | orphan P2 k=12 · c12 (0.54 / J 0.00) | distinct |
| orphan P2 k=12 · c3 | 10 | death_penalty_and_echegaray (0.43 / J 0.00) | death_penalty_and_echegaray (0.908) | 0 | distinct | orphan P0 k=4 · c1 (0.83 / J 0.05) | **same direction, different documents** |
| orphan P2 k=12 · c10 | 10 | lawyer_ethics_initiative (0.17 / J 0.00) | constitutional_doctrine (0.953) | 3 | distinct | kw · constitution (0.27 / J 0.04) | distinct |
| orphan P2 k=12 · c12 | 10 | international_law_disputes (0.48 / J 0.02) | international_law_disputes (0.932) | 0 | distinct | orphan P2 k=12 · c8 (0.54 / J 0.00) | distinct |
| kw · supreme court | 75 | with_due_respect_persona (0.78 / J 0.20) | with_due_respect_persona (0.995) | 25 | distinct | kw · congress (0.84 / J 0.15) | **same direction, different documents** |
| kw · congress | 15 | with_due_respect_persona (0.68 / J 0.07) | with_due_respect_persona (0.980) | 15 | distinct | kw · supreme court (0.84 / J 0.15) | **same direction, different documents** |
| kw · grave abuse of discretion | 50 | supreme_court_history (0.76 / J 0.07) | due_process (0.990) | 21 | distinct | kw · reynato s. puno (0.80 / J 0.06) | distinct |
| kw · judicial independence | 22 | honors_received (0.61 / J 0.02) | honors_received (0.984) | 21 | distinct | kw · hilario g. davide jr. (0.74 / J 0.05) | distinct |
| kw · integrity | 27 | jbc_discernment_and_appointment (0.66 / J 0.08) | jbc_discernment_and_appointment (0.982) | 23 | distinct | kw · transparency (0.51 / J 0.16) | distinct |
| kw · reynato s. puno | 21 | supreme_court_history (0.81 / J 0.03) | supreme_court_history (0.993) | 22 | **same direction as supreme_court_history, different documents** | kw · vicente v. mendoza (0.86 / J 0.18) | **same direction, different documents** |
| kw · ombudsman | 17 | with_due_respect_persona (0.50 / J 0.03) | with_due_respect_persona (0.984) | 19 | distinct | kw · supreme court (0.41 / J 0.02) | distinct |
| kw · sandiganbayan | 26 | due_process (0.61 / J 0.05) | due_process (0.986) | 18 | distinct | kw · ombudsman (0.40 / J 0.05) | distinct |
| kw · vicente v. mendoza | 18 | supreme_court_history (0.76 / J 0.04) | supreme_court_history (0.988) | 20 | distinct | kw · reynato s. puno (0.86 / J 0.18) | **same direction, different documents** |
| kw · transparency | 24 | honors_received (0.46 / J 0.00) | honors_received (0.983) | 25 | distinct | kw · integrity (0.51 / J 0.16) | distinct |
| kw · fidel v. ramos | 20 | faith_journey (0.61 / J 0.04) | faith_journey (0.989) | 30 | distinct | kw · integrity (0.48 / J 0.04) | distinct |
| kw · people power | 17 | judicial_activism_and_political_question (0.40 / J 0.04) | constitutional_doctrine (0.988) | 29 | distinct | kw · vicente v. mendoza (0.31 / J 0.03) | distinct |
| kw · hilario g. davide jr. | 23 | judicial_reform (0.80 / J 0.12) | judicial_reform (0.992) | 25 | **same direction as judicial_reform, different documents** | kw · judicial independence (0.74 / J 0.05) | distinct |
| kw · constitution | 18 | constitutional_doctrine (0.47 / J 0.02) | constitutional_doctrine (0.988) | 25 | distinct | kw · supreme court (0.41 / J 0.16) | distinct |

**Summary.** Of 23 viable candidates: **0** are rephrases of a prior-art topic (centered ≥ 0.80 *and* document overlap ≥ 0.30); **3** point in the *same direction* as a prior-art topic but with different documents (centered ≥ 0.80, overlap < 0.30: orphan P2 k=12 · c2 → faith_journey (0.84, J 0.06), kw · reynato s. puno → supreme_court_history (0.81, J 0.03), kw · hilario g. davide jr. → judicial_reform (0.80, J 0.12)). That second category matters: the prior-art *topic* may be right while its *matcher* misses the documents, which is a coverage failure, not a duplicate. Among the candidates themselves, 0 are rephrases of another candidate and 6 have a same-direction, different-document neighbour. **17** exceed raw 0.95 against at least one prior-art centroid (the prompt's literal test) — median number of prior-art topics above raw 0.95 per candidate: 19 of 33, which is why the raw test cannot be used to decide.

Nearest-prior-art centered cosine over the viable candidates: min 0.17, median 0.61, max 0.84. Candidates with nearest centered cosine below 0.5 have no close prior-art neighbour: orphan P0 k=4 · c1, orphan P2 k=12 · c4, orphan P2 k=12 · c7, orphan P2 k=12 · c3, orphan P2 k=12 · c10, orphan P2 k=12 · c12, kw · transparency, kw · people power, kw · constitution.

### Closest candidate pairs (centered scale)

| centered cosine | doc-overlap J | candidate A | candidate B |
|---:|---:|---|---|
| 0.862 | 0.18 | kw · reynato s. puno | kw · vicente v. mendoza |
| 0.839 | 0.15 | kw · supreme court | kw · congress |
| 0.832 | 0.05 | orphan P0 k=4 · c1 | orphan P2 k=12 · c3 |
| 0.798 | 0.06 | kw · grave abuse of discretion | kw · reynato s. puno |
| 0.742 | 0.05 | kw · judicial independence | kw · hilario g. davide jr. |
| 0.682 | 0.03 | kw · grave abuse of discretion | kw · vicente v. mendoza |
| 0.537 | 0.00 | orphan P2 k=12 · c8 | orphan P2 k=12 · c12 |
| 0.518 | 0.02 | orphan P2 k=12 · c1 | kw · grave abuse of discretion |
| 0.510 | 0.16 | kw · integrity | kw · transparency |
| 0.503 | 0.05 | kw · judicial independence | kw · transparency |
| 0.494 | 0.00 | kw · transparency | kw · hilario g. davide jr. |
| 0.487 | 0.00 | orphan P2 k=12 · c1 | kw · reynato s. puno |

### For reference: the prior-art topics against each other on the same scales

| centered cosine | doc-overlap J | topic A | topic B |
|---:|---:|---|---|
| 0.952 | 0.36 | foundation_for_liberty_and_prosperity | flp_donors_and_partners |
| 0.933 | 0.60 | twin_beacons_doctrine | foundation_for_liberty_and_prosperity |
| 0.930 | 0.32 | flp_scholarship_programs | flp_donors_and_partners |
| 0.928 | 0.15 | foundation_for_liberty_and_prosperity | museum_for_liberty_and_prosperity |
| 0.926 | 0.17 | early_life_sampaloc | eulogies_and_passing |
| 0.906 | 0.37 | msme_and_entrepreneurship+prosperity_fund_msme | museum_for_liberty_and_prosperity |
| 0.905 | 0.38 | foundation_for_liberty_and_prosperity | flp_scholarship_programs |
| 0.898 | 0.15 | family_and_marriage | early_life_sampaloc |
| 0.892 | 0.18 | foundation_for_liberty_and_prosperity | msme_and_entrepreneurship+prosperity_fund_msme |
| 0.885 | 0.09 | museum_for_liberty_and_prosperity | flp_donors_and_partners |
| 0.879 | 0.23 | mentors_and_legal_lineage | early_life_sampaloc |
| 0.875 | 0.14 | twin_beacons_doctrine | msme_and_entrepreneurship+prosperity_fund_msme |

On the centered scale 29 prior-art pairs reach 0.80, and 5 of those also overlap ≥ 0.30 in documents — the prior-art rephrases by the same two-part test: foundation_for_liberty_and_prosperity ~ flp_donors_and_partners (0.95, J 0.36); twin_beacons_doctrine ~ foundation_for_liberty_and_prosperity (0.93, J 0.60); flp_scholarship_programs ~ flp_donors_and_partners (0.93, J 0.32); msme_and_entrepreneurship+prosperity_fund_msme ~ museum_for_liberty_and_prosperity (0.91, J 0.37); foundation_for_liberty_and_prosperity ~ flp_scholarship_programs (0.91, J 0.38).

## Step 10 — the three degenerate prior-art topics

Evidence at 1,290 documents (matcher membership, production centroid recipe), against the 79-document counts the topic map was generated from. Three separate questions, because passing one does not answer the others: (1) do the members share a *direction*? (2) does that direction have anything to do with the topic's *label*? (3) *why* did the matcher select them?

| topic | docs @79 | docs @1,290 | chunks | docs by format (col / book / spe / bio) | (1) coherence: members vs same-size random groups | (3) members selected by ONE matcher term | (2) members whose title or keywords mention the topic's subject | nearest prior-art topics, centered |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| robot_identity_meta | 0 | 0 | 0 | 0 / 0 / 0 / 0 | - | - | - | - |
| honors_received | 2 | 24 | 377 | 7 / 10 / 5 / 2 | 0.297 vs 0.212 (p95 0.238) | 33% | 10 of 24 (42%) | jbc_discernment_and_appointment 0.61; judicial_reform 0.56; bar_exam_and_legal_education 0.40 |
| death_penalty_and_echegaray | 1 | 30 | 821 | 10 / 17 / 1 / 2 | 0.337 vs 0.190 (p95 0.231) | 67% | 18 of 30 (60%) | supreme_court_history 0.44; due_process 0.41; impeachment_accountability 0.32 |

*Coherence* asks whether the members share a direction beyond chance. It does **not** say the direction is the topic: a set of documents can be coherent because they are all about the judiciary while the matcher picked them for an unrelated word. Column (2) counts members whose own title or curated keywords mention the topic's subject; column (3) is the share of members the matcher selected on a single term.

### `robot_identity_meta`

* **0 member documents and 0 chunks at 1,290 scale** (also 0 at 79). Its centroid is the global mean vector, the same fallback used for any memberless topic, so a routing cosine against it measures how ordinary a query is, not how close it is to a subject.
* Tier `meta`: Questions about whether this is the real CJP, an AI, a robot, or how it works. Answered fully in persona as Chief Justice Panganiban himself — gracious, lightly amused, never describing himself as an AI, robot,
* Corpus evidence that looks *related*: 8 document(s) mention robots or AI in the title or keywords: `CA031` Partners in rule of law, constitutionalism, AI; `CA034` AI in justice and governance; `CD011` Celebrating AIM and AI management; `CE011` Robotics, for better or for worse; `CE018` AI and the freedom to ask; `CE019` AI can create value and build trust. Curated-keyword values (>= 5 docs) containing 'robot' or 'artificial intelligence': 'artificial intelligence' x7. Read their titles: they are columns about robotics and AI as a subject, not the persona speaking about its own identity, which is what this topic's definition covers. That is a routing intent, not a corpus dimension.

### `honors_received`

* **(1) Direction.** 24 member documents, 377 chunks; formats (col / book / spe / bio) 7 / 10 / 5 / 2; books by work: Battles in the Supreme Court x2; Justice and Faith x2; Reforming the Judiciary x2; Transparency, Unanimity & Diversity x2; With Due Respect x1. Coherence 0.297 vs 0.212 for random groups of 24 (95th percentile 0.238): **more coherent than chance**.
* **(2) Label.** 10 of 24 members (42%) mention the topic's subject in their own title or keywords. Nearest prior-art topics (centered): jbc_discernment_and_appointment 0.61; judicial_reform 0.56; bar_exam_and_legal_education 0.40.
* **(3) Why the matcher selected them.** Matcher terms that fire (documents): 'manila overseas press club' x9; 'Manila Overseas Press Club' x9; 'bantayog' x8; 'Bantayog ng mga Bayani' x8; 'honorary doctorate' x8; 'haligi' x2. 8 of 24 members (33%) were selected on a single term.
* Exemplars (nearest the members' centre): `BD020` Justice and Faith -- Ch. 1: On Developing My Decision-Writin; `BD054` Judicial Renaissance -- Ch. 9: Judging the Judges; `BD028` Battles in the Supreme Court -- Ch. 1: A WINDOW TO THE COURT; `BD035` Transparency, Unanimity & Diversity -- Ch. 1: Problems and S; `GC033` Chapter 13: 21st Chief Justice of the Philippines
* **Read:** the members share a direction, but **that direction is not the topic's label**: fewer than half mention it. The matcher is selecting documents for incidental terms, and the coherence found is that of some other theme they have in common. Real content at this scale is *not* established for this label.

### `death_penalty_and_echegaray`

* **(1) Direction.** 30 member documents, 821 chunks; formats (col / book / spe / bio) 10 / 17 / 1 / 2; books by work: A Centenary of Justice x3; The Bio-Age Dawns on the Judiciary x2; Battles in the Supreme Court x2; Reforming the Judiciary x2; Leveling the Playing Field x2. Coherence 0.337 vs 0.190 for random groups of 30 (95th percentile 0.231): **more coherent than chance**.
* **(2) Label.** 18 of 30 members (60%) mention the topic's subject in their own title or keywords. Nearest prior-art topics (centered): supreme_court_history 0.44; due_process 0.41; impeachment_accountability 0.32.
* **(3) Why the matcher selected them.** Matcher terms that fire (documents): 'death penalty' x28; 'echegaray' x12; 'leo echegaray' x9. 20 of 30 members (67%) were selected on a single term.
* Exemplars (nearest the members' centre): `BA049` The Bio-Age Dawns on the Judiciary -- Ch. 14: Update on Deat; `BA092` Leveling the Playing Field -- Ch. 21: New Jurisprudence on C; `BA070` Transparency, Unanimity & Diversity -- Ch. 16: Death Penalty; `BA059` Leadership by Example: The Davide Standard -- Ch. 6: The Dea; `BA054` Battles in the Supreme Court -- Ch. 4: BATTLES OVER LIFE AND
* **Read:** the members share a direction *and* most mention the subject: a real, if narrow, dimension of the corpus.

### The byte-identical pair: `honors_received` and `robot_identity_meta`

At 79 documents both had no usable members, so both centroids fell back to the same global mean vector and were byte-identical: every query was *equally close* to both, and both leaked into secondary tags as if they were topics. What the measurements at 1,290 support:

* **`robot_identity_meta`**: still 0 documents and 0 chunks. Nothing in the corpus supports it as a corpus dimension. Its centroid is the global mean.
* **`honors_received`**: now 24 documents and 377 chunks, so the byte-identical fallback no longer applies to it. But only 10 of its 24 members mention honors in their title or keywords, and the matcher terms that select them are: 'manila overseas press club' x9; 'Manila Overseas Press Club' x9; 'bantayog' x8; 'Bantayog ng mga Bayani' x8. The topic is no longer degenerate in the numeric sense, and its semantic content is **not established**.
* **What the evidence supports:** (a) the two must never again share a centroid, and a memberless topic must not receive a fallback vector that competes in routing; (b) `robot_identity_meta` has no corpus content and belongs in the router's intent layer, outside the centroid set; (c) `honors_received` was not independently re-found by any of the three derivation lines (no orphan cluster, no curated keyword clears the threshold), so it should enter v2 only if a purpose-built matcher shows genuine honors content. Whether either survives is Phase 4's call.
* **`death_penalty_and_echegaray`**: now 30 documents / 821 chunks (1 document at 79), and 18 of 30 members (60%) mention its subject. It is real and narrow, and **book-dominated** (17 of 30 members are book chapters); the curated keywords 'death penalty', 'leo echegaray' and 'people v. echegaray' each appear in only 5 documents, below the 15-document threshold, so the vocabulary line alone would not have surfaced it.

## Sensitivity: candidates below the prompt's 15-document threshold

26 further uncaught curated keywords reach 10–14 documents: “commission on elections” (14), “philippine judicial academy” (14), “leveling the playing field” (14), “pork barrel” (14), “integrated bar of the philippines” (13), “plunder” (12), “jose c. vitug” (12), “salary standardization law” (12), “public trust” (11), “2007” (11), “verba legis” (11), “supreme court of the philippines” (10), “judicial” (10), “social justice” (10), “psychological incapacity” (10), “court of appeals” (10), “office of the solicitor general” (10), “second plenary council of the philippines” (10), “2001” (10), “tañada v. angara” (10), “ill-gotten wealth” (10), “party-list system” (10), “judicial renaissance” (10), “far eastern university” (10), “plague of ships” (10), “smartmatic” (10). Not used as candidates; listed so the threshold's effect is visible.

