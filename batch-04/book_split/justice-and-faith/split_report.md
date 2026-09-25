# B0 split report: Justice and Faith

| | |
|---|---|
| Title | Justice and Faith |
| Author | Justice Artemio V. Panganiban |
| Publisher | **Not stated in the file.** There is no copyright page in the transcription; the front matter survives only as images. Please confirm. |
| Year | 1997–1998 (the latest piece in the book is dated October 22, 1997; Ch. 1 reports his second year on the Court, which ended October 10, 1997) |
| Source file | `batch-04/incoming/books/Justice and Faith.docx` (1,355 paragraphs, 44,161 words, 17 images) |
| Book slug | `justice-and-faith` |

**Result: 11 chapters and 7 skipped parts.** Chapter numbers run 1–11 with no gaps.

## How the structure was worked out
- The file has **no table of contents and no page numbers**; the cover, title page and photo pages are images with no text layer. The structure comes from the headings in the text, and the Narvasa Foreword confirms it: the book is "a collection of writings and speeches of the author's own choice and excerpting", arranged in two parts.
  - Part **JUSTICE**: Ch. 1–5.
  - Part **FAITH**: Ch. 6–11.
  - Appendix A, then the back-matter accolades.
- **The book does not number its pieces.** The chapter numbers 1–11 are assigned in book order; the report says so here rather than claiming printed numbers. There are no gaps.
- **Start and end pages are blank** for every part.
- Section headings are the bold or styled standalone heading lines inside each piece, written as `##`, with headings printed over two lines joined. Ch. 2 is made almost entirely of such headings — one per subject ("On Promoting Substantial Justice", "On Technicalities", and so on) above each quoted excerpt.
- The text was not changed.

## Parts in order

| # | Part | Class | Reason / flag | Words |
|---|---|---|---|---|
| 1 | Front matter: cover, title page, photo pages (images only) | SKIP | cover; title page; photo section | 0 |
| 2 | Foreword by Chief Justice Andres R. Narvasa | SKIP | foreword, by someone else | 283 |
| 3 | Part title: JUSTICE | SKIP | part divider | 1 |
| 4 | Ch. 1 On Developing My Decision-Writing Style | CHAPTER | **long** | 9,304 |
| 5 | Ch. 2 Selected Quotations from Ponencias and Opinions | CHAPTER | **long** | 7,013 |
| 6 | Ch. 3 Legal Aspects of Joint Ventures | CHAPTER | **long** · occasion unclear | 10,355 |
| 7 | Ch. 4 Advice for Aspiring Attorneys | CHAPTER | speech (FEU) | 3,547 |
| 8 | Ch. 5 Profiles of Supreme Court Justices | CHAPTER | speech, 1997-10-22 | 805 |
| 9 | Part title: FAITH | SKIP | part divider | 1 |
| 10–15 | Ch. 6–11 (Faith Brought Me to the Supreme Court; Faith in God and in Ourselves; Be Not Afraid; Jesus, Shepherd and Leader of All Time; Offering to the Father; Invocation) | CHAPTER | all six are talks | 11,506 |
| 16 | APPENDIX (divider) | SKIP | appendices | 1 |
| 17 | Appendix A. A Man of God and of the Law | SKIP | appendix, by someone else | 1,345 |
| 18 | Back matter: From the Men of Justice and Faith (accolades) | SKIP | blurbs and accolades · **not in the file** | 0 |

Chapter word counts are in `split_plan.csv`. They run from 269 (Ch. 11, the Invocation) to 10,355 (Ch. 3).

## Decisions for the team
1. **Nothing to register.** All 11 chapters are **already in the corpus**, as `BD020`, `BA041`, `BB008`, `BD021`, `BC012`, `BC013`, `BC014`, `BC015`, `BC016`, `BC017` and `BC018`. Chapter by chapter the word counts agree with the corpus files (differences of 30–60 words, the corpus header plus OCR). The Foreword (`BC011`), Appendix A (`BC019`) and the back matter (`BC020`) are also in the corpus. **B1 assigns no new IDs for this book.** The split is kept as the traceable source-of-record.
2. **long** (over 6,000 words; decide at B1 whether to split at the `##` sections)
   - Ch. 1 *On Developing My Decision-Writing Style* (9,304): a Prologue plus numbered sections on his method; it divides cleanly.
   - Ch. 2 *Selected Quotations from Ponencias and Opinions* (7,013): about fifty short excerpts, each under its own subject heading. If the corpus ever wants quotable units, this is the chapter to split.
   - Ch. 3 *Legal Aspects of Joint Ventures* (10,355).
3. **Speeches** (`collected_piece = yes`): Ch. 4–11. Only one carries its own date in the file — **Ch. 5**, the remarks he made as master of ceremonies at the retirement rites for Justice Justo P. Torres Jr. on **October 22, 1997**. For the rest, the occasion is in `original_outlet` and `original_date` is left blank rather than guessed; the corpus already holds dates for them, which the team should reconcile at B1. **Ch. 3's occasion is not named at all** and is flagged `occasion-unclear`: it reads as a paper for a business audience, opening on the 1995 US–Russia joint space mission.
4. **Appendix A "A Man of God and of the Law" was skipped as written by someone else** — it is a tribute to CJP, not by him. It is already in the corpus as `BC019`.

## Flag, do not fix
1. **No table of contents, page numbers, copyright page or back matter** in the file. The 17 images are the cover, the title page and a photo section; none has a text layer.
2. **The back-matter accolades ("From the Men of Justice and Faith") are not in the file**, although the corpus has them as `BC020`.
3. **Footnote rules survive as text.** Lines of the form `—--------------` mark where footnotes were separated from the body, in Ch. 1 especially. They were kept as printed.
4. **Ch. 5 is a string of short introductions**, one per justice, each under the justice's name as a heading. It is kept as one chapter as printed; B1 may split it if the corpus stores such items individually.
5. **OCR noise**, kept as is. Examples: "modest as it is in volume thought not in quality" (for *though*), "Because of his, he gives them" (for *this*), double spaces after initials.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 42,530 + skipped words 1,631 = 44,161 = whole file | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. Page coverage could not be checked, because the file has no page numbers. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers (assigned 1–11 in book order; the book prints none) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (11 chapter files, 11 CHAPTER rows) |
| Each chapter matches its corpus document | **Pass** for all 11 |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
