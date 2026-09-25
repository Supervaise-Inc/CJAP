# B0 split report: Liberty and Prosperity

| | |
|---|---|
| Title | Liberty and Prosperity |
| Author | Chief Justice Artemio V. Panganiban |
| Publisher | **Not stated in the file.** There is no copyright page in the transcription. The Preface says it is an SC publication with a CD version, so probably the Supreme Court Printing Services; please confirm. |
| Year | 2006 (Foreword dated July 31, 2006; Preface dated July 31, 2006; "current only as of July 31, 2006") |
| Source file | `batch-04/incoming/books/Liberty and Prosperity.docx` (2,847 paragraphs, 92,428 words, cover image only). The file says it is a "Complete text transcription from the supplied 314-page scan". |
| Book slug | `liberty-and-prosperity` |

**Result: 35 chapters and 5 skipped parts.** Chapter numbers run 1–35 with no gaps.

## How the structure was worked out
- **There is no table of contents in the file**, so the structure comes from the headings in the text. The Preface's description of the book confirms it:
  - Part I "A Judicial Philosophy and Program": Ch. 1–18, with Ch. 18 "a kind of Epilogue".
  - Part II "Significant Decisions": an Introduction and Ch. 19–35.
- **Start and end pages are blank for every part.** The transcriber's editorial note says "the original pagination is identified in bracketed source-page markers", but **no page markers are in the file** (see flag 1).
- Chapter titles printed over several lines were joined. Examples: Ch. 19 "The Senate v. Ermita: Validity of EO 464 Barring Executive Officials from Appearing in Congress", and Ch. 35's title, kept with its printed hyphen.
- Section headings are the bold or styled heading lines inside each chapter, all written as `##`.
  - Headings printed over two lines were joined, such as "Do Your Best, and / God Will Do the Rest" and "First Issue: / Res Judicata".
  - A group heading directly followed by its first sub-heading was left as two headings. For example, "The Separate Opinions" followed by "Concurring Opinion of the Chief Justice".
- The text was not changed.

## Parts in order

| # | Part | Class | Reason / flag | Words |
|---|---|---|---|---|
| 1 | Title and transcriber's editorial note | SKIP | title page | 58 |
| 2 | Foreword by Jovito R. Salonga | SKIP | foreword, by someone else | 3,522 |
| 3 | Preface by Panganiban | SKIP | preface · **candidate** | 3,370 |
| 4 | Part I title | SKIP | part divider | 7 |
| 5–22 | Ch. 1–18 (Part I: speeches and essays) | CHAPTER | see `split_plan.csv` | 43,596 |
| 23 | Part II title + Introduction | SKIP | part divider and short part guide | 526 |
| 24–40 | Ch. 19–35 (Part II: case summaries) | CHAPTER | Ch. 21 **long** | 41,349 |

The per-chapter titles and word counts are in `split_plan.csv`. Ch. 1 is the shortest at 378 words: his statement on appointment. Ch. 21 *David v. Arroyo* is the longest at 6,420 words (with title).

## Decisions for the team
1. **candidate:** the **Preface** (3,370 words). It is his own essay: the book's plan, the eight roles of a Chief Justice, his work load and his retirement. It overlaps in substance with the Foreword and with Ch. 4 and Ch. 10.
2. **long:** Ch. 21 *David v. Arroyo* (PP 1017), 6,407 body words and 17 sections. It could be split into the Decision and the Separate Opinions at B1.
3. **Part II Introduction skipped** (about 500 words). It mostly reproduces his Foreword to the SC publication *In Defense of Liberty* and lists the chapters. If the team wants it, it would fit at the start of Ch. 19. Please confirm.
4. **Speeches** (`collected_piece = yes`, occasion from each speech's opening in `original_outlet`). Part I chapters 1–3, 5–9, 11, 12, 14 and 16–18 are speeches.
   - **Ch. 8** is itself a compendium of three 2006 speeches to the youth, including an April 1, 2006 commencement address. It is kept as one chapter per rule 1; B1 may want to check it against three separate speech records.
   - Ch. 4, 10, 13 and 15 read as papers or lectures without a named occasion, so they are marked `no`.
   - **B1 should check all of Part I against the 153 speeches in the corpus.** Many are from his chief-justice year (Dec 2005–2006), which the corpus's speeches may already cover.

## Flag, do not fix
1. **The transcription is missing what its own note promises.**
   - It says source-page markers are included, but none are present.
   - It says footnotes are "transcribed immediately after the source page", but no footnote texts were found. The note markers remain in the text, for example "legal staff20" in the Preface and "[4]" in the Foreword.
   - It says the scan had 314 pages, and the file has no index, appendices or back matter. **Please check the printed book for appendices** after Ch. 35.
2. **Text by someone else inside chapters.**
   - Ch. 21: a long quotation of the Court's dispositive ruling on PP 1017 (paragraphs 1914–1920, about 600 words).
   - The Part II chapters summarize and quote other justices' separate and dissenting opinions. For example: the Chief Justice and Santiago concurrences and the Tinga dissent in *David*, the Carpio and Santiago dissents in *Estrada v. Escritor*, and Justice Tinga in Ch. 19, 28, 30, 32 and 35.
3. **The Foreword is 3,522 words by Jovito R. Salonga.** It quotes CJP at length and was skipped whole, as a foreword by someone else.
4. **OCR noise and gaps**, kept as is. Examples: "Upon assuming the chief justiceship of the immediately vowed" (Ch. 4, words missing); "My father was a mere high school primary school" (Ch. 2, garbled); and duplicate item "4." in the Foreword's list.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 84,945 + skipped words 7,483 = 92,428 = whole book | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. Page coverage could not be checked, because the file has no page markers. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers follow the book (1–35) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (35 chapter files, 35 CHAPTER rows) |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
