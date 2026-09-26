# CE-7 · step 6 — orphan clustering (document level, then chunk level)

**Date** 2026-09-26. Population, method and every caveat first; clusters after.

## Populations

The prompt specifies the documents scoring **zero** on every prior-art matcher (P0). That set is **46 documents** — too few to support k up to 40, and step 4 already showed the zero test is insensitive. Two broader populations are therefore clustered alongside it, and labelled as additions:

| population | docs | by format (col / book / spe / bio) | chunks |
|---|---:|---:|---:|
| P0 strict (zero score) | 46 | 25 / 13 / 7 / 1 | 565 |
| P1 weak (score ≤ 1) | 240 | 150 / 67 / 17 / 6 | 2526 |
| P2 embedding orphans (bottom 10% per format) | 131 | 81 / 30 / 16 / 4 | 1108 |

Each document is represented by the **mean of its chunk vectors** (unit-normalised), so a long book chapter and a short column are one point each. k-means (`n_init` 10, fixed seed), silhouette on cosine distance, k = 2…40 (capped at N−1). **Null**: the same procedure on the same number of *randomly drawn documents* from the whole corpus (3 draws averaged) — a silhouette only counts as structure to the extent it beats that.

## Document-level silhouette curves, k = 2…40

| k | P0 silhouette | P0 null | P1 silhouette | P1 null | P2 silhouette | P2 null |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.133 | 0.127 | 0.097 | 0.133 | 0.130 | 0.146 |
| 3 | 0.094 | 0.074 | 0.086 | 0.106 | 0.126 | 0.085 |
| 4 | 0.119 | 0.073 | 0.077 | 0.071 | 0.133 | 0.086 |
| 5 | 0.131 | 0.072 | 0.065 | 0.068 | 0.125 | 0.087 |
| 6 | 0.136 | 0.071 | 0.074 | 0.075 | 0.121 | 0.078 |
| 7 | 0.137 | 0.057 | 0.075 | 0.068 | 0.121 | 0.080 |
| 8 | 0.109 | 0.089 | 0.074 | 0.070 | 0.123 | 0.068 |
| 9 | 0.171 | 0.084 | 0.081 | 0.075 | 0.120 | 0.055 |
| 10 | 0.145 | 0.074 | 0.071 | 0.072 | 0.128 | 0.072 |
| 11 | 0.184 | 0.076 | 0.054 | 0.074 | 0.132 | 0.074 |
| 12 | 0.173 | 0.080 | 0.059 | 0.067 | 0.139 | 0.054 |
| 13 | 0.155 | 0.069 | 0.083 | 0.046 | 0.132 | 0.072 |
| 14 | 0.169 | 0.088 | 0.084 | 0.070 | 0.134 | 0.072 |
| 15 | 0.174 | 0.082 | 0.078 | 0.062 | 0.133 | 0.067 |
| 16 | 0.177 | 0.079 | 0.064 | 0.049 | 0.142 | 0.064 |
| 17 | 0.147 | 0.070 | 0.077 | 0.061 | 0.125 | 0.070 |
| 18 | 0.172 | 0.077 | 0.088 | 0.057 | 0.164 | 0.071 |
| 19 | 0.171 | 0.082 | 0.082 | 0.063 | 0.162 | 0.070 |
| 20 | 0.177 | 0.093 | 0.061 | 0.064 | 0.137 | 0.070 |
| 21 | 0.172 | 0.078 | 0.079 | 0.067 | 0.149 | 0.069 |
| 22 | 0.171 | 0.085 | 0.054 | 0.082 | 0.159 | 0.071 |
| 23 | 0.170 | 0.071 | 0.079 | 0.066 | 0.143 | 0.078 |
| 24 | 0.182 | 0.084 | 0.075 | 0.061 | 0.154 | 0.062 |
| 25 | 0.182 | 0.089 | 0.074 | 0.059 | 0.156 | 0.076 |
| 26 | 0.170 | 0.079 | 0.072 | 0.073 | 0.173 | 0.068 |
| 27 | 0.167 | 0.096 | 0.083 | 0.060 | 0.163 | 0.076 |
| 28 | 0.156 | 0.094 | 0.081 | 0.066 | 0.159 | 0.064 |
| 29 | 0.168 | 0.094 | 0.098 | 0.070 | 0.193 | 0.056 |
| 30 | 0.160 | 0.097 | 0.100 | 0.072 | 0.188 | 0.077 |
| 31 | 0.155 | 0.082 | 0.075 | 0.061 | 0.177 | 0.062 |
| 32 | 0.157 | 0.093 | 0.078 | 0.054 | 0.191 | 0.062 |
| 33 | 0.144 | 0.080 | 0.090 | 0.065 | 0.148 | 0.073 |
| 34 | 0.140 | 0.079 | 0.082 | 0.063 | 0.204 | 0.067 |
| 35 | 0.126 | 0.078 | 0.069 | 0.064 | 0.178 | 0.071 |
| 36 | 0.129 | 0.085 | 0.091 | 0.069 | 0.193 | 0.070 |
| 37 | 0.125 | 0.076 | 0.088 | 0.060 | 0.186 | 0.084 |
| 38 | 0.110 | 0.079 | 0.079 | 0.064 | 0.204 | 0.078 |
| 39 | 0.107 | 0.076 | 0.113 | 0.073 | 0.196 | 0.083 |
| 40 | 0.100 | 0.069 | 0.091 | 0.069 | 0.186 | 0.064 |

### Knees

| population | N | silhouette maximum | max excess over null | inertia elbow (kneedle) | k range within 0.02 of the maximum | best k with average cluster ≥ 10 docs | mean excess over null (all k) |
|---|---:|---:|---:|---:|---:|---:|---:|
| P0 strict (zero score) | 46 | k=11 (0.184) | k=11 (+0.108) | k=11 | 9–29 | k=4 (cap 4) | +0.069 |
| P1 weak (score ≤ 1) | 240 | k=39 (0.113) | k=39 (+0.041) | k=13 | 2–39 | k=13 (cap 24) | +0.011 |
| P2 embedding orphans (bottom 10% per format) | 131 | k=38 (0.204) | k=29 (+0.137) | k=18 | 29–40 | k=12 (cap 13) | +0.081 |

**Reading the curves.** P0: mean silhouette excess over null +0.069, maximum 0.184. P1: mean silhouette excess over null +0.011, maximum 0.113. P2: mean silhouette excess over null +0.081, maximum 0.204. A silhouette below ~0.25 is conventionally weak structure; none of these curves leaves that band.

## Cluster detail — P0 (the prompt's population)

Two views: **k = 11**, the silhouette maximum (the prompt's “chosen k”, the knee of the full curve), and **k = 4**, the coarsest scale at which clusters average ≥ 10 documents (the smallest size this phase treats as a viable dimension). At the first, clusters are small; that is reported, not hidden.

### P0 view 1: P0 strict (zero score) at k = 11

silhouette 0.184 · bootstrap stability (ARI of 20 × 80% resamples vs the full fit): mean 0.46, worst 0.20 · cluster sizes (docs): [7, 6, 6, 5, 5, 4, 4, 3, 2, 2, 2]

**Cluster 4** — **7 distinct docs**, 50 raw chunks (7.1 chunks/doc)
* format mix, each as a share of that format's own docs — col 7 (28.0% of pop. / 0.9% of corpus)
* top-15 TF-IDF terms: crude, steel, ofws, buses, countries, traffic, abolish, economy, petroleum, logging, ofw, dubai, liter, immigration, demand
* exemplars (nearest the cluster centre): `CA436` Many faces of DAP; `CA470` To abolish or not to abolish the PCGG; `CC092` Good enough for the first week; `CE116` OFWs to the world; `CE112` How to be a tourism billionaire

**Cluster 2** — **6 distinct docs**, 44 raw chunks (7.3 chunks/doc)
* format mix, each as a share of that format's own docs — col 5 (20.0% of pop. / 0.6% of corpus) · spe 1 (14.3% of pop. / 0.7% of corpus)
* top-15 TF-IDF terms: accused, maguindanao massacre, maguindanao, trial court, massacre, trial, leak, witnesses, twice, postponement, unblemished, different, reyes, witness, evidence
* exemplars (nearest the cluster centre): `CE094` Show proof or apologize; `CA520` Speeding up justice in Maguindanao massacre; `CA297` Hastening trials in criminal cases; `CA522` Canard of a leak; `CA129` Murders, autopsies, and death certificates

**Cluster 3** — **6 distinct docs**, 58 raw chunks (9.7 chunks/doc)
* format mix, each as a share of that format's own docs — col 2 (8.0% of pop. / 0.2% of corpus) · boo 3 (23.1% of pop. / 1.0% of corpus) · bio 1 (100.0% of pop. / 2.9% of corpus)
* books by work: The Bio-Age Dawns on the Judiciary ×2; Battles in the Supreme Court ×1
* top-15 TF-IDF terms: dawns judiciary, bio-age dawns, justices, bio-age, dawns, conscience, magistrates, personal, judged, esteem, meritorious, judges, appellate, free ideas, jurist
* exemplars (nearest the cluster centre): `BD025` The Bio-Age Dawns on the Judiciary -- Ch. 5: Excellence and Ethics in ; `BD030` Battles in the Supreme Court -- Ch. 11: Epilogue: THE REAL VICTORY; `BD026` The Bio-Age Dawns on the Judiciary -- Ch. 6: Veracious and Venerable M; `CA255` Focus on trial judges; `CA521` Justices' SALN and other FAQs

**Cluster 6** — **5 distinct docs**, 30 raw chunks (6.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 1 (4.0% of pop. / 0.1% of corpus) · boo 1 (7.7% of pop. / 0.3% of corpus) · spe 3 (42.9% of pop. / 2.0% of corpus)
* books by work: Love God, Serve Man ×1
* top-15 TF-IDF terms: god, asta, charo, lord, santuario san, santuario, special minister, american dream, san antonio, drink, ordinary parishioner, parishioner, serve, mission, arrangements protocols
* exemplars (nearest the cluster centre): `SC104` God of Justice and Love; `SC109` Equality Before God and His Church; `CC117` The same yesterday, today and tomorrow (1); `SC118` A Toast to Charo; `BB010` Love God, Serve Man -- Ch. 13: A Salute to ASTA

**Cluster 10** — **5 distinct docs**, 145 raw chunks (29.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 2 (8.0% of pop. / 0.2% of corpus) · boo 3 (23.1% of pop. / 1.0% of corpus)
* books by work: The Bio-Age Dawns on the Judiciary ×3
* top-15 TF-IDF terms: judiciary appendix, appendix, genetic, dawns judiciary, bio-age dawns, bio-age, dawns, rape, victim, civil degree, information, dna, personal information, heavier, protection
* exemplars (nearest the cluster centre): `BA050` The Bio-Age Dawns on the Judiciary -- Appendix C: DNA as Evidence; `BE029` The Bio-Age Dawns on the Judiciary -- Appendix D: Being Moral in the B; `BE028` The Bio-Age Dawns on the Judiciary -- Appendix B: GMO & Food Products; `CA094` Prime duty of lawyers, prosecutors, judges; `CA242` Right to be forgotten

**Cluster 9** — **4 distinct docs**, 93 raw chunks (23.2 chunks/doc)
* format mix, each as a share of that format's own docs — boo 4 (30.8% of pop. / 1.3% of corpus)
* books by work: The Bio-Age Dawns on the Judiciary ×3; Leadership by Example: The Davide Standard ×1
* top-15 TF-IDF terms: dawns judiciary, bio-age dawns, bio-age, dawns, disqualified, comelec, election, elective, votes, section, election laws, candidate, mayor, popular sovereignty, three-term
* exemplars (nearest the cluster centre): `BA047` The Bio-Age Dawns on the Judiciary -- Ch. 12: Macalintal v. Comelec — ; `BA046` The Bio-Age Dawns on the Judiciary -- Ch. 11: Ang Bagong Bayani v. Com; `BA042` The Bio-Age Dawns on the Judiciary -- Ch. 7: Socrates v. Comelec — The; `BA064` Leadership by Example: The Davide Standard -- Ch. 13: Upholding Popula

**Cluster 11** — **4 distinct docs**, 76 raw chunks (19.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 1 (4.0% of pop. / 0.1% of corpus) · boo 2 (15.4% of pop. / 0.7% of corpus) · spe 1 (14.3% of pop. / 0.7% of corpus)
* books by work: The Bio-Age Dawns on the Judiciary ×2
* top-15 TF-IDF terms: contract, contractor, pdrci, labor-only contracting, arbitration clause, labor-only, contracting, dawns judiciary, bio-age dawns, arbitration, bio-age, dawns, investment, method, capitalized
* exemplars (nearest the cluster centre): `BA045` The Bio-Age Dawns on the Judiciary -- Ch. 10: Agan v. Piatco — Validit; `BA043` The Bio-Age Dawns on the Judiciary -- Ch. 8: Republic v. Meralco — Ora; `SA096` A Milestone at PDRCI; `CA312` Job contracting vs labor-only contracting

**Cluster 1** — **3 distinct docs**, 20 raw chunks (6.7 chunks/doc)
* format mix, each as a share of that format's own docs — col 3 (12.0% of pop. / 0.4% of corpus)
* top-15 TF-IDF terms: voter, glitches, ballots, preproclamation, voters, manual, preproclamation controversies, ballot, elections, cheating, automation, manual elections, comelec, goons, guns goons
* exemplars (nearest the cluster centre): `CE067` Huwag kang gunggong'; `CE066` Back to manual elections?; `CE052` The cost of presidential campaigns

**Cluster 5** — **2 distinct docs**, 18 raw chunks (9.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 2 (8.0% of pop. / 0.2% of corpus)
* top-15 TF-IDF terms: lct, mysterious stem, block, stem cells, daniel block, cells, clinic, petra, stem, prostate, mysterious, petra block, morato, serrano, daniel
* exemplars (nearest the cluster centre): `CC025` Mysterious stem cells: LCT procedure (3); `CC024` Mysterious stem cells: Unraveling the mystery (Part 4)

**Cluster 7** — **2 distinct docs**, 16 raw chunks (8.0 chunks/doc)
* format mix, each as a share of that format's own docs — spe 2 (28.6% of pop. / 1.3% of corpus)
* top-15 TF-IDF terms: ids, directors, independent directors, independent director, corporation, corporation code, independent judgment, articles bylaws, bylaws, director, independent, shareholders, corporate, subsidiaries, sec
* exemplars (nearest the cluster centre): `SB094` Rights, Duties and Perks of Independent Directors; `SB065` Attributes of a Good Independent Director

**Cluster 8** — **2 distinct docs**, 15 raw chunks (7.5 chunks/doc)
* format mix, each as a share of that format's own docs — col 2 (8.0% of pop. / 0.2% of corpus)
* top-15 TF-IDF terms: laundering, money laundering, ransom, unlawful activity, kidnapping, depositing, dealers, tax evasion, casinos, amla, transacted, proceeds, evasion, proceeds unlawful, cash proceeds
* exemplars (nearest the cluster centre): `CA347` Money Laundering 101; `CA222` Laundering dirty money

### P0 view 2: P0 strict (zero score) at k = 4

silhouette 0.119 · bootstrap stability (ARI of 20 × 80% resamples vs the full fit): mean 0.33, worst 0.01 · cluster sizes (docs): [30, 8, 5, 3]

**Cluster 1** — **30 distinct docs**, 456 raw chunks (15.2 chunks/doc)
* format mix, each as a share of that format's own docs — col 13 (52.0% of pop. / 1.6% of corpus) · boo 12 (92.3% of pop. / 4.0% of corpus) · spe 4 (57.1% of pop. / 2.6% of corpus) · bio 1 (100.0% of pop. / 2.9% of corpus)
* books by work: The Bio-Age Dawns on the Judiciary ×10; Leadership by Example: The Davide Standard ×1; Battles in the Supreme Court ×1
* top-15 TF-IDF terms: bio-age dawns, dawns judiciary, bio-age, dawns, judiciary, personal, trial, person, code, different, judges, director, rules, accused, justices
* exemplars (nearest the cluster centre): `BD025` The Bio-Age Dawns on the Judiciary -- Ch. 5: Excellence and Ethics in ; `CA521` Justices' SALN and other FAQs; `CE094` Show proof or apologize; `BA047` The Bio-Age Dawns on the Judiciary -- Ch. 12: Macalintal v. Comelec — ; `BD030` Battles in the Supreme Court -- Ch. 11: Epilogue: THE REAL VICTORY

**Cluster 2** — **8 distinct docs**, 58 raw chunks (7.2 chunks/doc)
* format mix, each as a share of that format's own docs — col 8 (32.0% of pop. / 1.0% of corpus)
* top-15 TF-IDF terms: crude, million, tax, steel, ofws, buses, countries, billion, traffic, economy, guns, petroleum, logging, ofw, barrel
* exemplars (nearest the cluster centre): `CA436` Many faces of DAP; `CC092` Good enough for the first week; `CE116` OFWs to the world; `CE052` The cost of presidential campaigns; `CE067` Huwag kang gunggong'

**Cluster 4** — **5 distinct docs**, 30 raw chunks (6.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 1 (4.0% of pop. / 0.1% of corpus) · boo 1 (7.7% of pop. / 0.3% of corpus) · spe 3 (42.9% of pop. / 2.0% of corpus)
* books by work: Love God, Serve Man ×1
* top-15 TF-IDF terms: god, asta, charo, lord, santuario san, santuario, special minister, american dream, san antonio, drink, ordinary parishioner, parishioner, serve, mission, arrangements protocols
* exemplars (nearest the cluster centre): `SC104` God of Justice and Love; `SC109` Equality Before God and His Church; `CC117` The same yesterday, today and tomorrow (1); `SC118` A Toast to Charo; `BB010` Love God, Serve Man -- Ch. 13: A Salute to ASTA

**Cluster 3** — **3 distinct docs**, 21 raw chunks (7.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 3 (12.0% of pop. / 0.4% of corpus)
* top-15 TF-IDF terms: laundering, money laundering, ransom, unlawful activity, kidnapping, depositing, dealers, tax evasion, casinos, amla, transacted, proceeds, evasion, cash proceeds, proceeds unlawful
* exemplars (nearest the cluster centre): `CA347` Money Laundering 101; `CA222` Laundering dirty money; `CE066` Back to manual elections?

## Cluster detail — P2 (format-fair embedding orphans; addition)

Described at **k = 12** (best null-adjusted silhouette with an average cluster of ≥ 10 documents; the silhouette maximum is at k=38 but there clusters average 3.4 documents).

### P2: P2 embedding orphans (bottom 10% per format) at k = 12

silhouette 0.139 · bootstrap stability (ARI of 20 × 80% resamples vs the full fit): mean 0.48, worst 0.39 · cluster sizes (docs): [22, 17, 14, 13, 11, 10, 10, 10, 9, 7, 5, 3]

**Cluster 2** — **22 distinct docs**, 172 raw chunks (7.8 chunks/doc)
* format mix, each as a share of that format's own docs — col 3 (3.7% of pop. / 0.4% of corpus) · boo 12 (40.0% of pop. / 4.0% of corpus) · spe 5 (31.2% of pop. / 3.3% of corpus) · bio 2 (50.0% of pop. / 5.7% of corpus)
* books by work: Love God, Serve Man ×5; Justice and Faith ×5; With Due Respect ×2
* top-15 TF-IDF terms: jesus, lord, god, christ, love, faith, bld, prayer, man, spirit, life, serve, disciples, holy, holy spirit
* exemplars (nearest the cluster centre): `BC016` Justice and Faith -- Ch. 9: Jesus, Shepherd and Leader of All Time; `CC034` Jesus Christ, our King and Leader (2); `BC017` Justice and Faith -- Ch. 10: Offering to the Father; `BC027` Love God, Serve Man -- Ch. 9: Bukas Loob sa Diyos: Called to Evangeliz; `SC153` The Leader in Jesus

**Cluster 4** — **17 distinct docs**, 126 raw chunks (7.4 chunks/doc)
* format mix, each as a share of that format's own docs — col 16 (19.8% of pop. / 2.0% of corpus) · boo 1 (3.3% of pop. / 0.3% of corpus)
* books by work: Liberty and Prosperity ×1
* top-15 TF-IDF terms: million, cash, tax, billion, banks, taxes, bank, funds, pay, corruption, transactions, deposits, spending, money, proceeds
* exemplars (nearest the cluster centre): `CA222` Laundering dirty money; `CA299` Bank deposits as evidence of corruption; `CE052` The cost of presidential campaigns; `CA145` Why Soce is important; `CA337` PDAF and DAP in new budget?

**Cluster 1** — **14 distinct docs**, 140 raw chunks (10.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 9 (11.1% of pop. / 1.1% of corpus) · boo 5 (16.7% of pop. / 1.7% of corpus)
* books by work: Leadership by Example: The Davide Standard ×2; Liberty and Prosperity ×2; Transparency, Unanimity & Diversity ×1
* top-15 TF-IDF terms: code, contracting, safety, order, labor-only, labor-only contracting, contractor, prior, employees, right, shall, act, prior marriage, authority, substantial capital
* exemplars (nearest the cluster centre): `BA106` Liberty and Prosperity -- Ch. 32: Mirasol v. DPWH: Regulation of Traff; `BA062` Leadership by Example: The Davide Standard -- Ch. 11: Common Meaning o; `CA234` Right to regulate passage in subdivisions; `CA276` Legal and illegal labor contracting; `BB016` Leadership by Example: The Davide Standard -- Ch. 10: Civil Servants' 

**Cluster 7** — **13 distinct docs**, 90 raw chunks (6.9 chunks/doc)
* format mix, each as a share of that format's own docs — col 11 (13.6% of pop. / 1.4% of corpus) · boo 2 (6.7% of pop. / 0.7% of corpus)
* books by work: With Due Respect ×2
* top-15 TF-IDF terms: ballots, voters, comelec, election, votes, precinct, ballot, candidates, candidate, elections, electoral, voter, electors, polls, total
* exemplars (nearest the cluster centre): `BE015` With Due Respect (Vol. 5) -- Ch. 9: 'Hindi Puede ang Puede na'; `BA019` With Due Respect (Vol. 5) -- Ch. 1: Subverting the Popular Will; `CE066` Back to manual elections?; `CA350` VVPAT and other electoral reforms; `CE044` Withdraw the Comelec Precinct Finder

**Cluster 8** — **11 distinct docs**, 88 raw chunks (8.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 6 (7.4% of pop. / 0.7% of corpus) · boo 1 (3.3% of pop. / 0.3% of corpus) · spe 3 (18.8% of pop. / 2.0% of corpus) · bio 1 (25.0% of pop. / 2.9% of corpus)
* books by work: Love God, Serve Man ×1
* top-15 TF-IDF terms: store, jollibee, jfc, manila, awardee, world-class, tea, tony, meal, world, caktiong, tan caktiong, tony tan, chickenjoy, rvr
* exemplars (nearest the cluster centre): `CC070` Henry Sy Sr.: Vision and passion; `SD022` A Truly World-Class Filipino Entrepreneur; `CC044` World-class Filipino enterprise; `CC023` Bert Lina's legacy of love; `CC039` Toyota PH, celebrating 35 years as #1

**Cluster 3** — **10 distinct docs**, 159 raw chunks (15.9 chunks/doc)
* format mix, each as a share of that format's own docs — col 6 (7.4% of pop. / 0.7% of corpus) · boo 4 (13.3% of pop. / 1.3% of corpus)
* books by work: The Bio-Age Dawns on the Judiciary ×3; Leveling the Playing Field ×1
* top-15 TF-IDF terms: bio-age, human, cell, dawns judiciary, bio-age dawns, dawns, scientific, vaccines, dna, marie, cells, genetic, vaccine, science, carmina
* exemplars (nearest the cluster centre): `BE028` The Bio-Age Dawns on the Judiciary -- Appendix B: GMO & Food Products; `BE034` Leveling the Playing Field -- Ch. 14: Ethics in the Biotechnological R; `CE102` Controversial consequences of biotechnology; `CA058` Why courts are interested in new sciences; `CE058` Use of aborted fetuses in vaccines

**Cluster 10** — **10 distinct docs**, 67 raw chunks (6.7 chunks/doc)
* format mix, each as a share of that format's own docs — col 6 (7.4% of pop. / 0.7% of corpus) · boo 1 (3.3% of pop. / 0.3% of corpus) · spe 2 (12.5% of pop. / 1.3% of corpus) · bio 1 (25.0% of pop. / 2.9% of corpus)
* books by work: With Due Respect ×1
* top-15 TF-IDF terms: democracy, dynasties, ids, governance, dynasty, chel, code, dynasties endure, directors, independent directors, birth, article section, grounded, independent director, children
* exemplars (nearest the cluster centre): `CE014` Dynasty, not evil per se; merely abused; `CE016` Why dynasties endure; `SB065` Attributes of a Good Independent Director; `SB094` Rights, Duties and Perks of Independent Directors; `CA518` Rights of illegitimate children

**Cluster 12** — **10 distinct docs**, 79 raw chunks (7.9 chunks/doc)
* format mix, each as a share of that format's own docs — col 7 (8.6% of pop. / 0.9% of corpus) · boo 3 (10.0% of pop. / 1.0% of corpus)
* books by work: With Due Respect ×3
* top-15 TF-IDF terms: japan, china, world, nuclear, war, billion, lou, duck, hotels, mvp, plan, avoid, war iii, middle east, buses
* exemplars (nearest the cluster centre): `BC005` With Due Respect (Vol. 7) -- Ch. 12: Japan, the New and the Old; `BB002` With Due Respect (Vol. 7) -- Ch. 7: Understanding China; `CC092` Good enough for the first week; `CE063` Unity in the war on COVID-19; `CB014` Work for peace but brace for war

**Cluster 5** — **9 distinct docs**, 74 raw chunks (8.2 chunks/doc)
* format mix, each as a share of that format's own docs — col 3 (3.7% of pop. / 0.4% of corpus) · spe 6 (37.5% of pop. / 3.9% of corpus)
* top-15 TF-IDF terms: cathedral, bells, cathedral-basilica, manila cathedral, manila cathedral-basilica, immaculate, carillon, cardinal, belfry, immaculate conception, church, manila, cathedral-basilica foundation, sylvia, bert
* exemplars (nearest the cluster centre): `CC104` Mother church of all churches' reopens; `CC015` Manila Cathedral: sad news, good news; `SC100` Bulwark of Filipino Catholicism; `SC070` Thank You from the Manila Cathedral; `SC077` The Manila Cathedral-Basilica Reopens

**Cluster 9** — **7 distinct docs**, 59 raw chunks (8.4 chunks/doc)
* format mix, each as a share of that format's own docs — col 6 (7.4% of pop. / 0.7% of corpus) · boo 1 (3.3% of pop. / 0.3% of corpus)
* books by work: With Due Respect ×1
* top-15 TF-IDF terms: cells, stem cells, lct, stem, mysterious stem, cell, block, therapy, cancer, sheep, cell therapy, siegfried, mysterious, siegfried block, medical
* exemplars (nearest the cluster centre): `CC027` Mysterious stem cells: Autologous (1); `CC024` Mysterious stem cells: Unraveling the mystery (Part 4); `CC025` Mysterious stem cells: LCT procedure (3); `CC026` Mysterious stem cells: ASC infusion process (2); `CC029` Search for the illusive fountain of youth

**Cluster 11** — **5 distinct docs**, 33 raw chunks (6.6 chunks/doc)
* format mix, each as a share of that format's own docs — col 5 (6.2% of pop. / 0.6% of corpus)
* top-15 TF-IDF terms: intelligence, cybersecurity, digital, curious, research, robots, data, personalized, adaptive, companies, humans, artificial intelligence, create, enhance, nvidia
* exemplars (nearest the cluster centre): `CE019` AI can create value and build trust; `CE018` AI and the freedom to ask; `CE011` Robotics, for better or for worse; `CE033` I won't fly QR again; Nvidia on a blitz; `CE078` The future is now

**Cluster 6** — **3 distinct docs**, 21 raw chunks (7.0 chunks/doc)
* format mix, each as a share of that format's own docs — col 3 (3.7% of pop. / 0.4% of corpus)
* top-15 TF-IDF terms: nixon, pardon, biden, watergate, clinton, ford, nixon's, biden's, oxymoron, trump, joe, divided united, states, watergate scandal, clemency
* exemplars (nearest the cluster centre): `CA510` Impeachment and resignation; `CA194` Can presidents pardon themselves?; `CE056` An oxymoron: A divided United States

## P1 (weak coverage; addition) — no cluster detail

Mean silhouette excess over the random-document null is +0.011 and the maximum is 0.113 (null at that k: 0.073). **The 240 weakly-covered documents do not form clusters any more than 240 random documents do.** They are documents whose metadata happened to match few matcher terms, not a missing topic; clustering them further would describe noise.

## Chunk-level cross-check

Population chunks are all the chunks of the population's documents. Two runs each, because book chapters contribute 18 chunks against a column's 7: **unweighted** (every chunk counts once — carries the book skew) and **document-weighted** (every chunk weighted 1 / its document's chunk count, so each document counts once). Silhouette is computed unweighted in both (scikit-learn has no weighted silhouette); only the k-means fit differs.

*(Chunk clusters are numbered independently of document clusters; the cross-table below shows the correspondence.)*

### P0: P0 strict (zero score) — 565 chunks from 46 documents

| k | unweighted | doc-weighted |
|---:|---:|---:|
| 2 | 0.109 | 0.109 |
| 3 | 0.108 | 0.120 |
| 4 | 0.115 | 0.130 |
| 5 | 0.119 | 0.113 |
| 6 | 0.141 | 0.141 |
| 7 | 0.152 | 0.114 |
| 8 | 0.125 | 0.129 |
| 9 | 0.137 | 0.125 |
| 10 | 0.150 | 0.162 |
| 11 | 0.162 | 0.171 |
| 12 | 0.167 | 0.168 |
| 16 | 0.168 | 0.166 |
| 20 | 0.221 | 0.195 |
| 24 | 0.188 | 0.207 |
| 28 | 0.209 | 0.232 |
| 32 | 0.247 | 0.238 |
| 36 | 0.208 | 0.252 |
| 40 | 0.210 | 0.262 |

Silhouette maximum: unweighted k=32 (0.247); document-weighted k=37 (0.279). Document-level knee for this population: k=11.

**unweighted k-means, k = 11** — per cluster: raw chunks, distinct documents, share of the cluster's chunks that come from its 3 biggest documents (high ⇒ a few documents), *cohesion* = average share of each member document's own chunks that also sit in this cluster (high ⇒ whole documents, low ⇒ passages from many documents), format mix as a share of each format's chunks in the population.

| cluster | chunks | distinct docs | top-3 doc share | cohesion | format mix (share of that format's population chunks) | shape |
|---:|---:|---:|---:|---:|---|---:|
| 4 | 85 | 2 | 100% | 0.70 | col 2.2% · boo 24.5% | **≤ 3 docs (skew artefact)** |
| 6 | 76 | 12 | 33% | 0.88 | col 41.2% · boo 0.3% | document-shaped |
| 3 | 75 | 12 | 51% | 0.67 | col 15.4% · boo 12.7% · bio 83.3% | document-shaped |
| 5 | 65 | 4 | 98% | 0.71 | col 3.3% · boo 17.5% · spe 2.2% | document-shaped |
| 8 | 63 | 3 | 100% | 0.84 | col 2.2% · boo 17.8% | **≤ 3 docs (skew artefact)** |
| 2 | 55 | 17 | 38% | 0.47 | col 23.1% · spe 26.1% · bio 16.7% | passage-shaped |
| 7 | 36 | 3 | 100% | 0.95 | col 9.3% · boo 5.7% | **≤ 3 docs (skew artefact)** |
| 10 | 33 | 2 | 100% | 1.00 | boo 10.0% | **≤ 3 docs (skew artefact)** |
| 1 | 30 | 1 | 100% | 1.00 | boo 9.1% | **≤ 3 docs (skew artefact)** |
| 9 | 30 | 6 | 70% | 0.81 | col 3.3% · boo 2.1% · spe 37.0% | document-shaped |
| 11 | 17 | 3 | 100% | 0.67 | boo 0.3% · spe 34.8% | **≤ 3 docs (skew artefact)** |

*Clusters drawn from ≤ 3 documents: **6 of 11**, holding 264 of 565 chunks (47%). A long book chapter can fill a chunk cluster by itself; that is a property of chapter length, not evidence of a dimension of the corpus.*

**doc-weighted k-means, k = 11** — per cluster: raw chunks, distinct documents, share of the cluster's chunks that come from its 3 biggest documents (high ⇒ a few documents), *cohesion* = average share of each member document's own chunks that also sit in this cluster (high ⇒ whole documents, low ⇒ passages from many documents), format mix as a share of each format's chunks in the population.

| cluster | chunks | distinct docs | top-3 doc share | cohesion | format mix (share of that format's population chunks) | shape |
|---:|---:|---:|---:|---:|---|---:|
| 10 | 155 | 8 | 68% | 0.81 | col 2.2% · boo 45.3% · bio 16.7% | document-shaped |
| 9 | 135 | 5 | 96% | 0.71 | col 2.7% · boo 39.3% | document-shaped |
| 1 | 56 | 12 | 39% | 0.65 | col 25.3% · boo 0.3% · spe 19.6% | document-shaped |
| 4 | 55 | 8 | 65% | 0.69 | col 7.1% · boo 11.2% · spe 2.2% · bio 66.7% | document-shaped |
| 6 | 36 | 7 | 61% | 0.72 | col 19.2% · boo 0.3% | document-shaped |
| 11 | 28 | 27 | 14% | 0.14 | col 9.3% · boo 1.5% · spe 10.9% · bio 16.7% | passage-shaped |
| 5 | 26 | 6 | 69% | 0.69 | col 2.7% · boo 1.8% · spe 32.6% | document-shaped |
| 2 | 23 | 4 | 87% | 0.84 | col 12.6% | document-shaped |
| 3 | 23 | 5 | 91% | 0.61 | col 3.3% · boo 0.3% · spe 34.8% | document-shaped |
| 7 | 14 | 2 | 100% | 0.94 | col 7.7% | **≤ 3 docs (skew artefact)** |
| 8 | 14 | 2 | 100% | 0.78 | col 7.7% | **≤ 3 docs (skew artefact)** |

*Clusters drawn from ≤ 3 documents: **2 of 11**, holding 28 of 565 chunks (5%). A long book chapter can fill a chunk cluster by itself; that is a property of chapter length, not evidence of a dimension of the corpus.*

**Agreement between the levels (k = 11 at both).** Adjusted Rand index between the document-level clusters and each document's *modal* chunk cluster: unweighted **0.52**, document-weighted **0.53** (1 = identical partitions, 0 = chance). On average 92% of a document's chunks fall in its single most common chunk cluster.

| doc-level cluster | docs | avg share of a doc's chunks in its modal chunk cluster | modal chunk clusters of its docs |
|---:|---:|---:|---|
| 1 | 3 | 95% | chunk-cl 6×3 |
| 2 | 6 | 81% | chunk-cl 2×5, chunk-cl 3×1 |
| 3 | 6 | 88% | chunk-cl 3×6 |
| 4 | 7 | 95% | chunk-cl 6×6, chunk-cl 2×1 |
| 5 | 2 | 94% | chunk-cl 7×2 |
| 6 | 5 | 96% | chunk-cl 9×5 |
| 7 | 2 | 100% | chunk-cl 11×2 |
| 8 | 2 | 100% | chunk-cl 6×2 |
| 9 | 4 | 99% | chunk-cl 10×2, chunk-cl 8×2 |
| 10 | 5 | 88% | chunk-cl 4×1, chunk-cl 7×1, chunk-cl 1×1 |
| 11 | 4 | 89% | chunk-cl 5×3, chunk-cl 2×1 |

### P2: P2 embedding orphans (bottom 10% per format) — 1108 chunks from 131 documents

| k | unweighted | doc-weighted |
|---:|---:|---:|
| 2 | 0.097 | 0.097 |
| 3 | 0.092 | 0.097 |
| 4 | 0.104 | 0.091 |
| 5 | 0.104 | 0.108 |
| 6 | 0.111 | 0.109 |
| 7 | 0.101 | 0.099 |
| 8 | 0.102 | 0.113 |
| 9 | 0.107 | 0.103 |
| 10 | 0.110 | 0.113 |
| 11 | 0.121 | 0.120 |
| 12 | 0.119 | 0.108 |
| 16 | 0.116 | 0.113 |
| 20 | 0.121 | 0.112 |
| 24 | 0.113 | 0.136 |
| 28 | 0.151 | 0.140 |
| 32 | 0.137 | 0.137 |
| 36 | 0.147 | 0.149 |
| 40 | 0.156 | 0.148 |

Silhouette maximum: unweighted k=39 (0.178); document-weighted k=38 (0.160). Document-level knee for this population: k=12.

**unweighted k-means, k = 12** — per cluster: raw chunks, distinct documents, share of the cluster's chunks that come from its 3 biggest documents (high ⇒ a few documents), *cohesion* = average share of each member document's own chunks that also sit in this cluster (high ⇒ whole documents, low ⇒ passages from many documents), format mix as a share of each format's chunks in the population.

| cluster | chunks | distinct docs | top-3 doc share | cohesion | format mix (share of that format's population chunks) | shape |
|---:|---:|---:|---:|---:|---|---:|
| 1 | 158 | 36 | 22% | 0.55 | col 14.3% · boo 14.7% · spe 10.7% · bio 31.2% | document-shaped |
| 5 | 132 | 25 | 33% | 0.63 | col 3.6% · boo 23.6% · spe 13.9% · bio 25.0% | document-shaped |
| 10 | 127 | 27 | 21% | 0.61 | col 17.3% · boo 6.5% | document-shaped |
| 7 | 111 | 103 | 6% | 0.15 | col 12.8% · boo 5.8% · spe 8.2% · bio 25.0% | passage-shaped |
| 2 | 91 | 21 | 29% | 0.58 | col 7.5% · boo 0.8% · spe 33.6% · bio 18.8% | document-shaped |
| 8 | 87 | 18 | 25% | 0.69 | col 11.9% · boo 4.5% | document-shaped |
| 4 | 86 | 19 | 37% | 0.53 | col 9.9% · boo 7.1% · spe 0.8% | document-shaped |
| 6 | 81 | 1 | 100% | 1.00 | boo 21.2% | **≤ 3 docs (skew artefact)** |
| 12 | 81 | 16 | 41% | 0.61 | col 8.2% · boo 8.6% | document-shaped |
| 9 | 61 | 11 | 43% | 0.71 | col 3.4% · boo 0.3% · spe 32.8% | document-shaped |
| 3 | 52 | 7 | 65% | 0.78 | col 5.4% · boo 5.2% | document-shaped |
| 11 | 41 | 8 | 56% | 0.61 | col 5.8% · boo 1.8% | document-shaped |

*Clusters drawn from ≤ 3 documents: **1 of 12**, holding 81 of 1108 chunks (7%). A long book chapter can fill a chunk cluster by itself; that is a property of chapter length, not evidence of a dimension of the corpus.*

**doc-weighted k-means, k = 12** — per cluster: raw chunks, distinct documents, share of the cluster's chunks that come from its 3 biggest documents (high ⇒ a few documents), *cohesion* = average share of each member document's own chunks that also sit in this cluster (high ⇒ whole documents, low ⇒ passages from many documents), format mix as a share of each format's chunks in the population.

| cluster | chunks | distinct docs | top-3 doc share | cohesion | format mix (share of that format's population chunks) | shape |
|---:|---:|---:|---:|---:|---|---:|
| 2 | 169 | 14 | 63% | 0.76 | col 10.2% · boo 28.5% | document-shaped |
| 1 | 143 | 22 | 36% | 0.73 | col 13.6% · boo 16.0% · spe 1.6% | document-shaped |
| 7 | 125 | 24 | 25% | 0.65 | col 17.2% · boo 6.3% | document-shaped |
| 6 | 107 | 99 | 7% | 0.15 | col 12.2% · boo 6.0% · spe 6.6% · bio 25.0% | passage-shaped |
| 9 | 98 | 22 | 29% | 0.55 | col 12.1% · boo 6.8% · spe 0.8% | document-shaped |
| 4 | 96 | 17 | 35% | 0.62 | col 3.6% · boo 17.0% · spe 8.2% | document-shaped |
| 11 | 80 | 17 | 31% | 0.59 | col 2.7% · boo 6.5% · spe 28.7% · bio 25.0% | document-shaped |
| 3 | 78 | 20 | 31% | 0.58 | col 3.9% · boo 8.6% · spe 11.5% · bio 50.0% | document-shaped |
| 10 | 77 | 14 | 27% | 0.77 | col 10.7% · boo 3.7% | document-shaped |
| 12 | 54 | 8 | 44% | 0.89 | col 3.4% · spe 27.9% | document-shaped |
| 5 | 47 | 9 | 45% | 0.73 | col 4.9% · spe 14.8% | document-shaped |
| 8 | 34 | 9 | 44% | 0.60 | col 5.4% · boo 0.5% | document-shaped |

*Clusters drawn from ≤ 3 documents: **0 of 12**, holding 0 of 1108 chunks (0%). A long book chapter can fill a chunk cluster by itself; that is a property of chapter length, not evidence of a dimension of the corpus.*

**Agreement between the levels (k = 12 at both).** Adjusted Rand index between the document-level clusters and each document's *modal* chunk cluster: unweighted **0.44**, document-weighted **0.37** (1 = identical partitions, 0 = chance). On average 79% of a document's chunks fall in its single most common chunk cluster.

| doc-level cluster | docs | avg share of a doc's chunks in its modal chunk cluster | modal chunk clusters of its docs |
|---:|---:|---:|---|
| 1 | 14 | 82% | chunk-cl 1×6, chunk-cl 4×6, chunk-cl 3×2 |
| 2 | 22 | 74% | chunk-cl 5×19, chunk-cl 2×2, chunk-cl 9×1 |
| 3 | 10 | 81% | chunk-cl 12×5, chunk-cl 1×2, chunk-cl 6×1 |
| 4 | 17 | 73% | chunk-cl 1×6, chunk-cl 10×5, chunk-cl 4×4 |
| 5 | 9 | 90% | chunk-cl 9×8, chunk-cl 2×1 |
| 6 | 3 | 71% | chunk-cl 1×2, chunk-cl 10×1 |
| 7 | 13 | 86% | chunk-cl 8×11, chunk-cl 1×1, chunk-cl 3×1 |
| 8 | 11 | 81% | chunk-cl 2×9, chunk-cl 10×2 |
| 9 | 7 | 73% | chunk-cl 11×6, chunk-cl 2×1 |
| 10 | 10 | 78% | chunk-cl 1×5, chunk-cl 3×2, chunk-cl 10×2 |
| 11 | 5 | 78% | chunk-cl 12×5 |
| 12 | 10 | 86% | chunk-cl 10×8, chunk-cl 1×1, chunk-cl 2×1 |

## Where document-level and chunk-level evidence disagree

* **P0 strict (zero score).** Document-level silhouette maximum k=11 (0.184); chunk-level maximum k=32 (0.247) unweighted, k=37 (0.279) document-weighted; partition agreement (ARI, unweighted / document-weighted) 0.52 / 0.53. Where the unweighted and document-weighted chunk runs pick different k or produce different clusters, the difference is the book skew (a book chapter's 18 chunks outvote a column's 7).
* **P2 embedding orphans (bottom 10% per format).** Document-level silhouette maximum k=38 (0.204); chunk-level maximum k=39 (0.178) unweighted, k=38 (0.160) document-weighted; partition agreement (ARI, unweighted / document-weighted) 0.44 / 0.37. Where the unweighted and document-weighted chunk runs pick different k or produce different clusters, the difference is the book skew (a book chapter's 18 chunks outvote a column's 7).

* **Skew, measured (P0):** at the document-level k, chunk clusters drawn from ≤ 3 documents number 6 of 11 in the unweighted run and 2 of 11 once every document counts once. The difference is the book skew.
* **Skew, measured (P2):** at the document-level k, chunk clusters drawn from ≤ 3 documents number 1 of 12 in the unweighted run and 0 of 12 once every document counts once. The difference is the book skew.

**Rule used to read the tables above.** A cluster with high *cohesion* (whole documents land together) and a document-level counterpart is **document-shaped** — a candidate dimension of the corpus. A cluster with low cohesion drawn from many documents, each contributing a few passages, is **passage-shaped** — a recurring passage-level motif (a quotation, a story, a structural section) that does not describe what any document is *about*; it should not become a topic on its own.

