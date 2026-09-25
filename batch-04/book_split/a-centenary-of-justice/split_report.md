# B0 split report: A Centenary of Justice

| | |
|---|---|
| Title | A Centenary of Justice (cover: *Kataas-taasang Hukuman 1901–2001 · Katarungan at Bayan Magpakailanman*) |
| Author | Justice Artemio V. Panganiban |
| Publisher | **Not stated in the file** — there is no copyright page in the transcription. The corpus records it as the Supreme Court Press; please confirm. |
| Year | 2001 (the book covers his sixth year on the Court, October 11, 2000 – October 10, 2001, and the SC centenary of June 11, 2001) |
| Source file | `batch-04/incoming/books/A Centenary of Justice.docx` (1,689 paragraphs, 85,999 words, no images) |
| Book slug | `a-centenary-of-justice` |

**Result: 20 chapters and 15 skipped parts.** Chapter numbers run 1–20 with no gaps.

## How the structure was worked out
- The file **has a Contents page** (paragraphs 46–85) with page numbers, so `start_page` and `end_page` are filled for every chapter and appendix: each chapter ends on the page before the next one begins.
- Two parts: **Part I Centenary Celebrations** (Ch. 1–12) and **Part II Judicial Jousts** (Ch. 13–20), then Appendices A–D and an Index.
- Chapter titles printed over two or three lines were joined, for example Ch. 13 "Estrada v. Desierto and Estrada v. Arroyo: Constitutional Succession to the Presidency".
- Section headings are the bold or styled standalone heading lines inside each chapter, written as `##`, with headings printed over two lines joined.
- The text was not changed.

### One title taken from the Contents, not from the chapter heading
**Ch. 11.** The chapter heading printed above the text repeats Chapter 1's title, "A Renaissance in the Judiciary". That is a misprint: the Contents (p. 118) gives **"E-Values for Lawyers"**, the chapter's own headnote opens "*E-Values for Lawyers* is a carryover from the three fundamental principles…", and the corpus already holds the chapter under that title. The plan therefore uses **E-Values for Lawyers** as `chapter_title` and records the misprint in `part_label_as_printed`, flagged `printed-heading-wrong`. **Please confirm.**

## Parts in order

| # | Part | Class | Pages | Words |
|---|---|---|---|---|
| 1 | Front cover (image) | SKIP · cover | – | 0 |
| 2 | Title page | SKIP · title page | – | 16 |
| 3 | The Cover: the SC Centenary Logo, with remarks of Justice Leonardo A. Quisumbing, June 9, 2000 | SKIP · publisher's notes, by someone else | – | 229 |
| 4 | A Centennial Prayer for the Courts | SKIP · epigraph | – | 89 |
| 5 | Contents | SKIP · table of contents | – | 280 |
| 6 | Foreword by CJ Hilario G. Davide Jr. | SKIP · foreword, by someone else | xix–xx | 523 |
| 7 | Preface by Panganiban | SKIP · preface · **candidate** | xxi– | 1,526 |
| 8 | PART I — Centenary Celebrations (part title) | SKIP · part divider | – | 4 |
| 9–20 | Ch. 1–12 | CHAPTER | 1–140 | 29,682 |
| 21 | PART II — Judicial Jousts (part title) | SKIP · part divider | – | 4 |
| 22–29 | Ch. 13–20 | CHAPTER | 141–374 | 49,087 |
| 30 | APPENDICES (divider) | SKIP · appendices | – | 1 |
| 31 | Appendix A. A Salute to My Mentor (Jovito R. Salonga) | SKIP · appendix · **candidate** | 375–379 | 1,229 |
| 32 | Appendix B. Justice Is God's Work | SKIP · appendix · **candidate** | 380–386 | 1,699 |
| 33 | Appendix C. A Prelude to Paperless Courts | SKIP · appendix · **candidate** | 387–390 | 735 |
| 34 | Appendix D. MPGR (tribute to Justice Minerva P. Gonzaga-Reyes) | SKIP · appendix · **candidate** | 391–394 | 895 |
| 35 | Index | SKIP · index · **not in the file** | 395– | 0 |

Per-chapter titles, pages and word counts are in `split_plan.csv`. The longest chapter is Ch. 15 *Cruz v. Secretary of Environment* (13,470 words); the shortest is Ch. 9 (565 words).

## Decisions for the team
1. **Only one chapter is new to the corpus. Ch. 20 *Social Weather Stations v. Comelec: May Election Surveys Be Banned?* (2,867 words).** Its ID `BA040` was retired on 2026-09-22 for "no source text"; the text is now in hand, so B1 assigns it a **new ID** with the note *replaces retired BA040*. The other nineteen chapters are already registered (`BD010`, `BA032`, `BA033`, `BD011`–`BD017`, `BC006`, `BA034`–`BA039`, `BB006`, `BB007`).
2. **Appendix D "MPGR" (895 words) is also newly recovered.** Its ID `BC009` was retired for the same reason. It is a SKIP part under the B0 rules and is marked **candidate**, so B1 does not register it automatically. If the team wants it, it takes a new ID with the note *replaces retired BC009*.
3. **candidate** (skipped, but complete pieces in CJP's own words of 800+ words)
   - **Preface** (1,526 words): his sixth-year report and an account of the centenary.
   - **Appendix A. A Salute to My Mentor** (1,229 words) — already in the corpus as `BC007`.
   - **Appendix B. Justice Is God's Work** (1,699 words) — already in the corpus as `BC008`.
   - **Appendix C. A Prelude to Paperless Courts** (735 words, under 800) — already in the corpus as `BD019`.
   - **Appendix D. MPGR** (895 words) — see decision 2.
4. **long** (over 6,000 words; decide at B1 whether to split at the `##` sections): Ch. 2 *Old Doctrines and New Paradigms* (12,137), Ch. 13 *Estrada* (9,454), Ch. 14 *The Death Penalty Cases* (8,676), Ch. 15 *Cruz* (13,470).
5. **Speeches** (`collected_piece = yes`): Ch. 2, 4, 6, 7, 8, 9, 10, 11 and 12. The editors' headnotes name the occasion and the exact date for each, and those are in `original_date` and `original_outlet` — for example the Anvil Awards keynote of February 23, 2001 (Ch. 12) and the Calamba City Lawyers League speech of August 24, 2001 (Ch. 11). **B1 should check these nine against the speeches corpus.**

## Flag, do not fix
1. **Editors' headnotes are inside the chapters.** Most Part I chapters open with a bracketed note written about CJP in the third person ("[As overall chair of the Supreme Court Centenary Celebrations, Justice Panganiban…]"). They are printed as part of the chapter and were kept there, as in *Love God, Serve Man*. **B2 may want to lift each note into the header or source metadata.**
2. **Index missing.** The Contents lists an Index at p. 395; it is not in the file.
3. **Corpus defect (new, D-12), found while checking this book against `data/text/`.**
   - All **22 A Centenary of Justice files carry YAML front matter** (`---` … `---` with `id:`, `book_id:`, `word_count:` and empty `primary_topics: []` placeholders) ahead of the `#` title. They are the only 22 files in `data/text/` that do. This breaks the contract `.md` format.
   - **`BA039.md` (Ch. 19) does not stop at the end of Ch. 19.** It runs on through Appendix A (1,262 words), Appendix B (1,740), Appendix C (770) and Appendix D plus the book's back matter (6,466) — 14,413 words against the chapter's own 3,395. It therefore duplicates `BC007`, `BC008` and `BD019`, and it is where the text of retired `BC009` and `BC010` actually ended up.
   - Several other chapters differ from their corpus copies by more than OCR noise: Ch. 2 (12,137 here vs 14,283 in `BA032`), Ch. 12 (2,033 vs 3,291 in `BD016`), Ch. 13 (9,454 vs 7,961 in `BA036`), Ch. 16 (5,309 vs 6,015) and Ch. 17 (5,139 vs 5,742). The corpus copies were built from a different source. **These belong in the deferred corpus-regenerate pass, with this split as the source of record.**
4. **Text by someone else inside kept chapters.** The Part II chapters quote Court decisions and other justices' separate and dissenting opinions at length; the longest runs are in Ch. 15 (*Cruz*) and Ch. 13 (*Estrada*). No run by another author stands as a separate piece.
5. **OCR noise**, kept as is. Examples: "an otherwise humdrum existence", "Battles in the Supreme Court,'" (stray apostrophe), broken hyphenation across line ends.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 78,769 + skipped words 7,230 = 85,999 = whole file | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. The Contents pages (xix–395) map to exactly one part each. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers follow the book (1–20) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (20 chapter files, 20 CHAPTER rows) |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
