# Taxonomy v2 — proposal (Phase 4 / CE-9)

**Status: PROPOSAL FOR SIGN-OFF. Nothing here is applied.** Branch `deliverable/2026-09` at `c8e58cc` when this was written. `scripts/build_topic_map.py`, `config.py`, `corpus/voice/topic_map.json` and `data/index/topic_centroids.npy` are untouched (verified at write time: scripts/build_topic_map.py ✓, config.py ✓, corpus/voice/topic_map.json ✓, data/index/topic_centroids.npy ✓); no document has been tagged. Every number below is written by `batch-04/ce7_analysis/ce9_14b_build.py` (with `ce9_14_assemble.py`) from measurements produced by the `ce9_*` scripts beside it (section 12). Similarity is on the **centred scale** throughout; no raw cosine is offered as evidence.

## 0. What you are asked to sign

**Recommended N = 30.** Chosen at the *medium* granularity (the tree cut into 33 clusters of at least 20 documents each) and then reduced by tests that only make sense once a dimension is *deployed* — built from the documents its own matcher catches, which is what the production recipe does:

* **−1** the business-leaders-and-philanthropy cluster is merged into the Foundation dimension: on deployed centroids they are 0.74–0.78 apart whatever the matcher (the donors *are* the business leaders). The Foundation dimension is now `foundation_for_liberty_and_prosperity`.
* **−3** three clusters could not be given a finished matcher and are not proposed: Public Officials' Duties and Data Privacy (23 docs); The Chief Justiceship and a Judicial Career (21 docs); Corporate Governance and Integrity (21 docs). The best readable term set catches 6, 0 and 4 of their documents. They are real in embedding space and invisible to the metadata the matchers read (section 10).
* **+1** `death_penalty_and_echegaray` is carried as a dimension of its own, as the brief said it survives: a 13-document fragment at the fine level, 30 documents by matcher. That forces criminal law's own matcher down to libel and cybercrime (`libel_and_cybercrime`). Against the 0.60 precision bar used for the others one lands just under and one just over (57% and 61%), and both beat the combined one-dimension version (54%) — section 5.

**The two thresholds** (section 7): `TOPIC_MERGE_COSINE = 0.75` (centred) and `TOPIC_ASSIGN_MIN_COSINE = 0.31` (centred, best-chunk, one global value).

**Sign-off is one line.** Copy this, delete any id you do not want, change either value if you disagree:

```
APPROVED: life_story_family_school_and_church, criminal_trials_and_prosecutions, international_law_disputes, property_contracts_and_economic_rights, how_the_supreme_court_decides, libel_and_cybercrime, presidential_power_martial_law_people_power, elections_and_automated_voting, judiciary_milestones_and_tributes, judicial_reform, party_list_charter_change_and_dynasties, science_technology_and_the_law, economy_taxes_and_prosperity, impeachment_accountability, foundation_for_liberty_and_prosperity, public_funds_budget_and_bank_evidence, us_supreme_court_and_american_politics, independent_commissions_and_appointments, twin_beacons_doctrine, marcos_robredo_election_contest, bangsamoro_peace_process, supreme_court_vacancies_and_chief_justiceship, faith_journey, asean_law_association, ill_gotten_wealth_and_the_pcgg, citizenship_and_residency_grace_poe, marriage_annulment_and_the_family_code, bar_exam_and_legal_education, jbc_discernment_and_appointment, death_penalty_and_echegaray | TOPIC_MERGE_COSINE=0.75 | TOPIC_ASSIGN_MIN_COSINE=0.31
```

**Read these before you sign — they are where this proposal is weakest:**

1. **Matchers are seeds, not classifiers.** A dimension's matcher catches a median of 66% of its own cluster, and a median of 54% of what it catches is inside that cluster. Its job is to give the centroid a clean set of members; everything else is tagged by centroid affinity. The figures here are in-sample; on unseen documents recall is lower (section 8). 6 dimensions rest on fewer than 25 caught documents: `how_the_supreme_court_decides` (21), `economy_taxes_and_prosperity` (17), `independent_commissions_and_appointments` (15), `asean_law_association` (11), `citizenship_and_residency_grace_poe` (24), `bar_exam_and_legal_education` (20).
2. **Separability has thin margins.** No pair of dimensions reaches 0.70 on deployed centroids, but the three closest sit at 0.68–0.69: `life_story_family_school_and_church` ↔ `faith_journey` **0.69**, `supreme_court_vacancies_and_chief_justiceship` ↔ `jbc_discernment_and_appointment` **0.69**, `life_story_family_school_and_church` ↔ `foundation_for_liberty_and_prosperity` **0.68**. That is why the recommended merge gate is 0.75, not 0.70 (section 7).
3. **Biography is the one format I cannot call finished.** At the recommended floor 3 of 35 biography chapters are orphaned (8.6%) against 3.6% overall. With n = 35 that is not statistically distinguishable from the rest (Fisher p = 0.13), but all three are judicial-career chapters of the kind the unbuilt chief-justiceship cluster would hold. Decide whether to ship with those three or hold until biography chapters carry a discriminating tag (section 9).
4. **Two of the brief's expectations came out differently.** `death_penalty_and_echegaray` survives, but only as a marginal dimension (above). The Puno pool that Phase 3 read as "same direction as `supreme_court_history`" is *not* a dimension: its 21 chapters are all books and spread over 11 dimensions (section 5). `robot_identity_meta` moves to the router, as the brief said.
5. **The code has to change with the metric** (section 11): the merge gate and the floor are only meaningful on centred vectors, so `build_centroids_fullcorpus.py`, `merge_tag_topics.py` and — the part most likely to be missed — the runtime `retrieval.route()` all need the corpus mean vector. `build_topic_map.load_docs()` also never reads `corpus/books/`.

## 1. Why the v1 merge gate collapsed the taxonomy (P3.3)

**The P3.3 collapse is explained, and it was not the topics.** The merge gate `TOPIC_MERGE_COSINE = 0.95` was applied to *raw* cosine between centroids, and in this embedding space raw cosine is below the noise floor. Reproduced by `ce9_00b_p33.py` from the *stored, untouched* v1 centroids:

* **The collapse re-runs exactly.** 220 of the 561 pairs of the 34 stored centroids have raw cosine above 0.95; the archived run recorded 220 merged pairs; union-find over them leaves **3 topics** (3 recorded, from 34).
* **Random document groups clear the gate.** Two independent random 30-document groups sit at raw cosine **0.984** (lowest of 600 pairs: 0.962) — above 0.95 every time. (Phase 3's own run of the same test: 0.985.) The stored v1 centroids sit at median 0.942 (mean 0.933, min 0.753) — *below* what random groups produce, so the gate fires on 39% of all pairs of genuinely different topics.
* **No raw threshold rescues it.** Raising the gate leaves 3 topics at 0.96, 5 at 0.97, 10 at 0.98, 26 at 0.99, and all 34 only when nothing can merge (1.01). Every raw value that keeps a plausible number of topics is above the level random groups reach.
* **On the centred scale the same random groups are unrelated**: mean -0.027, 95th percentile 0.243, maximum 0.422 (Phase 3: 0.019 / 0.282 / 0.369, same test, slightly different group construction).

Raw cosine in this space is dominated by a component shared by every chunk (the corpus mean); centring removes it. This is the whole explanation of the 34 → 3 collapse, and it is why every separability figure below is on the centred scale and no raw figure is offered as evidence.

## 2. Method

1. **Centred scale.** `mu` = the mean of all 13,549 chunk vectors; every vector below is `unit(v − mu)`. A dimension's centroid is `unit(mean of all chunks of its member documents − mu)` — the production recipe (`build_centroids_fullcorpus.py`) on the centred scale. A document's affinity to a dimension is either *best-chunk* (max over its chunks) or *document-mean*; both are reported.
2. **Derivation from the whole corpus, not only the orphans.** Ward linkage on the 1,290 centred document-mean vectors (803 columns, 299 book chapters, 153 speeches, 35 biography chapters). The structure is real and weak: document-level silhouette 0.059–0.098 across every cut from k=8 to k=54, against -0.001–0.002 when the feature columns are shuffled; bootstrap adjusted-Rand 0.42–0.52. All of it sits well below the 0.20 ceiling Phase 3 reported. **There is no natural N**; N is a granularity choice and is presented as one (section 3).
3. **A granularity family with one knob.** Start from the k=54 cut. Repeatedly (a) merge the closest pair if its centred centroid cosine is ≥ 0.70 (a duplicate at the working line of 0.70 used to build the family; section 7 explains why the config gate is higher), else (b) fold the smallest cluster below *m* documents into its nearest neighbour. *m* alone sets N: m=30 → 17, m=20 → 33, m=10 → 49. Nothing is hand-split or hand-merged.
4. **Nameable.** Each dimension's name and one-sentence definition are written from its cluster's top terms, curated keywords, entities and exemplars (`ce9_spec.py`); none lists members.
5. **Controls that were run.** Shuffled-feature null for the tree (above); random-membership control for every matcher (a random document set of the same size scores at the base rate); held-out estimate for the matcher induction procedure (learn on a random half, score the other half, centroids from the training half only); random-set control for induction (recall 0.00). Every number in this document is written by `ce9_14_assemble.py` from a `cache/*.json` produced by an earlier `ce9_*` script.

## 3. Granularity: three levels, one recommendation

The dimension list is a choice along one curve. Same family, three values of *m* (the smallest cluster allowed), measured on the centred scale:

| level | rule: smallest dimension (docs) | N | dimension size (docs) | marginal (10–19 docs) | closest pair of dimensions (centred cosine) | same dimension, two random halves: median / worst | a doc's nearest dimension is its own | silhouette vs shuffled-feature null | keyword matchability on unseen docs: recall / P@2 / lift | dimensions with no usable keyword matcher |
| :--- | :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |
| coarse | ≥ 30 | 17 | 39 – 222 (17% max) | 0 | 0.47 | 0.90 / 0.82 | 80% | 0.070 vs -0.008 | 39% / 54% / 5.2× | 0 |
| **medium** | ≥ 20 | 33 | 20 – 148 (11% max) | 0 | 0.66 | 0.87 / 0.70 | 82% | 0.070 vs -0.014 | 29% / 50% / 8.8× | 1 |
| fine | ≥ 10 | 49 | 11 – 93 (7% max) | 17 | 0.69 | 0.86 / 0.66 | 83% | 0.090 vs -0.019 | 22% / 58% / 12.9× | 4 |

*Keyword matchability* is the earlier automatic induction procedure, learned on half the documents and scored on the other half (centroids from the training half only), so its figures are comparable **across levels**; they are not the final matchers' figures (section 8). Its random-set control recall is 0.00 at every level.

**What the coarse level (N = 17) blurs** — it merges recommended-level dimensions that a reader would never confuse:

* **222 documents** = Life Story: Family, School and Church (148) + Faith: Scripture, Prayer and the Gospel (26) + Business Leaders and Philanthropy (24) + The ASEAN Law Association (24)
* **100 documents** = Libel and Cybercrime (56) + Public Officials' Duties and Data Privacy (23) + Marriage, Annulment and the Family Code (21)
* **95 documents** = Elections and Automated Voting (48) + The Marcos-Robredo Election Contest (26) + Citizenship and Residency: the Grace Poe Case (21)
* **85 documents** = The Judiciary's Milestones and Tributes (43) + The Bar Exam and Legal Education (21) + The Chief Justiceship and a Judicial Career (21)
* **73 documents** = Independent Commissions and Appointments (27) + Supreme Court Vacancies and the Chief Justiceship (26) + The Judicial and Bar Council (20)
* **90 documents** = International Law: the West Philippine Sea and Arbitration (64) + The Bangsamoro Peace Process (26)
* **57 documents** = The Economy, Taxes and Wages (36) + Corporate Governance and Integrity (21)
* **64 documents** = Impeachment (35) + The US Supreme Court and American Politics (29)
* **60 documents** = The Foundation for Liberty and Prosperity and Its Benefactors (33) + Liberty and Prosperity: the Twin Beacons (27)
* **55 documents** = Public Funds, the Budget and Bank Evidence (32) + Ill-Gotten Wealth and the PCGG (23)

**What the fine level (N = 49) fragments** — 17 of its 49 dimensions have 10–19 documents, its closest pair of dimensions is already 0.69 apart (at the duplicate line), and 4 have no usable keyword matcher. What it splits out of the medium dimensions:

* **Life Story: Family, School and Church** (148) → 93 docs on *god, feu, life, university, student, love*; 31 docs on *cardinal, cathedral, church, catholic, pope, archbishop*; 12 docs on *rotary, rotary club, club, rcm, club manila, serve man*; 12 docs on *cells, stem, cell, stem cells, lct, block*
* **Criminal Trials, Prosecutions and the ICC** (94) → 76 docs on *sbn, bail, evidence, accused, prosecution, trial*; 18 docs on *icc, bensouda, prosecutor, rome statute, investigation, preliminary*
* **International Law: the West Philippine Sea and Arbitration** (64) → 52 docs on *china, sea, scs, chinese, eez, arbitral*; 12 docs on *arbitration, disputes, icj, settlement, arbitral, dispute*
* **Property, Contracts and Labor Rights** (62) → 49 docs on *property, contracts, section, ownership, contract, shares*; 13 docs on *employer, labor, labor code, workers, employee, employees*
* **How the Supreme Court Decides** (59) → 40 docs on *ata, justices, opinions, petitions, lawyers, decisions*; 19 docs on *independence, duty, justices, power, judiciary, executive*
* **Libel and Cybercrime** (56) → 32 docs on *accused, evidence, criminal, search, facts, trial*; 13 docs on *death penalty, penalty, appellant, victim, death, rape*; 11 docs on *libel, cyberlibel, ressa, maria ressa, cybercrime, keng*
* **Presidential Power, Martial Law and People Power** (53) → 18 docs on *gma, respect, gma's, neri, noynoy, neri's*; 18 docs on *rebellion, martial, martial law, proclamation, invasion, powers*; 17 docs on *estrada, edsa, arroyo, swear, noon, davide*
* **Judicial Reform and Court Delay** (42) → 24 docs on *reform, judicial reform, judiciary, apjr, program, reforms*; 18 docs on *backlog, trial courts, courts, judges, average, docket*
* **Party-List, Charter Change and Political Dynasties** (40) → 21 docs on *cha-cha, dynasties, con-ass, charter, congress, con-con*; 19 docs on *party-list, underrepresented, marginalized underrepresented, seats, marginalized, veterans*
* **Science, Technology and the Law** (39) → 22 docs on *digital, information, internet, data, age, technology*; 17 docs on *bio-age, scientific, genetic, dawns judiciary, bio-age dawns, dna*
* **The Economy, Taxes and Wages** (36) → 18 docs on *world, asean, prosperity, china, economy, korea*; 18 docs on *million, pay, tax, refund, wage, vat*
* **Public Funds, the Budget and Bank Evidence** (32) → 20 docs on *deposits, accounts, dollar, omb, corona, psbank*; 12 docs on *gaa, budget, dap, appropriations, pdaf, fund*

**Recommendation: the medium level** (m = 20, 33 clusters). It is the only one of the three with no marginal dimension and a closest pair (0.66) clearly under the duplicate line; its held-out keyword recall (29%) beats the fine level's (22%) — the fine level buys a higher precision (58% vs 50% at P@2) with 16 more dimensions, most of them marginal. It is also the coarsest level that still keeps apart the subjects a visitor would ask about (elections vs the Marcos–Robredo contest vs citizenship; impeachment vs US politics; the sea dispute vs the Bangsamoro peace process). A coarser cut is defensible if the demo does not need those distinctions — the 17-dimension level is a real alternative, not a strawman. The deployed tests then take the medium level from 33 to **30** (section 0).

## 4. Table 1 — the proposed taxonomy (30 dimensions)

`doc_count` is the number of documents the dimension's matcher catches on the 1,290-document corpus (the v1 `topic_map.json` convention). `separability` is the highest centred cosine between this dimension's **deployed** centroid and any other's. `status`: **25 Dimension holds (two of them marginal) · 5 Same direction, wrong members · 0 Not established** — a row that were *Not established* would not be here; the one that was, `honors_received`, is in Table 2. Every dimension's `derived_from` is a Ward-tree cluster of the whole corpus; where a Phase 3 candidate or a curated-keyword pool also names it that is listed, and where none does the row says so — 11 of the 30 rest on the tree alone.

| id | display_name | tier | theme_anchor (share of its docs) | doc_count (matcher-caught) | derived_from | separability (max centred cosine vs any other) | 3 exemplars | prior_art_id | status |
| :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- | :--- | :--- |
| life_story_family_school_and_church | Life Story: Family, School and Church | core | C (86%) | 193 | Ward-tree cluster, 148 docs; corroborated by pool “rotary club of manila” 11/17; pool “jovito r. salonga” 11/22 | 0.69 vs faith_journey | `BC045` Liberty and Prosperity -- Ch. 2: Humble Begi; `SC023` So Unworthy and So Humbled, Yet So Honored a; `SC062` Nurturing Lives, Fulfilling Dreams | absorbs family_and_marriage, mentors_and_legal_lineage, early_life_sampaloc, eulogies_and_passing, friendships_and_civic_circles | Dimension holds |
| criminal_trials_and_prosecutions | Criminal Trials, Prosecutions and the ICC | core | A (91%) | 164 | Ward-tree cluster, 94 docs; corroborated by P3 pool sandiganbayan (13 docs); pool “sandiganbayan” 13/26 | 0.48 vs public_funds_budget_and_bank_evidence | `CA374` Update on PDAF cases of 3 senators; `CA392` Revilla's battle for bail; `CA410` Spotlight on Sandiganbayan | absorbs icc_and_duterte | Dimension holds |
| international_law_disputes | International Law: the West Philippine Sea and Arbitration | core | A (78%) | 85 | Ward-tree cluster, 64 docs; corroborated by pool “arbitral award” 10/12; pool “nine-dash line” 8/8 | 0.48 vs bangsamoro_peace_process | `CA450` Most vexing security problem; `CA062` The Maritime Zones Act, Asean, and China; `CA010` Understanding the arbitral award | international_law_disputes · absorbs eez_resource_sovereignty | Dimension holds |
| property_contracts_and_economic_rights | Property, Contracts and Labor Rights | core | B (48%) | 66 | Ward-tree cluster, 62 docs; corroborated by P3 P2 k=12 · c1 (8 docs) | 0.42 vs ill_gotten_wealth_and_the_pcgg | `BB033` Judicial Renaissance -- Ch. 15: La Bugal B'l; `BB040` Liberty and Prosperity -- Ch. 27: Didipio v.; `BB021` Transparency, Unanimity & Diversity -- Ch. 1 | — | Dimension holds |
| how_the_supreme_court_decides | How the Supreme Court Decides | subordinate | A (75%) | 21 | Ward-tree cluster, 59 docs; corroborated by P3 pool judicial independence (11 docs); pool “judicial independence” 11/22 | 0.52 vs impeachment_accountability | `BA084` Leveling the Playing Field -- Ch. 1: Judicia; `BA033` A Centenary of Justice -- Ch. 3: Obra Maestr; `CA212` A Supreme Court worthy of public trust | — | Dimension holds |
| libel_and_cybercrime | Libel and Cybercrime | subordinate | A (96%) | 28 | Ward-tree cluster, 56 docs; corroborated by pool “maria ressa” 6/6; pool “people v. echegaray” 5/5 | 0.43 vs death_penalty_and_echegaray | `CA251` Is Maria Ressa liable for libel?; `CA422` The dissents; `CA213` Saving Maria Ressa | — | Dimension holds - marginal (P@3 0.61; matcher covers the libel/cybercrime part of its cluster, centroid 0.61 of the cluster's) |
| presidential_power_martial_law_people_power | Presidential Power, Martial Law and People Power | core | A (60%) | 45 | Ward-tree cluster, 53 docs; corroborated by P3 pool people power (8 docs); pool “cory aquino” 5/8 | 0.44 vs impeachment_accountability | `BE003` With Due Respect (Vol. 1) -- Ch. 3: Rage for; `CA358` Constitutionality of Edsa 1 and Edsa 2; `BE006` With Due Respect (Vol. 1) -- Ch. 7: Will GMA | philippine_political_landscape | Dimension holds |
| elections_and_automated_voting | Elections and Automated Voting | core | A (67%) | 91 | Ward-tree cluster, 48 docs; corroborated by P3 P2 k=12 · c7 (7 docs); pool “smartmatic” 10/10; pool “pcos” 8/8 | 0.50 vs party_list_charter_change_and_dynasties | `BA063` Leadership by Example: The Davide Standard -; `BE015` With Due Respect (Vol. 5) -- Ch. 9: 'Hindi P; `CE067` Huwag kang gunggong' | — | Dimension holds |
| judiciary_milestones_and_tributes | The Judiciary's Milestones and Tributes | subordinate | C (47%) | 37 | Ward-tree cluster, 43 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.57 vs judicial_reform | `BD010` A Centenary of Justice -- Ch. 1: A Renaissan; `SC090` A New Writing Career; `SC025` Overwhelmed with Honor and Joy | — | Dimension holds |
| judicial_reform | Judicial Reform and Court Delay | core | A (50%) | 54 | Ward-tree cluster, 42 docs; corroborated by pool “action program for judicial reform” 9/15; pool “davide watch” 8/9 | 0.58 vs bar_exam_and_legal_education | `BD039` Reforming the Judiciary -- Ch. 3: Battling C; `BD049` Judicial Renaissance -- Ch. 1: A Transformed; `BD050` Judicial Renaissance -- Ch. 2: The APJR: An  | judicial_reform | Same direction, wrong members |
| party_list_charter_change_and_dynasties | Party-List, Charter Change and Political Dynasties | core | A (72%) | 68 | Ward-tree cluster, 40 docs; corroborated by pool “party-list system” 7/10; pool “banat v. comelec” 6/7 | 0.50 vs elections_and_automated_voting | `CA192` Party-list, 'quo vadis'?; `CA147` Solving the party-list fiasco; `CA260` Abolish or reform party-list | — | Dimension holds |
| science_technology_and_the_law | Science, Technology and the Law | core | E (44%) | 63 | Ward-tree cluster, 39 docs; corroborated by P3 P2 k=12 · c3 (8 docs) | 0.42 vs death_penalty_and_echegaray | `BE027` The Bio-Age Dawns on the Judiciary -- Append; `CA034` AI in justice and governance; `BE026` The Bio-Age Dawns on the Judiciary -- Ch. 1: | ai_and_technology | Dimension holds |
| economy_taxes_and_prosperity | The Economy, Taxes and Wages | subordinate | B (39%) | 17 | Ward-tree cluster, 36 docs; corroborated by P3 P2 k=12 · c12 (4 docs) | 0.57 vs twin_beacons_doctrine | `CB017` Unleashing entrepreneurial ingenuity (2); `SB073` Unleashing Entrepreneurial Ingenuity; `CE091` Internet, the globalization equalizer | — | Dimension holds |
| impeachment_accountability | Impeachment | core | A (91%) | 47 | Ward-tree cluster, 35 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.52 vs how_the_supreme_court_decides | `BA086` Leveling the Playing Field -- Ch. 15: Franci; `CA061` How do you solve a problem like Sara?; `CA004` Due process in impeachment | impeachment_accountability | Same direction, wrong members |
| foundation_for_liberty_and_prosperity | The Foundation for Liberty and Prosperity and Its Benefactors | anchor | D (58%) | 107 | Ward-tree clusters of 33 (Foundation) + 24 (business leaders and philanthropy) docs, merged: their deployed centroids are 0.74-0.78 apart; corroborated by P3 P2 k=12 · c8 (5 docs); pool “tan yan kee foundation” 14/16; pool “foundation for liberty and prosperity” 9/13 | 0.68 vs life_story_family_school_and_church | `SD021` A Fruitful Past Decade and a Hope-filled New; `CD018` FLP expanding into prosperity; `CD008` FLP's 2024 law scholars, fellows, and winner | foundation_for_liberty_and_prosperity · absorbs msme_and_entrepreneurship+prosperity_fund_msme, flp_scholarship_programs, museum_for_liberty_and_prosperity, flp_donors_and_partners | Same direction, wrong members |
| public_funds_budget_and_bank_evidence | Public Funds, the Budget and Bank Evidence | core | A (94%) | 47 | Ward-tree cluster, 32 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.48 vs criminal_trials_and_prosecutions | `CA506` Bank deposits as evidence; `CA388` Who won in new DAP ruling?; `CA407` The DAP decision | — | Dimension holds |
| us_supreme_court_and_american_politics | The US Supreme Court and American Politics | core | A (59%) | 50 | Ward-tree cluster, 29 docs; corroborated by pool “scotus” 8/9 | 0.33 vs impeachment_accountability | `CA026` Sink or sail with Potus and Scotus; `CA078` Scotus hands Trump a major victory; `CE031` Trump's stunning landslide, legal effects | global_geopolitics | Dimension holds |
| independent_commissions_and_appointments | Independent Commissions and Appointments | subordinate | A (67%) | 15 | Ward-tree cluster, 27 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.41 vs impeachment_accountability | `CA146` What now, Comelec, COA, and CSC bosses?; `CA150` Speedy, independent, and trustworthy; `CA159` No 'acting' appointments to Comelec | — | Dimension holds |
| twin_beacons_doctrine | Liberty and Prosperity: the Twin Beacons | anchor | A (41%) | 41 | Ward-tree cluster, 27 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.64 vs foundation_for_liberty_and_prosperity | `BD060` Liberty and Prosperity -- Ch. 4: Twin Beacon; `SA145` Safeguarding the Liberty and Nurturing the P; `SD150` Spreading the Gospel of Liberty and Prosperi | twin_beacons_doctrine · absorbs rule_of_law, economic_governance_and_business_law | Same direction, wrong members |
| marcos_robredo_election_contest | The Marcos-Robredo Election Contest | subordinate | A (50%) | 38 | Ward-tree cluster, 26 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.42 vs elections_and_automated_voting | `CA183` Marcos lost in 2016, remains viable in 2022; `CE050` Sara, the game changer; `CE049` The Bongbong-Sara juggernaut | — | Dimension holds |
| bangsamoro_peace_process | The Bangsamoro Peace Process | subordinate | A (77%) | 28 | Ward-tree cluster, 26 docs; corroborated by pool “bangsamoro basic law” 6/7 | 0.48 vs international_law_disputes | `CA480` A little vague but not unconstitutional; `CA386` MILF aspiration unchanged; `CA390` How much do we love peace? | — | Dimension holds |
| supreme_court_vacancies_and_chief_justiceship | Supreme Court Vacancies and the Chief Justiceship | subordinate | A (58%) | 28 | Ward-tree cluster, 26 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.69 vs jbc_discernment_and_appointment | `CA185` Bewildering early retirements in SC; `CE070` Passion to eradicate corruption; `CC064` Duterte appointees to dominate SC | — | Dimension holds |
| faith_journey | Faith: Scripture, Prayer and the Gospel | core | C (96%) | 49 | Ward-tree cluster, 26 docs; corroborated by P3 P2 k=12 · c2 (15 docs) | 0.69 vs life_story_family_school_and_church | `BC017` Justice and Faith -- Ch. 10: Offering to the; `BC016` Justice and Faith -- Ch. 9: Jesus, Shepherd ; `CC034` Jesus Christ, our King and Leader (2) | faith_journey | Same direction, wrong members |
| asean_law_association | The ASEAN Law Association | subordinate | A (38%) | 11 | Ward-tree cluster, 24 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.50 vs foundation_for_liberty_and_prosperity | `SA055` Welcome to the Philippines ALA; `SA015` Consensus, Rule of Law, Liberty, and Prosper; `SC046` Welcome to My Household | asean_law_association | Dimension holds |
| ill_gotten_wealth_and_the_pcgg | Ill-Gotten Wealth and the PCGG | subordinate | A (70%) | 27 | Ward-tree cluster, 23 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.42 vs property_contracts_and_economic_rights | `CA229` P200-B ill-gotten wealth case not lost; `CA321` Ill-gotten wealth of Marcoses; `CA171` Do the Marcoses have ill-gotten wealth? | — | Dimension holds |
| citizenship_and_residency_grace_poe | Citizenship and Residency: the Grace Poe Case | subordinate | A (95%) | 24 | Ward-tree cluster, 21 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.32 vs elections_and_automated_voting | `CA381` Grace Poe's citizenship; `CA370` Q and A on Grace Poe's natural-born citizens; `CA363` Analyzing the SET decision | — | Dimension holds |
| marriage_annulment_and_the_family_code | Marriage, Annulment and the Family Code | subordinate | A (90%) | 29 | Ward-tree cluster, 21 docs; corroborated by pool “psychological incapacity” 6/10 | 0.41 vs death_penalty_and_echegaray | `BA066` Transparency, Unanimity & Diversity -- Ch. 1; `BA027` With Due Respect (Vol. 7) -- Ch. 1: Sanctity; `CA148` Bigamy and psychological incapacity | — | Dimension holds |
| bar_exam_and_legal_education | The Bar Exam and Legal Education | subordinate | D (38%) | 20 | Ward-tree cluster, 21 docs; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only) | 0.58 vs judicial_reform | `CC102` Bar exam and legal education (3); `CC103` Bar exam and legal education (2); `CA110` Welcome to the new attorneys With Due Respec | bar_exam_and_legal_education | Dimension holds |
| jbc_discernment_and_appointment | The Judicial and Bar Council | subordinate | A (60%) | 34 | Ward-tree cluster, 20 docs; corroborated by pool “bar council” 6/9; pool “judicial” 6/10 | 0.69 vs supreme_court_vacancies_and_chief_justiceship | `BD006` With Due Respect (Vol. 3) -- Ch. 4: Reformin; `CA491` Transparent, accountable and dignified; `BD008` With Due Respect (Vol. 3) -- Ch. 6: Responsi | jbc_discernment_and_appointment | Dimension holds |
| death_penalty_and_echegaray | The Death Penalty and the Echegaray Reflection | subordinate | A (57%) | 30 | curated-keyword pool (“leo echegaray” 5/5 and “people v. echegaray” 5/5 pool documents inside one cluster; Phase 3 coherence 0.34 vs null p95 0.23; a 13-document fragment at the fine level) | 0.43 vs criminal_trials_and_prosecutions | `BA059` Leadership by Example: The Davide Standard -; `BA054` Battles in the Supreme Court -- Ch. 4: BATTL; `BA049` The Bio-Age Dawns on the Judiciary -- Ch. 14 | death_penalty_and_echegaray | Dimension holds - marginal (P@3 0.57 < 0.60 bar; separable only while criminal law's matcher omits its terms) |

### Tier distribution and theme anchors

| tier | n | dimensions |
| :--- | :--- | :--- |
| anchor | 2 | `foundation_for_liberty_and_prosperity`, `twin_beacons_doctrine` |
| core | 13 | `life_story_family_school_and_church`, `criminal_trials_and_prosecutions`, `international_law_disputes`, `property_contracts_and_economic_rights`, `presidential_power_martial_law_people_power`, `elections_and_automated_voting`, `judicial_reform`, `party_list_charter_change_and_dynasties`, `science_technology_and_the_law`, `impeachment_accountability`, `public_funds_budget_and_bank_evidence`, `us_supreme_court_and_american_politics`, `faith_journey` |
| subordinate | 15 | `how_the_supreme_court_decides`, `libel_and_cybercrime`, `judiciary_milestones_and_tributes`, `economy_taxes_and_prosperity`, `independent_commissions_and_appointments`, `marcos_robredo_election_contest`, `bangsamoro_peace_process`, `supreme_court_vacancies_and_chief_justiceship`, `asean_law_association`, `ill_gotten_wealth_and_the_pcgg`, `citizenship_and_residency_grace_poe`, `marriage_annulment_and_the_family_code`, `bar_exam_and_legal_education`, `jbc_discernment_and_appointment`, `death_penalty_and_echegaray` |
| meta | 0 | — |

Rule: **anchor** is a policy label, not a size — the Chief Justice's organising philosophy (`twin_beacons_doctrine`) and the Foundation, as in v1; **core** = at least 40 documents caught; **subordinate** = fewer; **meta** is empty because `robot_identity_meta` leaves the taxonomy. Tier is informational in the code (router-prompt preface, tie-break); it is one line to change.

`theme_anchor` is the plurality theme letter of the dimension's derived cluster (A 22, B 2, C 3, D 2, E 1). It matters more than it looks: `app/service.py` turns it into a spoken register cue, and the per-topic token budgets in `answer_pipeline.py` were seeded from it. Where the plurality is under half the cluster the anchor is a judgement call: `property_contracts_and_economic_rights` (B 48%), `judiciary_milestones_and_tributes` (C 47%), `science_technology_and_the_law` (E 44%), `economy_taxes_and_prosperity` (B 39%), `twin_beacons_doctrine` (A 41%), `asean_law_association` (A 38%), `bar_exam_and_legal_education` (D 38%).

## 5. The two named verdicts, and the same-direction cases

**`robot_identity_meta` — moves to the router (verdict confirmed).** 0 documents, 0 chunks; its v1 centroid is the corpus-mean fallback. It is already a router intent (`corpus/voice/router_prompt.md`) and a deterministic regex gate (`app/retrieval.py` `input_gate`). What must be kept outside the taxonomy: the intent id, its 120-token budget (`answer_pipeline.py` and `cj_chat.py` line 162), its `META` register cue (`app/service.py` line 68) and the hard-coded identity response (`answer_pipeline.py` line 802). Removing the taxonomy entry without providing those breaks `service._theme_of` for that id.

**`death_penalty_and_echegaray` — survives, as a marginal dimension.** The evidence:

* It is real and narrow: Phase 3 measured cohesion 0.34 against a null 95th percentile of 0.23; 30 documents, 17 of them book chapters; the curated pools “leo echegaray” 5/5 and “people v. echegaray” 5/5 sit inside one cluster; at the fine level it is a 13-document cluster (*death penalty, penalty, appellant, victim, death, rape*).
* At the recommended level it is *not* its own cluster: it is a fragment of the 56-document criminal-law cluster, 0.60 from the rest of that cluster.
* **The trap.** As a matcher-defined dimension it is separable only if no other dimension carries its terms. With `death penalty` in criminal law's matcher the two deployed centroids are **0.96** apart (all 30 of its documents are also in criminal law). With criminal law restricted to libel and cybercrime, its nearest dimension is **0.43** away. So the criminal-law dimension is narrowed to `libel_and_cybercrime` — which is not the whole 56-document cluster: its centroid is 0.61 from the cluster's own, and the cluster's 32 evidence-and-procedure documents have no dimension of their own (0 of those 32 have `criminal_trials_and_prosecutions` as their best-chunk dimension and 0 is an orphan).
* **The cost, and why splitting is still the better option.** Neighbourhood precision is 57% for the death-penalty dimension and 61% for `libel_and_cybercrime`, against a bar of 60% (random-membership control 3% / 11%). The single combined dimension — libel, cybercrime and the death penalty in one matcher — scores 54% on 56 documents, lower than either half. If you would rather have one dimension, delete `death_penalty_and_echegaray` from the sign-off line and add `death penalty` and `echegaray` to `libel_and_cybercrime`'s matcher; the merge gate then never sees the pair.

**The same-direction cases.** `faith_journey` keeps its id and gets a new matcher: its v1 centroid is 0.80 from the scripture-and-prayer dimension while only 22 of its 298 matcher documents are in it. Davide ↔ `judicial_reform` holds: 9 of the 23 Davide chapters land in `judicial_reform`, more than in any other dimension, so the v1 topic was right and its matcher missed them. **Puno ↔ `supreme_court_history` does not hold up as a dimension:** the 21 Puno chapters are all books and spread over 11 dimensions (7 in property and contracts — they are decisions he wrote); Phase 3's 0.81 was two diffuse directions agreeing. `supreme_court_history` is dropped (Table 2).

## 6. Table 2 — the fate of the 34 v1 topics

(35 topics in the v1 taxonomy; v1's stored centroids had already merged `msme_and_entrepreneurship` and `prosperity_fund_msme` into one, shown as one row.) The document counts are the v1 matchers run on the current 1,290-document corpus; the stored `topic_map.json` `doc_count` (from the 79-document corpus, before books) is shown beside it.

| v1 topic | docs its v1 matcher catches (1,290-doc corpus) | stored topic_map doc_count (v1, stale) | fate | evidence (centred scale) | why |
| :--- | ---: | ---: | :--- | :--- | :--- |
| `rule_of_law` | 211 | 30 | absorbed into `twin_beacons_doctrine` | cohesion 0.21 (random 0.09); → twin_beacons_doctrine: cos 0.72, 20/211 of its docs inside, 74% of the dimension | A concept mentioned across the corpus, not a place in it: 211 matcher documents, member cohesion barely above random. Its centroid sits at 0.72 from the twin-beacons dimension, whose matcher already carries 'rule of law'. |
| `twin_beacons_doctrine` | 213 | 27 | carried, matcher rewritten (`twin_beacons_doctrine`) | cohesion 0.31 (random 0.10); → twin_beacons_doctrine: cos 0.74, 24/213 of its docs inside, 89% of the dimension | Same direction, wrong members: the v1 matcher fires on 213 documents, 24 of which are the 27-document dimension. |
| `foundation_for_liberty_and_prosperity` | 136 | 25 | carried, matcher rewritten (`foundation_for_liberty_and_prosperity`) | cohesion 0.42 (random 0.12); → foundation_for_liberty_and_prosperity: cos 0.91, 33/136 of its docs inside, 100% of the dimension | The Foundation dimension holds (centred cosine 0.91); the v1 matcher over-fires 4x. |
| `with_due_respect_persona` | 197 | 10 | dropped | cohesion 0.20 (random 0.09); nearest dimension: independent_commissions_and_appointments at 0.54 | The column's stance is a property of the voice, not a subject: 197 matcher documents, nearest dimension only 0.54. It belongs in the voice card (already there), not the taxonomy. |
| `constitutional_doctrine` | 611 | 28 | dropped | cohesion 0.17 (random 0.07); nearest dimension: impeachment_accountability at 0.69 | A catch-all: 611 documents (47% of the corpus) at cohesion barely above random. Its specific subjects live on as impeachment, presidential power, charter change, the commissions and how the Court decides. |
| `due_process` | 145 | 8 | dropped | cohesion 0.23 (random 0.12); nearest dimension: libel_and_cybercrime at 0.66 | Cross-cutting doctrine with no cluster of its own (nearest dimension 0.66, 12 of 145 documents inside it); its content is criminal procedure and criminal law. |
| `judicial_reform` | 106 | 6 | carried, matcher rewritten (`judicial_reform`) | cohesion 0.39 (random 0.11); → judicial_reform: cos 0.84, 27/106 of its docs inside, 64% of the dimension | Dimension holds (0.84). The Davide pool (23 book chapters) lands here: 9 of them inside this dimension, more than in any other. |
| `supreme_court_history` | 406 | 33 | dropped | cohesion 0.14 (random 0.08); nearest dimension: how_the_supreme_court_decides at 0.63 | Diffuse: 406 matcher documents (31% of the corpus), nearest dimension 0.63. The Puno pool that Phase 3 read as 'same direction' does not form a dimension of its own (21 book chapters spread over 11 dimensions, 7 of them in property and contracts). The institution's subjects are carried by the tributes/milestones, vacancies, chief-justiceship and how-the-Court-decides dimensions. |
| `impeachment_accountability` | 171 | 5 | carried, matcher rewritten (`impeachment_accountability`) | cohesion 0.27 (random 0.11); → impeachment_accountability: cos 0.84, 27/171 of its docs inside, 77% of the dimension | Dimension holds (0.84); the v1 matcher fires on 171 documents for a 35-document subject. |
| `international_law_disputes` | 78 | 15 | carried, matcher rewritten (`international_law_disputes`) | cohesion 0.43 (random 0.12); → international_law_disputes: cos 0.95, 46/78 of its docs inside, 72% of the dimension | Dimension holds (0.95). The v1 matcher would pass the acceptance test as it stands (1.2x, P@3 0.68, recall 72%); the new one is better on all three (1.3x, P@3 0.72 on the same partition-neighbourhood definition, recall 83%) - and it is the closest v1 came to a finished matcher. |
| `icc_and_duterte` | 156 | 16 | absorbed into `criminal_trials_and_prosecutions` | cohesion 0.26 (random 0.11) | Its coherent core is an 18-document ICC cluster (13 of them v1 matcher hits) that the recommended level folds into criminal trials - it is one of the fine level's fragments; the other 143 of its 156 matcher documents are diffuse (cohesion 0.26 vs 0.09 random). |
| `judicial_activism_and_political_question` | 78 | 5 | dropped | cohesion 0.23 (random 0.14); nearest dimension: twin_beacons_doctrine at 0.57 | No cluster (nearest dimension 0.57): 78 documents on a doctrine mentioned across several subjects; 'judicial activism' catches 9 documents in total. |
| `asean_law_association` | 39 | 4 | carried, matcher rewritten (`asean_law_association`) | cohesion 0.44 (random 0.16); → asean_law_association: cos 0.86, 10/39 of its docs inside, 42% of the dimension | Dimension holds (0.86). The v1 matcher passes the acceptance test as it stands (1.6x, P@3 0.62) but only 26% of what it catches is in the dimension; the new one is stricter (11 documents, 82% inside) at similar recall (38% vs 42%). |
| `death_penalty_and_echegaray` | 30 | 1 | carried, matcher rewritten (`death_penalty_and_echegaray`) | cohesion 0.34 (random 0.19) | The brief's verdict holds, at a price. Real and narrow (Phase 3: cohesion 0.34 vs null p95 0.23; 30 documents, 17 of them book chapters). It passes all four tests as a dimension of its own - but only while criminal law's matcher does not carry its terms: with them in the same dimension the two are 0.96 apart; with libel/cybercrime alone it is 0.43 from the nearest dimension. Neighbourhood precision is 0.57, just under the 0.60 bar used for the others. |
| `bar_exam_and_legal_education` | 132 | 20 | carried, matcher rewritten (`bar_exam_and_legal_education`) | cohesion 0.36 (random 0.11); → bar_exam_and_legal_education: cos 0.69, 15/132 of its docs inside, 71% of the dimension | Same direction, wrong members: the v1 centroid is closer to the life-story dimension (0.73) than to the bar-exam one (0.69) because 43 of its 132 matcher documents are life-story documents. |
| `economic_governance_and_business_law` | 43 | 7 | absorbed into `twin_beacons_doctrine` | cohesion 0.43 (random 0.14); → twin_beacons_doctrine: cos 0.86, 10/43 of its docs inside, 37% of the dimension | Centred cosine 0.86 with the twin-beacons dimension (duplicate at any sensible threshold); 'deferential interpretation' and the business-policy vocabulary are already in that dimension's matcher. |
| `eez_resource_sovereignty` | 29 | 7 | absorbed into `international_law_disputes` | cohesion 0.42 (random 0.17); → international_law_disputes: cos 0.67, 9/29 of its docs inside, 14% of the dimension | 29 matcher documents at cohesion 0.42; 9 sit in the sea-dispute dimension (0.67) and 9 in property and contracts. Joint development in the South China Sea is a sub-theme of the dimension it joins. |
| `family_and_marriage` | 272 | 22 | absorbed into `life_story_family_school_and_church` | cohesion 0.27 (random 0.09); → life_story_family_school_and_church: cos 0.93, 90/272 of its docs inside, 61% of the dimension | Centred cosine 0.93 with the life-story dimension. (Marriage as LAW - annulment, the Family Code - is a different, new dimension.) |
| `mentors_and_legal_lineage` | 156 | 16 | absorbed into `life_story_family_school_and_church` | cohesion 0.28 (random 0.10); → life_story_family_school_and_church: cos 0.78, 48/156 of its docs inside, 32% of the dimension | Centred cosine 0.78 with the life-story dimension; the recommended level has no stable split inside it. |
| `faith_journey` | 298 | 20 | carried, matcher rewritten (`faith_journey`) | cohesion 0.25 (random 0.07); → faith_journey: cos 0.80, 22/298 of its docs inside, 85% of the dimension | Same direction, wrong members (the Phase 3 case): 0.80 to the scripture-and-prayer dimension, 22 of its 298 matcher documents inside it. The v1 matcher fires on any mention of God or faith; the members are the Gospel/prayer chapters. |
| `early_life_sampaloc` | 87 | 14 | absorbed into `life_story_family_school_and_church` | cohesion 0.48 (random 0.11); → life_story_family_school_and_church: cos 0.92, 55/87 of its docs inside, 37% of the dimension | Centred cosine 0.92 with the life-story dimension. |
| `jbc_discernment_and_appointment` | 110 | 5 | redefined as `jbc_discernment_and_appointment` | cohesion 0.35 (random 0.10); → jbc_discernment_and_appointment: cos 0.83, 19/110 of its docs inside, 95% of the dimension | The v1 definition is the Chief Justice's own seven JBC rejections (a personal story); the v1 matcher keys on 'jbc' and so catches the Council's institutional documents (0.83). It is redefined to what its members are; the personal story ('Seven Rejections') sits in the scripture-and-prayer dimension. |
| `eulogies_and_passing` | 109 | 15 | absorbed into `life_story_family_school_and_church` | cohesion 0.30 (random 0.11); → life_story_family_school_and_church: cos 0.86, 38/109 of its docs inside, 26% of the dimension | Centred cosine 0.86 with the life-story dimension. |
| `friendships_and_civic_circles` | 76 | 12 | absorbed into `life_story_family_school_and_church` | cohesion 0.43 (random 0.15); → life_story_family_school_and_church: cos 0.86, 29/76 of its docs inside, 20% of the dimension | Centred cosine 0.86 with the life-story dimension (0.80 with business leaders and philanthropy, where its 8 funder documents sit). |
| `honors_received` | 24 | 2 | dropped | cohesion 0.30 (random 0.22); nearest dimension: judiciary_milestones_and_tributes at 0.69 | Not established: 24 matcher documents, of which only 10 (42%) mention an honour at all (Phase 3); they scatter (5 life story, 4 tributes, 3 how-the-Court-decides). Honours are an incident inside tributes and life story, not a subject. |
| `flp_scholarship_programs` | 109 | 19 | absorbed into `foundation_for_liberty_and_prosperity` | cohesion 0.45 (random 0.10); → foundation_for_liberty_and_prosperity: cos 0.89, 28/109 of its docs inside, 85% of the dimension | Centred cosine 0.89 with the Foundation dimension. |
| `museum_for_liberty_and_prosperity` | 20 | 10 | absorbed into `foundation_for_liberty_and_prosperity` | cohesion 0.65 (random 0.22); → foundation_for_liberty_and_prosperity: cos 0.90, 11/20 of its docs inside, 33% of the dimension | Centred cosine 0.90 with the Foundation dimension; 20 matcher documents. |
| `flp_donors_and_partners` | 143 | 19 | absorbed into `foundation_for_liberty_and_prosperity` | cohesion 0.36 (random 0.12); → foundation_for_liberty_and_prosperity: cos 0.89, 29/143 of its docs inside, 88% of the dimension | Centred cosine 0.89 with the Foundation dimension (0.79 with business leaders and philanthropy). |
| `lawyer_ethics_initiative` | 47 | 4 | dropped | cohesion 0.23 (random 0.16); nearest dimension: the unbuilt cluster 'Corporate Governance and Integrity' at 0.42 | No cluster: no dimension within centred cosine 0.5; 47 matcher documents at cohesion 0.23 vs 0.17 random. |
| `ai_and_technology` | 99 | 11 | redefined as `science_technology_and_the_law` | cohesion 0.27 (random 0.11); → science_technology_and_the_law: cos 0.65, 21/99 of its docs inside, 54% of the dimension | Centred cosine 0.65; the coherent subject is broader than AI - DNA and the bio-age, the internet and data, then AI. |
| `global_geopolitics` | 83 | 10 | redefined as `us_supreme_court_and_american_politics` | cohesion 0.34 (random 0.13); → us_supreme_court_and_american_politics: cos 0.77, 26/83 of its docs inside, 90% of the dimension | Centred cosine 0.77; 26 of its 83 matcher documents are 90% of the Trump/US-Supreme-Court dimension. The ICJ half is an arbitration fragment of the sea-dispute dimension. |
| `philippine_political_landscape` | 238 | 16 | redefined as `presidential_power_martial_law_people_power` | cohesion 0.23 (random 0.10); → presidential_power_martial_law_people_power: cos 0.73, 34/238 of its docs inside, 64% of the dimension | Centred cosine 0.73 with the presidential-power dimension (GMA, martial law, EDSA); its Marcos-administration part is the Marcos-Robredo dimension. |
| `msme_and_entrepreneurship+prosperity_fund_msme` | 47 | 16 | absorbed into `foundation_for_liberty_and_prosperity` | cohesion 0.41 (random 0.15); → foundation_for_liberty_and_prosperity: cos 0.87, 15/47 of its docs inside, 45% of the dimension | v1 already merged these two into one centroid; that centroid is at 0.87 from the Foundation dimension. |
| `robot_identity_meta` | 0 | — | moved out of the taxonomy into the router | 0 documents / 0 chunks; a routing intent | 0 documents, 0 chunks: an intent, not a subject. Already an LLM-router intent (router_prompt.md) and a regex input gate (app/retrieval.py input_gate). |

**Counts:** absorbed: **13**, carried, matcher rewritten: **9**, dropped: **7**, redefined: **4**, moved to the router: **1** — 34 v1 topics in all. Every v1 matcher was rewritten; none was reused unchanged (two — `international_law_disputes`, `asean_law_association` — pass the acceptance test as they stand and were beaten by their replacement). 15 of the 30 dimensions have no v1 predecessor.

**Id remap for Phase 5** (v1 id → v2 id): `rule_of_law` → `twin_beacons_doctrine`; `twin_beacons_doctrine` → `twin_beacons_doctrine`; `foundation_for_liberty_and_prosperity` → `foundation_for_liberty_and_prosperity`; `judicial_reform` → `judicial_reform`; `impeachment_accountability` → `impeachment_accountability`; `international_law_disputes` → `international_law_disputes`; `icc_and_duterte` → `criminal_trials_and_prosecutions`; `asean_law_association` → `asean_law_association`; `death_penalty_and_echegaray` → `death_penalty_and_echegaray`; `bar_exam_and_legal_education` → `bar_exam_and_legal_education`; `economic_governance_and_business_law` → `twin_beacons_doctrine`; `eez_resource_sovereignty` → `international_law_disputes`; `msme_and_entrepreneurship+prosperity_fund_msme` → `foundation_for_liberty_and_prosperity`; `family_and_marriage` → `life_story_family_school_and_church`; `mentors_and_legal_lineage` → `life_story_family_school_and_church`; `faith_journey` → `faith_journey`; `early_life_sampaloc` → `life_story_family_school_and_church`; `jbc_discernment_and_appointment` → `jbc_discernment_and_appointment`; `eulogies_and_passing` → `life_story_family_school_and_church`; `friendships_and_civic_circles` → `life_story_family_school_and_church`; `flp_scholarship_programs` → `foundation_for_liberty_and_prosperity`; `museum_for_liberty_and_prosperity` → `foundation_for_liberty_and_prosperity`; `flp_donors_and_partners` → `foundation_for_liberty_and_prosperity`; `ai_and_technology` → `science_technology_and_the_law`; `global_geopolitics` → `us_supreme_court_and_american_politics`; `philippine_political_landscape` → `presidential_power_martial_law_people_power`. Dropped: `with_due_respect_persona`, `constitutional_doctrine`, `due_process`, `supreme_court_history`, `judicial_activism_and_political_question`, `honors_received`, `lawyer_ethics_initiative`. Live files keyed by v1 ids: `corpus/voice/{topic_map.json, router_prompt.md, voice_card.md}` and at least 9 files under `eval/`; the live corpus JSONs carry no topic tags, so nothing needs retagging in `corpus/`.

## 7. Table 3 — the two thresholds

### `TOPIC_MERGE_COSINE` → **0.75, on the centred scale** (v1: 0.95 on the raw scale)

**The metric changes and the code must change with it** — 0.75 means nothing on raw cosine, where independent random groups score 0.98 (section 1).

| what is compared (deployed centroids, centred) | typical | tail | n |
| :--- | :--- | :--- | :--- |
| independent random document groups of the dimensions' own sizes (null) | mean -0.04 | p95 0.24 · p99 0.34 · max 0.54 | 4,000 pairs |
| the proposed dimensions, every pair of *different* dimensions | median -0.03 | p90 0.33 · p95 0.42 · max 0.69 | 435 pairs; ≥0.5: 11, ≥0.6: 4, ≥0.7: 0 |
| one dimension against ITSELF (its caught docs split at random into two halves) | median 0.80 | p10 0.61 · p05 0.56 · min 0.36 | 900 splits |

* **Above the noise.** Random groups of the dimensions' own sizes reach 0.54 at most in 4,000 draws (95th percentile 0.24; Phase 3's own run of the same idea: mean 0.019, 95th 0.282). Anything under ~0.55 is indistinguishable from unrelated document groups.
* **Above every pair we decided is distinct.** 435 pairs of proposed dimensions; the highest is 0.694; 3 are at 0.65 or above and 0 at 0.70 or above. A gate at 0.70 would sit 0.006 above the closest pair — one rebuild away from silently merging a pair the sign-off has approved, which is how P3.3 collapsed. At 0.75 the margin is 0.056.
* **Below a genuine duplicate.** Splitting one dimension's own documents at random into two halves — the best model of "the same subject twice" — gives a median centroid cosine of 0.80; 65% of such splits are at or above 0.75, 76% at or above 0.70, 91% at or above 0.60. So the gate is a **backstop for accidental duplicates, not a discriminator**: at 0.75 it catches about two of three of them. The separability that matters is enforced by this document (Table 1), not by the gate.
* The Ward family was built with a working duplicate line of 0.70 on *partition* centroids (closest pair 0.66); deployed centroids are noisier than partition centroids (matchers admit some out-of-cluster documents), which is the reason the config value is higher.

### `TOPIC_ASSIGN_MIN_COSINE` → **0.31, centred scale, best-chunk, one global value** (v1: 0.68 raw, inert — it orphaned 0.0% under every definition)

*Definition.* Best-chunk (a document's affinity is its best chunk's cosine to the dimension), evaluated **leave-one-out**: a member document is removed from its own dimension's centroid before its affinity is measured, so the number is not inflated by a document matching itself. Best-chunk separates real dimensions from noise better than document-mean (area under the curve of observed best affinity over a random-membership null: **0.918** vs **0.889**; by format, best-chunk: columns 0.93, books 0.91, speeches 0.93, biography 0.86), and it is what `merge_tag_topics.py` already uses.

*Value.* The null is the same procedure with **random** document sets of the dimensions' own sizes, taking a maximum over all 30 dimensions per document: best-chunk median **0.306**, 90th percentile 0.400, 95th 0.434. The recommended 0.31 is that median: a document is an orphan when its best dimension is no better than what a random set of documents would typically give it. Observed best-chunk affinity has median 0.480 and 5th percentile 0.324.

**What this floor is and is not.** It is a *noise-median floor for flagging orphans*, not a significance test. A floor at the null's 95th percentile (0.434) would orphan **34% of all documents** — which shows how weak per-document evidence is in this space, and why the top-3 rank and the tagging margin, not the floor, decide what a document is about. At 0.31: 46 documents (3.6%) are orphans; of the rest, 698 keep three tags, 321 two and 225 one (top three by best-chunk, at or above the floor).

**Global, per-format, or within-format percentile.** Orphan rates (leave-one-out) under each policy:

| policy | orphans, all docs | columns | books | speeches | biography |
| :--- | ---: | ---: | ---: | ---: | ---: |
| **A. one global floor 0.31, best-chunk** (recommended) | 46 (3.6%) | 32 (4.0%) | 7 (2.3%) | 4 (2.6%) | 3 (8.6%) |
| B. per-format floors at each format's own null median, best-chunk (columns 0.29, books 0.33, speeches 0.33, biography 0.32) | 37 (2.9%) | 17 (2.1%) | 11 (3.7%) | 5 (3.3%) | 4 (11.4%) |
| C. within-format percentile: each format's own lowest 3.6% (floors columns 0.31, books 0.33, speeches 0.33, biography 0.27) | 48 (3.7%) | 29 (3.6%) | 11 (3.7%) | 6 (3.9%) | 2 (5.7%) |
| D. one global floor 0.28, document-mean (its null median) | 82 (6.4%) | 63 (7.8%) | 8 (2.7%) | 9 (5.9%) | 2 (5.7%) |

Per-format floors at each format's own noise median (B) lower the columns rate by about two points and raise the books rate by about one and a half — a couple of points of parity for a config change from one number to four — so I recommend the single global value (A). A within-format percentile (C) forces equal rates by construction and would flag documents in a format that is perfectly covered; it is a policy, not evidence. Document-mean (D) is the weaker separator and orphans columns more. The Phase 3 finding that books need a higher floor than columns holds here too (books' noise median 0.33 vs columns' 0.29) but is small on this scale.

## 8. Matchers

The taxonomy engine is unchanged (v1 `_doc_haystack` + `score_topic`: word-boundary match over title, summary, topic tags, keywords, register markers and entity names; a document is in the dimension if any term matches). Every term is a plain readable phrase that catches **at least 5 documents**; nothing is a regular expression. Method: candidate terms = the cluster's top TF-IDF terms, the curated keywords and entity names lifted inside it; a greedy pick scoring each term by cluster documents gained minus 0.35× outside documents gained, under a per-term precision filter; a per-format top-up; then defining vocabulary tried in a fixed order and admitted only while the union stays under 1.9× the cluster with at least 65% of caught documents in the dimension's neighbourhood; then the edits printed in `ce9_edits.py` and `ce9_19_freeze.py`, each with the measurement that forced it (`noon`, `fisherman`, `levy` were precise on their clusters and meaningless as subjects).

**Reading the table.** *Share in its own embedding neighbourhood* = of the documents the matcher catches, the share that have this dimension among their 3 nearest (`MAX_TOPIC_TAGS` = 3), leave-one-out, with dimension centroids built from the matcher-caught members. The random-membership control replaces each dimension's members with a random set of the same size (it lands on the base rate, as it should). The cluster columns compare the matcher to the tree's cluster; *fidelity* is the cosine between the centroid built from the caught documents and the cluster's own centroid.

| dimension | cluster docs | docs its matcher catches | caught ÷ cluster | share in its own embedding neighbourhood (top-3) | lift over base rate | same, random-membership control | caught docs that are in the derived cluster | cluster docs the matcher catches | caught by format col/book/spe/bio | cluster recall by format % col/book/spe/bio | centroid built from the caught docs vs the derived cluster's own (cos) | terms |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- | ---: | ---: |
| life_story_family_school_and_church | 148 | 193 | 1.3× | 77% | 3.3× | 10% | 50% | 65% | 74/43/53/23 | 50/82/63/90 | 0.93 | 9 |
| criminal_trials_and_prosecutions | 94 | 164 | 1.7× | 70% | 4.1× | 4% | 43% | 74% | 139/21/4/0 | 73/88/–/– | 0.89 | 9 |
| international_law_disputes | 64 | 85 | 1.3× | 74% | 7.7× | 8% | 62% | 83% | 73/6/6/0 | 91/43/0/– | 0.97 | 5 |
| property_contracts_and_economic_rights | 62 | 66 | 1.1× | 70% | 7.1× | 17% | 53% | 56% | 25/33/6/2 | 55/58/50/– | 0.94 | 7 |
| how_the_supreme_court_decides | 59 | 21 | 0.4× | 76% | 7.2× | 10% | 67% | 24% | 14/6/1/0 | 24/20/50/– | 0.81 | 3 |
| libel_and_cybercrime | 56 | 28 | 0.5× | 61% | 8.1× | 11% | 43% | 21% | 24/3/1/0 | 27/11/–/– | 0.61 | 4 |
| presidential_power_martial_law_people_power | 53 | 45 | 0.8× | 64% | 9.7× | 4% | 62% | 53% | 25/14/3/3 | 61/43/0/100 | 0.90 | 7 |
| elections_and_automated_voting | 48 | 91 | 1.9× | 82% | 7.6× | 8% | 47% | 90% | 58/31/2/0 | 91/88/100/– | 0.97 | 2 |
| judiciary_milestones_and_tributes | 43 | 37 | 0.9× | 76% | 5.8× | 3% | 49% | 42% | 9/12/16/0 | 31/54/41/– | 0.89 | 3 |
| judicial_reform | 42 | 54 | 1.3× | 81% | 7.7× | 4% | 54% | 69% | 19/29/5/1 | 45/100/50/– | 0.94 | 3 |
| party_list_charter_change_and_dynasties | 40 | 68 | 1.7× | 75% | 7.3× | 18% | 56% | 95% | 46/17/5/0 | 97/86/100/– | 0.97 | 5 |
| science_technology_and_the_law | 39 | 63 | 1.6× | 73% | 12.2× | 3% | 43% | 69% | 29/29/5/0 | 61/75/100/– | 0.84 | 4 |
| economy_taxes_and_prosperity | 36 | 17 | 0.5× | 94% | 7.9× | 35% | 71% | 33% | 14/1/2/0 | 34/33/25/– | 0.90 | 3 |
| impeachment_accountability | 35 | 47 | 1.3× | 68% | 6.1× | 2% | 49% | 66% | 41/6/0/0 | 68/57/–/– | 0.94 | 5 |
| foundation_for_liberty_and_prosperity | 57 | 107 | 1.9× | 91% | 4.4× | 5% | 51% | 96% | 61/5/40/1 | 94/100/100/– | 0.96 | 12 |
| public_funds_budget_and_bank_evidence | 32 | 47 | 1.5× | 77% | 5.7× | 21% | 55% | 81% | 42/5/0/0 | 81/100/–/– | 0.93 | 5 |
| us_supreme_court_and_american_politics | 29 | 50 | 1.7× | 78% | 16.8× | 12% | 58% | 100% | 49/1/0/0 | 100/–/–/– | 0.95 | 2 |
| independent_commissions_and_appointments | 27 | 15 | 0.6× | 80% | 12.0× | 13% | 67% | 37% | 13/0/2/0 | 42/0/–/– | 0.87 | 3 |
| twin_beacons_doctrine | 27 | 41 | 1.5× | 80% | 8.4× | 0% | 39% | 59% | 12/9/20/0 | 30/60/83/– | 0.93 | 3 |
| marcos_robredo_election_contest | 26 | 38 | 1.5× | 74% | 7.1× | 21% | 47% | 69% | 31/4/1/2 | 67/100/–/– | 0.86 | 2 |
| bangsamoro_peace_process | 26 | 28 | 1.1× | 68% | 8.6× | 4% | 54% | 58% | 24/3/1/0 | 52/100/–/– | 0.88 | 3 |
| supreme_court_vacancies_and_chief_justiceship | 26 | 28 | 1.1× | 82% | 9.3× | 14% | 57% | 62% | 23/4/1/0 | 67/–/0/– | 0.93 | 5 |
| faith_journey | 26 | 49 | 1.9× | 80% | 6.0× | 2% | 43% | 81% | 11/24/11/3 | 100/79/75/67 | 0.94 | 3 |
| asean_law_association | 24 | 11 | 0.5× | 100% | 20.8× | 9% | 82% | 38% | 5/0/6/0 | 21/0/75/– | 0.85 | 1 |
| ill_gotten_wealth_and_the_pcgg | 23 | 27 | 1.2× | 74% | 8.5× | 11% | 56% | 65% | 23/4/0/0 | 60/100/–/– | 0.87 | 4 |
| citizenship_and_residency_grace_poe | 21 | 24 | 1.1× | 75% | 20.6× | 8% | 75% | 86% | 22/2/0/0 | 89/50/–/– | 0.98 | 2 |
| marriage_annulment_and_the_family_code | 21 | 29 | 1.4× | 79% | 13.1× | 28% | 55% | 76% | 16/10/2/1 | 77/83/50/– | 0.91 | 1 |
| bar_exam_and_legal_education | 21 | 20 | 1.0× | 70% | 12.4× | 15% | 45% | 43% | 14/4/2/0 | 70/0/67/– | 0.80 | 2 |
| jbc_discernment_and_appointment | 20 | 34 | 1.7× | 76% | 8.9× | 3% | 47% | 80% | 21/9/2/2 | 75/88/–/– | 0.88 | 3 |
| death_penalty_and_echegaray | — | 30 | — | 57% | 6.2× | 3% | — | — | 10/17/1/2 | –/–/–/– | — | 2 |

**Result.** Median neighbourhood share **76%** (random-membership control 9%, base rate 10%); median documents caught 39. The v1 matchers under the *same* definition: median neighbourhood share **39%** (base rate 7%) and median documents caught **109**; the largest v1 matchers fire on 611, 406 and 298 documents. No new matcher catches more than 193 documents or more than 1.9× its cluster.

**What this does and does not show.**

* **In-sample.** The final lists were chosen on the same 1,290 documents they are scored on, against the deliverable's own metric. The honest generalisation evidence is the earlier automatic procedure of the same family: on unseen documents (learn on a random half, score the other, centroids from the training half only) it recovered **44%** of its clusters' documents at neighbourhood precision **59%** (6.9× the base rate), against a random-set control of 0.00 recall (`ce9_results/ce9_07_heldout.log`). Expect the final lists to do somewhat worse than the table on new documents.
* **Keyword matching is weak in this corpus and cannot be made strong.** The haystack is title, summary, topic tags, keywords and entities. The words that *define* a subject ('impeachment', 'martial law', 'election') are also mentioned across other subjects, so any term precise enough to seed a centroid catches only part of the subject: median cluster recall 66%, and 7 of 29 dimensions are below half. That is acceptable **only because a matcher's job here is to give the centroid clean members**: median fidelity is 0.91; below 0.85: `how_the_supreme_court_decides` (0.81), `libel_and_cybercrime` (0.61), `science_technology_and_the_law` (0.84), `bar_exam_and_legal_education` (0.80). Everything else is tagged by affinity, which is what `merge_tag_topics.py` already does.
* **All four formats.** 59 of 61 (dimension × format) cells with at least 3 cluster documents have at least one caught document. The 2 that do not: `independent_commissions_and_appointments` × books (3 docs), `bar_exam_and_legal_education` × books (8 docs).

### v1 matchers under the same definition (baseline)

| v1 topic | docs its matcher catches | share in its own embedding neighbourhood (top-3) | lift over base rate |
| :--- | ---: | ---: | ---: |
| `constitutional_doctrine` | 611 | 37% | 1.7× |
| `supreme_court_history` | 406 | 40% | 1.9× |
| `faith_journey` | 298 | 38% | 3.5× |
| `family_and_marriage` | 272 | 39% | 2.8× |
| `philippine_political_landscape` | 238 | 43% | 2.8× |
| `twin_beacons_doctrine` | 213 | 23% | 5.3× |
| `rule_of_law` | 211 | 16% | 4.2× |
| `with_due_respect_persona` | 197 | 31% | 2.9× |
| `impeachment_accountability` | 171 | 53% | 3.6× |
| `icc_and_duterte` | 156 | 47% | 3.6× |
| `mentors_and_legal_lineage` | 156 | 27% | 4.5× |
| `due_process` | 145 | 58% | 2.2× |
| `flp_donors_and_partners` | 143 | 31% | 5.5× |
| `foundation_for_liberty_and_prosperity` | 136 | 35% | 8.0× |
| `bar_exam_and_legal_education` | 132 | 29% | 4.8× |
| `jbc_discernment_and_appointment` | 110 | 56% | 5.7× |
| `eulogies_and_passing` | 109 | 25% | 4.6× |
| `flp_scholarship_programs` | 109 | 28% | 9.1× |
| `judicial_reform` | 106 | 63% | 6.9× |
| `ai_and_technology` | 99 | 31% | 4.9× |
| `early_life_sampaloc` | 87 | 59% | 6.0× |
| `global_geopolitics` | 83 | 59% | 9.2× |
| `international_law_disputes` | 78 | 69% | 7.6× |
| `judicial_activism_and_political_question` | 78 | 23% | 4.4× |
| `friendships_and_civic_circles` | 76 | 53% | 5.4× |
| `lawyer_ethics_initiative` | 47 | 23% | 8.6× |
| `msme_and_entrepreneurship+prosperity_fund_msme` | 47 | 28% | 8.7× |
| `economic_governance_and_business_law` | 43 | 42% | 7.3× |
| `asean_law_association` | 39 | 54% | 12.0× |
| `death_penalty_and_echegaray` | 30 | 50% | 4.7× |
| `eez_resource_sovereignty` | 29 | 66% | 5.7× |
| `honors_received` | 24 | 17% | 2.5× |
| `museum_for_liberty_and_prosperity` | 20 | 65% | 23.3× |

## 9. Per-format orphan rate at the recommended floor and set

At floor 0.31, best-chunk, leave-one-out, the 30 dimensions above:

| format | documents | orphans | rate |
| :--- | ---: | ---: | ---: |
| columns | 803 | 32 | 4.0% |
| books | 299 | 7 | 2.3% |
| speeches | 153 | 4 | 2.6% |
| biography | 35 | 3 | 8.6% |
| **all** | 1290 | 46 | 3.6% |

Sensitivity — the best-chunk floor grid ("held-out" = leave-one-out; "as production would print it" leaves each member document inside its own centroids and so reads lower):

| floor | orphan rate, all docs (held-out) | columns | books | speeches | biography | all docs, as production would print it (own doc inside its centroids) | random-membership null |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.26 | 0.8% | 0.9% | 0.3% | 0.0% | 5.7% | 0.6% | 21.3% |
| 0.28 | 1.7% | 1.6% | 1.7% | 1.3% | 5.7% | 1.6% | 33.2% |
| 0.30 | 2.8% | 3.1% | 1.7% | 2.6% | 5.7% | 2.3% | 46.3% |
| 0.32 | 4.7% | 5.5% | 3.0% | 2.6% | 11.4% | 4.0% | 58.9% |
| 0.34 | 8.3% | 9.8% | 5.4% | 4.6% | 14.3% | 7.5% | 70.1% |
| 0.36 | 12.9% | 16.1% | 7.4% | 5.9% | 17.1% | 11.3% | 78.4% |
| 0.40 | 22.0% | 26.2% | 14.7% | 13.7% | 25.7% | 20.1% | 90.1% |

* **Columns are orphaned first** (4.0% vs books 2.3%), the same direction as Phase 3, but the gap is not significant on these counts (Fisher p = 0.27).
* **Biography: 3 of 35 (8.6%) — not finished.** The orphans: `GC012` *The Call from Malacañang -- and the First Refusal* (best affinity 0.258, nearest `marcos_robredo_election_contest`); `GC015` *The Bench* (best affinity 0.302, nearest `judiciary_milestones_and_tributes`); `GC018` *Retirement Without Retreat* (best affinity 0.255, nearest `judiciary_milestones_and_tributes`). All three belong to the cluster this proposal could not build a matcher for (the chief justiceship and a judicial career). Biography's separation from noise is the weakest of the four formats (AUC 0.86 vs 0.93 for columns). Fisher p = 0.13 against the other formats: three documents cannot prove a pattern and I am not claiming one; I am saying I cannot rule it out, and the three documents are exactly where the missing dimension would be.
* The tag budget: 698 documents (54%) keep three tags, 321 two, 225 one and 46 none.

## 10. What I decided not to propose, and why

**Recommended-level clusters that are not dimensions**

| what | why it is not a dimension |
| :--- | :--- |
| recommended-level cluster d24: Business Leaders and Philanthropy (24 docs) | MERGED into the Foundation dimension: on deployed centroids it is 0.74-0.78 of it whatever its matcher (the donors ARE the business leaders); partition centroids 0.58. |
| recommended-level cluster d26: Public Officials' Duties and Data Privacy (23 docs) | NOT PROPOSED, matcher unfinished: the best readable term set catches 6 of its 23 documents (no term reaches 0.5 precision at df >= 5; 'privacy' catches 48 documents, 8 of them inside). |
| recommended-level cluster d31: The Chief Justiceship and a Judicial Career (21 docs) | NOT PROPOSED, matcher unfinished: no readable term catches even 30% of its own documents (best: 'art's' 34 docs / 10 inside; 'davide standard' 16 / 4); a union of every promising term catches 570+ documents. Real in embedding space (10 biography chapters), invisible to metadata. |
| recommended-level cluster d32: Corporate Governance and Integrity (21 docs) | NOT PROPOSED, matcher unfinished: best readable set catches 4 of 21 documents; 'corporate governance' (16 docs, 7 inside), 'independent directors' (7, 4) and 'governance' (125 docs, 15 inside) are the only handles. |

**The three unbuilt clusters are not wrong; they are unreachable.** They are the smallest and most vocabulary-diffuse of the 33. What would unlock them is metadata, not a cleverer matcher: a curator-added tag on the ~20 documents of each, after which each can be tested against the four rules.

**The fine level's extra dimensions.** Section 3 lists the 16 fragments the fine level adds. None is promoted except the death-penalty fragment (section 5). Each is 11–19 documents, sits about 0.69 from its sibling (at the duplicate line) and would need its own matcher and separability test; any can be promoted individually on request.

**Phase 3's viable candidates** — 9 orphan clusters and 14 curated-keyword pools. Where each lands in the recommended partition:

| Phase 3 candidate | docs | where its documents land (dimension, docs) | verdict |
| :--- | ---: | :--- | :--- |
| Phase 3 orphan cluster P0 k=4 · c1 | 30 | criminal_trials_and_prosecutions 4; property_contracts_and_economic_rights 3; science_technology_and_the_law 3 | spread over dimensions (best holds 13%): a residual group of weakly covered documents, not a subject |
| Phase 3 orphan cluster P2 k=12 · c2 | 22 | faith_journey 15; life_story_family_school_and_church 4; marcos_robredo_election_contest 1 | is mostly `faith_journey` (68%) |
| Phase 3 orphan cluster P2 k=12 · c4 | 17 | economy_taxes_and_prosperity 5; public_funds_budget_and_bank_evidence 4; property_contracts_and_economic_rights 2 | spread over dimensions (best holds 29%): a residual group of weakly covered documents, not a subject |
| Phase 3 orphan cluster P2 k=12 · c1 | 14 | property_contracts_and_economic_rights 8; libel_and_cybercrime 2; how_the_supreme_court_decides 1 | is mostly `property_contracts_and_economic_rights` (57%) |
| Phase 3 orphan cluster P2 k=12 · c7 | 13 | elections_and_automated_voting 7; us_supreme_court_and_american_politics 2; independent_commissions_and_appointments 1 | is mostly `elections_and_automated_voting` (54%) |
| Phase 3 orphan cluster P2 k=12 · c8 | 11 | foundation_for_liberty_and_prosperity (its business-leaders cluster) 5; life_story_family_school_and_church 3; economy_taxes_and_prosperity 2 | partly inside `foundation_for_liberty_and_prosperity (its business-leaders cluster)` (45%), otherwise spread |
| Phase 3 orphan cluster P2 k=12 · c3 | 10 | science_technology_and_the_law 8; economy_taxes_and_prosperity 2 | is mostly `science_technology_and_the_law` (80%) |
| Phase 3 orphan cluster P2 k=12 · c10 | 10 | party_list_charter_change_and_dynasties 2; the unbuilt cluster 'Corporate Governance and Integrity' 2; libel_and_cybercrime 1 | spread over dimensions (best holds 20%): a residual group of weakly covered documents, not a subject |
| Phase 3 orphan cluster P2 k=12 · c12 | 10 | economy_taxes_and_prosperity 4; asean_law_association 2; international_law_disputes 2 | partly inside `economy_taxes_and_prosperity` (40%), otherwise spread |
| Phase 3 pool: supreme court | 75 | how_the_supreme_court_decides 11; presidential_power_martial_law_people_power 9; party_list_charter_change_and_dynasties 6 | spread over dimensions (best holds 15%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: congress | 15 | presidential_power_martial_law_people_power 4; how_the_supreme_court_decides 2; party_list_charter_change_and_dynasties 2 | spread over dimensions (best holds 27%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: grave abuse of discretion | 50 | property_contracts_and_economic_rights 12; how_the_supreme_court_decides 6; impeachment_accountability 6 | spread over dimensions (best holds 24%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: judicial independence | 22 | how_the_supreme_court_decides 11; science_technology_and_the_law 3; jbc_discernment_and_appointment 2 | is mostly `how_the_supreme_court_decides` (50%) |
| Phase 3 pool: integrity | 27 | jbc_discernment_and_appointment 6; presidential_power_martial_law_people_power 4; life_story_family_school_and_church 3 | spread over dimensions (best holds 22%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: reynato s. puno | 21 | property_contracts_and_economic_rights 7; judiciary_milestones_and_tributes 3; elections_and_automated_voting 2 | spread over dimensions (best holds 33%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: ombudsman | 17 | criminal_trials_and_prosecutions 4; independent_commissions_and_appointments 3; public_funds_budget_and_bank_evidence 3 | spread over dimensions (best holds 24%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: sandiganbayan | 26 | criminal_trials_and_prosecutions 13; ill_gotten_wealth_and_the_pcgg 5; libel_and_cybercrime 2 | is mostly `criminal_trials_and_prosecutions` (50%) |
| Phase 3 pool: vicente v. mendoza | 18 | libel_and_cybercrime 4; party_list_charter_change_and_dynasties 3; elections_and_automated_voting 2 | spread over dimensions (best holds 22%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: transparency | 24 | presidential_power_martial_law_people_power 5; science_technology_and_the_law 4; judiciary_milestones_and_tributes 3 | spread over dimensions (best holds 21%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: fidel v. ramos | 20 | life_story_family_school_and_church 6; presidential_power_martial_law_people_power 2; elections_and_automated_voting 2 | spread over dimensions (best holds 30%): a word or a name that occurs across subjects, not a subject |
| Phase 3 pool: people power | 17 | presidential_power_martial_law_people_power 8; life_story_family_school_and_church 2; elections_and_automated_voting 2 | partly inside `presidential_power_martial_law_people_power` (47%), otherwise spread |
| Phase 3 pool: hilario g. davide jr. | 23 | judicial_reform 9; the unbuilt cluster 'The Chief Justiceship and a Judicial Career' 3; how_the_supreme_court_decides 2 | partly inside `judicial_reform` (39%), otherwise spread |
| Phase 3 pool: constitution | 18 | how_the_supreme_court_decides 2; impeachment_accountability 2; bangsamoro_peace_process 2 | spread over dimensions (best holds 11%): a word or a name that occurs across subjects, not a subject |

The pools are words and names — 'supreme court', 'integrity', 'transparency', 'grave abuse of discretion', the names of former justices — that occur across subjects; none is a dimension. A few *corroborate* one (`sandiganbayan` half inside criminal trials, `people power` inside presidential power, `judicial independence` half inside how-the-Court-decides). The orphan clusters mostly land inside a single dimension (P2 k=12 · c2 → faith_journey (68%), P2 k=12 · c1 → property_contracts_and_economic_rights (57%), P2 k=12 · c7 → elections_and_automated_voting (54%), P2 k=12 · c3 → science_technology_and_the_law (80%)); one, P0 k=4 · c1 (30 documents), is a residual bag whose best dimension holds only 13% of it.

**Concept dimensions.** `rule_of_law`, `due_process`, `constitutional_doctrine`, `judicial_activism_and_political_question`, `with_due_respect_persona`: concepts and stances mentioned across the corpus have no place in it (Table 2).

## 11. Phase 5 dependencies — code that changes with this proposal (nothing was changed here)

1. **Centring (the metric change).** Store the corpus mean `mu` (768 floats, the mean of all chunk vectors) beside the centroids and record its hash in `topic_centroids_meta.json`. `scripts/build_centroids_fullcorpus.py`: centroid = `unit(mean(member chunks) − mu)`; its zero-member fallback (`gmean`) is no longer needed (every dimension here has at least 11 members; assert it). `scripts/merge_tag_topics.py`: the pair test at lines 42–46 then runs on centred centroids as written, but line 69 `cmat @ final_cen.T` must use centred chunk vectors (`unit(cmat − mu)`), and the floor at line 77 becomes 0.31 with the merge gate 0.75.
2. **Runtime routing — the part most likely to be missed.** `app/retrieval.py` line 91, `cos = cen @ qv`, uses raw query vectors against the centroids. If the stored centroids become centred, `qv` must be centred too, and every constant calibrated on raw route scores must be re-derived: `TOPIC_SOFTMAX_TEMPERATURE` (0.7), `OUT_OF_SCOPE_THRESHOLD` (0.15), `THEME_CONF_THRESHOLD` (0.51, derived from frozen route bands) and `TOPIC_MARGIN_THRESHOLD` (0.01). Two ways out, for you to choose: (a) centre only at build time and keep a raw copy of the new centroids for runtime routing (smallest blast radius; runtime routing stays as weakly discriminating as it is today), or (b) centre both and recalibrate. I recommend (a) for Phase 5 and (b) as a measured follow-up.
3. **`build_topic_map.load_docs()` (line 691) reads `columns`, `speeches` and `biography` — never `books`.** The 299 book chapters (23% of the corpus, 41% of the chunks) would not be tagged or counted. Add `books/**`. The stored v1 `topic_map.json` `doc_count`s (e.g. 30 for `rule_of_law`) are stale for that reason and because they predate the 1,290-document corpus.
4. **Topic-id-keyed tables.** `answer_pipeline.py` / `cj_chat.py` lines 127–163 (per-topic token budgets seeded from `theme_anchor`; an id missing from the table falls back to `TOKEN_BUDGET_DIM_DEFAULT` = 220, so new ids degrade gracefully but silently); `router_prompt.md` (regenerated from the taxonomy); `service.py` lines 96–118; the comment at `config.py` line 617 (names `honors_received`); at least 9 files under `eval/` (found by searching for `faith_journey`; search for every v1 id). The remap is in section 6.
5. **`robot_identity_meta`** keeps an entry outside the taxonomy (section 5).
6. **Verification.** `verify_pin.py` fails until Phase 5 regenerates the chunk/centroid pin, as before; the corpus mean vector must be pinned with it.

## 12. Reproduction and controls

All scripts are in `batch-04/ce7_analysis/` (read-only on the repo; cached intermediates in `cache/`, not committed; `ce9_results/` holds copies of the JSON outputs this document is built from, plus the held-out log): `ce9_00_entry.py` (branch/HEAD/file-hash guards), `ce9_00b_p33.py` (the collapse), `ce9_01_tree.py` / `ce9_03_levels.py` (tree and the three levels), `ce9_08*_*.py` (fate, candidate-side view, corroboration, pools, v1-matcher reuse), `ce9_12_readable.py` → `ce9_13_finalize.py` → `ce9_19_freeze.py` (matchers; `ce9_edits.py` holds the hand edits), `ce9_09_deploy.py` (deployed centroids, separability, both thresholds, orphan rates, v1 baseline), `ce9_17_pairs.py` (separability iteration), `ce9_14_assemble.py` + `ce9_14b_build.py` (this document), `ce9_20_verify_taxonomy_block.py` (proves Appendix A splices into a copy of `build_topic_map.py`, imports, and reproduces Table 1's document counts). Controls run: shuffled-feature null for the tree; random-membership control for every matcher; random-set control for induction; leave-one-out for every affinity; a 6-replicate multiple-comparison null for the floor. Hypotheses tried and **disproved along the way**: that a per-term precision filter alone yields readable matchers (it yields memorised names — `p11`, `kee`, `wdr3` — and was replaced); that a cluster-membership precision test finds a topic's defining words (it excludes them, because they are mentioned elsewhere); that the death-penalty pair is inseparable (on partition centroids it is 0.60; on deployed centroids it is 0.96 only while criminal law's matcher carries its terms).

## Appendix A — the complete `TAXONOMY` list

Replaces the `TAXONOMY` statement in `scripts/build_topic_map.py` **whole** — currently lines 70–645, from `TAXONOMY: list[dict[str, Any]] = [` to its closing `]` inclusive. (The brief cites 69–649; the extra lines are a blank line above and the blank lines and `# -- Matching engine` banner below, which should stay.) 30 entries. Not applied; `ce9_20_verify_taxonomy_block.py` splices this block into a copy, imports it and checks it.

```python
TAXONOMY: list[dict[str, Any]] = [
    # ===== Anchors (2) =====
    {
        "id": "foundation_for_liberty_and_prosperity",
        "display_name": "The Foundation for Liberty and Prosperity and Its Benefactors",
        "definition": "The Foundation's work and people: scholarships and dissertation fellows, its museum and Prosperity Fund, and the business leaders and donors who fund it.",
        "tier": "anchor",
        "theme_anchor": "D",
        "matchers": {
            "keywords": [
                "rvr", "csr", "philanthropy", "philanthropist", "busog lusog", "dissertation writing", "corporate social responsibility",
            ],
            "entities": [
                "jollibee", "george ty", "flp scholars society", "tan yan kee foundation", "museum for liberty and prosperity",
            ],
        },
    },
    {
        "id": "twin_beacons_doctrine",
        "display_name": "Liberty and Prosperity: the Twin Beacons",
        "definition": "The Chief Justice's core philosophy that liberty and prosperity depend on each other, and that both rest on the rule of law and social justice.",
        "tier": "anchor",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "social order", "twin beacons", "liberty prosperity",
            ],
            "entities": [],
        },
    },
    # ===== Core (13) =====
    {
        "id": "life_story_family_school_and_church",
        "display_name": "Life Story: Family, School and Church",
        "definition": "The Chief Justice's own life: his family, his schooling and mentors, his church and community life, and the eulogies and tributes he gives to people who shaped him.",
        "tier": "core",
        "theme_anchor": "C",
        "matchers": {
            "keywords": [
                "eulogy", "sampaloc", "jovito r. salonga",
            ],
            "entities": [
                "sylvia lina", "yale law school", "mapa high school", "far eastern university", "feu institute of law", "rotary club of manila",
            ],
        },
    },
    {
        "id": "criminal_trials_and_prosecutions",
        "display_name": "Criminal Trials, Prosecutions and the ICC",
        "definition": "How major criminal cases actually proceed in the Philippines: bail, probable cause, the Sandiganbayan and the plunder and pork-barrel trials, and the International Criminal Court's case against Duterte.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "bail", "plunder", "napoles", "probable cause", "moral turpitude", "warrant of arrest",
            ],
            "entities": [
                "mark jimenez", "fatou bensouda", "icc pre-trial chamber",
            ],
        },
    },
    {
        "id": "international_law_disputes",
        "display_name": "International Law: the West Philippine Sea and Arbitration",
        "definition": "The Philippines' sea dispute with China: the 2016 arbitral award, UNCLOS, the exclusive economic zone and the nine-dash line, and what international arbitration can and cannot enforce.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "icj", "west philippine sea",
            ],
            "entities": [
                "unclos", "un charter", "mutual defense treaty",
            ],
        },
    },
    {
        "id": "property_contracts_and_economic_rights",
        "display_name": "Property, Contracts and Labor Rights",
        "definition": "Supreme Court decisions on ownership, contracts, natural resources, investment and labor, read for what they mean for livelihoods and business.",
        "tier": "core",
        "theme_anchor": "B",
        "matchers": {
            "keywords": [
                "investors", "monopolies", "res judicata", "voting shares", "agan v. piatco",
            ],
            "entities": [
                "labor code", "department of environment and natural resources",
            ],
        },
    },
    {
        "id": "presidential_power_martial_law_people_power",
        "display_name": "Presidential Power, Martial Law and People Power",
        "definition": "The limits of presidential power in a crisis: martial law and rebellion, EDSA and the presidencies of Estrada and Arroyo.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "coup", "marawi", "romulo neri", "constitutional authoritarianism", "lagman vs medialdea",
            ],
            "entities": [
                "maute group", "edsa shrine",
            ],
        },
    },
    {
        "id": "elections_and_automated_voting",
        "display_name": "Elections and Automated Voting",
        "definition": "How Philippine elections are run and litigated: the Commission on Elections, precinct-count optical scanners and the disputes over automation.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ballots", "comelec's",
            ],
            "entities": [],
        },
    },
    {
        "id": "judicial_reform",
        "display_name": "Judicial Reform and Court Delay",
        "definition": "Reforming the courts: the Action Program for Judicial Reform, case backlogs, judges' pay and how to speed up justice.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "zero backlog", "judicial compensation",
            ],
            "entities": [
                "action program for judicial reform",
            ],
        },
    },
    {
        "id": "party_list_charter_change_and_dynasties",
        "display_name": "Party-List, Charter Change and Political Dynasties",
        "definition": "How Congress is chosen and the Constitution is amended: the party-list system, Charter change and political dynasties.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "con-ass", "dynasty", "charter change", "party-list seats",
            ],
            "entities": [
                "party-list law",
            ],
        },
    },
    {
        "id": "science_technology_and_the_law",
        "display_name": "Science, Technology and the Law",
        "definition": "How courts and lawyers should deal with new science: DNA and genetics, cloning, the internet and artificial intelligence.",
        "tier": "core",
        "theme_anchor": "E",
        "matchers": {
            "keywords": [
                "bio-age", "genetic", "smartphone", "artificial intelligence",
            ],
            "entities": [],
        },
    },
    {
        "id": "impeachment_accountability",
        "display_name": "Impeachment",
        "definition": "The impeachment process from the House to the Senate: its rules and limits, and the Corona and Sara Duterte cases.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "senate trial", "articles of impeachment", "francisco v. house of representatives",
            ],
            "entities": [
                "nixon", "sara duterte",
            ],
        },
    },
    {
        "id": "public_funds_budget_and_bank_evidence",
        "display_name": "Public Funds, the Budget and Bank Evidence",
        "definition": "How public money is spent and traced: the budget, the DAP and PDAF rulings, and bank deposits used as evidence of corruption.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "amla", "malampaya fund",
            ],
            "entities": [
                "psbank", "general appropriations act", "senate blue ribbon committee",
            ],
        },
    },
    {
        "id": "us_supreme_court_and_american_politics",
        "display_name": "The US Supreme Court and American Politics",
        "definition": "Commentary on the American presidency and the US Supreme Court, from Trump to Biden and the electoral college, and what they teach the Philippines.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "kagan", "donald",
            ],
            "entities": [],
        },
    },
    {
        "id": "faith_journey",
        "display_name": "Faith: Scripture, Prayer and the Gospel",
        "definition": "Reflections on scripture and prayer, on Jesus and the Gospel and on the Bukas Loob sa Diyos community, drawn mainly from the faith-themed books.",
        "tier": "core",
        "theme_anchor": "C",
        "matchers": {
            "keywords": [
                "gospel", "apostles",
            ],
            "entities": [
                "luke",
            ],
        },
    },
    # ===== Subordinate (15) =====
    {
        "id": "how_the_supreme_court_decides",
        "display_name": "How the Supreme Court Decides",
        "definition": "How the Court reasons and writes its decisions, and why the judiciary's independence from the other branches matters.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ata", "judicial activism", "decision-writing style",
            ],
            "entities": [],
        },
    },
    {
        "id": "libel_and_cybercrime",
        "display_name": "Libel and Cybercrime",
        "definition": "Criminal libel and cybercrime cases: the Maria Ressa cyberlibel prosecution, libel of public figures online, and the Cybercrime Prevention Act.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "libel", "cyberlibel", "cybercrime",
            ],
            "entities": [
                "maria ressa",
            ],
        },
    },
    {
        "id": "judiciary_milestones_and_tributes",
        "display_name": "The Judiciary's Milestones and Tributes",
        "definition": "Celebrations of the judiciary and of the people in it: the Supreme Court centenary, retirements, book launches, honors and tributes to fellow justices.",
        "tier": "subordinate",
        "theme_anchor": "C",
        "matchers": {
            "keywords": [
                "toast", "toobin",
            ],
            "entities": [
                "centenary executive committee",
            ],
        },
    },
    {
        "id": "economy_taxes_and_prosperity",
        "display_name": "The Economy, Taxes and Wages",
        "definition": "Economic policy seen through a lawyer's eyes: growth, jobs, taxes and wages, and what makes nations prosper.",
        "tier": "subordinate",
        "theme_anchor": "B",
        "matchers": {
            "keywords": [
                "minimum wage", "inclusive growth",
            ],
            "entities": [
                "asean integration",
            ],
        },
    },
    {
        "id": "death_penalty_and_echegaray",
        "display_name": "The Death Penalty and the Echegaray Reflection",
        "definition": "The Chief Justice's writing on capital punishment: the Echegaray case, the 2006 abolition of the death penalty and the conscience-versus-institution distinction.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "echegaray",
            ],
            "entities": [
                "death penalty",
            ],
        },
    },
    {
        "id": "independent_commissions_and_appointments",
        "display_name": "Independent Commissions and Appointments",
        "definition": "The constitutional commissions and the Ombudsman: how their officials are appointed, how long they serve and how independent they really are.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ad interim", "independent commission",
            ],
            "entities": [
                "ombudsman law",
            ],
        },
    },
    {
        "id": "bangsamoro_peace_process",
        "display_name": "The Bangsamoro Peace Process",
        "definition": "The peace agreements with the MILF, the Bangsamoro Basic Law and the question of whether they fit the Constitution.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "peace process", "armed conflict",
            ],
            "entities": [
                "moa-ad",
            ],
        },
    },
    {
        "id": "marcos_robredo_election_contest",
        "display_name": "The Marcos-Robredo Election Contest",
        "definition": "The vice-presidential protest of 2016 and the 2022 campaign that followed: canvassing, protests and what the results meant.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ppcrv's", "robredo",
            ],
            "entities": [],
        },
    },
    {
        "id": "supreme_court_vacancies_and_chief_justiceship",
        "display_name": "Supreme Court Vacancies and the Chief Justiceship",
        "definition": "Who sits on the Court and who leads it: retirements, appointments by President Duterte and the succession to the chief justiceship.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "jbc nominees", "senior justices", "duterte appointees", "cj teresita j. leonardo-de castro",
            ],
            "entities": [
                "cj renato corona",
            ],
        },
    },
    {
        "id": "asean_law_association",
        "display_name": "The ASEAN Law Association",
        "definition": "The regional association of lawyers and judges the Chief Justice helped lead, and the rule of law in Southeast Asia.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [],
            "entities": [
                "ala philippines",
            ],
        },
    },
    {
        "id": "ill_gotten_wealth_and_the_pcgg",
        "display_name": "Ill-Gotten Wealth and the PCGG",
        "definition": "The recovery of wealth amassed under Marcos: sequestration, forfeiture and the Sandiganbayan's rulings.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "luisita", "marcoses", "sequestration", "estate of marcos v. republic",
            ],
            "entities": [],
        },
    },
    {
        "id": "bar_exam_and_legal_education",
        "display_name": "The Bar Exam and Legal Education",
        "definition": "How lawyers are trained and admitted: the bar examinations, legal education and the profession's duties.",
        "tier": "subordinate",
        "theme_anchor": "D",
        "matchers": {
            "keywords": [
                "passers",
            ],
            "entities": [
                "legal education board",
            ],
        },
    },
    {
        "id": "citizenship_and_residency_grace_poe",
        "display_name": "Citizenship and Residency: the Grace Poe Case",
        "definition": "Who counts as a natural-born citizen (foundlings, dual citizens and residency), argued through the Grace Poe case.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "poe's", "naturalized",
            ],
            "entities": [],
        },
    },
    {
        "id": "marriage_annulment_and_the_family_code",
        "display_name": "Marriage, Annulment and the Family Code",
        "definition": "How the law treats marriage: psychological incapacity, nullity, divorce and the Family Code.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [],
            "entities": [
                "family code",
            ],
        },
    },
    {
        "id": "jbc_discernment_and_appointment",
        "display_name": "The Judicial and Bar Council",
        "definition": "How judges are nominated: the Council's role, its rules and the shortlist for each vacancy.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "jbc's", "ex-officio", "jbc chair",
            ],
            "entities": [],
        },
    },
]
```
