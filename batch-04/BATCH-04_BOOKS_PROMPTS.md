# Batch-04 — BOOKS: split → `.md` → enriched rows

For books. Columns have their own file: `BATCH-04_COLUMNS_PROMPTS.md`. Both feed the same merge steps (P5–P8)
in `BATCH-04_PROMPTS.md`. Follows **CJAP_Robot_Project_Plan_v2.xlsx → Corpus Expansion** CE-3 · CE-1 · CE-1a ·
CE-1b, using the formats on the **Data Flow** sheet. Paths are relative to the Final Project Folder.

| # | Step | Output | Human check |
|---|---|---|---|
| B0 | CE-3 split each book into chapters — **one run per book** | `batch-04/book_split/<book>/` chapter files + `split_plan.csv` | Confirm chapters and skipped parts |
| B1 | CE-1 intake + IDs for the confirmed chapters | rows in `batch-04/intake_manifest.csv` | Confirm IDs, themes, long-chapter splits |
| B2 | CE-1a chapter files → contract `.md` | `batch-04/data_text/<ID>.md` | Skim 5 files against the book |
| B3 | CE-1b enrichment | `batch-04/books_enriched.xlsx` | — |
| B4 | CE-1b QA | `batch-04/qa_books.md` + `spot_check_books.xlsx` | Sign off 10 rows |
| → | Merge | P5–P8 in `BATCH-04_PROMPTS.md` | |

## Before you start

1. Put each book file (`.docx`, `.pdf`, `.doc`) in `batch-04/incoming/books/`, one file per book.
2. Books already partly in the corpus: A Centenary of Justice (22 chapters), The Bio-Age Dawns on the Judiciary (20),
   Justice and Faith (14), With Due Respect Vols. 1–6 (10 each) and Vol. 7 (15). B1 adds only the missing chapters.
3. Not CJ Panganiban's writing, so not added as a book: the 1987 Philippine Constitution.
4. Next free book IDs: BA051 · BB009 · BC023 · BD027 · BE030. Retired, never reused: BA040, BC009, BC010, BD018.

---

## B0 · CE-3 — Split each book into chapter documents  (Cowork, books only)

Run once per book, before B1.

**The rule in one line:** every chapter becomes its own document, however short. Forewords, appendices and
other parts with little content of his own do not become documents; they are listed, not lost.

```
B0 — BOOK SPLIT: separate <book file> into one document per chapter

BOUNDARIES
- Input: ONE file in batch-04/incoming/books/. Output only under batch-04/book_split/<book_slug>/.
- Do not assign IDs, do not enrich, and do not touch data/ or corpus/.
- Do not edit, shorten, merge or reorder the author's text. Only cut it at chapter boundaries and remove
  running headers, footers, page numbers and file-conversion markup (backslash escapes like "\." or "\-",
  stray "__" or "*" pairs left by Word/PDF conversion — defect D-9 came from exactly this).

RULES
1. ONE CHAPTER = ONE DOCUMENT, whatever its length. A 400-word chapter is still its own document.
   Never merge short chapters together, and never split a chapter into parts in this step.
2. DO NOT CREATE A DOCUMENT for UNNUMBERED parts with little or no content of his own. Classify them SKIP:
   cover · title and copyright pages · dedication · epigraph · table of contents · foreword · preface ·
   acknowledgments · introduction or commentary written by someone else · list of photos/figures ·
   photo sections · appendices and annexes · bibliography / references · glossary · index ·
   about the author · blurbs, accolades and book reviews · publisher's notes.
3. KEEP AS A CHAPTER the author's own Introduction, Prologue or Epilogue when it carries his argument
   or story (not just thanks or a list of contents) — flag it so the team can confirm.
4. SKIPPED BUT WORTH A LOOK: if a skipped part is a complete piece in CJP's own words of 800+ words
   (a full speech, tribute or column reproduced in an appendix), still SKIP it, but mark it
   "candidate" so the team can decide to add it later as a separate document.
5. COLLECTION BOOKS (e.g. With Due Respect, which reprint his columns or speeches): each reprinted piece is
   one chapter document. Record its original date and outlet if the book prints them, so B1 can check
   it against the 785 columns and 153 speeches already in the corpus.
6. VERY LONG CHAPTERS: a chapter over 6,000 words stays ONE document here; mark it "long" so the team
   can decide at B1 whether to split it at its sections.
7. A NUMBERED CHAPTER IS ALWAYS A CHAPTER, WHOEVER WROTE IT. If the book prints a chapter number above a
   piece by someone else — a reprinted column, a guest lecture, a reaction paper — it becomes a CHAPTER
   document like any other. Do NOT skip it under rule 2; that clause covers unnumbered parts only.
   - put `by-another-author` in `flags`, and name the author in `part_label_as_printed`;
   - keep the printed byline as the document's FIRST body line, so authorship survives the flag;
   - if the chapter holds several pieces by different authors, keep it as one document (rule 1) but put a
     `##` heading above each piece so B1 can split it per author without going back to the book.
   A gap in a book's chapter numbers must therefore mean the BOOK skipped that number. Any gap has to be
   explained as such in split_report.md. See docs/decisions/ADR-0019.
   B1 decides whether such a document is registered at all: it is not in CJP's voice, and the FLP corpus
   permission does not cover it — its rights line names the other author.

STEPS
1. Read the whole book. Work out its structure from the table of contents AND the headings in the text.
   Where they disagree, follow the headings in the text and report the difference.
2. Classify every part, in order, as CHAPTER or SKIP (with the reason from rule 2, 3 or 4).
3. For each CHAPTER write batch-04/book_split/<book_slug>/ch<NN>_<short-title-slug>.md:
   first line "# Chapter <N>: <chapter title as printed>", then the chapter text exactly as in the book,
   with its section headings as "## Heading". NN is two digits, in book order.
4. Write batch-04/book_split/<book_slug>/split_plan.csv with columns:
   order, book_title, part_label_as_printed, classification (CHAPTER/SKIP), skip_reason, chapter_no, chapter_title,
   start_page, end_page, word_count, file, collected_piece (yes/no), original_date, original_outlet,
   flags (candidate / long / author-introduction / unclear-boundary)
5. Write batch-04/book_split/<book_slug>/split_report.md: book title, author, publisher, year;
   the number of chapters and skipped parts; the skipped list with reasons; every "candidate",
   "long" and "author-introduction" flag; and the coverage check below.

SELF-CHECKS (must pass)
- COVERAGE: words in chapter files + words in skipped parts ≈ words in the whole book (within 3%).
  Every page belongs to exactly one part.
- NO OVERLAP: each chapter file's first and last sentence appear in that file only.
- No chapter file is empty. Chapter numbers follow the book; report any gap instead of renumbering.
- No file was created for a SKIP part.

FLAG, DO NOT FIX
- Missing or duplicated pages · a chapter that seems to run into the next · more than a page of text by
  someone else inside a chapter · a part you cannot classify.
STOP and wait for the team to confirm split_plan.csv before running B1.
```

---

## B1 · CE-1 — Intake and IDs for the confirmed chapters  (Cowork)

```
B1 — register the confirmed book chapters in batch-04/intake_manifest.csv and assign IDs

BOUNDARIES
- Work only inside batch-04/. Do NOT touch data/, corpus/ or the pinned data/csv sheets.
- Register ONLY rows marked CHAPTER in each confirmed batch-04/book_split/<book>/split_plan.csv.
  Never add a row for a SKIP part.
- Never reuse or renumber an ID. Retired IDs (data/csv/retired_doc_ids.csv) stay taken.

STEPS
1. For every confirmed chapter record: source (the chapter file path), material_type = book chapter,
   title "<Book title> -- Ch. <N>: <Chapter title>", publication date, publisher, rights/consent status
   ("CJP-authored, covered by the FLP corpus permission" unless the book says otherwise — FLAG any doubt),
   book_title, chapter_no, est_words (from split_plan.csv).
2. DUPLICATE CHECK. Compare each chapter's normalised title against every corpus/*/*/*.json title and
   archive/phase1/id_map_phase1_to_live.csv. For a COLLECTED PIECE (a reprinted column or speech), also
   compare its original date and outlet with the existing columns and speeches. List every match in a
   "duplicates" section and do not register it.
   Books already partly in the corpus (A Centenary of Justice, The Bio-Age Dawns on the Judiciary,
   Justice and Faith, With Due Respect Vols. 1-7): register only the chapters that are not there yet.
   The four retired Centenary IDs (BA040, BC009, BC010, BD018) stay retired; if one of those parts is now
   available in full AND is a chapter under the B0 rules, give it a NEW ID and note "replaces retired <ID>".
3. LONG CHAPTERS (flagged "long" in B0): ask the team — keep whole, or split at its sections into
   "<Book title> -- Ch. <N>.<n>: <Section title>" documents with consecutive IDs.
4. THEME. One theme letter A-E per chapter by its main subject (A liberty and rule of law · B prosperity and
   economic philosophy · C biographical and personal · D FLP mission and foundation · E current events
   commentary) with a one-line reason. Chapters of one book may have different themes.
5. IDs. Next free book IDs from the Data Flow register: BA051 · BB009 · BC023 · BD027 · BE030 (re-check
   against corpus/, the manifest and retired_doc_ids.csv first). Within a series, assign in book order.
6. DATES. Text YYYY-MM-DD plus date_precision: "day", "month" (YYYY-MM-01) or "year" (YYYY-01-01). Use the
   chapter's own date if printed (collected columns and speeches), otherwise the book's publication date.
7. Append to batch-04/intake_manifest.csv (keep its existing header and rows).
8. Write batch-04/intake_books_report.md: chapters per book, IDs used, duplicates, long-chapter decisions
   needed, and every flag.

SELF-CHECKS (must pass)
- One manifest row per CHAPTER row in the confirmed split plans (minus duplicates); none for SKIP parts.
- No doc_id appears twice in the manifest, in corpus/, or in retired_doc_ids.csv.
- Every row has a theme, a date with a precision, and a rights status.

FLAG, DO NOT FIX
- Unclear rights · a missing or ambiguous date · a probable duplicate · a chapter not written by CJP.
STOP and wait for the team to confirm IDs and themes.
```

---

## B2 · CE-1a — Chapter files → contract `.md`  (Cowork)

```
CE-1a — convert every confirmed batch-04 book chapter into one source .md in the contract format

BOUNDARIES
- Read batch-04/intake_manifest.csv (confirmed rows only). Write only to batch-04/data_text/.
- Do NOT write to data/text/ — files move there at CE-4. Do not edit the originals in batch-04/incoming/.
- Do not rewrite, summarise, translate or "tidy" CJP's wording. Only fix extraction damage
  (broken hyphenation across lines, page headers/footers, page numbers, OCR splits).

STEPS
1. For each manifest row, take the text of exactly that document from its source. Use the
   chapter file from B0 (batch-04/book_split/<book>/ch<NN>_….md), not the whole book, and drop its
   "# Chapter N: …" line (the manifest title replaces it). Parts marked SKIP in B0 are never converted.
2. Write batch-04/data_text/<doc_id>.md in this exact shape:

   # <title from the manifest>
   Date:       <publication_date>
   Publisher:  <publisher>
   Source:     <URL, or "<book title>, <publisher> <year>, pp. x–y">
   By: Artemio V. Panganiban

   <body in markdown>

   - Keep the author's section headings as "## Heading"; turn bold-only heading lines into "## Heading".
   - Keep paragraphs, block quotes (">"), and lists. Keep footnotes at the end under "## Notes".
   - NO YAML '---' block anywhere, and no horizontal rules ('---', '***').
   - File name = the three-digit doc_id (CA530.md, never CA53.md). UTF-8.
3. For each file record: word count, number of '##' headings, first and last sentence, and any gap
   (unreadable page, missing section, garbled OCR).
4. Write batch-04/source_check.md with that table plus a list of items whose text is incomplete.

SELF-CHECKS (must pass)
- One .md per confirmed manifest row, and no extra files.
- Every file's first line is "# " + the manifest title; lines 2–5 are the header; line 6 is blank.
- No file contains a line that is exactly '---'.
- The body word count is within ±5% of the B0 split_plan word_count (explain any outlier).

FLAG, DO NOT FIX
- Missing pages or sections · text that looks like it belongs to another chapter · passages not by CJP
  (quoted decisions, forewords) that are longer than a page — keep them, but list them.
```

---

## B3 · CE-1b — Enrichment for book chapters  (Cowork)

```
CE-1b — draft one enriched row per batch-04 document, matching the existing corpus

BOUNDARIES
- Read batch-04/data_text/<ID>.md and batch-04/intake_manifest.csv. Write only
  batch-04/books_enriched.xlsx (append).
- Do NOT touch the pinned data/csv/*_curated_normalized.xlsx — that is CE-4.
- Every claim in a row must come from that document's text. No outside knowledge, no invented quotes.

REFERENCE FIRST
Open data/csv/cjp_books_curated_normalized.xlsx and read 3 rows of the same theme as a style reference
(e.g. BA001, BD010, BE001).
Match their depth and phrasing, not their content.

THE 15 FIELDS (sheet name cjp_books_curated, header row exactly as below)
Date | Title | Article Code | Link | Keyword/s | primary_topics | sub_topics | signature_phrases |
entities | stances | notable_anecdotes | target_audience | register_markers |
decision_framework_signals | one_paragraph_summary

- Date: TEXT "YYYY-MM-DD" from the manifest (set the cell format to Text first).
- Title, Article Code (= doc_id), Link: from the manifest. Link may be blank for books.
- List fields are JSON arrays of strings; entities is a JSON object; stances is a JSON array of objects.
  Write them as valid JSON text in the cell (double quotes, no trailing commas).

TYPICAL SIZES for book chapters in the existing corpus (medians — aim near them, never pad):
  Keyword/s                       20   names, cases, laws, key quoted phrases; multi-word kept whole
  primary_topics                   4   full sentences: what the chapter is centrally about
  sub_topics                       8   the supporting points, in the order made
  signature_phrases                5   VERBATIM from the text — his words, 3–20 words each
  entities   {people, institutions, cases, laws_treaties, events} — each a list; add "(role)" after a name
  stances                          3   {"claim", "rhetorical_move", "confidence"}
  notable_anecdotes                4   strings: first-hand moments and stories, one sentence of context
  target_audience                  3
  register_markers                 5   tone, structure, rhetorical habits
  decision_framework_signals       5   the tests and principles he applies
  one_paragraph_summary      ~300 words, one paragraph, neutral, past-tense reporting of his argument
  For a chapter over 3,000 words, scale up (keywords, sub_topics, signature phrases, anecdotes) so the
  whole chapter is represented, not just its opening.

STEPS
1. For each document: read the whole .md, then fill the 15 fields.
2. signature_phrases: copy exactly as in the text, including punctuation. After drafting, search the
   .md for each phrase (compare with curly/straight quotes and dashes normalised) and replace any
   phrase that is not found with one that is. Record how many were replaced.
3. confidence (in stances): "asserted", "asserted with evidence", "hedged", or "reported (not his view)".
4. Append the row to the right workbook. Keep one sheet per workbook.

SELF-CHECKS (must pass)
- Row count == manifest rows with material_type = book chapter.
- Every JSON cell parses. Every Date cell is text matching YYYY-MM-DD.
- 100% of signature_phrases are found verbatim in their document's .md.
- No two rows share an Article Code; every Article Code has a data_text/<ID>.md.

FLAG, DO NOT FIX
- A document too short to support the typical sizes (say so; do not pad) · content by someone other
  than CJP · a date in the text that contradicts the manifest.
```

---

## B4 · CE-1b QA — Check the book rows  (Cowork)

```
CE-1b QA — independent check of the batch-04 enriched rows, then a human spot-check sheet

BOUNDARIES
- Read-only on everything except batch-04/qa_books.md and batch-04/spot_check_books.xlsx.
- Do not edit the enriched workbooks — report what should change.

STEPS
1. Re-run every B3 self-check and report pass/fail with counts.
2. For every row, check against its .md:
   a. each signature phrase is verbatim (quotes/dashes normalised);
   b. every name in entities.people appears in the text;
   c. every notable_anecdote describes something actually in the text;
   d. the summary makes no claim the text does not support.
3. Pick 10 rows at random (seed = 4, spread across the books), and write spot_check_books.xlsx with:
   doc_id, title, the .md path, the summary, 3 signature phrases, 2 stances, and empty columns
   "reviewer", "OK / fix", "notes".
4. Write qa_books.md: the pass/fail table, every failure with the exact cell and reason, and the
   spot-check list.

SELF-CHECKS
- Every row checked; every failure names doc_id + column + the offending text.

FLAG, DO NOT FIX
- Anything that fails a check. The team fixes B3 output and re-runs B4 until it is clean and the
  10-row spot check is signed. Then continue with P5 in BATCH-04_PROMPTS.md.
```
