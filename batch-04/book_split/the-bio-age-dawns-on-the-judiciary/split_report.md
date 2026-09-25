# B0 split report: The Bio-Age Dawns on the Judiciary

| | |
|---|---|
| Title | The Bio-Age Dawns on the Judiciary |
| Author | Justice Artemio V. Panganiban |
| Publisher | **Not stated in the file** — there is no copyright page in the transcription. The corpus records the book as 2003; please confirm the imprint. |
| Year | 2003 (his eighth year on the Court; the Preface describes his move from the Senate Electoral Tribunal to the HRET on July 1, 2003, and Ch. 6 refers to the Session Hall reopening of April 1, 2003) |
| Source file | `batch-04/incoming/books/The Bio-Age Dawns on the Judiciary.docx` (2,379 paragraphs, 103,330 words, no images) |
| Book slug | `the-bio-age-dawns-on-the-judiciary` |

**Result: 14 chapters and 8 skipped parts.** Chapter numbers run 1–14 with no gaps.

## How the structure was worked out
- **There is no table of contents in the file**, so the structure comes from the headings in the text, which the Davide Foreword confirms: "As in his previous books, Part II (consisting of eight chapters) is a first person account of what this jurist had previously termed as the 'judicial jousts'."
  - **Part I**: Ch. 1–6, the speeches and papers.
  - **Part II**: Ch. 7–14, the cases.
  - Appendices A–D, each by a different author.
- **Start and end pages are blank.** The file has no page numbers.
- Chapter titles printed over two or three lines were joined, for example Ch. 13 "The New Rules on Psychological Incapacity as a Ground to Void a Marriage".
- Section headings are the bold or styled standalone heading lines inside each chapter, written as `##`, with headings printed over two lines joined.
- The text was not changed.

## Parts in order

| # | Part | Class | Reason / flag | Words |
|---|---|---|---|---|
| 1 | Front matter: cover and title page | SKIP | cover; title page | 11 |
| 2 | Foreword by CJ Hilario G. Davide Jr. | SKIP | foreword, by someone else | 519 |
| 3 | Preface by Panganiban | SKIP | preface · **candidate** | 1,395 |
| 4 | PART I (part title) | SKIP | part divider | 2 |
| 5–10 | Ch. 1–6 | CHAPTER | Ch. 1 and 2 **long** | 30,508 |
| 11 | PART II (part title) | SKIP | part divider | 2 |
| 12–19 | Ch. 7–14 | CHAPTER | Ch. 10, 12, 14 **long** | 42,438 |
| 20 | Appendix A. Life Technologies and the Rule of Law, by Dr. Franklin M. Zweig | SKIP | appendix, by someone else | 4,493 |
| 21 | Appendix B. GMO & Food Products, by Justice Leonardo A. Quisumbing | SKIP | appendix, by someone else | 3,202 |
| 22 | Appendix C. DNA as Evidence, by Prof. Pacifico A. Agabin | SKIP | appendix, by someone else | 14,901 |
| 23 | Appendix D. Being Moral in the Brave, New World | SKIP | appendix, by someone else | 5,859 |

Per-chapter titles and word counts are in `split_plan.csv`. The longest chapter is Ch. 2 *Judicial Globalization* (12,589 words); the shortest is Ch. 9 *PCGG v. Desierto* (1,666).

## Decisions for the team
1. **Nothing to register.** All 14 chapters are **already in the corpus**, as `BE026`, `BD022`–`BD026`, `BA042`–`BA049`. Chapter by chapter the word counts agree with the corpus files (differences of 25–35 words, the corpus header). The Foreword (`BC021`), the Preface (`BC022`) and all four appendices (`BE027`, `BE028`, `BA050`, `BE029`) are in the corpus too. **B1 assigns no new IDs for this book.** The split is kept as the traceable source-of-record.
2. **The four appendices are by other authors and were skipped.** The book itself says so: "(In deference to the authors, the following articles — reprinted with their permission — have not been edited to conform to the style of this book.)" They are Dr. Franklin M. Zweig (A), Justice Leonardo A. Quisumbing (B) and Prof. Pacifico A. Agabin (C); Appendix D, "Being Moral in the Brave, New World", is also a reprinted article and not CJP's. They are almost 29,000 words — 28% of the file — which is why the skipped-word total is so large here. **They are nonetheless already in the corpus** (`BE027`, `BE028`, `BA050`, `BE029`), which the team may want to revisit, since the corpus is meant to hold CJP's own voice. **Please confirm.**
3. **candidate:** the **Preface** (1,395 words) — his eighth-year report. Already in the corpus as `BC022`.
4. **long** (over 6,000 words; decide at B1 whether to split at the `##` sections): Ch. 1 *Enter the Bio-Age* (6,379), Ch. 2 *Judicial Globalization* (12,589), Ch. 10 *Agan v. Piatco* (8,612), Ch. 12 *Macalintal v. Comelec* (6,341), Ch. 14 *Update on Death Penalty Cases* (11,370).
5. **Speeches** (`collected_piece = yes`): Ch. 2, 4, 5 and 6. The occasion is in `original_outlet` — the First Australasia Judicial Educators Forum convened by Philja (Ch. 2), the 61st anniversary of the Adamson University College of Law (Ch. 4), an after-dinner talk on appellate practice (Ch. 5), and the tribute to Justice Vicente V. Mendoza in the SC Session Hall (Ch. 6). **None of them is dated in the file**, so `original_date` is left blank rather than guessed. **B1 should check all four against the speeches corpus.**

## Flag, do not fix
1. **Nearly a third of the file is by other authors** — the four appendices, 28,455 words (see decision 2).
2. **Text by someone else inside kept chapters.** The Part II chapters quote Court decisions and other justices' separate and dissenting opinions at length; the longest runs are in Ch. 10 (*Agan v. Piatco*), Ch. 12 (*Macalintal*, the Tinga and Ynares-Santiago opinions) and Ch. 9 (Justice Gutierrez's dissent).
3. **No table of contents, page numbers, copyright page or index** in the file.
4. **OCR noise**, kept as is. Examples: "I'his gathering provides" (for *This*), "on the merits of a cas" (for *case*), "[voluntary renunciation" (missing the capital).

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 72,946 + skipped words 30,384 = 103,330 = whole file | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. Page coverage could not be checked, because the file has no page numbers. |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers follow the book (1–14) | **Pass**, no gaps |
| No file created for a SKIP part | **Pass** (14 chapter files, 14 CHAPTER rows) |
| Each chapter matches its corpus document | **Pass** for all 14 |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
