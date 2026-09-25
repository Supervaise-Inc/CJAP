# B0 split report: With Due Respect

| | |
|---|---|
| Title | With Due Respect: Selected columns from the Philippine Daily Inquirer |
| Author | Chief Justice Artemio V. Panganiban (retired); edited by John Nery |
| Publisher | Inquirer Books, a unit of the Philippine Daily Inquirer, Inc., Makati City |
| Year | 2011, 2012 (copyright "Philippine Daily Inquirer 2011, 2012"; CIP entry c2012, 320 pp.). ISBN 978-971-8935-07-1 |
| Source file | `batch-04/incoming/books/WITH_DUE_RESPECT_FINAL.docx` (1,962 paragraphs, 65,732 words, 2 images) |
| Book slug | `with-due-respect`, with one sub-folder per volume: `vol-1` … `vol-7` |

**Result: 75 chapters and 13 skipped parts.** The volumes are numbered 1–10, 1–10, 1–10, 1–10, 1–10, 1–10 and 1–15, with no gaps.

## How the structure was worked out
- The book is one physical volume divided into **seven "Books"**. The corpus already calls them *With Due Respect (Vol. 1)* … *(Vol. 7)*, so this split uses the same names and gives each volume **its own sub-folder, its own `split_plan.csv` and its own chapter numbering**, which is how the book prints them (each Book restarts at Chapter 1).
  - Vol. 1 On Gloria Macapagal-Arroyo · Vol. 2 On the Supreme Court · Vol. 3 On Legal Reform · Vol. 4 On Matters of Law · Vol. 5 On Election Reform · Vol. 6 On the 2010 Vote and the Aquino Presidency · Vol. 7 Of Life and Faith.
  - `book_split/with-due-respect/split_plan.csv` is the combined plan for all seven, with a `volume` column added.
- **This is a collection book (rule 5):** every chapter is one *With Due Respect* column reprinted from the *Philippine Daily Inquirer*. Each one is `collected_piece = yes`, with `original_outlet` = the Inquirer column and `original_date` taken from the date line the book prints at the end of each column.
- **Start and end pages are blank.** The file has no page numbers, and the printed Contents page numbers are OCR debris ("Can GMA Reign Beyond 2010? 33", "Hail to the Court; A Toast to Truth 1411"), so they were not used.
- Chapter titles are taken **from the text, not the Contents**, where the two differ:
  - Vol. 2 Ch. 8 — text "Who Will Discipline Supreme Court **Justices**?"; Contents "Justice?".
  - Vol. 5 Ch. 5 — text "**Q&A** on the Comelec Leadership"; Contents "Q & A".
  - Vol. 7 Ch. 1 — text "**Sanctity** of Life and of Marriage"; Contents "Sanctify".
- Section headings are the standalone bold lines inside each column, written as `##`.
  - Vol. 1 Ch. 1 is the one column whose headings lost their bold in the Word conversion. Its four headings ("GMA' Sona", "Regain credibility first", "Lead internal transformation", "Fortify democratic institutions") were restored by hand; "How?" in the same column is body text and was left as body text.
  - Vol. 1 Ch. 4's "Completing the CBCP's joy" also lost its bold and was restored.
- The text was not changed.

## Parts in order

| Vol. | Part | Class | Reason / flag | Words |
|---|---|---|---|---|
| — | Cover and title page | SKIP | title page | 41 |
| — | Copyright page, CIP data, imprint | SKIP | copyright page | 129 |
| — | Table of Contents | SKIP | table of contents | 439 |
| — | Foreword by Isagani Yambot, Publisher, PDI | SKIP | foreword, by someone else | 514 |
| 1 | BOOK 1: On Gloria Macapagal-Arroyo + Ch. 1–10 | divider SKIP + 10 CHAPTERS | | 8,769 |
| 2 | BOOK 2: On the Supreme Court + Ch. 1–10 | divider SKIP + 10 CHAPTERS | | 8,513 |
| 3 | BOOK 3: On Legal Reform + Ch. 1–10 | divider SKIP + 10 CHAPTERS | Ch. 9 is an excerpt, 134 words | 7,737 |
| 4 | BOOK 4: On Matters of Law + Ch. 1–10 | divider SKIP + 10 CHAPTERS | | 8,290 |
| 5 | BOOK 5: On Election Reform + Ch. 1–10 | divider SKIP + 10 CHAPTERS | | 8,599 |
| 6 | BOOK 6: On the 2010 Vote and the Aquino Presidency + Ch. 1–10 | divider SKIP + 10 CHAPTERS | | 8,924 |
| 7 | BOOK 7: Of Life and Faith + Ch. 1–15 | divider SKIP + 15 CHAPTERS | | 13,562 |
| — | Colophon | SKIP | publisher's note | 34 |
| — | Back cover blurb (quoted from the Yambot foreword) | SKIP | blurb | 181 |

Chapter word counts run from 134 (Vol. 3 Ch. 9) to 987 (Vol. 7 Ch. 8), the length of a newspaper column. **No chapter is "long"** and none needs splitting.

## Decisions for the team
1. **Nothing to register.** All 75 chapters are **already in the corpus** as `BA001`–`BA031`, `BB001`–`BB005`, `BC001`–`BC005`, `BD001`–`BD009` and `BE001`–`BE025`. Volume-by-volume and chapter-by-chapter, the split matches the corpus one to one, and every chapter's word count matches its corpus file once the corpus file's five-line header is discounted (differences of 24–33 words throughout). **B1 assigns no new IDs for this book.** The split is kept as the traceable source-of-record for those 75 documents.
2. **Vol. 3 Ch. 9 "Like Cory or Like Ferdie" is only 134 words** in the book — the publisher reprinted an excerpt, not the whole column. The corpus title already says so ("Like Cory or Like Ferdie (excerpt)"). The book's own chapter title has no "(excerpt)"; the split keeps the book's title and this note records the difference.
3. **No candidate pieces.** The only non-CJP prose is Isagani Yambot's Foreword, which was skipped whole. There is no preface, acknowledgements, appendix or index by CJP in this book.
4. **Dates.** Each column ends with its printed publication date, and that date is in `original_date`. Four of those date lines are garbled by OCR and were read through; those rows carry the flag `ocr-garbled-date-line`:
   - Vol. 1 Ch. 5 "(March 23, 2008" — closing bracket missing.
   - Vol. 4 Ch. 7 "(February 21, 2010)" printed in the middle of a reflowed final paragraph.
   - Vol. 5 Ch. 5 "(October ,41 2007)" — read as October 14, 2007.
   - Vol. 6 Ch. 1 "(September , 6 2009)" — read as September 6, 2009.

   These 75 dates are also a **clean, independent check on the `Date` column of `data/csv/cjp_books_curated_normalized.xlsx`**, which is affected by the D-7 day/month swap (for example BE001 is printed August 12, 2007 but the sheet holds 2007-12-08). The `data/text/*.md` headers are right; the sheet is not.

## Flag, do not fix
1. **Corpus defect (new, D-11): `data/text/BA031.md` ends with the book's back matter.** The colophon ("COLOPHON / Printed on / Matte-coated 170 gsm…") and the back-cover blurb are appended to Vol. 7 Ch. 15, about 215 words that are not part of the column. This is the same class of leak as D-10 and is listed for the corpus-regenerate pass.
2. **OCR noise, kept as is.** Examples: "my journey from. hawking newspapers", "eh asked his secretary", "the remain der", "b e transparent", "t h e troubled years". The imprint page is scrambled ("PUBLISHER: . Rufino Javier Vicente D EDITOR: John Nery").
3. **No page numbers.** The Contents page numbers that survived OCR are unreliable and were not carried into the plan.
4. **Two images only** (cover and one interior page); there is no photo section.
5. **Chapter marker and title in one paragraph** in three places (Vol. 3 Ch. 7, Vol. 4 Ch. 1, Vol. 5 Ch. 1) and in the Contents' last line. Handled; both lines were dropped from the body and used as the chapter heading.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 64,394 + skipped words 1,338 = 65,732 = whole file | **Pass (100.0%)** in each of the seven volume plans and in the combined plan. Every non-empty paragraph belongs to exactly one part. Page coverage could not be checked, because the file has no page numbers. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers follow the book (1–10 per volume; 1–15 in Vol. 7) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (75 chapter files, 75 CHAPTER rows) |
| Each chapter matches its corpus document | **Pass** for all 75 (word counts agree within the corpus header allowance; the one outlier, BA031, is defect D-11 above) |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
