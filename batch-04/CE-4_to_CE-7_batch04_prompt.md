# Batch-04 — CE-4 → CE-7, straight off the Corpus Expansion runbook

**26 Sep 2026.** This follows the **Corpus Expansion** sheet of `CJAP_Robot_Project_Plan_v2.xlsx`, in ID
order, using its own "How" and "Done when" text. No invented phase numbering. Nothing here touches P4
(retrieval runtime, all 8 rows Done) or P5 (composition, Done bar P5.7).

Stops at **CE-8**, which the sheet marks *(human decision — no CC prompt)*.

## Where batch-04 stands

CE-1, CE-1a, CE-1b, CE-2 and CE-3 are complete — verified on disk:

| | |
|---|---|
| `batch-04/intake_manifest.csv` | 186 rows |
| `batch-04/data_text/` | 186 files |
| `books_enriched_normalized.xlsx` | **168** rows, sheet `cjp_books_curated` |
| `columns_enriched_normalized.xlsx` | **18** rows, sheet `cjp_columns_curated` |

Expected after CE-4: corpus **1,104 → 1,290**; pinned rows **1,109 → 1,295**; columns 785 → 803; book
chapters 131 → 299; **4 works → 12**.

## Full reconciliation — every .md and .xlsx accounted for

Audited 26 Sep across `batch-04/book_split/`, `batch-04/data_text/`, the intake manifest and the four
pinned workbooks. There is no unaccounted material.

| | count |
|---|---:|
| Split-plan rows, 12 works / 18 volumes (the `with-due-respect` parent plan excluded — it aggregates the 7 volume plans) | **435** |
| − SKIP: part dividers 23, appendices 28, forewords by others 11, preface 9, cover 6, epigraph 6, title pages 24, other | −146 |
| = classified **CHAPTER** | **289** |
| − flagged `by-another-author`, deliberately not enriched | −2 |
| = enrichable chapters across all 12 works | **287** |
| − already in the corpus as chapters | −119 |
| = **new book chapters enriched in batch-04** | **168** |

And the corpus side closes too: **131** existing book chapters = 119 of the above **+ 12** items the
newer B0 split now classifies as SKIP but which an earlier, looser intake admitted as documents —
A Centenary of Justice +3 (Appendices A–C are their own doc_ids: BC007, BC008, BD019), Justice and
Faith +3, The Bio-Age Dawns on the Judiciary +6 (the four appendices by other authors are the open
question already logged).

**The two excluded chapters, for the record** — both flagged `by-another-author`, consistent with CE-3
and with the corpus rule that it carries CJP's own voice:

- *Leveling the Playing Field* ch. 9, "Law Without Borders" (1,022 words)
- *Reforming the Judiciary* ch. 2, "Forum on the APJR" (7,558 words)

### Expected end state after CE-4

| | now | +batch-04 | after |
|---|---:|---:|---:|
| Columns | 785 | +18 | **803** |
| Book chapters | 131 | +168 | **299** |
| Speeches | 153 | — | 153 |
| Biography | 35 | — | 35 |
| **Corpus documents** | **1,104** | **+186** | **1,290** |
| Pinned rows (incl. 5 retired) | 1,109 | +186 | 1,295 |
| Distinct works | 4 | +8 | **12** |

**Do not cross-check 299 against the split plan's 289 and conclude something is missing** — the 10-item
difference is the 12 legacy appendix/front-matter documents minus the 2 by-another-author exclusions,
reconciled above.

### What batch-04 does NOT contain

`BATCH-04_SPEECHES_PROMPTS.md` and `BATCH-04_BIOGRAPHY_PROMPTS.md` exist but **were never run** — there
are no `speeches_enriched*.xlsx` or `biography_enriched*.xlsx` anywhere, and the manifest holds only
`B*` and `C*` doc_ids. Speeches stay at 153 and biography at 35. Also still outstanding: the **~222
columns from Feb 2007 – Apr 2011** that were never sourced (803 + ~222 ≈ 1,025 is where "almost 1,000
columns" comes from). Both are future batches, not gaps in this one.

## One decision before CE-4 starts

**C-11 — `BC018`'s curated row is stale.** C-7 restored its body from 97 to 276 words, but the row still
says *"the source file is a short fragment"* and `entities.people` still reads *"Unnamed honoree"* when
the restored text names **Justice Regino C. Hermosisima, Jr.** The summary is appended to the `.md`, so
it is chunked and embedded.

I said last turn that CE-4's re-pin makes this free. **That was wrong under the runbook.** CE-17 is
explicit: *"Correct an existing doc — its own batch, never mixed with new material."* Bundling it into
batch-04 breaks the rule that made batch-03 clean.

So it is a real choice, and it is yours:

| | cost | cost |
|---|---|---|
| **A · Own CE-17 batch** (the runbook's default) | its own re-embed (~30 min GPU) and its own eval | keeps every diff attributable |
| **B · Bundle into batch-04** | free — rides CE-4's re-pin and CE-6's embed | a deliberate CE-17 exception; must be recorded in the decisions register with the reason |

If B, say so and it goes into the CE-4 step below. If you say nothing, the prompt runs **A** — batch-04
alone, BC018 untouched, corrected later as its own batch.

---

## The prompt

```
Batch-04 corpus expansion — CE-4 through CE-7, from the Corpus Expansion sheet.
Interpreter: set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe" — use %PY% throughout.
CE-4, CE-5 and CE-7 are $0. CE-6 is GPU time, no API tokens. Nothing here spends money.
STOP at CE-8 — the sheet marks it a human decision with no CC prompt.

CE-16 ABORT CRITERIA — read before starting, not after
- Any pre-existing row hash changed -> STOP, restore, re-run CE-4.
- Corpus verification fails at any point -> STOP; the corpus is no longer a known state.
- Encoder or dimensionality differs from the standing baseline -> STOP; a mixed vector space cannot
  be tuned back into shape.
Report which of these you checked at each step.

BOUNDARIES
- APPEND-ONLY. No pre-existing row, doc or chunk_id may change. That is the whole safety property.
- Do NOT create, merge or modify any centroid anywhere in this run. CE-7 produces the decision input;
  CE-8 makes the decision. Never run build_centroids.py or merge_tag_topics.py here.
- Do NOT edit voice_card.md, config.py, or any .py file.
- Do NOT touch gold_reference_set.csv, draft_queries_v1.json or the CE-11 files — that is CE-11/CE-12.
- Do NOT revisit the retrieval universe, the v4 allowlist, or any C-label drift measurement. Out of
  scope: P4 and P5 are Done.

----- CE-4 · Append-only merge into the corpus + re-pin -----

1. Record the before-state: corpus doc count by format, row counts in all four
   data/csv/cjp_*_curated_normalized.xlsx, and the corpus_snapshot.json totals. Back up the four
   pinned workbooks and corpus_snapshot.json to batch-04/backup_pre-CE4_2026-09-26/.
2. Append batch-04's rows into the PINNED workbooks — never the stale CSVs:
     batch-04/books_enriched_normalized.xlsx   (168 rows) -> data/csv/cjp_books_curated_normalized.xlsx
     batch-04/columns_enriched_normalized.xlsx (18 rows)  -> data/csv/cjp_columns_curated_normalized.xlsx
   Column order and header must match the destination exactly; the biography sheet has 14 columns, not
   15 (no Link) — do not "fix" that here. Append only; do not sort, re-order or rewrite existing rows.
   Confirm no appended Article Code collides with an existing one or appears in
   data/csv/retired_doc_ids.csv. Note BA108 carries superseded_doc_id = BA040 (retired) — that is
   correct and expected.
3. Copy batch-04/data_text/*.md (186 files) into data/text/. Refuse to overwrite: if any target exists,
   STOP and report which.
4. %PY% scripts\generate_corpus_from_xlsx.py --dry-run
   Report its counts before writing anything. It skips every ID in retired_doc_ids.csv and strips a
   stray YAML block from a source .md — both are reported by the script; quote what it says.
5. %PY% scripts\generate_corpus_from_xlsx.py
   Then rebuild the pin: %PY% scripts\build_corpus_snapshot.py  and  %PY% scripts\verify_pin.py
6. VERIFY — all must hold:
     corpus documents 1,104 -> 1,290 (exactly +186); columns 785 -> 803; book chapters 131 -> 299
     pinned rows 1,109 -> 1,295
     verify_pin.py exits 0
     CONTENT-AWARE DIFF: every one of the 1,104 pre-existing documents is byte-identical, and every
     pre-existing per-doc row_sha256 in corpus_snapshot.json is unchanged. Matching counts do NOT
     prove nothing was lost — compare hashes, document by document, and report the number compared.
     Any pre-existing hash that moved: STOP, restore from the backup, report.
7. Report the distinct book works now represented — expect 12 (With Due Respect counts as one work in
   seven volumes; 18 volumes in total).

----- CE-5 · Chunk NEW docs only -----

8. Note for this repo: scripts\chunk_corpus.py has no incremental mode — it rebuilds the doc store.
   The chunker is deterministic and no pre-existing document changed in CE-4, so a full run must
   reproduce every existing chunk_id exactly. Do NOT change any config knob.
   Before running, save a copy of corpus/index/chunks.jsonl and chunk_index.json to
   batch-04/backup_pre-CE5_2026-09-26/.
9. %PY% scripts\chunk_corpus.py
10. VERIFY — this is how "existing chunk_ids unchanged" gets proven rather than assumed:
     every chunk_id present before is still present, with identical text — report the count compared
     and any that differ (any difference: STOP)
     chunk count rises only by the new material; report before, after and the delta
     every one of the 186 new doc_ids resolves to >= 1 chunk; list any that do not
     chunks-per-doc for the new material: min, median, max, and the documents at each extreme
     boundary + anecdote spot-check on a sample of 5 new book chapters — confirm anecdotes are kept
     whole and headings split as expected
     no retired ID (BA040, BC009, BC010, BD018, SA085) has any chunk

----- CE-6 · One full re-embed, old + new in a SINGLE vector space -----

11. MANDATORY BEFORE THE RUN. data/index/pilot_dense.npy currently holds 1,104 docs / 9,804 chunks.
    build_corpus_dense.py's parity gate slices the new matrix down to that index's chunk_ids and
    raises RuntimeError if any is missing — and it runs AFTER the whole embed completes. Against a
    1,290-document corpus its chunk_ids will not resolve, so the run would burn the full embed and
    then fail. Rename it aside first, do not delete:
      data/index/pilot_dense.npy       -> data/index/_prebatch04_2026-09-26_pilot_dense.npy
      data/index/pilot_dense_meta.json -> data/index/_prebatch04_2026-09-26_pilot_dense_meta.json
    Also back up corpus_dense.npy + corpus_dense_meta.json — build_corpus_dense.py's except block
    unlinks CORPUS_DENSE_PATH on a late failure.
12. Confirm the encoder is unchanged from the standing baseline before embedding: EMBED_MODEL_ID
    BAAI/bge-base-en-v1.5, EMBED_DIM 768, EMBED_NORMALIZE True, backend cuda_fp32. A different model
    or dim is a CE-16 STOP.
13. %PY% scripts\build_corpus_dense.py
    One pass over the whole corpus, model resident. Expect roughly 12,000-13,000 chunks; on the GTX
    1650 this is tens of minutes. Report wall-clock and chunks/s.
14. %PY% scripts\make_runtime_dense_index.py --force
    No --allowlist. This rebuilds the runtime index the app actually loads (build_corpus_dense.py does
    not write it when no prior pilot index exists). Expect n_docs 1290.
15. %PY% scripts\build_sparse_index.py
    Rebuilds BM25 over all chunk text and extends the atomic-phrase dictionary with batch-04's curated
    keywords and entities. Multi-word keywords must stay single terms. Report n_chunks, n_phrases and
    the phrases-by-provenance breakdown, before and after.
16. %PY% scripts\build_date_index.py   then   %PY% scripts\check_date_index.py
    Report n_docs / dated / undated — expect 1,290 / 1,290 / 0 — and list any undated document.
    check_date_index.py's NO-REGRESSION GATE compares against the bge-large arch_baseline_v2.json and
    will mismatch all 40 by construction. That is known and is NOT a failure; report it and move on.
17. VERIFY: corpus_dense_meta.json records model_id, dim 768, backend, n_chunks, build_date and
    chunk_index_sha256; the matrix is float32 and unit-norm (report max deviation); its chunk_ids match
    corpus/index/chunks.jsonl exactly, same set and same order; no retired ID appears anywhere.

----- CE-7 · Orphan census — tag the NEW docs against the CURRENT topic map -----

18. Tag ONLY the 186 new doc_ids against the EXISTING 34 centroids, primary + secondary up to
    config.MAX_TOPIC_TAGS. DO NOT create, merge or modify any centroid. If the only available script
    would also rewrite centroids, do NOT run it — write the tagging as a read-only computation against
    data/index/topic_centroids.npy and the new rows of corpus_dense.npy, and say that is what you did.
19. Deliver the four outputs the sheet asks for, into batch-04/:
     (1) the tagging table for the 186 new documents — doc_id, primary, primary_cos, secondary
     (2) the max-cosine DISTRIBUTION for the new docs — histogram or deciles, not just a mean
     (3) the ORPHAN LIST: every new doc below config.TOPIC_ASSIGN_MIN_COSINE (0.68), with its
         best-matching topic and score
     (4) an ORPHAN CLUSTERING: are the orphans scattered misses, or do they share a subject? Group them
         and name the shared subject where one exists. This is the input CE-8 turns on — a list with no
         clustering does not let anyone choose a branch.
20. Re-run the INDEPENDENCE CHECK across the existing centroids on the enlarged corpus: for
    TOPIC_MERGE_COSINE from 0.95 to 0.999, report how many pairs exceed each threshold and how many
    topics would remain. Compute it directly from the centroid matrix — do NOT run merge_tag_topics.py.
    For context, before batch-04: 220 of 561 pairs above 0.95, mean pairwise 0.9334, and
    honors_received / robot_identity_meta are byte-identical zero-chunk centroids sharing one fallback.
    Report whether the enlarged corpus changes that picture.
21. Also report, because CE-8 will want it: how many of the 186 new documents are books, and whether
    the orphans skew toward book chapters. The current topic map was generated on 2026-05-25 from 79
    documents — 64 columns and 15 speeches, and no books at all. Say plainly whether the new material
    is finding a home in a taxonomy that never saw it.

REPORT — batch-04/CE-4_to_CE-7_report_2026-09-26.md
22. Every count before/after at each step; the content-aware diff results with the number of hashes
    compared; the chunk stability proof; the embed provenance and timing; and CE-7's four outputs plus
    the independence sweep. End with the decision input for CE-8 stated in one paragraph — scattered
    orphans, a coherent cluster, or independence violations — WITHOUT choosing a branch.

FLAG, DO NOT FIX
- Any pre-existing row, document or chunk_id that changed · verify_pin not exiting 0 · a doc_id
  collision or a retired ID reappearing · the encoder or dim differing from the baseline · any new
  document resolving to zero chunks · any script that would create, merge or modify a centroid ·
  any urge to choose the CE-8 branch yourself.
```

---

## After CE-8

The branch you choose decides the rest, and the sheet already lays it out:

| CE-7 says | branch | next |
|---|---|---|
| Scattered low-cosine orphans, no shared subject | **RETAG ONLY** | skip to CE-11 |
| A coherent orphan cluster the map has no dimension for | **EXPANSION** | CE-9 proposal + sign-off, then CE-10 |
| Independence violations, or a topic whose members no longer cohere | **FULL REBUILD** | CE-10 — centroids from scratch |

Given the topic map was built from 79 documents with no books in it, and 168 of the 186 new documents
are book chapters, expansion or rebuild looks more likely than retag — but that is what CE-7's evidence
is for, and CE-8 is yours to record in the decisions register with the evidence attached.

Then CE-11 (extend the gold set to the new material), CE-12 (promotion eval), CE-13 (re-check the
query-time thresholds on the new distribution), CE-14 (promote, tag, attest), CE-15 (update every
quoted number).
