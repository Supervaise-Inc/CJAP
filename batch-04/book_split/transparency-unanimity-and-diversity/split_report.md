# B0 split report: Transparency, Unanimity & Diversity

| | |
|---|---|
| Title | Transparency, Unanimity & Diversity |
| Author | Justice Artemio V. Panganiban |
| Publisher | Printed by the Supreme Court Printing Services, Padre Faura, Manila (copyright 2000 by the author; title page: "Printed by Supreme Court Press – November 2000") |
| Year | 2000 (Foreword dated October 12, 2000; Preface dated October 10, 2000) |
| Source file | `batch-04/incoming/books/Transparency Unanimity and Diversity.docx` (2,189 paragraphs, 103,921 words, cover image only) |
| Book slug | `transparency-unanimity-and-diversity` |

**Result: 24 chapters and 14 skipped parts.** Chapter numbers run 1–24 with no gaps.

## How the structure was worked out
- **There is no table of contents in the file**, so the structure comes from the headings in the text, which the Preface confirms:
  - Part I "Transparency": a Prologue and Ch. 1–6.
  - Part II "Unanimity": a Prologue and Ch. 7–15.
  - Part III "Diversity": a Prologue and Ch. 16–24.
  - Appendices A–C and an Index.
- **Start and end pages are blank.** The file has no contents and no page numbers. The Index at the end carries page references, but they cannot be tied to parts reliably.
- Chapter titles printed over several lines were joined. For example, Ch. 14 is "Cabaero v. Cantos: May an Answer With Counterclaim Be Filed in a Criminal Case?".
- Section headings are the bold heading lines inside each chapter, all written as `##`, with headings printed over two lines joined.
  - They include the "Epilogue" sections that close several speeches (Ch. 3–6, 17).
  - They also include the headings of CJP's own opinions that he quotes, such as the numbered heads of his *Serrano* dissent and his *Veterans* and *ABS-CBN* opinions. Those headings start with a quote mark, as printed.
- The text was not changed.

## Parts in order

| # | Part | Class | Reason / flag | Words |
|---|---|---|---|---|
| 1 | Cover title | SKIP | cover | 8 |
| 2 | About the Author (by the SC Public Information Office) | SKIP | about the author | 557 |
| 3 | Epigraph, Matthew 5:14-16 | SKIP | epigraph | 67 |
| 4 | Title page | SKIP | title page | 17 |
| 5 | Copyright page | SKIP | copyright page | 48 |
| 6 | Foreword by CJ Hilario G. Davide Jr. | SKIP | foreword, by someone else | 475 |
| 7 | Preface by Panganiban | SKIP | preface · **candidate** | 1,456 |
| 8 | Part I title + Prologue | SKIP | part divider and short part guide | 171 |
| 9–14 | Ch. 1–6 (Part I: transparency and the "e-values" speeches) | CHAPTER | Ch. 2–6 are speeches | see CSV |
| 15 | Part II title + Prologue | SKIP | part divider and short part guide | 195 |
| 16–24 | Ch. 7–15 (Part II: unanimous decisions) | CHAPTER | | see CSV |
| 25 | Part III title + Prologue | SKIP | part divider and short part guide | 165 |
| 26 | Ch. 16 Death Penalty Cases: A Moratorium on Death | CHAPTER | **long** | 8,794 |
| 27 | Ch. 17 Serrano v. NLRC | CHAPTER | **long** | 10,638 |
| 28–29 | Ch. 18 Lantion; Ch. 19 Veterans Federation Party v. Comelec | CHAPTER | Ch. 19 **long** | see CSV |
| 30–34 | Ch. 20–24 | CHAPTER | | see CSV |
| 35 | Appendix A. Chief Justice Davide: A Man of Integrity, Simplicity And Dedication | SKIP | appendix · **candidate** | 985 |
| 36 | Appendix B. An Overview of the Centenary Celebrations | SKIP | appendix · **candidate** | 1,477 |
| 37 | Appendix C. Service, Excellence and Truth | SKIP | appendix · **candidate** | 2,667 |
| 38 | Index | SKIP | index | 2,373 |

The chapter word counts are in `split_plan.csv`. Chapter words total 93,260 and skipped words total 10,661.

## Decisions for the team
1. **candidate** (skipped, but complete pieces in CJP's own words of 800+ words)
   - **Preface** (1,456 words): his fifth-anniversary essay on judicial transparency.
   - **Appendix A** (985 words): his introduction of CJ Davide as guest speaker. **Possible duplicate:** *Leadership by Example* Ch. 4, "Chief Justice Davide: An Introduction", is also an introduction of Davide and may be the same or a similar text. B1 should compare them.
   - **Appendix B** (1,477 words): his overview of the SC Centenary Celebrations, given as chairman of the Centenary Executive Committee at the June 9, 2000 kickoff.
   - **Appendix C** (2,667 words): "Service, Excellence and Truth", his speech to a Rotary District Conference. *Reforming the Judiciary* Ch. 6 refers back to "my last address during our Rotary District Conference in March 2000", which is probably this speech.
2. **long** (over 6,000 words; decide at B1 whether to split at the `##` sections)
   - Ch. 16, death penalty cases: 8,785 body words.
   - Ch. 17, *Serrano v. NLRC*: 10,624 words. About 4,700 of them are his quoted Separate Opinion (paragraphs 1552–1580).
   - Ch. 19, *Veterans Federation Party v. Comelec*: 7,158 words.
3. **Part Prologues skipped.** Each Part has a short Prologue in CJP's own words (171, 195 and 165 words) that mainly describes the chapters in it. They were skipped, as in the other books. Please confirm.
4. **Speeches** (`collected_piece = yes`).
   - Ch. 2: MAP.
   - Ch. 4: University of the East commencement.
   - Ch. 5: Phi Kappa Phi round table.
   - Ch. 6: CAP event honoring President Osmeña.
   - Ch. 3: an evening address whose occasion is not named in the text; it is marked `yes`, with that note in `original_outlet`.
   - Ch. 1 has no named occasion and is marked `no`.
   - **B1 should check these against the speeches corpus.**

## Flag, do not fix
1. **No table of contents or page numbers** in the file.
2. **Quoted text.** The long quoted runs in the Part II and III chapters are mostly from CJP's own ponencias and opinions, for example his *Serrano* dissent, *Veterans*, *ABS-CBN* and *Basher*. Other justices' opinions are summarized or quoted more briefly. Examples: the Bellosillo and Vitug opinions in *Serrano*, and the majority in *Veterans*. No run by another author exceeds about a page.
3. **About the Author** is written by the SC Public Information Office (557 words), and it was skipped.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 93,260 + skipped words 10,661 = 103,921 = whole book | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. Page coverage could not be checked, because the file has no page numbers. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers follow the book (1–24) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (24 chapter files, 24 CHAPTER rows) |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
