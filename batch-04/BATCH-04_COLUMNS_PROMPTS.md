# Batch-04 — COLUMNS: paste from Inquirer → `.md` → enriched row

For the *With Due Respect* columns. **You paste each column's text into Claude (Cowork); Claude writes the `.md`
source and the enriched row.** Books have their own file: `BATCH-04_BOOKS_PROMPTS.md`. Both feed the same
merge steps (P5–P8) in `BATCH-04_PROMPTS.md`.

Follows **CJAP_Robot_Project_Plan_v2.xlsx → Corpus Expansion** CE-1 · CE-1a · CE-1b, using the formats on the
**Data Flow** sheet. All paths are relative to the Final Project Folder.

*Revised 23 Sep 2026 after the first full run (18 columns, C1 + C2). What changed is listed at the end.*

| # | Step | You do | Claude does | Output |
|---|---|---|---|---|
| C0 | Start a column session | Paste the C0 prompt once | Loads the rules and the next free IDs | — |
| C1 | One column | Paste the article (template or straight from the page) | Cleans it, finds the URL if missing, checks for duplicates, assigns an ID, writes the `.md`, the manifest row and the enriched row | `batch-04/data_text/<ID>.md`, a row in `intake_manifest.csv` and `columns_enriched.xlsx` |
| C2 | Batch check | Paste C2 when all columns are in | Runs the QA and builds a 10-row spot-check sheet | `batch-04/qa_columns.md`, `spot_check_columns.xlsx` |
| → | Merge | Follow P5–P8 in `BATCH-04_PROMPTS.md` | | |

## Columns collected

The corpus stopped at **18 May 2026** (CA025, "SC penalizes unethical conduct"). All 18 expected Mondays were
pasted on 23 Sep 2026 and passed C1 and C2. The next column to collect is **2026-09-28**.

| # | Date | ID | # | Date | ID |
|---|---|---|---|---|---|
| 1 | 2026-05-25 | ☑ CA530 | 10 | 2026-07-27 | ☑ CA537 |
| 2 | 2026-06-01 | ☑ CA531 | 11 | 2026-08-03 | ☑ CA538 |
| 3 | 2026-06-08 | ☑ CA532 | 12 | 2026-08-10 | ☑ CA539 |
| 4 | 2026-06-15 | ☑ CA533 | 13 | 2026-08-17 | ☑ CA540 |
| 5 | 2026-06-22 | ☑ CA534 | 14 | 2026-08-24 | ☑ CA541 |
| 6 | 2026-06-29 | ☑ CA535 | 15 | 2026-08-31 | ☑ CA542 |
| 7 | 2026-07-06 | ☑ CA536 | 16 | 2026-09-07 | ☑ CD030 |
| 8 | 2026-07-13 | ☑ CB020 | 17 | 2026-09-14 | ☑ CD031 |
| 9 | 2026-07-20 | ☑ CB021 | 18 | 2026-09-21 | ☑ CA543 |

**CA529 was removed on 23 Sep 2026.** "Rule of, or by, law" (2 Feb 2018) is by **Michael L. Tan ("Pinoy Kasi")**,
not by CJP; it had been filed as his in the Phase-1 record (CA016). CA529 stays an unused ID — do not re-stage it.
batch-04 columns are the 18 above. Lesson for C1: always confirm the byline on the article page, not only the
paste; a column that does not sound like him is worth checking early.

---

## C0 · Start a column session  (paste once)

```
C0 — COLUMN SESSION for batch-04. Read this, confirm, then wait for columns.

CONTEXT
- Project: CJAP robot knowledge base. Base folder: the Final Project Folder.
- I will paste Inquirer "With Due Respect" columns by Artemio V. Panganiban, one or more per message,
  either in the COLUMN template (=== COLUMN === … === END ===) or copied straight from the article page.
- For each one you do the whole C1 procedure below. Work only in batch-04/.

BEFORE THE FIRST COLUMN
1. Read batch-04/intake_manifest.csv and data/csv/retired_doc_ids.csv, and list every doc_id in corpus/
   (use the "id" field inside each corpus/*/*/*.json).
2. Work out the next free ID per column series from the highest ID used anywhere (corpus, manifest, retired):
   expected after the 23 Sep run CA544 · CB022 · CC118 · CD032 · CE121. Report what you found.
3. Read 3 existing column rows in data/csv/cjp_columns_curated_normalized.xlsx (e.g. CA025, CC018, CE003)
   and 2 matching data/text/<ID>.md files, as the style reference.
   Note: the pinned rows use free-form confidence values, "--" dashes and very long lists. For NEW rows
   follow C1 below (four confidence values, typical sizes), not the pinned rows.
4. Open the byline pages https://opinion.inquirer.net/byline/artemio-v-panganiban (and /page/2) and note
   the title, URL and date of each recent column, so a paste without a URL can be matched.
5. Confirm you are ready. Do not write anything yet.
```

---

## C1 · Paste template  (one block per column; several blocks per message is fine)

Copy the text from the article page on inquirer.net: title, byline line, and body. Don't worry about stray
web text; Claude removes it. Pasting the page as-is (without the template) also works; if the URL is
missing, Claude takes it from the byline pages and tells you.

```
=== COLUMN ===
URL: https://opinion.inquirer.net/…
TITLE: <title as published>
DATE: <as shown, e.g. 05:30 AM May 25, 2026>
TEXT:
<paste the byline and the full article body here>
=== END ===
```

This template is only for the chat. It is never saved; the `.md` has the shape in step 5.

### What Claude does with each pasted column (the C1 procedure, part of C0)

```
C1 — for EACH pasted column:

BOUNDARIES
- Write only: batch-04/data_text/<ID>.md, a row in batch-04/intake_manifest.csv, a row in
  batch-04/columns_enriched.xlsx. Never touch data/, corpus/ or the pinned data/csv sheets.
- Never change his wording. Remove only web clutter. Never invent or "complete" missing text.
- Keep printed typos and odd spellings exactly as printed (e.g. "grabbed in shimmering crimson") and
  FLAG them in the report; never correct them.

1. CHECK THE PASTE
   - Title, date, byline and body present. Author is Artemio V. Panganiban (byline).
   - URL: if missing, take it from the byline pages (title + date must both match). If it cannot be
     found there or by a search limited to opinion.inquirer.net, STOP and ask me. Never guess a URL.
   - Remove web clutter: breadcrumb links ("Columnists", "Columns"), the "With Due Respect" label,
     "@inquirerdotnet" and source links in the byline, "Share:", ADVERTISEMENT and
     "Article continues after this advertisement", "by Taboola" / "Sponsored Links" / "You May Like"
     blocks and their ad links, "Read Next", "Subscribe to our daily newsletter", "Don't miss out…",
     "READ: …" and other related-article links, share/like text, photo captions and credits,
     comment-policy or disclaimer lines, the closing "Comments to …@…" email line, and the closing
     rule line ("—————-").
   - Keep: every paragraph of the article, his CAPITALISED lead-in phrases exactly as printed, quotes,
     curly quotes and dashes as printed, and any "* * *" section breaks (keep them as their own
     "* * *" line, never '---').
   - Word count (body only, from the paragraph after the By: line): typical is 750–1,050.
     Below 600 or above 1,200 → FLAG "possible incomplete paste" and ask me before continuing.
2. DUPLICATE CHECK — compare the normalised title, the URL (and its article number) and the date against
   every corpus/*/*/*.json and the batch-04 manifest. If it matches, STOP for this column and tell me
   which doc it matches.
3. DATE — convert to text YYYY-MM-DD (05:30 AM May 25, 2026 → 2026-05-25). date_precision = day.
   Keep the printed time as-is on the By: line (it varies: 05:15, 05:30, 05:35 AM).
4. TITLE — as published, trimmed of leading/trailing spaces, with a straight apostrophe (' not ’), as in
   the existing corpus titles ("The SC's 125th …", "Sara's options"). Use the same title in the .md,
   manifest and enriched row. (Inside the body, keep his curly quotes.)
5. THEME + ID — choose one theme A–E by its main subject (A liberty and rule of law · B prosperity and
   economic philosophy · C biographical and personal · D FLP mission and foundation · E current events
   commentary) with a one-line reason, then take the next free ID IN THAT THEME'S SERIES
   (theme B → CBnnn, theme D → CDnnn, …). Say if torn and name the other theme.
   Precedents from the corpus: legal explainers, court rulings, impeachment, ICC, civil registry,
   juvenile justice → A; central bank, energy, economy → B; FLP projects, scholars, museum → D.
   Check how similar existing columns were themed before deciding.
6. WRITE batch-04/data_text/<ID>.md exactly in this shape, matching the existing data/text files
   (UTF-8, LF line endings, ends with a newline, no YAML, no '---' lines, plain title line,
   no blank lines between paragraphs):

   <Title>
   Date:       <YYYY-MM-DD>
   Publisher:  Philippine Daily Inquirer (Inquirer Opinion)
   Source:     <URL>

   By: Artemio V. Panganiban | <time and date as printed>
   <body paragraphs, one per line, no blank lines between them>

7. MANIFEST ROW → append to batch-04/intake_manifest.csv (keep its CRLF line endings and quoting):
   source=<URL>, material_type=column, title, publication_date, date_precision=day,
   publisher="Philippine Daily Inquirer (Inquirer Opinion)", theme, theme_reason,
   rights_consent_status="CJP-authored Inquirer column, same basis as the existing 785",
   doc_id, superseded_doc_id="", book_title="", chapter_no="", est_words=<body word count>, note="".
8. ENRICHED ROW → append to batch-04/columns_enriched.xlsx (sheet cjp_columns_curated; header exactly:
   Date | Title | Article Code | Link | Keyword/s | primary_topics | sub_topics | signature_phrases |
   entities | stances | notable_anecdotes | target_audience | register_markers |
   decision_framework_signals | one_paragraph_summary)
   - Date as TEXT (cell format "@"), never a date value.
   - List fields as JSON arrays of strings; entities a JSON object with exactly the keys
     people, institutions, cases, laws_treaties, events; stances a JSON array of objects with exactly
     the keys "claim", "rhetorical_move", "confidence". confidence is ONLY one of: asserted /
     asserted with evidence / hedged / reported (not his view). Use "reported (not his view)" when he
     sets out someone else's position (the OSG, opposing counsel, another justice).
   - Typical sizes for columns: Keyword/s ~8 · primary_topics ~5–7 · sub_topics ~14 ·
     signature_phrases ~10–15 · stances ~5–7 · notable_anecdotes ~5 · target_audience ~5 ·
     register_markers ~8–12 · decision_framework_signals ~6 · summary ~300 words (280–350), one paragraph.
     Never pad a short column to reach them.
   - signature_phrases are copied VERBATIM from the .md, 3–20 words each (count the words; cut a longer
     line to a complete clause, never mid-phrase). Search the .md for each one (curly/straight quotes
     and dashes treated as equal); replace any that is not found.
   - entities.people: each name exactly as it appears in the text (e.g. "President Duterte", not a fuller
     name the text never uses). A short role may follow in parentheses. No descriptions that are not
     names ("three unnamed minors" goes in events, not people).
   - Acronyms: use the form the text uses; if the text only spells a body out in full, write it in full
     (or full name + acronym in parentheses).
   - Everything must come from this column's text — no outside facts, no invented quotes. Quoted
     fragments in anecdotes and the summary must appear in the .md. Record any disclosure he makes
     about his own role (e.g. board adviser) in stances or anecdotes.
9. REPORT, one line per column:
   <ID> · <date> · <title> · theme <X> (<reason>) · <words> words · duplicates: none/<match> ·
   phrases verbatim <n>/<n> · flags: <…>
   Flags include: URL looked up, theme torn, printed typos kept, unusual byline time.
   Then the updated next free IDs and the running count (<n> of 18, which weeks remain).

SELF-CHECKS (every column, before reporting)
- The .md's first line is the plain title (no "# "); lines 2–4 are Date/Publisher/Source; line 5 is blank;
  line 6 is the By: line; no blank lines after it; no line is exactly '---'; the file ends with a newline.
- The .md title, Date and Source equal the manifest's title, publication_date and source, and the
  enriched row's Title, Date and Link.
- The manifest, the .md file name and the enriched row share the same doc_id, and the ID's series letter
  matches the theme.
- est_words equals the body word count.
- Every JSON cell parses; entities has the five keys; every confidence value is one of the four.
- 100% of signature phrases are found verbatim, and every one is 3–20 words.
- Every name in entities.people appears in the text.
```

---

## C2 · Batch check  (paste when all columns are in)

```
C2 — QA for the batch-04 COLUMNS, then a human spot-check sheet.

BOUNDARIES: read-only except batch-04/qa_columns.md and batch-04/spot_check_columns.xlsx.
Do not edit the enriched workbook — report what should change.

1. Coverage: list which of the expected Mondays (2026-05-25 … 2026-09-21, or the range for this batch)
   are in the manifest and which are missing. Confirm there are no two columns with the same date or URL.
2. Re-run every C1 self-check for every column (column rows only; include CA529).
3. For every row check against its .md: each signature phrase verbatim and 3–20 words; every name in
   entities.people appears in the text (compare the name without any parenthetical role); every notable
   anecdote describes something in the text; the summary makes no claim the text does not support; the
   date matches the byline.
   Method: first an automated pass (every quoted fragment and every number in anecdotes and the summary
   must be in the .md; flag sentences whose content words are mostly absent), then read every flagged
   sentence against the text. Say which rows got the read-through and which the automated pass only.
4. IDs: contiguous within each series from the register's next free number; none reused in corpus/;
   none retired.
5. Pick 10 rows at random with Python random.Random(4).sample() over the column doc_ids in manifest
   order → spot_check_columns.xlsx with doc_id, title, .md path, summary, 3 signature phrases,
   2 stances (claim [rhetorical_move; confidence]), and empty columns reviewer / OK-or-fix / notes
   (OK-or-fix as an OK/Fix dropdown). Add a how_to sheet with the method.
6. Write qa_columns.md: pass/fail table (one row per doc_id, one column per check), every failure
   (doc_id + column + offending text), missing weeks, the ID table, "What should change" (per failing
   row) and advisories (theme borderlines, printed typos kept), and the spot-check list.
STOP. When the team has fixed any failures and signed the 10-row spot check, continue with P5 in
BATCH-04_PROMPTS.md.
```

---

## What changed on 23 Sep 2026 (from the first run)

| Area | Before | Now | Why |
|---|---|---|---|
| `.md` shape | `# <Title>`, blank line between paragraphs | Plain title, no blank lines between paragraphs, `* * *` kept as its own line | Match the older `data/text` column style you chose (none of the 785 has a `# ` title) |
| URL | Required in the paste | Looked up on the byline pages if missing; never guessed; ask if not found | Pastes straight from the page have no URL |
| Web clutter | Generic list | Adds breadcrumbs, "With Due Respect" label, @inquirerdotnet, "Share:", "Article continues after this advertisement", Taboola / Sponsored Links / You May Like, closing "—————-" | These appeared in every paste |
| Title | As published | Trimmed, straight apostrophe | Match existing corpus titles |
| Theme/ID | "next free ID" | Next free ID **in the theme's series**, with precedents | Theme B/D columns must take CB/CD IDs |
| Signature phrases | 3–20 words (not checked) | 3–20 words is a self-check; cut at a clause | 19 phrases in 11 rows were over 20 words |
| entities.people | Not specified | Names exactly as in the text; no non-names | C2 failures on CA529 |
| Confidence | Four values | Four values, plus when to use "reported (not his view)"; self-check added | Pinned rows use free-form values; CA529 failed |
| Typos | Not specified | Keep as printed and flag | CA532, CA538, CA539 |
| Self-checks | 3 | 7 (header, cross-file equality, series letter, word count, keys, phrase length, people) | Catch in C1 what C2 found |
| C2 | Method open | Seeded sampling method, automated + read-through method, OK/Fix dropdown, "What should change" section | As run on 23 Sep |
| C0 | Next IDs CA530 … | CA544 · CB022 · CC118 · CD032 · CE121; byline pages noted up front | After this run |
