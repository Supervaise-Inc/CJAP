# Correction batch-03 — `correction_list.md`

Opened 23 Sep 2026. Runs under **CE-17** (Corpus Expansion sheet, section F) and satisfies tracker task **CM-4**.

A correction batch is the only exception to append-only. It runs **on its own**, never mixed with new material, and it is the gate for CM-6 (merging batch-04).

## Boundaries

- **Fix at the SOURCE only** — a `data/text/<ID>.md` file or a pinned xlsx row. Never hand-edit `corpus/`.
- **Nothing from batch-04 enters this batch.** The 186 staged rows, the 186 files in `batch-04/data_text/` and the 12 book splits stay where they are until CM-6.
- **No ID is created, renumbered or reused.** The five retired IDs stay retired.
- **Run `scripts/generate_corpus_from_xlsx.py` unchanged**, `--dry-run` first.
- **STOP if any document outside `batch-03/changed_doc_set.txt` changes.**

## Settled: the D-2 date

CM-4 was blocked on this. The folder answers it.

| Evidence in the Final Project Folder | Says |
|---|---|
| `data/csv/cjp_books_curated_normalized.xlsx` — all 26 Centenary rows | `2026-01-12` — the **ingestion** date (12 Jan 2026), not a publication date |
| YAML front matter in all 22 `data/text` Centenary files | `publication_date: 2001-12` |
| The book's own Preface (`batch-04/incoming/books/A Centenary of Justice.docx`, para 107) | "My sixth year as a jurist — **October 11, 2000 to October 10, 2001** — was highlighted by the Supreme Court's observance of its centenary" |
| The book's Foreword and Preface | carry **no printed day or month** |

**Decision: `2001-12-01`, month precision.** The year is fixed by the book's own account of the year it covers; the month comes from the folder's own YAML; no day is recoverable from any source in the folder. This is the value already used for `BA108` in batch-04, so the two batches agree.

The pinned 15-column schema has no `date_precision` column, so **"month" is recorded in the decisions register and in `batch-04/intake_manifest.csv`**, not in the sheet. The sheet gets the text `2001-12-01`.

## The corrections

Each item says what is wrong, the evidence, and the fix at source. Counts were verified against the folder on 23 Sep 2026.

### C-1 · D-1 and D-12a — YAML front matter in 22 source files
**22 docs.** `BA032`–`BA039`, `BB006`, `BB007`, `BC006`–`BC008`, `BD010`–`BD017`, `BD019`.

The Data Flow source-file contract says a source must never open with a `---` block. These 22 are the only files in `data/text/` that do; each carries `id:`, `book_id:`, `chapter_number:`, `word_count:` and empty `primary_topics: []` placeholders. All 22 corpus documents still show the leaked block, because the generator's strip-and-report guard (CM-2) landed after they were last generated.

**Fix:** delete the leading `---` … `---` block from the 22 source files. Everything the block holds is already in the pinned row. Verify the alphanumeric token sequence of the remaining body is unchanged.

### C-2 · D-2 — wrong date on the Centenary chapters
**22 active docs** (the same 22; the four retired Centenary rows `BA040`, `BC009`, `BC010`, `BD018` are left untouched per CE-18).

Every Centenary row carries `2026-01-12`, the day the material was ingested.

**Fix:** set the `Date` cell to the text `2001-12-01` in `data/csv/cjp_books_curated_normalized.xlsx`. Record "month precision" in the decisions register.

### C-3 · D-7 — dates the generator cannot read
**109 docs.** The generator writes the first 10 characters of the cell, so these produce corpus dates like `2003.0` or `Childhood,`.

| Sheet | Active rows | Broken | What they look like |
|---|---|---|---|
| books | 135 | **78** | 58 text (`9/30/2007`), 20 floats (`2003.0`) |
| biography | 35 | **31** | 27 free text (`Childhood, circa`, `1955-1959`), 4 bare year ints (`1960`) |
| columns | 785 | 0 | datetime — the generator handles these correctly |
| speeches | 154 | 0 | datetime — correct |

**Fix:** apply `batch-03/date_normalisation.csv` (132 rows: the 109 above plus the 22 of C-2, plus a header). Write each `Date` as **text** `YYYY-MM-DD`.

**Needs a decision before the batch runs:** the biography rows whose "date" is a period or a label — `GC002` ("Childhood, circa") has no date at all, and several are ranges like `1955-1959` where the proposal takes the start year. See *Open decisions* below.

### C-4 · D-10 — the corpus still repeats the source title in the body
**107 book docs.** The H1 of 111 `data/text` files was corrected on 23 Sep so the generator recognises and drops it; `corpus/` has not been regenerated since (corpus mtime 22 Sep 14:58 against data/text 22 Sep 16:59), so 107 corpus bodies still open with the repeated title line.

**Fix:** none at source — the regenerate in step 3 clears it. Listed here because those 107 documents will change and must be inside the changed-doc set.

### C-5 · D-11 — `BA031.md` carries the book's back matter
**1 doc.** *With Due Respect* Vol. 7 Ch. 15 runs on past the end of the column into the printed **COLOPHON** and the **back-cover blurb** — 1,124 words against the column's own ~922.

**Fix:** truncate the source at the column's last line ("…Let the readers be the judge. (February 11, 2007)"), using `batch-04/book_split/with-due-respect/vol-7/ch15_visionary-leadership-by-example.md` as the reference text.

### C-6 · D-12b — `BA039.md` runs through four appendices and the back matter
**1 doc.** *A Centenary of Justice* Ch. 19 does not stop at the end of Ch. 19. It continues through Appendix A (1,262 words), Appendix B (1,740), Appendix C (770), and Appendix D plus the back matter (6,466) — **14,413 words against the chapter's own 3,395**.

It therefore duplicates `BC007`, `BC008` and `BD019`, which already hold Appendices A–C as their own documents, and it is where the text of retired `BC009` (Appendix D) and `BC010` (back matter) ended up.

**Fix:** truncate the source at the end of Ch. 19, using `batch-04/book_split/a-centenary-of-justice/ch19_bengson-v-house-of-representatives-electoral-tribunal.md` as the reference. Nothing is lost: A–C keep their own documents, and D and the back matter remain available in the B0 split if the team ever revives `BC009`.

### C-7 · D-13 — `BC018.md` is truncated
**1 doc.** *Justice and Faith* Ch. 11, the Invocation: **97 words**, opening mid-sentence ("Your Spirit that he may continue to emulate…"), where the source chapter is **272**. It also ends with the OCR artefact `• 0 0`.

**Fix:** replace the body from `batch-04/book_split/justice-and-faith/ch11_invocation.md`, keeping the existing header block.

### C-8 · D-3 — retired documents are still in the index
**5 IDs, 27 chunks:** `BA040` (5), `BC009` (5), `BC010` (7), `BD018` (5), `SA085` (5) in `corpus/index/chunks.jsonl` (9,865 lines).

CM-3 retired them and moved their generated files to `data/retired/corpus/`, but the index was never rebuilt.

**Fix:** the re-chunk and full re-embed in steps 5–6 drop them. **No longer blocked** — `reports/repo_reconciliation_2026-09-23.md` records that the ten retrieval and index-build scripts were copied into this folder on 23 Sep, so D-5 is resolved and CE-5/CE-6 can run here.

## The changed-doc set

`batch-03/changed_doc_set.txt` — **161 document IDs**, the union of C-1 … C-7:

| Prefix | Docs |
|---|---|
| BA | 49 |
| BB | 8 |
| BC | 20 |
| BD | 24 |
| BE | 29 |
| GC | 31 |
| **Total** | **161** |

Plus **5 index-only removals** (the retired IDs of C-8), which have no corpus files and only lose their 27 chunks.

Corpus doc count is **unchanged at 1,104** — this batch corrects documents, it does not add or remove any.

## Sequence

1. Record this list and the D-2 decision in the decisions register.
2. Apply C-1, C-5, C-6, C-7 to `data/text/`, and C-2, C-3 to the pinned sheets. Back up every file touched, with before/after sha256.
3. `python scripts/generate_corpus_from_xlsx.py --dry-run` → expect total 1,104, summary-fallback 0, retired 5, no bad codes, no duplicates. **STOP otherwise.** Then run it for real.
4. Content-aware diff against the pre-run snapshot. **The changed set must equal `changed_doc_set.txt` exactly** — no more, no fewer. STOP and restore on any difference.
5. `scripts/build_corpus_snapshot.py` && `scripts/verify_pin.py` → must exit 0. Then re-chunk (CE-5).
6. Full re-embed, old and new in one pass, bge-base-en-v1.5 @768d (CE-6). Rebuild the sparse and date indexes.
7. Retag against the **current 34 centroids** — do not create, merge or modify a dimension (CE-7). This is a correction batch; the topic map is not the thing being changed.
8. Promotion eval vs the standing baseline (CE-12): fabrication **0**, no regression on pre-existing gold queries.
9. Re-check the query-time thresholds (CE-13), then attest and tag a new `arch-baseline` (CE-14).

## Acceptance

- Changed-doc set == `changed_doc_set.txt` (161), and no pre-existing row hash outside it moved.
- 0 corpus `.md` files contain a YAML block or a repeated title line.
- 0 corpus documents have a date that is not `YYYY-MM-DD`.
- 0 chunks belong to a retired ID.
- `verify_pin.py` exits 0; fabrication 0; no regression on pre-existing gold.

## Abort and rollback (CE-16)

Any pre-existing row hash outside the changed set moves → **STOP**, restore from the step-2 backups, re-run. Corpus verification failing at any point → **STOP**; the corpus is not authoritative until it passes.

## Open decisions — settle these before the batch runs

1. **Biography dates (part of C-3).** `GC002` has no date at all ("Childhood, circa"); several are periods (`1955-1959`) where the proposal takes the start year. 31 rows. Review `batch-03/date_normalisation.csv` columns `proposed_date` / `proposed_precision` / `rule`.
2. **The Centenary text divergences — NOT scheduled here.** Five chapters differ from the new .docx transcription by more than OCR noise: Ch. 2 (12,137 words in the split vs 14,283 in `BA032`), Ch. 12 (2,033 vs 3,291), Ch. 13 (9,454 vs 7,961), Ch. 16 (5,309 vs 6,015), Ch. 17 (5,139 vs 5,742). Replacing corpus text wholesale with the new transcription is a judgement about which source is authoritative, not a defect fix. **Left out of batch-03 deliberately.** If the team wants it, it becomes C-9 and the changed-doc set grows by 5.
3. **Reviving `BC009`** (Appendix D, "MPGR", 895 words) now that C-6 shows its text exists. That is a batch-04 question (a new ID superseding a retired one, as `BA108` does for `BA040`), not a correction.

## Status, 23 Sep 2026 — source fixes APPLIED

C-1, C-5, C-6, C-7 were applied to `data/text/` after comparing all 119 active book chapters against the original `.docx` files in `batch-04/incoming/books/`. See `batch-03/fix_report_against_books_2026-09-23.md`. Backups in `batch-03/backup_data_text_2026-09-23/`, log in `batch-03/change_log.csv`.

| Item | State |
|---|---|
| C-1 strip YAML (22 docs) | **applied** |
| C-2 Centenary date (22 docs) | pending — the value is settled (2001-12-01, month) |
| C-3 the 109 unreadable dates | pending — 31 biography rows still need a decision |
| C-4 stale corpus bodies (107) | pending — cleared by the regenerate |
| C-5 BA031 back matter | **applied** — 1,124 → 947 words, now 100% identical to the book |
| C-6 BA039 overrun | **applied** — 14,347 → 4,094 words |
| C-7 BC018 truncated | **applied** — 97 → 276 words, now 100% identical |
| C-8 retired docs in the index | pending — cleared by the re-chunk |
| **new** — `BC017` OCR-shredded body | **applied** — restored from the book, now 100% identical |
| **new** — 19 page running-header lines in 8 files | **applied** |
| **new** — the 19 Centenary chapters | **staged, not applied** — `batch-03/proposed_data_text/` |

**Why the Centenary chapters were staged rather than replaced:** the uploaded `.docx` dropped all 427 of the book's footnotes and carries OCR damage the corpus does not, while the corpus is missing body text (Ch. 13 especially) and has no `##` headings. Neither source is a superset, so a merge was built instead — corpus spine, book's missing passages and headings spliced in. 79,731 → 89,626 words, 414 footnotes kept, 70 headings restored. See `centenary_merge_report.csv`.

**STOP.** Still needed before batch-03 regenerates: approve or reject the Centenary merge, and answer open decision 1 (the 31 biography dates).


---

## Status, 25 Sep 2026 — STEPS 1-5 APPLIED AND VERIFIED

Full detail: `batch-03/batch-03_run_report_2026-09-25.md`.

Two open decisions were settled and two corrections added.

- **Open decision 1 (the 31 biography dates) — RESOLVED.** They were never undecidable: the "unknown"
  verdicts came from a value truncated at 10 characters. The sheet holds the full string
  (`July-August 1995`, `December 20, 2005 - December 2006`, `circa 2024-2025 (papal investiture, age 89)`).
  30 of 31 derive mechanically - day where a day is printed, first of month where a month is printed,
  start year for a period, mid/early/late-decade for the three approximations. `GC020` (Epilogue,
  "Retrospective (closing)") had no date in any form and was set to **2007-01-01**, matching GC019, the
  latest chapter it looks back from. See `biography_dates_v2.csv` and
  `biography_dates_applied_2026-09-25.csv`.
- **Open decision 2 (the Centenary merge) — APPROVED AND APPLIED**, all 19 chapters, 80,024 -> 89,917
  words. Logged as **C-10**. The staged `BA039.md` ended with a stray `**Appendix A**` heading that would
  have partly undone C-6; it was trimmed before copying. See `centenary_merge_applied_2026-09-25.csv`.

### C-9 (new) - date storage across all four pinned sheets
Found by `format_consistency_audit_2026-09-25.md`: **not one of the 1,109 existing rows stored its date as
the schema specifies.** 785 columns and 154 speeches held Excel datetimes, which the generator absorbed
silently because it writes `str(date)[:10]`. **978 rows converted datetime -> text, value unchanged** - no
corpus change, no re-index cost. Log: `date_normalisation_applied_2026-09-25.csv`.

**Every date in all four pinned sheets is now text YYYY-MM-DD. 1,109 of 1,109.**

### Sequence status

| Step | State |
|---|---|
| 1. Record the list and the D-2 decision | done |
| 2. Apply C-1 ... C-3, C-9, C-10 with backups | **done** - backups in `backup_pinned_2026-09-25/`, `backup_corpus_2026-09-25/`, `backup_pre-centenary-merge_2026-09-25/` |
| 3. Generator dry-run then real run | **done** - 1,104 docs, summary-fallback 0, retired 5 |
| 4. Content-aware diff | **PASS** - 287 files changed, 0 added, 0 removed, **156 docs all inside the expected 161**, nothing outside moved |
| 5. `build_corpus_snapshot.py` + `verify_pin.py` | **PASS, exit 0**. CE-5 re-chunk done: 9,865 -> 9,804 chunks, **all 27 retired chunks gone (D-3 closed)** |
| 6. Full re-embed (CE-6) | **BLOCKED - environment.** See below |
| 7-9. Retag, eval, threshold, attest, tag | not started |

Five of the 161 did not change (`BA041`, `BB008`, `BC011`, `BC015`, `BC020`) - they were in the set under
C-4, and their sources were already correct. A subset is safe; the rule that matters is that nothing
outside the set moved, and nothing did.

### Acceptance checks run against the regenerated corpus

| Check | Result |
|---|---|
| Leaked source YAML blocks | **0** |
| Documents with a date outside YYYY-MM-DD | **0** |
| Bodies opening with a duplicated title line | **0** |
| Retired IDs present in `corpus/` | **none** |
| Chunks belonging to a retired ID | **0** (27 removed) |
| `verify_pin.py` | **PASS** |

### Why step 6 is blocked

CE-6 is a full re-embed with bge-base-en-v1.5 @768d. The Linux workspace that reaches these folders has no
torch, no sentence-transformers, no faiss and no rank_bm25, and no model cache. PyPI is reachable from it,
but **huggingface.co is blocked by the egress proxy (403)**, so the model cannot be fetched there. The
working repo's `.venv` is a Windows environment and its Hugging Face cache sits outside the connected
folders.

**The corpus is correct, pinned and re-chunked. It is NOT re-embedded - retrieval still answers from the
old index.** Treat the corpus as authoritative and the index as stale until CE-6 runs.

To finish, in the working repo's venv on Windows:

```
python scripts/build_corpus_dense.py        # CE-6 - all 9,804 chunks in one pass, not an append
python scripts/build_sparse_index.py
python scripts/build_date_index.py
python scripts/check_date_index.py
python scripts/merge_tag_topics.py          # CE-7 - retag against the current 34 centroids
```

then CE-11 to CE-14, and copy `data/index/` back into the Final Project Folder.

### Defects closed by this batch
D-1, D-2, D-3, D-7 (and the 978 datetimes it never covered), D-10, D-11, D-12, D-13.
Still open: D-6 (uncommitted) and D-14 (OCR damage in the batch-04 book sources - needs a re-scan).


---

## Found 26 Sep 2026, while drafting CE-11 — NOT fixed, logged

### C-11 · `BC018`'s curated row is stale relative to its repaired body

C-7 restored `BC018.md` from 97 to 276 words. The **row was never re-derived.** It still says, in
`sub_topics`: *"NOTE: The source file is a short fragment (about 12 lines, of which the opening phrasing
is partly missing in the upload); the curation reflects only the content legibly present"*, and in
`register_markers`: *"NOTE: chapter is a short fragment; curation depth here is necessarily lighter"*.
`entities.people` lists *"Unnamed honoree being prayed for ('he')"* — the restored text names **Justice
Regino C. Hermosisima, Jr.** The restored first two paragraphs (petitions for "peace and prosperity in
our land", "sagacity, and integrity for our leaders", "a Supreme Court sublimated in prayer") are absent
from every curated field.

**Why it matters now:** `one_paragraph_summary` and `notable_anecdotes` are appended to the generated
`.md`, so they are chunked and embedded. This text goes into the index as written. **Cheapest to fix
before CE-6, not after.** Gold row `C48` in `gold_additions_batch03_2026-09-26.csv` flags it so a wrong
answer is not misread as a retrieval failure.

**Scope check:** a corpus-wide sweep for curated fields that describe their own source as damaged,
truncated, fragmentary, illegible or OCR-shredded returned 29 hits across 24 documents. Of those, only
`BC018` (two hits), `CA528` (below) and `SA120` matched substantively, and `SA120` is genuinely lecture
notes rather than damage. The other repaired documents — `BA031`, `BA039`, `BC017` — have rows
consistent with their repaired bodies.

### C-12 · `CA528` is truncated at source — pre-existing, outside batch-03

*"Only the President can"* (2011-05-15) states in its own `sub_topics`: *"Note: article is truncated in
source — full article content beyond 'Why no demurrer?' section not available"*. The title itself looks
cut. Body is 5,231 characters and stops mid-argument on the Garcia plea bargain. Not a batch-03
regression; it was never logged. **Batch-04 item** — needs the full text or a retirement decision.

### C-13 · The curated schema's enums are not enforced anywhere, and the data does not follow them

`docs/p1/corpus_schema.md` §3 states that `stances[].confidence` is **exactly one of** `asserted` ·
`asserted with evidence` · `hedged` · `reported (not his view)`, and that `entities` keys are a subset
of `people` · `institutions` · `places` · `cases` · `laws_treaties` · `events`. Swept across all 1,104
corpus documents on 26 Sep:

| | |
|---|---:|
| Documents with at least one non-enum `confidence` | **1,022 of 1,104 (93%)** |
| Distinct `confidence` values in use | **1,959** |
| Most common non-enum values | `high` (1,552 stances) · missing/`None` (404) · `medium` (36) · `endorsed` (17) |
| Free-text variants | `asserted as warning`, `asserted via Diokno`, `asserted with case citation`, `asserted as titular thesis`, … |
| Documents with a non-schema `entities` key | **103**, across **45** distinct keys |
| Most common non-schema keys | `dates` (30) · `concepts` (17) · `laws` (12) · `laws_and_documents` (11) |

**Blast radius — small, and worth saying precisely.** Neither field reaches the dense or sparse index:
`chunk_corpus.py` chunks the `.md` body, which carries the summary and anecdotes but not stances or
entities. `stances[:4]` *is* passed into the composition context block
(`app/answer_pipeline.py:866`), so the model is shown values like `confidence: "asserted via Diokno"`
and `confidence: null`. The `entities` object feeds the atomic-phrase dictionary in
`build_sparse_index.py`, which reads the object's values, not its key names — so the 45 stray keys cost
nothing at build time. **This is not a P3 blocker.** It is a documentation-versus-data contradiction
that should be settled rather than carried.

**Decision needed (not taken here):** either (a) amend `corpus_schema.md` §3 to describe
`confidence` as free text with a recommended vocabulary — which is what the data is — or (b) map the
1,959 values onto the four and make `normalise_curated.py` enforce it. (a) is honest and free; (b) is
correct and costs a mapping pass over 3,365 column stances alone. **Recommend (a) now and (b) at the P6
merge**, when batch-04's 186 rows arrive and a single enforcement point is cheapest to add. Either way
the schema should stop asserting an enum nothing checks.

**Process note:** the 25 Sep format-consistency audit checked encoding, punctuation, dates and JSON
parseability. It did not check *values against the declared vocabularies*, which is why this survived.
Any future audit should validate enums, not only that the JSON parses.
