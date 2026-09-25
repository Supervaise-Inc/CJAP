# Batch-04 — BIOGRAPHY: split → `.md` → enriched rows

For biographies ABOUT CJ Panganiban written by someone else (GC series; theme is always **C — Biographical and
personal**). A biography is split like a book (one document per chapter), but the author is the biographer, the
date is the period the chapter covers, and his own words appear only as quotations. Feeds the shared merge
P5–P8 in `BATCH-04_PROMPTS.md`. Runbook: **CJAP_Robot_Project_Plan_v2.xlsx → Corpus Expansion** CE-3 · CE-1 ·
CE-1a · CE-1b.

| # | Step | Output | Human check |
|---|---|---|---|
| G0 | Split the biography into chapters — **one run per biography** | `batch-04/book_split/<bio>/` chapter files + `split_plan.csv` | Confirm chapters and skipped parts |
| G1 | Intake + IDs | rows in `batch-04/intake_manifest.csv` | Confirm IDs and period dates |
| G2 | Chapter files → contract `.md` | `batch-04/data_text/GC<NNN>.md` | Skim 5 files against the original |
| G3 | Enrichment | `batch-04/biography_enriched.xlsx` | — |
| G4 | QA | `batch-04/qa_biography.md` + `spot_check_biography.xlsx` | Sign off 10 rows |

Already in the corpus: **GC001–GC020** Reginald T. Yu, *Liberty and Prosperity: The Making of Chief Justice
Artemio Villaseñor Panganiban Jr.* (Prologue to Epilogue), and **GC021–GC035** the 15-chapter biography
(Chapter 1 Early Years … Chapter 15 Papal Award). Your "Chapter 1…15_ok.docx" files are GC021–GC035; G1's
duplicate check will catch them. Next free ID: **GC036**.

---

## G0 · Split a biography into chapter documents  (Cowork, one run per biography)

```
G0 — BIOGRAPHY SPLIT: separate <biography file(s)> into one document per chapter

BOUNDARIES
- Input: the biography in batch-04/incoming/biography/ (one file, or one file per chapter).
  Output only under batch-04/book_split/<bio_slug>/. No IDs, no enrichment, nothing in data/ or corpus/.
- Do not edit, shorten, merge or reorder the text. Cut only at chapter boundaries; remove running
  headers/footers, page numbers and file-conversion markup (backslash escapes like "\." "\-", stray "__"
  or "*" pairs left by Word/PDF conversion).

RULES
1. ONE CHAPTER = ONE DOCUMENT, however short. Never merge chapters.
2. KEEP the Prologue and Epilogue as their own documents when they tell part of the story.
3. SKIP (no document; listed with a reason): cover, title and copyright pages, dedication, epigraph-only
   pages, table of contents, foreword or preface by someone other than the biographer, acknowledgments,
   list of photos, photo sections and captions, appendices, chronology tables, bibliography, notes-only
   sections, index, about the author, blurbs.
4. A chapter-opening scripture verse or epigraph stays at the top of its chapter (as a quote), not a document.
5. A chapter over 6,000 words stays whole and is flagged "long".

STEPS
1. Read the whole biography; take the structure from the table of contents AND the chapter headings in the
   text (follow the text when they disagree, and report it).
2. Classify every part CHAPTER or SKIP (with the reason).
3. Each CHAPTER → batch-04/book_split/<bio_slug>/ch<NN>_<slug>.md: first line "# Chapter <N>: <Title>"
   (or "# Prologue: <Title>" / "# Epilogue: <Title>"), then the text exactly, sub-headings as "## …".
4. split_plan.csv: order, part_label_as_printed, classification, skip_reason, chapter_no, chapter_title,
   start_page, end_page, word_count, file, period_covered (e.g. "1936–1950", "Jan 2001"), flags.
5. split_report.md: biography title, biographer, publisher, year; chapter and skip counts; the skipped
   list; flags; the coverage check.

SELF-CHECKS — chapter words + skipped words ≈ whole biography (±3%); no overlap between chapter files;
no file for a SKIP part; no "\." escapes or stray "__" left in any chapter file.
FLAG, DO NOT FIX — missing pages · unclear boundaries · long passages that are not biography text.
STOP until the team confirms split_plan.csv.
```

---

## G1 · Intake and IDs  (Cowork)

```
G1 — register the confirmed biography chapters and assign GC IDs

BOUNDARIES — work only in batch-04/; register only CHAPTER rows from the confirmed split_plan.csv;
never reuse or renumber an ID.

1. DUPLICATE CHECK — compare each chapter title (normalised) with GC001–GC035 in corpus/biography/ and the
   batch-04 manifest. "Chapter 1 Early Years" etc. are already GC021–GC035. A match → list it, do not register.
2. IDs — from GC036 upward, in chapter order. Theme is always C.
3. TITLE — "<Chapter N>: <Chapter title>" as in GC021–GC035 (Prologue / Epilogue: "PROLOGUE: <title>").
4. DATE — the START of the period the chapter covers, as text YYYY-MM-DD with date_precision
   (day / month → YYYY-MM-01 / year → YYYY-01-01). Put the full period ("1955–1959", "early 1990s") in
   the manifest note. Never write free text like "Childhood" in the date (that is defect D-7).
5. MANIFEST ROW: source=<chapter file>, material_type=biography chapter, title, publication_date,
   date_precision, publisher=<biography publisher>, theme=C, theme_reason="biography",
   rights_consent_status=<biographer's permission — FLAG if not on file>, doc_id, book_title=<biography title>,
   chapter_no, est_words, note="period: …; biographer: <name>".
6. intake_biography_report.md: IDs used, duplicates, rights flags.
SELF-CHECKS — one row per confirmed new chapter; every date is YYYY-MM-DD with a precision.
FLAG — unclear rights from the biographer · no identifiable period for a chapter.
STOP for the team to confirm.
```

---

## G2 · Chapter files → contract `.md`  (Cowork)

```
G2 — write batch-04/data_text/GC<NNN>.md for every confirmed biography chapter

BOUNDARIES — write only batch-04/data_text/; never data/text/ (that is CE-4). No rewording.

For each manifest row (material_type = biography chapter):
   # <Title from the manifest>
   Date:       <YYYY-MM-DD>
   Publisher:  <publisher of the biography>
   Source:     <biography title>, <biographer>, <year>, pp. x–y
   By: <biographer's name>

   <chapter text: epigraph as "> quote", paragraphs separated by blank lines, sub-headings as "## …">
- Take the text from the G0 chapter file and drop its first "# …" line (the manifest title replaces it).
- No YAML, no '---' lines, no backslash escapes, no stray "__" / "*" markup.
SELF-CHECKS — one file per row; header lines as above; body words within ±5% of split_plan word_count.
Write batch-04/source_check_biography.md with word counts and any gaps.
```

---

## G3 · Enrichment  (Cowork)

```
G3 — one enriched row per biography chapter → batch-04/biography_enriched.xlsx
(sheet cjp_biography_curated; the same 15 fields in order: Date | Title | Article Code | Link | Keyword/s |
primary_topics | sub_topics | signature_phrases | entities | stances | notable_anecdotes | target_audience |
register_markers | decision_framework_signals | one_paragraph_summary)

REFERENCE — read GC001, GC002 and GC021 in data/csv/cjp_biography_curated_normalized.xlsx first.

BIOGRAPHY-SPECIFIC RULES
- The narrator is the BIOGRAPHER. Stances are the biographer's claims about CJP; set confidence to
  "biographer-asserted" (or "quoted from CJP" when the chapter quotes him directly).
- signature_phrases: VERBATIM from the chapter. Prefer lines that quote CJP or capture his principles;
  the biographer's best lines may be included. Check every phrase by string search.
- register_markers: include the biographer's voice (e.g. "Reginald T. Yu authorial voice — …").
- entities.people: always include "Artemio V. Panganiban (subject)"; add "(role)" after each name.
- Link: blank unless the biography is online.
- Date as TEXT from the manifest.
- Typical sizes (existing biography): Keyword/s ~5 · primary_topics ~5 · sub_topics ~19 ·
  signature_phrases ~10 · stances ~6 · notable_anecdotes ~9 · target_audience ~5 · register_markers ~7 ·
  decision_framework_signals ~6 · summary ~300 words. Never pad a short chapter.
- Everything from the chapter text only — no outside facts about his life.
SELF-CHECKS — row count == biography rows in the manifest; every JSON cell parses; 100% phrases verbatim;
every Date is text YYYY-MM-DD.
```

---

## G4 · QA  (Cowork)

```
G4 — QA for the batch-04 BIOGRAPHY rows, then a spot-check sheet.
Read-only except batch-04/qa_biography.md and batch-04/spot_check_biography.xlsx.
1. Re-run the G2 and G3 self-checks.
2. Per row against its .md: phrases verbatim; people in the text; anecdotes in the text; summary supported;
   no stance attributed to CJP that the text only has the biographer saying.
3. Chronology: dates increase with chapter order (report any that go backwards, with the period note).
4. 10 random rows (seed = 4) → spot_check_biography.xlsx; qa_biography.md with every failure.
STOP. After fixes and the signed spot check, continue with P5 in BATCH-04_PROMPTS.md.
```
