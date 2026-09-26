# CE-7 · step 8 — per-work coverage

**Date** 2026-09-26. For each of the twelve works: which dimensions its chapters land on under three independent lenses, and how many chapters have **no home** under any of them. A work whose chapters have no home is evidence for a missing dimension, not a labelling problem.

## Lenses

1. **Prior-art matchers** (`_doc_haystack` + `score_topic`): a chapter is *matcher-zero* at best score 0 and *weak* at best score ≤ 1. The matchers are broad (step 4), so “landing on” a topic here says little; the counts of *weak* chapters say more.
2. **Embedding, centered scale.** Each chapter's mean chunk vector minus the corpus mean, compared with the prior-art centroids (also centered; step 5 showed that raw cosine cannot separate topics in this space). A chapter is *embedding-distant* when its nearest prior-art centroid is below the **books' own 10th percentile** (0.320) — a book-relative cut, so the format shift found in step 5 does not inflate the count.
3. **Candidate dimensions from lines 1–2:** the 14 curated keywords appearing in ≥ 15 documents that no prior-art matcher catches (step 7), and the orphan clusters (step 6: P0 at k=11, P2 at k=12).

**No home** = weak on the matchers (best score ≤ 1) **and** carries none of the uncaught-keyword candidates **and** is embedding-distant. All three conditions, so the count is conservative.

## Summary by work

| work | chapters | chunks | matcher-zero | weak (best score ≤ 1) | embedding-distant | carry ≥ 1 uncaught-keyword candidate | **no home** | nearest prior-art topic to the whole work (centered cosine) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| With Due Respect | 75 | 560 | 0 | 9 (12.0%) | 12 (16.0%) | 61 (81.3%) | 1 | with_due_respect_persona (0.77) |
| A Centenary of Justice | 23 | 584 | 0 | 4 (17.4%) | 1 (4.3%) | 19 (82.6%) | 0 | supreme_court_history (0.61) |
| The Bio-Age Dawns on the Judiciary | 20 | 588 | 10 | 17 (85.0%) | 5 (25.0%) | 5 (25.0%) | 4 | death_penalty_and_echegaray (0.55) |
| Justice and Faith | 14 | 275 | 0 | 1 (7.1%) | 0 (0.0%) | 7 (50.0%) | 0 | faith_journey (0.61) |
| Liberty and Prosperity **(new)** | 35 | 604 | 0 | 9 (25.7%) | 3 (8.6%) | 18 (51.4%) | 0 | judicial_activism_and_political_question (0.57) |
| Transparency, Unanimity & Diversity **(new)** | 24 | 589 | 0 | 4 (16.7%) | 2 (8.3%) | 8 (33.3%) | 0 | due_process (0.75) |
| Love God, Serve Man **(new)** | 22 | 309 | 1 | 3 (13.6%) | 2 (9.1%) | 4 (18.2%) | 0 | faith_journey (0.74) |
| Judicial Renaissance **(new)** | 21 | 527 | 0 | 3 (14.3%) | 0 (0.0%) | 14 (66.7%) | 0 | supreme_court_history (0.56) |
| Reforming the Judiciary **(new)** | 20 | 455 | 0 | 3 (15.0%) | 0 (0.0%) | 13 (65.0%) | 0 | supreme_court_history (0.68) |
| Leveling the Playing Field **(new)** | 20 | 478 | 0 | 6 (30.0%) | 2 (10.0%) | 12 (60.0%) | 1 | due_process (0.70) |
| Leadership by Example: The Davide Standard **(new)** | 14 | 327 | 1 | 5 (35.7%) | 3 (21.4%) | 7 (50.0%) | 1 | supreme_court_history (0.57) |
| Battles in the Supreme Court **(new)** | 11 | 303 | 1 | 3 (27.3%) | 0 (0.0%) | 5 (45.5%) | 0 | supreme_court_history (0.81) |

**Works with at least one matcher-zero chapter: 4 of 12** (The Bio-Age Dawns on the Judiciary, Love God, Serve Man, Battles in the Supreme Court, Leadership by Example: The Davide Standard). **Works with at least one chapter that has no home under all three lenses: 4 of 12.** Chapters with no home: 2 of 167 in the eight new works, 5 of 132 in the four earlier works. Chapters that are weak on the matchers: 36 of 167 (new) vs 31 of 132 (earlier).

## Where each work's chapters land

Per work: the prior-art topic each chapter is *nearest* to on the centered scale (hard assignment, counts), the uncaught-keyword candidates its chapters carry, and the orphan clusters it contributes to.

### With Due Respect — 75 chapters

* nearest prior-art topic per chapter (centered): with_due_respect_persona ×28; philippine_political_landscape ×9; jbc_discernment_and_appointment ×6; faith_journey ×5; due_process ×4 — top topic takes 37.3% of chapters
* uncaught-keyword candidates carried (chapters): “supreme court” ×43; “integrity” ×18; “congress” ×13; “transparency” ×11; “ombudsman” ×7; “people power” ×7
* orphan clusters contributed to: P2/k12.c12 ×3; P2/k12.c7 ×2; P2/k12.c2 ×2; P2/k12.c10 ×1
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): `BA010` Ch. 2: Legal Empowerment of the Poor

### A Centenary of Justice — 23 chapters

* nearest prior-art topic per chapter (centered): judicial_reform ×7; death_penalty_and_echegaray ×2; faith_journey ×2; supreme_court_history ×2; constitutional_doctrine ×2 — top topic takes 30.4% of chapters
* uncaught-keyword candidates carried (chapters): “vicente v. mendoza” ×6; “transparency” ×6; “integrity” ×5; “people power” ×4; “reynato s. puno” ×3; “grave abuse of discretion” ×2
* orphan clusters contributed to: none
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### The Bio-Age Dawns on the Judiciary — 20 chapters

* nearest prior-art topic per chapter (centered): death_penalty_and_echegaray ×5; ai_and_technology ×5; constitutional_doctrine ×2; impeachment_accountability ×1; supreme_court_history ×1 — top topic takes 25.0% of chapters
* uncaught-keyword candidates carried (chapters): “integrity” ×2; “grave abuse of discretion” ×1; “ombudsman” ×1; “hilario g. davide jr.” ×1; “transparency” ×1
* orphan clusters contributed to: P0/k11.c9 ×3; P0/k11.c10 ×3; P2/k12.c3 ×3; P0/k11.c11 ×2
* matcher-zero chapters: `BA042` Ch. 7: Socrates v. Comelec — The Three-Term Limi, `BA043` Ch. 8: Republic v. Meralco — Oral Argument, `BA045` Ch. 10: Agan v. Piatco — Validity of a BOT Contr, `BA046` Ch. 11: Ang Bagong Bayani v. Comelec — Party-Lis, `BA047` Ch. 12: Macalintal v. Comelec — Absentee Voting, `BA050` Appendix C: DNA as Evidence, `BD025` Ch. 5: Excellence and Ethics in Appellate Practi, `BD026` Ch. 6: Veracious and Venerable Magistrate, `BE028` Appendix B: GMO & Food Products, `BE029` Appendix D: Being Moral in the Brave New World
* **no home** (weak ∧ no keyword ∧ embedding-distant): `BA042` Ch. 7: Socrates v. Comelec — The Three-Term Limi, `BA043` Ch. 8: Republic v. Meralco — Oral Argument, `BA046` Ch. 11: Ang Bagong Bayani v. Comelec — Party-Lis, `BA047` Ch. 12: Macalintal v. Comelec — Absentee Voting

### Justice and Faith — 14 chapters

* nearest prior-art topic per chapter (centered): faith_journey ×5; honors_received ×2; due_process ×1; eez_resource_sovereignty ×1; jbc_discernment_and_appointment ×1 — top topic takes 35.7% of chapters
* uncaught-keyword candidates carried (chapters): “fidel v. ramos” ×3; “supreme court” ×2; “reynato s. puno” ×2; “vicente v. mendoza” ×2; “hilario g. davide jr.” ×2; “sandiganbayan” ×1
* orphan clusters contributed to: P2/k12.c2 ×5
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### Liberty and Prosperity (new) — 35 chapters

* nearest prior-art topic per chapter (centered): judicial_reform ×9; due_process ×6; supreme_court_history ×5; constitutional_doctrine ×4; eez_resource_sovereignty ×3 — top topic takes 25.7% of chapters
* uncaught-keyword candidates carried (chapters): “hilario g. davide jr.” ×9; “grave abuse of discretion” ×8; “fidel v. ramos” ×4; “people power” ×1; “judicial independence” ×1
* orphan clusters contributed to: P2/k12.c1 ×2; P2/k12.c4 ×1
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### Transparency, Unanimity & Diversity (new) — 24 chapters

* nearest prior-art topic per chapter (centered): due_process ×8; supreme_court_history ×4; constitutional_doctrine ×3; death_penalty_and_echegaray ×2; early_life_sampaloc ×2 — top topic takes 33.3% of chapters
* uncaught-keyword candidates carried (chapters): “reynato s. puno” ×3; “grave abuse of discretion” ×3; “vicente v. mendoza” ×2; “sandiganbayan” ×2; “fidel v. ramos” ×1; “integrity” ×1
* orphan clusters contributed to: P2/k12.c1 ×1
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### Love God, Serve Man (new) — 22 chapters

* nearest prior-art topic per chapter (centered): faith_journey ×11; friendships_and_civic_circles ×6; international_law_disputes ×1; lawyer_ethics_initiative ×1; eez_resource_sovereignty ×1 — top topic takes 50.0% of chapters
* uncaught-keyword candidates carried (chapters): “fidel v. ramos” ×3; “people power” ×1; “grave abuse of discretion” ×1
* orphan clusters contributed to: P2/k12.c2 ×5; P0/k11.c6 ×1; P2/k12.c8 ×1
* matcher-zero chapters: `BB010` Ch. 13: A Salute to ASTA
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### Judicial Renaissance (new) — 21 chapters

* nearest prior-art topic per chapter (centered): judicial_reform ×7; due_process ×6; eez_resource_sovereignty ×2; economic_governance_and_business_law ×2; honors_received ×2 — top topic takes 33.3% of chapters
* uncaught-keyword candidates carried (chapters): “grave abuse of discretion” ×7; “reynato s. puno” ×4; “hilario g. davide jr.” ×3; “transparency” ×1; “people power” ×1
* orphan clusters contributed to: none
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### Reforming the Judiciary (new) — 20 chapters

* nearest prior-art topic per chapter (centered): judicial_reform ×9; supreme_court_history ×3; due_process ×2; philippine_political_landscape ×1; constitutional_doctrine ×1 — top topic takes 45.0% of chapters
* uncaught-keyword candidates carried (chapters): “hilario g. davide jr.” ×4; “vicente v. mendoza” ×3; “sandiganbayan” ×3; “grave abuse of discretion” ×2; “reynato s. puno” ×2; “transparency” ×2
* orphan clusters contributed to: none
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

### Leveling the Playing Field (new) — 20 chapters

* nearest prior-art topic per chapter (centered): ai_and_technology ×4; judicial_activism_and_political_question ×3; due_process ×3; death_penalty_and_echegaray ×3; supreme_court_history ×2 — top topic takes 20.0% of chapters
* uncaught-keyword candidates carried (chapters): “grave abuse of discretion” ×10; “judicial independence” ×3; “hilario g. davide jr.” ×3; “sandiganbayan” ×1; “vicente v. mendoza” ×1; “reynato s. puno” ×1
* orphan clusters contributed to: P2/k12.c3 ×1
* matcher-zero chapters: none
* **no home** (weak ∧ no keyword ∧ embedding-distant): `BA085` Ch. 7: A Unique Mode of Nurturing Democracy

### Leadership by Example: The Davide Standard (new) — 14 chapters

* nearest prior-art topic per chapter (centered): due_process ×3; supreme_court_history ×2; honors_received ×2; jbc_discernment_and_appointment ×2; death_penalty_and_echegaray ×1 — top topic takes 21.4% of chapters
* uncaught-keyword candidates carried (chapters): “grave abuse of discretion” ×3; “vicente v. mendoza” ×2; “sandiganbayan” ×1; “reynato s. puno” ×1; “judicial independence” ×1; “integrity” ×1
* orphan clusters contributed to: P2/k12.c1 ×2; P0/k11.c9 ×1
* matcher-zero chapters: `BA064` Ch. 13: Upholding Popular Sovereignty in Electio
* **no home** (weak ∧ no keyword ∧ embedding-distant): `BA064` Ch. 13: Upholding Popular Sovereignty in Electio

### Battles in the Supreme Court (new) — 11 chapters

* nearest prior-art topic per chapter (centered): honors_received ×3; constitutional_doctrine ×2; supreme_court_history ×2; due_process ×2; death_penalty_and_echegaray ×1 — top topic takes 27.3% of chapters
* uncaught-keyword candidates carried (chapters): “grave abuse of discretion” ×3; “fidel v. ramos” ×2; “judicial independence” ×2; “reynato s. puno” ×1
* orphan clusters contributed to: P0/k11.c3 ×1
* matcher-zero chapters: `BD030` Ch. 11: Epilogue: THE REAL VICTORY
* **no home** (weak ∧ no keyword ∧ embedding-distant): none

## Reading

* The matchers place almost every chapter of every work somewhere, because a single incidental keyword hit is enough; the **weak** column is the honest measure of thin coverage.
* The centered-scale nearest-topic column shows whether a work is spread over the prior-art topics or piles onto one or two. A work whose chapters all share one nearest topic is being *absorbed* into it; that is either correct (the topic is genuinely about the work) or a sign the topic is too coarse — the exemplar titles decide which, and Phase 4 should read them.
* Uncaught-keyword candidates are curator-authored and skew toward the book formats (step 7). They are a mix of doctrinal terms, institutions and *people* (justices and presidents), so a chapter carrying one has a term the prior art does not name and the columns rarely use; whether that term is a *dimension* or just a proper name is a judgement for Phase 4, not something this count settles.

