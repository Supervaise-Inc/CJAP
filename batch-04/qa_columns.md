# batch-04 columns — C2 QA

Run: 23 Sep 2026 · Scope: 19 column rows in `batch-04/intake_manifest.csv` (CA529 + the 18 new columns) · Checked against C1 as updated on 23 Sep (plain title line, no blank lines between paragraphs).

## Result

- **18 of 19 rows pass every check.** CA530–CA543, CB020–CB021 and CD030–CD031 are clean.
- **CA529 fails 8 of the 15 checks (15 individual failures, listed below)**. It was staged earlier from the Phase-1 record and was never re-run through C1. Its authorship also needs confirming before any fix.
- Coverage complete: all 18 expected Mondays are present. No duplicate dates or URLs. IDs are contiguous and none is reused or retired.
- The enriched workbook was not edited. Changes needed are listed under "What should change".

## 1. Coverage (expected Mondays 2026-05-25 … 2026-09-21)

| # | Date | doc_id | Title |
|---|---|---|---|
| 1 | 2026-05-25 | CA530 | Government must speak with one voice |
| 2 | 2026-06-01 | CA531 | The fugitive |
| 3 | 2026-06-08 | CA532 | Correcting birth, marriage, and death data |
| 4 | 2026-06-15 | CA533 | Wanted: Senator-heroes |
| 5 | 2026-06-22 | CA534 | The SC's 125th: From tradition to innovation |
| 6 | 2026-06-29 | CA535 | For now, look at the means, not yet the end |
| 7 | 2026-07-06 | CA536 | Intention different from discernment to kill |
| 8 | 2026-07-13 | CB020 | Independence for the SC and BSP |
| 9 | 2026-07-20 | CB021 | Cheapest, most reliable, accessible power |
| 10 | 2026-07-27 | CA537 | Four truths on Sara's trial |
| 11 | 2026-08-03 | CA538 | Judicial truth vis-à-vis actual truth |
| 12 | 2026-08-10 | CA539 | Sara's options |
| 13 | 2026-08-17 | CA540 | Two-thirds |
| 14 | 2026-08-24 | CA541 | Is Quiboloy extraditable immediately? |
| 15 | 2026-08-31 | CA542 | Liberal jurisprudence on bigamy |
| 16 | 2026-09-07 | CD030 | FLP's futuristic museum finds a home |
| 17 | 2026-09-14 | CD031 | After 10 years, where are FLP's scholars now? |
| 18 | 2026-09-21 | CA543 | Commonsensical interpretation |

**Missing weeks: none.** Also in the manifest: CA529 (2018-02-02, recovered from Phase 1).

Duplicates: no two rows share a date (0) or a URL (0). The duplicate check against all 1,104 `corpus/*/*/*.json` found no match on title, URL or date.

## 2–3. Pass/fail by row

Anecdotes and summary: an automated check confirmed every quoted fragment and every number in the anecdotes and summaries appears in the `.md`; then each flagged sentence was read against the text. For the 18 new columns no unsupported claim was found. CA529 was checked by the automated step only.

| doc_id | Title line | Header | Body spacing | No --- | IDs match | Row = manifest | Manifest fields | Words | JSON | Entity keys | Confidence | Phrases verbatim | Phrase length | People in text | Date = byline | Anecdotes/summary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CA529 | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | PASS | **FAIL** | PASS | PASS | PASS | **FAIL** | **FAIL** | PASS | **FAIL** | **FAIL** | PASS (automated only) |
| CA530 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA531 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA532 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA533 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA534 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA535 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA536 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CB020 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CB021 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA537 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA538 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA539 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA540 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA541 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA542 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CD030 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CD031 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CA543 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

## Failures (doc_id · column · offending text)

| # | doc_id | Column | Offending text |
|---|---|---|---|
| 1 | CA529 | .md line 1 | # Rule of, or by, law |
| 2 | CA529 | .md lines 2-6 | Date:       2018-02-02 / Publisher:  Philippine Daily Inquirer (Inquirer Opinion) / Source:     https://opinion.inquirer.net/110720/rule-of-or-by-law / By: Artemio V. Panganiban /  |
| 3 | CA529 | .md body | 12 blank lines in body |
| 4 | CA529 | manifest | rights_consent_status/theme/other fields: Inquirer column by CJP — same basis as the other 785 columns; confirm at CE-1 |
| 5 | CA529 | stances.confidence | asserted as cultural critique |
| 6 | CA529 | stances.confidence | asserted with WJP data |
| 7 | CA529 | stances.confidence | asserted with historical and empirical backing |
| 8 | CA529 | stances.confidence | asserted as evidence of erosion |
| 9 | CA529 | stances.confidence | concerned framing |
| 10 | CA529 | signature_phrases (not verbatim) | batas (which actually means 'to decree') |
| 11 | CA529 | signature_phrases (not verbatim) | even in authoritarian countries, you might find forms of checks and balances |
| 12 | CA529 | entities.people | President Rodrigo Duterte (referenced via Davao police incident, Charter-change agenda) |
| 13 | CA529 | entities.people | Ferdinand Marcos Sr. (referenced via martial law era) |
| 14 | CA529 | entities.people | Three unnamed minors (January 21 Davao incident) |
| 15 | CA529 | date vs byline | byline is only "By: Artemio V. Panganiban" (no printed time or date), so the 2018-02-02 date cannot be checked against it |

## 4. IDs

| Series | IDs in batch-04 | Register start | Contiguous | Reused in corpus | Retired |
|---|---|---|---|---|---|
| CA | CA529–CA543 (15) | CA529 (reserved for CA016) | yes | none | none |
| CB | CB020–CB021 (2) | CB020 | yes | none | none |
| CC | — | CC118 | n/a | — | — |
| CD | CD030–CD031 (2) | CD030 | yes | none | none |
| CE | — | CE121 | n/a | — | — |

Next free after batch-04: **CA544 · CB022 · CC118 · CD032 · CE121**.

## What should change (for the team; the workbook was not edited)

**CA529 — decide authorship first.** Its text (the *batas* / Old Norse etymology, "In the past I've offered an alternative mix of cultural and social theories", a Friday date, no printed byline time) does not read like a CJP column. Check the byline at https://opinion.inquirer.net/110720/rule-of-or-by-law.
- If it is **not** his: remove CA529 from the manifest, the workbook and `data_text/`. CA529 then stays unused (note it in the register).
- If it **is** his, fix:
  1. `.md`: plain title line (drop "# "); add a blank line after `Source:`; `By:` line with the time and date as printed; remove the 12 blank lines between paragraphs.
  2. manifest `rights_consent_status` → "CJP-authored Inquirer column, same basis as the existing 785".
  3. `signature_phrases`: replace the 2 non-verbatim phrases with verbatim ones from the text.
  4. `stances.confidence`: map the 5 free-form values to asserted / asserted with evidence / hedged / reported (not his view).
  5. `entities.people`: use names as written in the text ("President Duterte"), drop "Ferdinand Marcos Sr." (text says only "Marcos martial law era") and "Three unnamed minors" (not a name; move to events).

**Advisories (no change required, reviewer to confirm):**
- CB020 "Independence for the SC and BSP" filed as theme B; A is arguable. Say if it should be CA544.
- CA539 keeps the printed "grabbed in shimmering crimson" (probably "garbed"); CA532 keeps "Feliciano Batholome"; CA538 keeps "Marvic MVF Leonen" (CA530 has "M.V.M."). All as printed.
- CA536 and CA537 anecdotes/institutions use the acronyms DSWD and AMLC; the text spells the names out in full. Acceptable as abbreviations.
- CB021: CJP discloses he is Meralco's board adviser and former independent director; captured in stances and anecdotes.
- Signature phrases in 11 rows were shortened on 23 Sep to meet the 3–20-word rule (still verbatim).

## 5. Spot check (10 rows, seed 4)

Chosen with Python `random.Random(4).sample()` over the 19 column doc_ids in manifest order. Sheet: `batch-04/spot_check_columns.xlsx` (reviewer / OK-or-fix / notes left empty).

1. CA536 — Intention different from discernment to kill
2. CB021 — Cheapest, most reliable, accessible power
3. CA532 — Correcting birth, marriage, and death data
4. CA539 — Sara's options
5. CA543 — Commonsensical interpretation
6. CA531 — The fugitive
7. CA530 — Government must speak with one voice
8. CA542 — Liberal jurisprudence on bigamy
9. CA529 — Rule of, or by, law
10. CA535 — For now, look at the means, not yet the end

## Resolution — CA529 removed (23 Sep 2026)

The byline on https://opinion.inquirer.net/110720/rule-of-or-by-law is **Michael L. Tan, "Pinoy Kasi", 05:16 AM February 02, 2018** — not Artemio V. Panganiban. "Rule of, or by, law" is therefore not his column. It entered the pipeline through the Phase-1 record (CA016), which had it filed as his.

Action taken: CA529 removed from `data_text/`, `columns_enriched.xlsx` and `intake_manifest.csv`. batch-04 columns are now the 18 new columns only, and the three files agree. **CA529 stays an unused ID; do not re-stage it.** The failures listed for CA529 above are kept as the record of why it was checked.

Still open: `archive/phase1/` keeps it as CA016 and `id_map_phase1_to_live.csv` maps CA016 → CA529. A note there would stop a future run from recovering it again (not done — outside batch-04).

## STOP
CA529 is resolved (removed). When the team has signed the 10-row spot check, continue with P5 in `BATCH-04_PROMPTS.md`. Note: the spot-check sheet still lists CA529 among its 10 rows; treat that row as closed by this resolution, or re-run step 5 to draw a replacement.
