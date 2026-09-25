# B0 split report: Love God, Serve Man

| | |
|---|---|
| Title | Love God, Serve Man: A Collection of Selected Speeches and Papers of Artemio V. Panganiban for the period 1984–1994 |
| Author | Artemio V. Panganiban (then a practising lawyer); edited by Isagani Yambot |
| Publisher | Philippine Daily Inquirer |
| Year | 1994 (Foreword June 6, 1994; Preface June 1, 1994; Acknowledgments August 31, 1994) |
| Source file | `batch-04/incoming/books/Love God Serve Man.docx` (1,118 paragraphs, 50,635 words, cover image only) |
| Book slug | `love-god-serve-man` |

**This is a collection book (rule 5).** **Result: 22 pieces kept as chapter documents, and 12 skipped parts.**

## How the structure was worked out
- There is no table of contents in the file. The book is arranged in five Parts, and each Part holds separately titled speeches and papers:
  - Part I "Panganiban, the Civic Leader"
  - Part II "the Practising Lawyer"
  - Part III "the Catholic Lay Leader"
  - Part IV "the Business Leader"
  - Part V "Other Papers"
- Each piece opens with an **Editor's note** by Isagani Yambot giving its occasion, date and where it was printed. I used these notes for `original_date` and `original_outlet`, and every chapter is `collected_piece = yes`.
- **The book does not number its pieces.** The chapter numbers 1–22 are assigned in book order, and the report says so here rather than claiming printed numbers. There are no gaps.
- **Start and end pages are blank.** The file has no page numbers or contents.
- Section headings are the bold or styled standalone heading lines inside each piece, plus a few unstyled standalone headings: the question headings in Ch. 8 and 11, "Introduction", and "Nature of PCP II". All are written as `##`, and headings printed over several lines were joined.
  - **Kept as text, not headings:** several styled lines where the Word conversion ran the heading's second line into the next body paragraph. Examples: "A 'Sick Society' That / Professes to Follow Christ …", "The Filipino is Basically / Productive and Law-Abiding …", "Called to Social / Transformation …", and "Vision of What Manila / Rotary Stands For …". Making them headings would have meant cutting a body paragraph, which B0 must not do. See flag 2.
- The text was not changed.

## Parts in order

| # | Part | Class | Date / outlet (from the Editor's note) | Words |
|---|---|---|---|---|
| 1 | Title page | SKIP · title page | | 29 |
| 2 | Foreword by Jaime L. Cardinal Sin | SKIP · foreword, by someone else | | 242 |
| 3 | Preface by Jovito R. Salonga | SKIP · preface, by someone else | | 860 |
| 4 | Editor's Note by Isagani Yambot | SKIP · commentary by someone else | | 459 |
| 5 | Acknowledgments by Panganiban | SKIP · acknowledgments (see decision 2) | | 1,751 |
| 6 | Part I title | SKIP · part divider | | 7 |
| 7 | Ch. 1 Love God, Serve Man | CHAPTER | 1990-07-12, RCM induction; Manila Bulletin | |
| 8 | Ch. 2 A Year of Love and Service | CHAPTER | 1991-06-27, RCM valedictory; Phil. Star, Manila Bulletin | |
| 9 | Ch. 3 'Salamat Po' | CHAPTER | RCM Eyebank Foundation (no date) | |
| 10 | Part II title | SKIP · part divider | | 7 |
| 11 | Ch. 4 On Improving the Administration of Justice | CHAPTER | 1992-10-17, PCCI conference | |
| 12 | Ch. 5 Legal Problems in International Trade Spawned by the AFTA | CHAPTER | 1993-10-27, 16th World Law Conference | |
| 13 | Ch. 6 Does the MNLF Have International Legal Personality? | CHAPTER | 1987-01-14, Manila Bulletin | |
| 14 | "Still Sans Status" by Melchor P. Aquino | **SKIP** · by someone else | Manila Bulletin, 1987-01-14 | 615 |
| 15 | Ch. 7 Legal Consequences of "Part-time" Service to the Government | CHAPTER | 1994-02-01, letter to PCAGC Chairman Domingo | |
| 16 | DOJ Opinion No. 33, s. 1994, by Sec. Franklin M. Drilon | **SKIP** · by someone else | | 1,331 |
| 17 | Part III title | SKIP · part divider | | 8 |
| 18–22 | Ch. 8–12 (Church, PPCRV, BLD, PCP II talks) | CHAPTER | 1991–1994; see CSV | |
| 23 | Part IV title | SKIP · part divider | | 7 |
| 24–26 | Ch. 13–15 (ASTA Rome 1985; tourism 1988; peace 1992) | CHAPTER | see CSV | |
| 27 | Part V title | SKIP · part divider | | 5 |
| 28–34 | Ch. 16–22 (Filipino values, NUSP keynote, Rotary Balita messages, prayers, a reflection, introductions) | CHAPTER | see CSV | |

The chapter word counts are in `split_plan.csv`. They range from 362 (Ch. 18, the Easter message) to 4,801 (Ch. 11), so no chapter is "long".

## Decisions for the team
1. **Two pieces by other authors were cut out and skipped.** The book reprints two pieces by others right after CJP's own:
   - Ambassador Melchor P. Aquino's *Manila Bulletin* column "Still Sans Status", after CJP's MNLF opinion (Ch. 6).
   - Justice Secretary Drilon's DOJ Opinion No. 33 (1994), after CJP's letter (Ch. 7).

   Each became its own SKIP part, so Ch. 6 and Ch. 7 contain only CJP's text. Please confirm.
2. **Acknowledgments (1,751 words, his own words) were skipped per rule 2.** They contain substantial personal narrative: his debt to Salonga, leaving Salonga's party, his wife, and President Ramos' comment. They are not a speech or column, so they are not marked "candidate". The team may still want them.
3. **Grouped pieces.** Two pieces are printed under one title but contain several short items. **Ch. 20** "Some Prayers and Invocations" has four prayers (1991–1994). **Ch. 22** "Introductions" has three speaker introductions: Salonga (1989), Soliven (1992) and Estanislao (1993). Each is kept as one chapter as printed; B1 may split them if the speeches corpus stores such items individually.
4. **Editor's notes are inside the chapters.** Every piece starts with a short Editor's note by Isagani Yambot, about 25–160 words each, which is text by someone else. They stay in the chapter files because the chapter is cut as printed. **B2 may want to move each note into the header or source metadata.**
5. **B1 overlap check.** These are pre-1995 pieces (1985–1994), before his Supreme Court years, so they are unlikely to be in the 153 speeches already in the corpus. **B1 should still check**, especially Ch. 1 "Love God, Serve Man" (July 12, 1990) and Ch. 17 "A Plea for Honesty" (NUSP, November 17, 1988).

## Flag, do not fix
1. **No table of contents, page numbers or back matter** in the file.
2. **Broken headings from the Word conversion.** Several headings lost their second line into the following paragraph, for example "Professes to Follow Christ Eighty-three percent…" in Ch. 16. The text is kept exactly as in the file. When B2 formats these documents, it may want to restore the heading by hand.
3. **Ch. 12 is a transcript** of an extemporaneous talk, partly in Filipino (the Editor's note says so). Ch. 4 is also transcribed from an extemporaneous report.
4. **OCR noise**, kept as is. Examples: "in al candor", "held a t the Rizal Park", and missing closing brackets in the Editor's notes.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 45,314 + skipped words 5,321 = 50,635 = whole book | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers (assigned 1–22 in book order; the book prints none) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (22 chapter files, 22 CHAPTER rows) |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
