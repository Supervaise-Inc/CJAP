# P2 — Corpus build report

One report covering all four P2 tasks. Numbers measured on **25 Sep 2026**, after correction batch-03.
Nothing here is carried forward from an earlier run.

## P2.1 Normalise — PASS

Script: `scripts/normalise_curated.py`. Reports: `batch-04/p5_normalise_books_report_2026-09-25.md`,
`batch-04/p5_normalise_columns_report_2026-09-25.md`, `batch-03/format_consistency_audit_2026-09-25.md`.

| Check | Result |
|---|---|
| Rows in / out | books 168 / 168 · columns 18 / 18 |
| Mojibake (`â€`, `Ã`, replacement char) | **0** across all six workbooks |
| Non-breaking spaces | **0** |
| Curly quotes remaining | **0** |
| Every JSON cell parses | **yes** — 1,680 book cells, 180 column cells, and every cell in the 1,109 pinned rows |
| Dates | **1,109 of 1,109 pinned rows are text `YYYY-MM-DD`** (was: 939 Excel datetimes, 105 unreadable strings and numbers, 65 other) |
| Second pass changes nothing | **yes** (idempotent) |
| Unparseable fields | none — reported rather than coerced, and there were none to report |

**Known weakness, not a failure:** dash folding is measured per pinned sheet at run time, so the books
sheet keeps 52 em/en dashes that the other three fold. One shared folding function would close it. See
`docs/p1/corpus_schema.md` §5.

## P2.2 Source-aware chunking — PASS

Script: `scripts/chunk_corpus.py`, heading-aware, all knobs from `config.py`.

| | |
|---|---:|
| Documents chunked | **1,104** (the full corpus, not a subset) |
| Chunks | **9,804** |
| Mean tokens per chunk | 313.7 (min 11, max 459) |
| Band / overlap | [200, 400] / 40 |
| Anecdote chunks kept whole | **1,330** |
| Retired documents still chunked | **0** — 27 chunks removed this run (closes D-3) |

Short pieces stay whole; long-form splits on headings. Verified on the documents most likely to break it:
the merged Centenary chapters moved as expected (BA032 77 → 97 chunks after +3,468 words) and the
truncated BA039 dropped from 76 to 28.

## P2.3 Doc store and chunk index — PASS

Outputs: `corpus/index/chunks.jsonl`, `corpus/index/chunk_index.json`.

| Check | Result |
|---|---|
| Corpus documents | 1,104 |
| Documents present in `chunk_index.json` | **1,104** |
| Documents with at least one chunk | **1,104** |
| Documents with no chunk | **none** |
| Chunk IDs pointing at a document not in the corpus | **none** |
| `chunk_index.json` vs `chunks.jsonl` document sets | **identical** |

Resolution is 100% in both directions: every document resolves to chunks, every chunk resolves to a
document.

**One gap:** the frozen evaluation allowlist (P1.5, `pilot_subset_frozen_v4.csv`, 95 documents) **is not
in the Final Project Folder** — it exists only in the working repo, so allowlist resolution could not be
checked here. Same class of problem as D-5, which was resolved by copying the retrieval scripts across.
Copy it in and re-run this check.

## P2.4 Pin the corpus — PASS

| | |
|---|---|
| `corpus_snapshot.json` rebuilt | 25 Sep, **1,109 docs across 4 source files** |
| `scripts/verify_pin.py` | **PASS, exit 0** |
| Per-file and per-row hashes | present for all four pinned sheets |

The snapshot counts 1,109 source rows against 1,104 corpus documents; the difference is the five retired
IDs, which keep their rows and have no corpus files. That is by design (CE-18).

"Frozen corpus" is now a claim a script fails on, which is the point of this task.

## What P2 does not cover

P2 ends at the doc store. The **dense and sparse indexes are P3, and they are stale** — batch-03 changed
156 documents and re-chunked, and CE-6 has not run. Until it does:

- the corpus is authoritative;
- the index answers from pre-correction text;
- no evaluation run is meaningful.

`batch-03/batch-03_run_report_2026-09-25.md` has the exact commands and why they must run on the Windows
venv.

## Coverage, for the record

1,104 documents today: 785 columns (17 Apr 2011 – 18 May 2026) · 131 book chapters from 4 of the 12 books
· 153 speeches (23 Nov 1994 – 27 Apr 2026) · 35 biography chapters. After the P6 merge: **1,290
documents, all 12 books, 803 columns**. The 2007–2011 column gap (~222 documents) is described in
`docs/p1/source_inventory.md`.
