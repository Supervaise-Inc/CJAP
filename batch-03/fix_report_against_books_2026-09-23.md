# Correcting `data/text` against the original book files — 23 Sep 2026

Every one of the 119 active book-chapter documents in the corpus was compared, paragraph by paragraph, against the chapter as it appears in the original `.docx` in `batch-04/incoming/books/` (via the verified B0 splits, which cover 100% of each book's words).

**Backups:** `batch-03/backup_data_text_2026-09-23/` (one file per document touched) · **log:** `batch-03/change_log.csv` (before/after sha256 and word counts).

## The result of the comparison

| | Chapters | |
|---|---|---|
| Already identical to the book | **95** | all of Bio-Age (14), 74 of 75 With Due Respect, 7 of 11 Justice and Faith |
| Fixed in this pass | **5** | BA031, BC017, BC018 → now 100% identical; plus BB008 and BC014, which were already within OCR noise |
| Staged for your review, not applied | **19** | every chapter of *A Centenary of Justice* — see the finding below |

After this pass, **100 of 119 chapters match their book exactly.**

## The finding that changed the plan

The instruction was to correct the corpus from the original book files. For eleven of the twelve books that is exactly right, and it is what I did. **For *A Centenary of Justice* it would have destroyed content**, so I staged the result instead of applying it.

The uploaded `.docx` for that book is not a superset of what the corpus holds:

- **It dropped every footnote.** 427 footnote paragraphs exist only in the corpus — case citations, cross-references, page references. For example `BA032`: *"1 Macias v. Malig (157 SCRA 762, 776, January 29, 1988, per Feliciano, J.) describes law as a 'learned profession.'"* and 118 more in that chapter alone.
- **It carries OCR damage the corpus does not.** In Ch. 12 the `.docx` reads *"May, I also congratulate the PRSP, especially its president — the hardworking and wellliked Gen. Honesto M. Isleta"*; the corpus has *"May I also congratulate … the hard-working and well-liked"*.
- **It also drops the book's italic and bold typography**, which the corpus preserves.

But the corpus is worse in the other direction:

- **It is missing body text.** Ch. 13 (`BA036`): the corpus has 7,873 words against the book's 9,546 — it is missing the whole "The Concurring Opinions" passage and about 1,300 words of the inhibition discussion.
- **It has no `##` section headings at all**, having flattened them into italic lines. The chunker is heading-aware, so this costs retrieval quality.

A straight replacement would have traded 427 footnotes for the missing body text. Neither direction is a clean win, so I built a merge instead.

## What was applied to `data/text/` — 26 files

| Fix | Docs | Detail |
|---|---|---|
| **C-1 / D-1 + D-12a** — strip YAML front matter | 22 | The only files in `data/text/` opening with a `---` block. Alphanumeric token sequence of every body verified unchanged. |
| **C-5 / D-11** — `BA031` back matter | 1 | Removed the printed COLOPHON and the back-cover blurb. 1,124 → **947** words. Now 100% identical to the book. |
| **C-6 / D-12b** — `BA039` overrun | 1 | Removed Appendices A–D and the back matter, which duplicated `BC007`/`BC008`/`BD019` and belonged to retired `BC009`/`BC010`. 14,347 → **4,094** words. |
| **C-7 / D-13** — `BC018` truncated | 1 | Was 97 words opening mid-sentence. Restored in full from the book: **276** words. Now 100% identical. |
| **`BC017`** — OCR-shredded body | 1 | The corpus text had interleaved words: *"rols his Many years ago, I was a restles hen was in sea rch of fame and fortune. s young man who"*. Restored from the book: 1,614 → **1,511** words. Now 100% identical. |
| **Running headers** | 8 | 19 page-furniture lines removed, e.g. `108 A CENTENARY OF JUSTICE A BENCHBOOK FOR JUDICIAL EXCELLENCE 109`, `APPENDICES 401`. |

### One thing I got wrong and reverted

My first running-header rule was too broad and stripped 16 lines from four files that were **real ALL-CAPS section headings**, not page furniture:

- `BD020` — `A. CRIMINAL CASES`, `B. NONCRIMINAL CASES`, `C. SEPARATE OPINIONS`
- `BB008` — `FIRST REGULAR INVESTMENT`, `NEGATIVE LIST`, `LIST A. FOREIGN OWNERSHIP IS LIMITED BY MANDATE OF THE CONSTITUTION…`
- `BC021` — `FROM THE CHAMBERS OF`, `CHIEF JUSTICE` (Davide's letterhead)
- `BC022` — `ARTEMIO V. PANGANIBAN` (the Preface signature)

All four were restored byte-for-byte from backup and removed from the change log. The rule now only removes lines that carry the book title or an appendix running head with a page number.

## What is staged, not applied — `batch-03/proposed_data_text/`

The 19 *A Centenary of Justice* chapters, merged: the **corpus as the spine** (it is the better transcription and holds the footnotes), with the book's missing passages and section headings spliced in. Where the two disagree on the same paragraph, both are kept unless one is a near-duplicate of the other.

| | |
|---|---|
| Words | 79,731 → **89,626** (+12%) |
| Footnotes preserved | **414** |
| `##` section headings restored | **70** |
| Paragraphs recovered from the book | **202** |
| Near-duplicate paragraphs suppressed | 108 |
| Residual near-identical repeats | **5** (3 in `BA032`, 1 each in `BA039`, `BB006`) |

Per-chapter numbers: `batch-03/centenary_merge_report.csv`.

**This is an algorithmic reconciliation of two imperfect transcriptions.** It is a clear improvement on either source alone, but it is not something I would drop into the corpus unreviewed — hence the staging folder. The biggest gains are Ch. 13 (7,873 → 10,034 words, 7 headings) and Ch. 2 (14,211 → 17,679, 21 headings, 119 footnotes kept).

## What still needs you

1. **Approve or reject the Centenary merge.** If you approve, the 19 files move from `batch-03/proposed_data_text/` into `data/text/` and join the batch-03 changed-doc set. If you reject, the 19 chapters stay as they are and keep their footnotes but not the missing text.
2. **A better scan of *A Centenary of Justice*** would remove the problem at the root — one with the footnotes intact. It is worth adding to `book_split/SOURCE_GAPS.md` as a priority item.
3. **The 31 biography dates** — still the open item on `batch-03/date_normalisation.csv` (`GC002` has no date at all; several are periods like `1955-1959`).

Nothing has been regenerated. `corpus/` is untouched and still reflects the pre-fix sources; the regenerate happens when batch-03 runs.
