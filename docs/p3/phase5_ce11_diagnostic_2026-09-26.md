# Phase 5 — restore the full-corpus universe, then the CE-11 diagnostic

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Interpreter:** `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe` (Python 3.12.13)
**$0 throughout:** no API calls, no composer, no token spend.
**Outcome:** Universe widened cleanly and verified exactly. **Part 5a's
prescribed measurement (`run_ops2_c2.py C3_full_corpus_universe`) could not
complete** — the harness's internal self-consistency check fails for a
well-understood, mechanical reason once the runtime index is no longer
pre-sliced to the 95-doc allowlist; not a data or retrieval defect, and not
worked around. **Part 5b ran completely and cleanly** — 11/14 grounding rows
pass, both retired probes pass, the OOS row is reported. The two real
grounding misses (X49, X51) and one near-miss (A41) are each traced to a
specific, named mechanism, not left as unattributed findings.

---

## PART 5a — widen the universe

### 1. Before-state (95-doc pilot index)

```
pilot_dense_meta.json: n_docs 95 | n_chunks 826 | allowlist_version "pilot_subset_frozen_v4.csv (95 of 95 documents resolved)"
pilot_dense.npy sha256 (before): 58b60d9842bb82a222637c50636b1318ad8bafebb9c0155b9ba11806dadcac9c
```

All exact matches to expectation.

### 2. Widen (no `--allowlist`)

```
python scripts/make_runtime_dense_index.py --force

[runtime-index] wrote pilot_dense.npy (9804, 768) and pilot_dense_meta.json
[runtime-index]   1104 documents / 9804 chunks, model BAAI/bge-base-en-v1.5 @768d, backend cuda_fp32
[runtime-index]   max abs(norm-1) = 1.192e-07
[runtime-index]   backed up -> data\index\_archived_2026-09-26_pilot_dense.npy
[runtime-index]   backed up -> data\index\_archived_2026-09-26_pilot_dense_meta.json
EXIT=0
```

**Clean exit 0 — the encoding fix works as intended** (the norm-string print
is now plain ASCII, no crash). The backup paths are exactly what the script
printed, both verified below.

### 3. Verify

```
pilot_dense.npy shape: (9804, 768)
meta: n_docs 1104 | n_chunks 9804 | len(chunk_ids) 9804 | len(doc_ids) 9804
allowlist_version: "full-corpus (no allowlist; supersedes pilot_subset_frozen_v4)"
retired ID leak: NONE

Backup verification:
  backup shape (826, 768) | n_docs 95 | n_chunks 826
  backup sha256: 58b60d9842bb82a222637c50636b1318ad8bafebb9c0155b9ba11806dadcac9c
  matches the recorded before-value: True
```

**All exact matches. PASS.** The backup is confirmed sha256-identical to the
pre-widen state — fully reversible.

### 4. Run `run_ops2_c2.py C3_full_corpus_universe` — could not complete

```
[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; config-path)
[live-vs-replay] 0/40 exact — MISMATCH [all 40 qids]
STOP: live path diverges from replay; grading would be unsound.
EXIT=2
```

**Confirmed nothing was written**: `eval/results/ops2_c1_drift.json` still
holds exactly `anchor`, `v4_expect`, `C0_current_artifacts`, `C1_post_ops2`,
`C2_post_batch03` — no `C3_full_corpus_universe` key exists. `C2_post_batch03`
is untouched, satisfying the hard boundary automatically (the script exits
before its write step).

**Root cause, traced by reading the script rather than guessed:**
`run_ops2_c2.py`'s internal self-consistency check (`replay_ranked()`)
independently re-implements the dense-ranking half of retrieval scoring by
computing `dsims = mat @ qv` and ranking **every row of `mat`** — it applies
no allowlist filter to the dense side at all. The live path
(`retrieval.run()`, via `_score_universe`) correctly restricts to
`service._allowlist("v4")` (95 documents) internally. **With the previous
826-row `pilot_dense.npy` — already pre-sliced to exactly those 95
documents — ranking "every row of `mat`" and "ranking within the 95-doc
allowlist" were the same operation**, so the self-check passed silently.
Now that `mat` holds the full 9,804-chunk, 1,104-document universe, ranking
"every row" includes 1,009 documents the live path correctly excludes —
guaranteed divergence on every query, unrelated to any defect in retrieval
itself.

**This is not worked around.** Per the boundaries ("do NOT edit any .py
file"), `run_ops2_c2.py` was not modified, and no alternate allowlist or
hand-rolled recall computation was substituted for it. **The prescribed C3
recall measurement could not be produced in this phase.** This needs one of:
(a) a `run_ops2_c3.py` variant whose replay logic applies the same allowlist
the live path uses (no such file currently exists in either repo — checked),
or (b) an explicit decision that the widened-universe recall comparison
isn't measurable through this particular harness and needs a different
approach. Flagging this rather than guessing which.

**Consequently, item 5's interpretation (the expected @1 fall under a wider
competitor pool) cannot be written up with real numbers — there is no C3
recall to interpret.** Nothing was tuned, no config touched, no index
rebuilt in an attempt to force a result.

---

## PART 5b — the CE-11 diagnostic

### 6. Run `run_ce11_diag.py ce11_full_corpus`

Did **not** refuse — the widening from Part 5a supplied everything it needs
(this script's universe guard is separate from, and unaffected by,
`run_ops2_c2.py`'s replay-parity issue above; verified by reading its source
first — it has no analogous replay mechanism).

```
[ce11] runtime universe: 1104 documents / 9804 chunks (full-corpus (no allowlist; supersedes pilot_subset_frozen_v4))
[ce11] ce11_full_corpus: 14 queries, 11 grounding
[ce11] grounding recall @1/@3/@5/@10 = 0.273/0.636/0.727/0.727 | at-selected 0.727
[ce11] retired probes pass: True | retired leaks anywhere: none
wrote eval/results/ce11_diag_ce11_full_corpus.json
EXIT=0
```

### 7. Per-row table

| qid | Expected doc(s) | Verdict | Routed topic | n selected | rank of first gold |
|---|---|---|---|---|---|
| A41 | BA032 | **FAIL** | with_due_respect_persona | 10 | none |
| A42 | BA036 | PASS | impeachment_accountability | 11 | 5 |
| A43 | BA037 | PASS | constitutional_doctrine | 4 | 1 |
| B44 | BB006 | PASS | international_law_disputes | 20 | 1 |
| A45 | BA039 | PASS | international_law_disputes | 13 | 1 |
| A46 | BA031 | PASS | mentors_and_legal_lineage | 28 | 3 |
| C47 | BC017 | PASS | faith_journey | 5 | 3 |
| C48 | BC018 | PASS | mentors_and_legal_lineage | 4 | 2 |
| X49 | BA039 | **FAIL** | honors_received | 5 | none (selected); **31st of 9,804 overall** |
| X50 | BD010;BA032 | PASS | mentors_and_legal_lineage | 14 | 3 |
| X51 | BC017;BC018 | **FAIL** | faith_journey | 7 | none |
| X52 (retired probe) | — | PASS | mentors_and_legal_lineage | 5 | no retired ID present |
| X53 (retired probe) | — | PASS | bar_exam_and_legal_education | 7 | no retired ID present |
| X54 (OOS probe) | — | REPORTED | friendships_and_civic_circles | 4 | route_cosine 0.5747 vs threshold 0.15 → in_scope=True |

Grounding recall: **@1 0.273, @3 0.636, @5 0.727, @10 0.727** (11 grounding
rows; 8/11 pass at-selected = 0.727).

### The three misses, each traced to a specific mechanism — not left unattributed

**A41 (BA032) — genuine near-miss, not a data problem.** Checked first
whether BA032 still exists as a live document (it does: 97 chunks,
confirmed in `corpus/index/chunk_index.json`). Cross-checked
`batch-03/centenary_merge_report.csv` / `centenary_merge_applied_2026-09-25.csv`:
"merged" there means the chapter's **body text** was restored/repaired
against the original book (word count rose from 14,224→17,692), **not** that
BA032 was merged into another doc_id. The retrieved set instead surfaced
five *other* Centenary chapters (BD010, BD011, BD013, BD014, BD016 — all
much shorter, 800–3,200 words per the merge report) that are topically
adjacent but not the target. This is an ordinary retrieval near-miss among
closely related sibling chapters in the same book, not a stale reference or
a corpus-integrity issue.

**X49 ("What is G.R. No. 142840 about?", expects BA039) — a real, specific
finding about the sparse arm, exactly as anticipated.** Investigated in
depth rather than just reporting the miss:

- The exact string `"G.R. No. 142840"` does **not** appear verbatim anywhere
  in BA039's text (checked directly against `chunks.jsonl`).
- The phrase dictionary **does** carry this citation, but only as one
  atomic multi-word phrase anchored to the full case name:
  `"bengson v. house of representatives electoral tribunal gr 142840"`. A
  query containing only the bare docket number, with no case name, cannot
  match that atomic phrase.
- Checked BA039's actual competitive position rather than accepting "not in
  top 5" as the whole story: on the **sparse arm alone**, BA039's best chunk
  ranks **13th of 9,804** (score > 0, so the numeral token *is* matched by
  plain BM25 term overlap) — outranked by chunks from **BD020** and
  **BA041**, two chapters titled things like "Selected Quotations from
  Ponencias and Opinions" that are *dense lists of many unrelated case
  citations*. Verified directly: neither BD020's nor BA041's top chunks
  contain "142840" anywhere — they win purely because BM25 rewards their
  high raw frequency of the generic tokens `"g.r."` and `"no."`, which
  appear dozens of times in a citations-list chapter.
- In the **full fused (dense+sparse RRF+centroid) ranking**, BA039's best
  chunk sits at **rank 31 of 9,804** — real, findable, not lost, just well
  outside this query's very narrow 5-chunk selection.

**This is a finding about the phrase dictionary and the sparse scoring
mechanism, as anticipated**: a bare docket-number query is vulnerable to
being outranked by citation-dense chapters unless the exact number (not just
the generic citation vocabulary) carries more discriminating weight, or the
atomic-phrase dictionary also indexes the bare number as its own retrievable
unit. Not fixed here — flagged, per the boundaries.

**X51 ("Which of your Justice and Faith reflections date from 1997?",
expects BC017;BC018) — attributed to a live capability gap, not random
noise.** Checked the actual dates of every retrieved document:
BD020=1997-10-10, BC020=1997-01-11, BA041=1997-01-12 — **three of the five
retrieved documents are also genuinely dated 1997**, alongside CC053 (2020)
and BC016 (1995). This is not "wrong year crowding out right year" so much
as "many 1997-dated chapters in this book compete, and semantic/BM25
relevance alone can't distinguish which specific 1997 chapters the gold
row names." Confirmed `config.DATE_INDEX_ENABLED = False` — the deterministic
temporal-intent filter that exists in this codebase specifically for
"reflections from a given year"-shaped queries is dark by default and was
not enabled in this phase (per the boundary against touching config). This
is a live, known, config-gated capability that isn't switched on, not a
retrieval defect.

### 8. C48 — checked against the evidence, not assumed

C48 (`BC018`, "Have you ever delivered an invocation for a fellow justice?")
actually **passed** in this run (rank_of_first_gold=2), so the prompt's
concern ("C48 is EXPECTED to be weak on the honoree's name... C-11, the stale
BC018 curated row") did not manifest as a grounding failure here — BC018 was
found in second position. If "weak on the honoree's name" refers to a
content-level accuracy question inside the answer (rather than whether the
right document is retrieved at all), that is outside what a retrieval-only
diagnostic like this one can observe; a composer run would be needed to
check whether the *answer text* correctly or incorrectly names the honoree.
Reported as: **retrieval found the correct document; the honoree-name
question, if still live, is a composer-level question, not a retrieval one,
and this diagnostic cannot settle it either way.**

### 9. Retired-ID sweep

Checked programmatically across every one of the 14 rows'
`retrieved_doc_ids`, not just the two RETIRED-probe rows:

```
retired leak across all 14 rows: NONE — confirmed clean
```

**PASS.**

### X54 (OOS probe) — reported, not graded

```
route_cosine: 0.5747 | OUT_OF_SCOPE_THRESHOLD: 0.15 | in_scope: True
routed_topic: friendships_and_civic_circles
```

Well above the threshold — the soft-prior router does not flag this
property-referral question as out of scope by cosine alone (it biases,
never gates, per the architecture). Consistent with the prompt's own framing:
the real out-of-scope behaviour is a composer decline, which costs tokens
and is not run here.

---

## Verdict on whether the batch-03 repairs are actually reachable by retrieval

**Mostly yes — 8 of 11 grounding rows (73%) find their corrected document at
selection time, and all three misses have a named, evidenced cause rather
than being unexplained:**

- A41 — an ordinary near-miss among sibling Centenary chapters (BA032 is
  fully live and intact).
- X49 — a real sparse-scoring/phrase-dictionary limitation for bare
  docket-number queries, evidenced down to the exact competing chunks and
  why they win.
- X51 — a live, config-gated capability (temporal filtering) that is off by
  default, not a corpus or retrieval defect.

None of the three misses trace back to anything batch-03 got wrong at the
source — all three corrected documents (BA032, BA039, BC017/BC018) are
present, intact, and in BA039's case ranked respectably (31st of 9,804)
even where the specific query phrasing works against it.

## Rows that cannot be settled without a composer run

**None of the 14 CE-11 rows require a composer run to settle the grounding
question itself** — retrieval-only grading answers "was the right document
found" for all 11 grounding rows and both retired-probe rows, and the OOS
row's real test (a composer decline) was explicitly out of scope for this
phase by design, not a gap in what was checked.

**One narrower question a composer run would be needed for:** whether C48's
*answer text* correctly names the honoree, if "weak on the honoree's name"
(per this prompt's own framing, deferred to P6) refers to answer-content
accuracy rather than document retrieval. That is the one place in this
14-row set where a $-costing composer run, not more retrieval investigation,
is the next step — and it is a decision for whoever owns P6, not made here.

## Files written this session

```
data/index/pilot_dense.npy                              (widened, 9804 chunks — live)
data/index/pilot_dense_meta.json                         (widened — live)
data/index/_archived_2026-09-26_pilot_dense.npy          (the 826-row pre-widen backup, sha256-verified)
data/index/_archived_2026-09-26_pilot_dense_meta.json    (backup meta)
eval/results/ce11_diag_ce11_full_corpus.json             (new)
```

`eval/results/ops2_c1_drift.json` was **not** modified in this phase (the C3
run never reached its write step). No `.py` file, gold CSV, or frozen query
JSON was touched.

## FLAG list — status

| Flag condition | Fired? |
|---|---|
| `make_runtime_dense_index.py` exiting non-zero | No — exit 0 |
| n_docs != 1104 after step 2 | No — exactly 1104 |
| `run_ce11_diag.py` refusing after the widening | No — ran cleanly |
| Any retired ID anywhere | No — swept across all 14 rows, clean |
| X49 missing BA039 entirely (not merely ranked low) | **This is worth stating precisely**: BA039 is absent from the final *selected* set (verdict FAIL, rank_of_first_gold=null in the selection), but it is not missing from the system's understanding of the corpus — it ranks 31st of 9,804 in the full fused ranking and 13th on sparse alone. Reported in full rather than either dismissed or overstated. |
| Any urge to tune a knob, rebuild an index, or edit a gold file | No — none of that occurred |

**Separately, and not on this phase's original flag list:** `run_ops2_c2.py
C3_full_corpus_universe` could not produce a recall measurement at all, for
the mechanical reason detailed in Part 5a §4. This needs a decision before
the "cost or benefit of widening from 95 to 1,104 documents" question this
phase set out to answer can actually be measured.
