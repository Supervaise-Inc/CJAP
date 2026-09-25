# Error fixes, 23 Sep 2026

Three sets of errors were on the list: the B1 manifest flags, the B0 source-file problems, and the corpus defects D-1…D-10. What was fixed, what is proposed and what is blocked:

## 1. B1 manifest flags — fixed in `batch-04/intake_manifest.csv`
| Was | Now |
|---|---|
| 52 rows with year-only dates | All dated to month precision from the book's own front matter: Leadership by Example 1999-10-01 (Preface, October 10, 1999), Liberty and Prosperity 2006-07-01 (Preface, July 31, 2006), Love God Serve Man 1994-08-01 (Acknowledgments, August 31, 1994). The reason is in each row's note. |
| Leveling the Playing Field publisher blank | Recorded as "Not stated in the file (Google Books lists the publisher as 'Artemio V. Panganiban, 2004')" |
| — | While rewriting the file, row CA529 was dropped and restored in the same pass; the manifest was verified afterwards at 186 rows with 186 unique doc_ids and nothing missing against the pre-B1 backup. |

The manifest now has no year-precision rows: 147 month and 39 day.

**Still open (cannot be fixed from the files):**
- **Rights for Love God, Serve Man (22 rows).** Published by the Philippine Daily Inquirer, edited by Isagani Yambot, whose notes open each piece. Needs a person to confirm PDI/editor consent.
- **Publisher for Leadership by Example and Liberty and Prosperity.** Neither file has a title or copyright page.
- **Reforming the Judiciary Ch. 3 (BA083's neighbour, BD039)** keeps the book date; its speech date (2002-08-21) appears only in the skipped Ch. 2.

## 2. B0 source-file problems — listed for re-supply
Nothing here can be repaired from the files we have, so `book_split/SOURCE_GAPS.md` now lists, book by book, exactly what to re-scan, in priority order:
1. the tail of Reforming the Judiciary Ch. 22 (the only registered chapter with incomplete text, BA083);
2. the appendices of Battles, Leveling the Playing Field and Reforming the Judiciary (several look like CJP pieces of 800+ words);
3. the missing footnotes of Battles, Judicial Renaissance and Liberty and Prosperity;
4. the front matter of Leadership by Example, Leveling the Playing Field and Liberty and Prosperity (publisher and page numbers).

OCR noise and the broken headings in Love God, Serve Man stay as printed: B0 must not edit the author's text, so they are B2/B3 corrections against the printed book.

## 3. Corpus defects
**D-9 Word-conversion markup in GC021–GC035 — FIXED.** All 15 biography chapters in `data/text` were cleaned: byte-order marks removed, about 2,770 Pandoc escapes (`\.`, `\-`, `\'`) unescaped, 123 `__bold__` runs converted to `**bold**`, and stray double spaces and blank lines tidied. **Check: the alphanumeric word sequence of every file is byte-for-byte identical to before**, so only markup changed. Backups and a change log are in `batch-04/backup_data_text_GC021-035_2026-09-23/`.

**D-2 and D-7 dates — proposed, not applied.** These values live in the pinned `data/csv/*.xlsx`, which B1 may not touch, so `batch-04/d7_date_normalisation_proposed.csv` lists all 131 rows for sign-off:
- 58 columns and book chapters in US `M/D/YYYY` form → ISO day dates.
- 22 A Centenary of Justice chapters carrying a wrong date → 2001-12-01, month precision (this is D-2).
- 20 Bio-Age chapters with the year stored as a float ("2003.0") → 2003-01-01, year.
- 19 biography chapters with period labels ("1955-1959") → start year plus a period field, and 12 that are not dates at all ("Childhood,", "circa 2024") and need a decision.
- **Root cause worth noting:** the biography values are cut at exactly 10 characters ("July-Augus", "2007-prese"), so the Date column was truncated on ingestion, not merely mistyped.

**Blocked**
- **D-1 (YAML leak) and D-10 (book-title fix)** are already corrected in `data/text`; they only need the corpus regenerate, which we agreed to run together with the remaining 4 books.
- **D-3 (27 chunks held by retired docs)** needs the chunk and index rebuild. The chunker and the date-index script are here, but the dense/sparse index builders are still only in the working repo, which is **D-5**. So D-3 waits for D-5.
- **D-4** (the missing normalisation script) is P5 work in the shared merge prompt.
