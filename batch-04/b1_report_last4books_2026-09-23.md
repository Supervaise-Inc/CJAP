# B1 — registering the last four books (23 Sep 2026)

Books covered: **A Centenary of Justice**, **Justice and Faith**, **The Bio-Age Dawns on the Judiciary**, **With Due Respect** (Vols. 1–7). With these, all **12 books** are split and checked.

## Result in one line

**120 chapters checked. One new ID assigned: `BA108`.** The other 119 chapters are already in the corpus, so nothing was registered for them. No ID was reused or renumbered.

| Book | Chapters | Already in the corpus | New IDs |
|---|---|---|---|
| A Centenary of Justice | 20 | 19 | **1** (`BA108`) |
| Justice and Faith | 11 | 11 | 0 |
| The Bio-Age Dawns on the Judiciary | 14 | 14 | 0 |
| With Due Respect (Vols. 1–7) | 75 | 75 | 0 |
| **Total** | **120** | **119** | **1** |

`batch-04/intake_manifest.csv` now has **186 rows** (185 before). The pre-run copy is `intake_manifest.backup_pre-B1b_2026-09-23.csv`.

## The one new row

| Field | Value |
|---|---|
| doc_id | **BA108** |
| superseded_doc_id | BA040 |
| title | A Centenary of Justice -- Ch. 20: *Social Weather Stations v. Comelec*: May Election Surveys Be Banned? |
| source | `batch-04/book_split/a-centenary-of-justice/ch20_social-weather-stations-v-comelec.md` |
| publication_date | 2001-12-01, precision **month** (from the corpus record; the file prints no month) |
| publisher | Not stated in the file (the corpus records Supreme Court Press) |
| theme | **A** — free expression: a ban on publishing election surveys struck down |
| rights | CJP-authored, covered by the FLP corpus permission |
| est_words | 2,867 |

`BA040` was retired on 2026-09-22 for "no source text (summary-only)". The chapter text is now in hand, so a **new** ID was assigned and the retired one recorded in `superseded_doc_id`, as the rules require — `BA040` stays taken. The contract `.md` is at `batch-04/data_text/BA108.md` (header plus body, no YAML, no `---` rules; body word count identical to the split file).

## Duplicate check

Every one of the 120 chapters was compared against **all 1,289 corpus documents** (`data/text/*.md` plus the 167 files added by the earlier B1 run) using 8-word shingle overlap over an inverted index.

- **119 chapters each matched exactly one existing document at 73–100%** — its own corpus twin, chapter for chapter, volume for volume. No chapter matched two different documents at a high rate, so there are no duplicate registrations to undo.
- **Ch. 20 of A Centenary of Justice is the only chapter with no twin.** Its best match anywhere in the corpus is 7.6% (`BD022`), which is ordinary shared vocabulary. This is what justifies the single new ID.

### Partial overlaps worth recording (not duplicates)
| Pair | Overlap | What it is |
|---|---|---|
| Centenary Ch. 16 ↔ `BA046` (Bio-Age Ch. 11) | 22–30% | The same case, *Ang Bagong Bayani v. Comelec*, discussed in two successive annual books |
| Centenary Ch. 2 ↔ `BD022` (Bio-Age Ch. 2) | 36% | "Old Doctrines and New Paradigms" and "Judicial Globalization" share long passages |
| With Due Respect Vol. 2 Ch. 5 ↔ `CA495` | 60% | His 2012 column "Wanted: New chief justice" quotes the book chapter at length and says so |
| With Due Respect Vol. 2 Ch. 3 ↔ `BD028` | 46% | Reused material on how the Court decides cases |
| With Due Respect Vol. 4 Ch. 7 ↔ `BA048`, `BA066` | 22–26% | *Divorce, Pinoy Style* reuses his psychological-incapacity material |
| Justice and Faith Ch. 11 ↔ `SC117` | 45% | A different invocation (Salonga's 88th birthday, 2008) in the same devotional language |
| Justice and Faith Ch. 9 ↔ `CC117`, `CC034` | 23–25% | The Good Shepherd material reused in later columns |

## Themes
No new theme letters were needed. The one new document is **A** (liberty and rule of law), matching the theme of the ID it replaces and of the neighbouring election-law chapters (`BA038`, `BA039`).

## Corpus defects found while checking (for the deferred regenerate pass)

These are **not** B1 changes. Nothing under `data/` was touched.

- **D-11 — `data/text/BA031.md` carries the book's back matter.** With Due Respect Vol. 7 Ch. 15 runs on into the COLOPHON and the back-cover blurb, about 215 words that are not part of the column.
- **D-12 — the 22 A Centenary of Justice files are the only files in `data/text/` with YAML front matter** (`---` … `---` with `id:`, `book_id:`, `word_count:` and empty `primary_topics: []` placeholders). This breaks the contract `.md` format.
  - **`BA039.md` (Ch. 19) does not stop at the end of Ch. 19.** It runs through Appendix A (1,262 words), Appendix B (1,740), Appendix C (770), and Appendix D plus the back matter (6,466) — 14,413 words against the chapter's own 3,395. It therefore duplicates `BC007`, `BC008` and `BD019`, and it is where the text of retired `BC009` and `BC010` ended up.
  - Other Centenary chapters differ from the new transcription by more than OCR noise: Ch. 2 (12,137 vs 14,283 in `BA032`), Ch. 12 (2,033 vs 3,291 in `BD016`), Ch. 13 (9,454 vs 7,961 in `BA036`), Ch. 16 (5,309 vs 6,015), Ch. 17 (5,139 vs 5,742).
- **D-13 — `data/text/BC018.md` (Justice and Faith Ch. 11, Invocation) is truncated.** It holds 97 words and opens mid-sentence ("Your Spirit that he may continue to emulate…"); the source chapter is 269 words. It also ends with the OCR artefact "• 0 0". `BC017` (Ch. 10) runs the other way, 1,614 words against the source's 1,495.
- **D-7 confirmed independently.** Each With Due Respect column prints its publication date, and those 75 dates match the `Date:` headers in `data/text/` but **not** the `Date` column of `data/csv/cjp_books_curated_normalized.xlsx` — for example `BE001` is printed August 12, 2007 and the sheet holds 2007-12-08. The `.md` headers are right; the sheet is not.

## Items still needing the team's word
1. **Appendix D of A Centenary of Justice, "MPGR"** (895 words, CJP's tribute to Justice Minerva P. Gonzaga-Reyes). Its ID `BC009` was retired for "no source text"; the text is now available. It is a SKIP part under the B0 rules and is marked **candidate**, so B1 did **not** register it. Say the word and it takes a new ID with *replaces retired BC009*.
2. **The four Bio-Age appendices** (`BE027`, `BE028`, `BA050`, `BE029`, about 28,500 words) are by Dr. Franklin M. Zweig, Justice Leonardo A. Quisumbing and Prof. Pacifico A. Agabin, reprinted with permission and expressly not edited by CJP. They are in the corpus, which is otherwise meant to hold CJP's own voice.
3. **The remaining "candidate" prefaces** listed in the four split reports.
4. `d7_date_normalisation_proposed.csv` still awaits sign-off.

**STOP.** Please confirm `BA108` and its theme before B2 runs on it.
