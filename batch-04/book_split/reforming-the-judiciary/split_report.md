# B0 split report: Reforming the Judiciary

| | |
|---|---|
| Title | Reforming the Judiciary |
| Author | Justice Artemio V. Panganiban |
| Publisher | Printed by the Supreme Court Printing Press, Padre Faura, Manila (copyright 2002 by the author) |
| Year | 2002 (title page: December 2002) |
| Source file | `batch-04/incoming/books/Reforming the Judiciary.docx` (2,142 paragraphs, 85,986 words, 13 page images) |
| Book slug | `reforming-the-judiciary` |

**Result: 21 chapters and 18 skipped parts.** The chapters are numbered 1–9 and 11–22. **Chapter 10 is skipped** because others wrote almost all of its text; **Chapter 2 is kept as a chapter** and flagged `by-another-author`; see decision 1. **The .docx is truncated**: it stops mid-sentence in Ch. 22, and the appendices and index are missing. See flag 1.

## How the structure was worked out
- The front matter exists only as scanned images. In order they are:
  - cover and jacket flap;
  - a "With compliments of" card;
  - a four-page **book review by Justice Romeo J. Callejo Sr.**, inserted in the volume;
  - the epigraph (Matthew 4:17);
  - the author photo and title page;
  - the copyright page and Contents;
  - CJ Davide's photo with the first Foreword page.
- I read the **Contents** from those images (pp. vii–ix). Start pages come from it, and each end page is the next start page minus 1.
- The chapter headings in the text match the Contents, with two title differences and one page misprint (see below).
- Section headings are the bold or styled heading lines inside each chapter, all written as `##`. Headings printed over two lines were joined.
- The text was not changed.

### Contents and text differences
- **Ch. 19:** the Contents has "*Equatorial v. Mayfair*"; the text has "Equatorial **Reality** v. Mayfair Theater", which should read "Realty". **Kept as in the text.**
- **Ch. 20:** the Contents has "*City of Makati v. CSC*"; the text has "Makati City v. Civil Service Commission". Kept as in the text.
- **Appendix A:** the Contents prints "Supreme Ties … 269". That is impossible, since Ch. 20 starts on p. 269 and Appendix B on p. 373. It is left blank in the plan.

## Parts in order

| # | Part | Class | Pages | Words |
|---|---|---|---|---|
| 1–7 | Cover, jacket flap, compliments card, **Callejo book review**, epigraph, title page, copyright + Contents (all images) | SKIP | –, vii–ix | 0 |
| 8 | Foreword by CJ Hilario G. Davide Jr. | SKIP · foreword, by someone else | xi–xii | 475 |
| 9 | Preface by Panganiban | SKIP · preface · **candidate** | xiii–xxii | 1,934 |
| 10 | Acknowledgements | SKIP | xxiii | 326 |
| 11 | Photo page + Part I title (image) | SKIP · part divider | 1–2 | 0 |
| 12 | Ch. 1 An Introduction to the APJR | CHAPTER | 3–12 | 1,878 |
| 13 | **Ch. 2 Forum on the APJR** | CHAPTER · **long** · **by-another-author** | 13–42 | 7,558 |
| 14–20 | Ch. 3–9 | CHAPTER (speeches) | 43–106 | see CSV |
| 21 | **Ch. 10 Why the Supreme Court Was Chosen "Filipino of the Year 2001"** | **SKIP** · by others (decision 1) | 107–122 | 4,014 |
| 22–26 | Ch. 11–15 | CHAPTER | 123–182 | see CSV |
| 27 | "PART II" title | SKIP · part divider | – | 2 |
| 28 | Ch. 16 Estrada v. Sandiganbayan | CHAPTER · **long** | 183–214 | 8,480 |
| 29–32 | Ch. 17–20 | CHAPTER | 215–289 | see CSV |
| 33 | Ch. 21 Government of the United States v. Purganan | CHAPTER · **long** | 290–337 | 10,677 |
| 34 | Ch. 22 Important Developments on the Death Penalty | CHAPTER · **long** · **truncated** | 338– | 6,201 |
| 35–38 | Appendices A–D | SKIP · **not in file** | –, 373–386 | 0 |
| 39 | Index | SKIP · **not in file** | 387– | 0 |

## Decisions for the team
1. **Ch. 2 is now a chapter; Ch. 10 is still skipped.** Both were first classified SKIP under the other-author rule. **Corrected on 24 Sep 2026 at the team's request: Ch. 2 is a CHAPTER**, so only Ch. 10 remains a gap. **Please confirm whether Ch. 10 should be restored the same way.**
   - **Ch. 2 "Forum on the APJR" (7,558 words) — now a CHAPTER**, flagged `long; by-another-author`. CJP's own words are about 350 words of introduction. The rest is:
     - CJ Davide's Ramon Magsaysay lecture, "Strengthening the Credibility of the Justice System in the Philippines";
     - Sen. Jovito R. Salonga's "A Comment";
     - Malou Mangahas's (PCIJ) "'Tree of Justice' Won't Grow on Arid Soil".

     The four pieces are separated inside the document by `##` headings — "The Lecture", "Strengthening the Credibility of the Justice System?", "Reactions", "I", "Chief Justice Davide's Lecture on the Credibility of Our System of Justice: A Comment", "II" and "\"Tree of Justice\" Won't Grow on Arid Soil" — so **B1 can split it into four documents if the team prefers one author per document.** Each byline stays in the body.
   - **Ch. 10 "Filipino of the Year 2001" (4,014 words).** CJP's own words are about 150 words of introduction. The rest is two reprinted *Philippine Daily Inquirer* pieces: the unsigned "They saved the constitutional system from collapse" (PDI, January 13, 2002), and Amando Doronila's "SC justices finally OK Gloria oath" (PDI, February 25, 2002).
   - Doronila's article narrates CJP's own role on January 20, 2001, but it is written by the journalist.
   - If the team prefers, CJP's short introductions could be added later as small documents, but they are well under 800 words.
2. **candidate:** the **Preface** (1,934 words). It covers his seventh-year report, the six new justices, the Canada visit, the CIDA grant and the bio-sciences work.
3. **long** (over 6,000 words; decide at B1 whether to split at the `##` sections)
   - Ch. 16 *Estrada v. Sandiganbayan*, the Plunder Law.
   - Ch. 21 *US v. Purganan*, extradition and bail: 10,662 body words.
   - Ch. 22, death penalty developments.
4. **Speeches** (`collected_piece = yes`): Ch. 3, 5, 6, 7, 9 and 11–14. The occasions are taken from each speech's opening, the Preface or a photo caption. Examples: AmCham (Ch. 3, dated August 21, 2002 by Salonga's comment), the FEU commencement and honorary doctorate (Ch. 12), and the Rotary Club of Downtown Manila "Tribute to Valedictorians" on April 6, 2002 (Ch. 13). **B1 should check these against the speeches corpus.**

## Flag, do not fix
1. **Missing pages: the file is truncated.** The last paragraph of Ch. 22 stops mid-sentence: "…the accused may no longer be held liable for illegal". It is item 9 of the chapter's list of developments, so the rest of Ch. 22 is missing. So are **Appendices A–D** (up to p. 386) and the **Index** (p. 387). The appendices are:
   - A. "Supreme Ties", reprinted from *People Asia*.
   - B. "International Citizen Par Excellence", his introduction of Dr. Hans Koechler, per the Preface.
   - C. "Mild, Eloquent, Loyal and Excellent".
   - D. "Dignified, Discerning, Diligent and Directed".

   B–D look like CJP tributes or introductions and could be "candidate" pieces, but they are not in the file.
2. **Text by someone else inside kept chapters.**
   - **Ch. 1** quotes the APJR **Executive Summary**, an SC institutional document (paragraphs 176–213, about 1,500 words), as most of the chapter.
   - **Ch. 15** quotes readers' letters and press comments about *A Centenary of Justice*.
   - **Ch. 17, 19 and 21** quote Court decisions and other justices’ opinions at length. The longest runs are in Ch. 21: about 1,000 words from the Separate and Dissenting Opinions (paragraphs 1942–1953) and more.
   - **Ch. 22** quotes long passages of Court decisions (about 1,900 words, paragraphs 2063–2088).
3. **The inserted book review by Justice Callejo** is only in the images; it is not in the text layer. It was skipped as a book review.

## Self-checks
| Check | Result |
|---|---|
| Coverage: chapter words 71,677 + skipped words 14,309 = 85,986 = whole book | **Pass (100.0%)**. Every non-empty paragraph belongs to exactly one part. The pages from the Contents (vii–338) map to exactly one part each. The Ch. 22 tail, the appendices and the Index are absent from the file (flag 1). |
| No overlap: each file's first and last sentence appear only in that file | **Pass** |
| No empty chapter file | **Pass** |
| Chapter numbers follow the book | **Pass, with one reported gap: Ch. 10** (skipped, decision 1). Ch. 2 restored 24 Sep 2026. Not renumbered. |
| No file created for a SKIP part | **Pass** (21 chapter files, 21 CHAPTER rows) |

**STOP.** Please confirm `split_plan.csv` before B1 runs on this book.
