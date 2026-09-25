# Batch-04 — SPEECHES: file or paste → `.md` → enriched row

For speeches, addresses, lectures, eulogies and messages delivered by CJ Panganiban. A speech arrives either as a
file (`.doc` / `.docx` / `.pdf` in `batch-04/incoming/speeches/`) or as text copied from cjpanganiban.com and
pasted into Claude. Both follow the same S1 procedure. They then feed the shared merge steps P5–P8 in
`BATCH-04_PROMPTS.md`. Runbook: **CJAP_Robot_Project_Plan_v2.xlsx → Corpus Expansion** CE-1 · CE-1a · CE-1b.

| # | Step | You do | Claude does | Output |
|---|---|---|---|---|
| S0 | Start a speech session | Paste S0 once | Loads the rules, the next free IDs and a style reference | — |
| S1 | One speech | Drop the file in `incoming/speeches/` or paste it with the template | Cleans, checks for duplicates, assigns ID, writes `.md` + manifest row + enriched row | `batch-04/data_text/<ID>.md`, a row in `intake_manifest.csv` and `speeches_enriched.xlsx` |
| S2 | Batch check | Paste S2 when all speeches are in | QA + 10-row spot-check sheet | `batch-04/qa_speeches.md`, `spot_check_speeches.xlsx` |

Already in the corpus: 153 speeches, the newest SE001 (27 Apr 2026). The four speech files in your Drive list
("Safeguarding the Liberty of the Peoples of the World" and "Safeguard Liberty, Conquer Poverty, Share Prosperity"
Parts One–Three) are already SA145, SB079, SA078 and SB075; S1's duplicate check will catch them.
Next free IDs: **SA150 · SB116 · SC154 · SD151 · SE109**. Retired, never reused: SA085.

---

## S0 · Start a speech session  (paste once)

```
S0 — SPEECH SESSION for batch-04. Read this, confirm, then wait.

CONTEXT
- CJAP robot knowledge base. Base folder: the Final Project Folder. Work only in batch-04/.
- Speeches arrive as files in batch-04/incoming/speeches/ or pasted with the SPEECH template
  (=== SPEECH === … === END ===). For each one, run the S1 procedure below.

BEFORE THE FIRST SPEECH
1. Read batch-04/intake_manifest.csv, data/csv/retired_doc_ids.csv and every doc_id in corpus/.
   Work out the next free ID per speech series (expected SA150 · SB116 · SC154 · SD151 · SE109). Report them.
2. Read 3 existing speech rows in data/csv/cjp_speeches_curated_normalized.xlsx (e.g. SA145, SE001, SC005)
   and their data/text/<ID>.md files as the style reference.
3. List any files already in batch-04/incoming/speeches/. Confirm you are ready. Write nothing yet.
```

---

## S1 · Paste template  (skip it for files — just say "process the files in incoming/speeches/")

```
=== SPEECH ===
URL: <cjpanganiban.com link, or "file: <file name>">
TITLE: <title as published>
DATE DELIVERED: <e.g. October 18, 2006>
OCCASION: <event, venue, audience — if known>
TEXT:
<paste the full speech>
=== END ===
```

### The S1 procedure (part of S0)

```
S1 — for EACH speech (file or paste):

BOUNDARIES
- Write only: batch-04/data_text/<ID>.md, a row in batch-04/intake_manifest.csv, a row in
  batch-04/speeches_enriched.xlsx. Never touch data/, corpus/ or the pinned data/csv sheets.
- Never change his wording. Never invent or complete missing text.

1. CHECK THE SOURCE
   - It is delivered BY Artemio V. Panganiban (not an introduction of him, not a citation read by someone else).
   - Remove only: web clutter (menus, share buttons, related posts, comments), page headers/footers and page
     numbers, and file-conversion markup (backslash escapes like "\." or "\-", stray "__" or "*" pairs).
   - Keep: salutations, the occasion line, every paragraph, quotes, closing prayers and thanks.
   - Typical length 500–2,200 words (median 912). Under 300 → FLAG "possible fragment" and ask me.
   - A speech file that holds SEVERAL speeches → one document per speech; ask me first if unsure.
   - A multi-part speech series (Part One / Two / Three) → one document per part.
2. DUPLICATE CHECK — normalised title, URL and delivery date against every corpus/*/*/*.json and the
   batch-04 manifest; also against the columns (he often turned a speech into a column). A match → STOP for
   this speech and tell me which doc it matches.
3. DATE — the DELIVERY date as text YYYY-MM-DD; precision day / month (YYYY-MM-01) / year (YYYY-01-01).
4. THEME + ID — one theme A–E by main subject (A liberty and rule of law · B prosperity and economic
   philosophy · C biographical and personal · D FLP mission and foundation · E current events commentary),
   a one-line reason, then the next free ID in that S-series.
5. WRITE batch-04/data_text/<ID>.md (UTF-8, no YAML, no '---' lines):

   # <Title>
   Date:       <YYYY-MM-DD>
   Publisher:  cjpanganiban.com          (or the book/program it came from, for a file)
   Source:     <URL, or "file: <name>">

   <Occasion line, e.g. "Keynote Address of Chief Justice ARTEMIO V. PANGANIBAN during …, <venue>, <date>.">
   <speech body, paragraphs separated by blank lines; his own section headings as "## Heading">

6. MANIFEST ROW: source, material_type=speech, title, publication_date (= delivery date), date_precision,
   publisher, theme, theme_reason, rights_consent_status="CJP-authored speech, covered by the FLP corpus
   permission", doc_id, superseded_doc_id="", book_title="", chapter_no="", est_words, note=<occasion>.
7. ENRICHED ROW → batch-04/speeches_enriched.xlsx (sheet cjp_speeches_curated; the same 15 fields in order:
   Date | Title | Article Code | Link | Keyword/s | primary_topics | sub_topics | signature_phrases |
   entities | stances | notable_anecdotes | target_audience | register_markers |
   decision_framework_signals | one_paragraph_summary)
   - Date as TEXT; lists as JSON arrays; entities a JSON object (people, institutions, cases,
     laws_treaties, events); stances [{"claim","rhetorical_move","confidence"}].
   - Typical sizes for speeches: Keyword/s ~16 · primary_topics ~4 · sub_topics ~10 · signature_phrases ~7 ·
     stances ~2 · notable_anecdotes ~4 · target_audience ~4 (include the actual audience of the occasion) ·
     register_markers ~6 (name the speech genre: keynote, eulogy, homily-like, commencement…) ·
     decision_framework_signals ~4 · summary ~300 words. Scale up for speeches over 3,000 words; never pad.
   - signature_phrases VERBATIM from the .md; check each (quotes/dashes normalised) and replace failures.
   - Everything from this speech's text only.
8. REPORT one line per speech: <ID> · <date> · <title> · theme <X> (<reason>) · <words> words ·
   duplicates · phrases verbatim n/n · flags. Then the updated next free IDs.

SELF-CHECKS — first line "# "+title; lines 2–4 Date/Publisher/Source; no '---' line; no "\." escapes left;
manifest, file name and enriched row share the doc_id; every JSON cell parses; 100% phrases verbatim.
```

---

## S2 · Batch check  (paste when all speeches are in)

```
S2 — QA for the batch-04 SPEECHES, then a human spot-check sheet.
BOUNDARIES: read-only except batch-04/qa_speeches.md and batch-04/spot_check_speeches.xlsx.

1. Re-run every S1 self-check for every speech row.
2. Against each .md: signature phrases verbatim; entities.people appear in the text; anecdotes are in the
   text; the summary makes no unsupported claim; the date is the delivery date named in the occasion line.
3. Duplicates: no two speeches with the same title+date; none duplicating an existing speech or column.
4. IDs contiguous per series from the next free number; none reused or retired.
5. 10 random rows (seed = 4) → spot_check_speeches.xlsx (doc_id, title, .md path, summary, 3 phrases,
   2 stances, empty reviewer / OK-or-fix / notes).
6. qa_speeches.md: pass/fail table, every failure (doc_id + field + text), spot-check list.
STOP. After fixes and the signed spot check, continue with P5 in BATCH-04_PROMPTS.md.
```
