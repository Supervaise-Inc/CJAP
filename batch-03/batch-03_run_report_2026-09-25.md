# Correction batch-03 — run report, 25 September 2026

Steps 1–5 of the batch-03 sequence are done and verified. **`verify_pin.py` exits 0.** The batch stops at
CE-6 for an environment reason, set out at the end.

## Decisions taken this run

- **Biography dates.** The 31 rows were never really undecidable. The "unknown" verdicts came from reading
  a value truncated at 10 characters — the sheet itself holds the full string. `July-Augus` is
  *July-August 1995*; `December 2` is *December 20, 2005 – December 2006*; `circa 2024` is
  *circa 2024-2025 (papal investiture, age 89)*. 30 of 31 derive mechanically: a day where a day is
  printed, the first of the month where a month is printed, the start year for a period,
  mid/early/late-decade for the three approximations. Recorded in
  `batch-03/biography_dates_applied_2026-09-25.csv` with the precision for each.
- **GC020**, the Epilogue ("Retrospective (closing)"), had no date in any form → **2007-01-01**, matching
  GC019, the latest dated chapter it looks back from.
- **The Centenary merge: applied.** All 19 chapters.

## What was applied

| Item | Scope | Result |
|---|---|---|
| **C-2** D-2 Centenary date | 22 docs | `2026-01-12` → text `2001-12-01` |
| **C-3** D-7 unreadable dates | 78 book + 31 biography | all now text `YYYY-MM-DD` |
| **C-9** (new) date storage | **978 rows** | Excel datetime → text, value unchanged |
| **C-10** (new) Centenary merge | 19 docs | 80,024 → 89,917 words; footnotes and headings restored |
| C-1, C-5, C-6, C-7 | 25 docs | already applied 23 Sep |

**Every date in all four pinned sheets is now text `YYYY-MM-DD`. 1,109 of 1,109.** That was the answer to
"do all normalisations have the same format" — they did not, and now they do.

One thing caught while applying the merge: the staged `BA039.md` ended with a stray `**Appendix A**`
heading, which would have partly undone C-6 (the chapter must stop at the end of Ch. 19). Trimmed before
copying.

## Verification

**Backups first** — `backup_pinned_2026-09-25/` (four sheets + sha256), `backup_corpus_2026-09-25/`
(all 2,214 files), `backup_pre-centenary-merge_2026-09-25/` (19 sources),
`backup_chunks_before_2026-09-25.jsonl`.

| Step | Result |
|---|---|
| Only the `Date` column moved in the pinned sheets | **PASS** — 1,078 Date cells, 0 other cells, verified cell-by-cell against the backup |
| Generator dry-run | 1,104 docs, summary-fallback **0**, retired **5**, no bad codes, no duplicates |
| Content-aware diff after regenerating | 287 files changed, **0 added, 0 removed** |
| Changed-doc set | **156 documents, every one inside the expected 161** — nothing outside moved |
| Acceptance 1 — leaked source YAML | **0** |
| Acceptance 2 — non-ISO dates in corpus | **0** |
| Acceptance 3 — duplicated title lines | **0** |
| Acceptance 4 — retired IDs in `corpus/` | **none** |
| `build_corpus_snapshot.py` | 1,109 docs across 4 source files |
| **`verify_pin.py`** | **PASS, exit 0** |
| CE-5 re-chunk | 9,865 → **9,804** chunks; **all 27 retired chunks gone (D-3 closed)** |

Five of the expected 161 did not change — `BA041`, `BB008`, `BC011`, `BC015`, `BC020`. They were in the
set under C-4 (stale bodies from the D-10 H1 fix); their sources were already correct, four of them
because the 23 Sep running-header rule was reverted on them. A subset is safe: the acceptance rule that
matters is that nothing *outside* the set moved, and nothing did.

## Defects closed

**D-1** (YAML leak) · **D-2** (Centenary date) · **D-3** (27 retired chunks) · **D-7** (unreadable dates —
and beyond its original scope: the 978 datetimes were never logged as a defect) · **D-10** (stale bodies)
· **D-11** (BA031 back matter) · **D-12** (BA039 overrun) · **D-13** (BC018 truncated).

Still open: **D-6** (uncommitted) and **D-14** (OCR damage in the batch-04 book sources, needing a
re-scan).

## Where it stops, and why

CE-6 is a **full re-embed with bge-base-en-v1.5 @768d**. It cannot run from this session:

- The Linux workspace that reaches your folders has **no torch, no sentence-transformers, no faiss and no
  rank_bm25**, and no model cache.
- PyPI is reachable from it, so the packages could be installed — but **`huggingface.co` is blocked by the
  egress proxy (403)**, so the model itself cannot be fetched there.
- Your working repo's `.venv` is a Windows environment and its Hugging Face cache sits outside the
  connected folders, so neither is usable from here.

**The corpus is correct, pinned and re-chunked. It is not yet re-embedded, so retrieval still answers from
the old index.** Until CE-6 runs, treat the corpus as authoritative and the index as stale.

### To finish it, in the working repo's venv on Windows

```
python scripts/build_corpus_dense.py        # CE-6 — full re-embed, all 9,804 chunks, one pass
python scripts/build_sparse_index.py
python scripts/build_date_index.py
python scripts/check_date_index.py
python scripts/merge_tag_topics.py          # CE-7 — retag against the current 34 centroids
```

Then CE-11 to CE-14: gold questions, promotion eval (fabrication 0, no regression on pre-existing gold),
threshold re-check, attestation and the `arch-baseline` tag.

One encoder, one dimensionality for the whole corpus — the re-embed is all 9,804 chunks in a single pass,
not an append. Copy the resulting `data/index/` back into the Final Project Folder when it is done.

## Then

Batch-03 promotion is what gates **P6**, the batch-04 merge. Once it is tagged, the 168 book rows and 18
column rows are ready to append — both workbooks are at 0 errors, with only the two signed spot checks
outstanding.
