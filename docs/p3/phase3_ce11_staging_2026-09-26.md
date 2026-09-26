# Phase 3 (revised) — comparator closure + CE-11 staging

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Interpreter:** `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe` (Python 3.12.13)
**$0 throughout:** no API calls, no composer, no token spend at any step.
**Outcome:** **Complete.** Comparator established and documented, the 95-doc
pilot universe restored (labelled, reversible), the frozen query set validated
against `FROZEN_SHA`, CE-11 staged as a separate non-frozen query set with no
fabricated fields, and both frozen references confirmed byte-unchanged.

Amendments A–D (dated 26 Sep, applied on top of
`docs/p3/Phase3_CE-11_and_comparator_fix_2026-09-26.md`) are folded in below
at the points they apply.

---

## Amendment A — hard precondition, confirmed in one line

`data/index/topic_centroids_meta.json`: **n_topics 34, merged_pairs empty** —
confirmed before touching anything. (Full detail — merge_cosine 1.01, drift
2.98e-08 vs the v4.2 anchor — is in the P3.3 recovery report; not re-verified
in depth here per the amendment's instruction not to re-run that recovery.)

## Amendment B — the claimed encoding patch is not in the file

Before using `scripts/make_runtime_dense_index.py` in Step 4, I read it
directly rather than trust the claim at face value:

```
sha256: 9d68309ce970d5e2c2bbfa859d84ec7636dd823be1e04b361a2cb3cae7c6d5d9
mtime:  2026-09-26 05:36:18 (after my earlier P3.3 work — the file was touched today)
```

**Partially true.** The `--allowlist` feature genuinely is new (confirmed
present in the source, needed for and used in Step 4 below). But the specific
claim — "its two Unicode norm strings are now ASCII and `main()` reconfigures
stdout/stderr with `errors="replace"`" — **does not hold**: both unicode
strings (`‖`, `−`) are still present verbatim at lines 97 and 228, and no
`reconfigure`/`errors=` call exists anywhere in the file. Confirmed by
`grep`, not by running it first. Consequently, in Step 4 I did **not** treat
a non-zero exit as automatically a genuine failure — I verified the actual
write by direct file inspection, same approach as the original P3.2b finding.
And that's exactly what happened: the script hit the identical
`UnicodeEncodeError` on line 228 as before, in the success-path print, after
both outputs were already written correctly (detail under Step 4 below).

## Amendment C — full-corpus index before-values (recorded before renaming)

```
pilot_dense_meta.json (before):
  n_docs 1104 | n_chunks 9804 | allowlist_version "full-corpus (no allowlist; supersedes pilot_subset_frozen_v4)"
pilot_dense.npy sha256 (before rename):
  c11f67848cd7bf911d0ccbc4cf8bc509267c24c79293849aaf3507b4e1cf19e1
```

All three match expectation exactly (1104 / 9804 / the stated allowlist_version
string).

## Amendment D — health-gate anchors, verbatim (for the CE-12 pre-check, not run here)

From `eval/results/arch_baseline_v4_2_provenance.json`,
`health_gate_machine_verified.anchors`:

```
A1 rule-of-law:        PASS n_selected=7
D21 museum-of-liberty:  PASS route=museum_for_liberty_and_prosperity n_selected=7
E28 roe-v-wade:         PASS n_selected=16
```

Result: 3/3 PASS. Not run in this phase — recorded for the record only, per
instructions.

---

## STEP 1 — finish the eval closure

### 1. Copy `reports\pilot-eval subset\` (whole dir), `run_ops2_c1.py`, `verify_v4_transition.py`

**Before copying**, checked for filename collisions: this repo already had 4
files in `reports/pilot-eval subset/` (from earlier project work). All four
were byte-identical to the source versions — no overwrite risk, confirmed
before copying.

**Source: 27 files. Destination after copy: 27 files.** All 27 sha256-matched:

```
CJP_Evaluation_Methodology_and_Results.docx  MATCH
CJP_grading_workbook_D_E.xlsx                MATCH
CJP_Robot_Evaluation_Scorecard.xlsx          MATCH
coverage_table.csv                           MATCH
coverage_table_v2.csv                        MATCH
coverage_table_v3.csv                        MATCH
coverage_table_v4.csv                        MATCH
draft_queries_v1.json                        MATCH
forced_inclusions.csv                        MATCH
forced_inclusions_v2.csv                     MATCH
forced_inclusions_v3.csv                     MATCH
forced_inclusions_v4.csv                     MATCH
pilot_subset_frozen.csv                      MATCH
pilot_subset_frozen_v2.csv                   MATCH
pilot_subset_frozen_v3.csv                   MATCH
pilot_subset_frozen_v4.csv                   MATCH
query_chunk_match_grading_v1.md              MATCH
selection_notes.txt                          MATCH
selection_notes_v2.txt                       MATCH
selection_notes_v3.txt                       MATCH
selection_notes_v4.txt                       MATCH
w111_prep_grounding_report.json              MATCH
w111_repair_report.json                      MATCH
w2_2_free_accounting.json                    MATCH
w2_topp2_report.json                         MATCH
w2_topp_report.json                          MATCH
_grading_payload.json                        MATCH
```

Two scripts:

```
scripts/run_ops2_c1.py           MATCH  sha256 a88f34d5d1ee76a8fc9c870a82566af6c200ef185b3bb0a0b7311937a15f74bc
scripts/verify_v4_transition.py  MATCH  sha256 8f4175ea95ddca8632773e85986745e55424e98e535cd6b469ff9ead6853e645
```

### 2. Re-run `check_date_index.py`

```
=== COVERAGE ===
docs 1104 | dated 1104 | undated 0
precision: {'day': 1104}
by source-class x precision: {'B:day': 131, 'C:day': 785, 'G:day': 35, 'S:day': 153}
undated doc_ids: []

=== IDEMPOTENCY GATE === rebuild sha == original: True (82a550e69c34)

STOP: retrieval changed with flag OFF -> [A1..X40, all 40 qids]

=== NO-REGRESSION GATE (flag OFF, 40q vs arch-baseline-v2) === byte-identical: False
EXIT=3
```

**COVERAGE and IDEMPOTENCY GATE both pass**, identical to the P3.4/P3.5 run.
**NO-REGRESSION GATE reports a mismatch on all 40 queries — expected, not a
new problem.** This gate compares live retrieval against
`arch_baseline_v2.json`, which Step 3 below independently confirms is a
bge-large, 827-chunk baseline from 2026-07-04 — a completely different
embedder than the live bge-base system. Every query would mismatch regardless
of any real regression from batch-03. Reported verbatim per instructions;
not treated as a failure requiring action.

---

## STEP 2 — validate the frozen query set

### 3. `draft_queries_v1.json` — FROZEN_SHA check

```
meta.frozen: True
meta.n: 40
len(queries): 40

computed sha256:   65492b650aec8dda5e76be21c32aaae3faf61f9663c6c58ace02b5a6c4bc9a63
expected FROZEN_SHA: 65492b650aec8dda5e76be21c32aaae3faf61f9663c6c58ace02b5a6c4bc9a63
MATCH: True
```

**PASS — exact match.** The gate would not fail; everything downstream is
comparable.

### 4. Stale fields noted, not acted on

```
meta.embed_regime: BAAI/bge-large-en-v1.5/1024d/cuda_fp32/allowlist_v4
meta.universe:     v4 allowlist (95 docs / 827 chunks)
```

Confirmed present exactly as the prompt describes. The query **strings** are
what the FROZEN_SHA hashes and are regime-independent; these two fields are
stale metadata from the file's original bge-large run and are not a
comparator.

---

## STEP 3 — establish the correct comparator, in writing

### 5. Read directly from `eval/results/`

**`arch_baseline_v4_retrieval.json`:**

```
anchor: "arch-baseline-v4 (embedder = bge-base-en-v1.5, ratified by Dok)"
recall_C_baseline: {'1': 0.618, '3': 0.882, '5': 0.882, '10': 0.971, 'chunks_sent': 0.941}
n: 34
```

**`arch_baseline_v4_2_provenance.json`:**

```
canonical_recall_machine_verified:
  basis: v4 gold, N=34, scope-aware, retrieval-only $0
  recall_at_1: 0.588 | recall_at_5: 0.882 | recall_at_chunks_sent: 0.941 | recall_at_10: 0.971
  evidence: eval/results/ops2_c1_drift.json (C1), bm25_drift_check.json (06b8129), verified again this session

health_gate_machine_verified: (see Amendment D above — 3/3 PASS, all three anchors verbatim)

promoted_artifacts_machine_verified:
  corpus_dense.npy:     shape (9865, 768)  model bge-base-en-v1.5  sha16 df5ca465c954e218
  topic_centroids.npy:  shape (34, 768)    recipe full-corpus member_chunk_mean (Phase B)  sha16 50600bdd34836db7
  pilot_dense.npy:      shape (827, 768)   sha16 0ec7d6f64d3c5b14  (OPS-2 slice of corpus_dense)
  pilot_sparse.pkl:     sha16 9dc1243621a96382  (batch-02 9,865-chunk BM25 rebuild)
```

**Note the small discrepancy between the two files' recall@1**: `_v4_retrieval.json`
reports 0.618, `_v4_2_provenance.json` reports 0.588 as the "canonical" figure.
Reported as-read from each file, not reconciled — the provenance file explicitly
labels its number "canonical" and "machine-verified," so that is the one worth
treating as the comparator figure, but the discrepancy itself is worth noting
rather than silently smoothing over.

### Comparator determination — independently verified, not taken on faith

**`arch_baseline_v2.json` is not the standing comparator for a bge-base run.**
Read directly (not assumed):

```
anchor: "arch-baseline-v2 (adaptive top-p softmax_temp/0.06 MIN_K=4 + streamed composer 640)"
run_timestamp: 2026-07-04T05:47:50+08:00
queries[0].universe: 827   (checked; consistent across the format — every query record carries this field)
```

`config_snapshot` in this file lists retrieval/composer knobs but no explicit
embedder id; combined with the 2026-07-04 timestamp (before the bge-base
full-corpus matrix, whose archived pilot index is dated 2026-07-17) and the
`_v4_retrieval.json` anchor string naming bge-base as the *later* ratified
embedder, **v2 predates the bge-base transition and is scoped to the
827-chunk pilot universe.** No contradiction found in the files against the
prompt's claim.

**The standing comparator for the current bge-base regime is
`arch-baseline-v4` / `v4.2`**, specifically `arch_baseline_v4_2_provenance.json`'s
`canonical_recall_machine_verified` block (0.588 / 0.882 / 0.941 / 0.971) and
its health-gate 3/3 PASS. `scripts/run_ops2_c1.py` (now copied in, Step 1) is
the existing $0 harness built to compare against it by label.

---

## STEP 4 — restore the comparable retrieval universe

### 6. Archive the full-corpus runtime index (before-values under Amendment C above)

```
data/index/pilot_dense.npy       -> data/index/_fullcorpus_2026-09-26_pilot_dense.npy
data/index/pilot_dense_meta.json -> data/index/_fullcorpus_2026-09-26_pilot_dense_meta.json
```

Both renames confirmed landed; both original paths confirmed absent
afterward.

### 7. Rebuild scoped to the 95-doc pilot allowlist

```
CJ_TOPIC_MERGE_COSINE unset (not relevant here) — env for this call:
  CJ_EMBED_MODEL_PATH, HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1

python scripts/make_runtime_dense_index.py --allowlist "reports/pilot-eval subset/pilot_subset_frozen_v4.csv" --force

[runtime-index] allowlist pilot_subset_frozen_v4.csv: 95 documents, 826 chunks
[runtime-index] wrote pilot_dense.npy (826, 768) and pilot_dense_meta.json
[runtime-index]   95 documents / 826 chunks, model BAAI/bge-base-en-v1.5 @768d, backend cuda_fp32
Traceback (most recent call last):
  ...line 228: print(f"[runtime-index]   max |‖v‖−1| = {dev:.3e}")
UnicodeEncodeError: 'charmap' codec can't encode character '\u2016' in position 23
EXIT=1
```

**`95 documents, 826 chunks` — the exact expected line.** 826, not 827,
treated as correct per the prompt (batch-03 re-chunked 18 of those 95
documents). **The non-zero exit is the same pre-existing console-encoding
false negative flagged under Amendment B** — confirmed by direct file
inspection (below), not by assuming it away:

```
data/index/pilot_dense.npy       2,537,600 bytes  mtime 2026-09-26 07:09
data/index/pilot_dense_meta.json    28,619 bytes  mtime 2026-09-26 07:09
```

2,537,600 bytes = 826 × 768 × 4 (float32) + npy header — matches exactly.
No `--force` backup was created, correctly — nothing existed at
`pilot_dense.npy` when this ran, since Step 6 had already renamed it away.

### 8. VERIFY the new runtime index

```
n_docs 95 | n_chunks 826 | dim 768 | model_id BAAI/bge-base-en-v1.5
len(chunk_ids) 826 | len(doc_ids) 826
allowlist_version: "pilot_subset_frozen_v4.csv (95 of 95 documents resolved)"
retired ID leak: []
matrix shape (826, 768) float32 | max |norm-1| = 1.192e-07
```

**All exact matches. PASS.**

### 9. Smoke test — real path, real (95-doc) universe

```
python -c "import json,sys; sys.path.insert(0,'app'); import config, retrieval; \
  ids=set(json.load(open(config.DENSE_INDEX_META_PATH,encoding='utf-8'))['doc_ids']); \
  print(len(ids)); print(retrieval.run('What did he say about the rule of law?', ids))"

95
TOP_TOPIC: global_geopolitics 0.6556
ROUTED: [('global_geopolitics', 0.6556), ('constitutional_doctrine', 0.6454), ('rule_of_law', 0.6443)]
SELECTED: SB028::c004 (1.1991), CA031::c000 (1.1535), CD003::c006 (1.0758),
          BC001::c003 (1.0568), SB028::c009 (1.0537), SB028::c014 (1.0114), SB028::c011 (0.9568)
```

**doc_id count 95 — exact.** Route top-3 are a near-tie
(spread 0.011), same pattern observed against the full-corpus universe in the
P3.3 recovery — a query-embedding property, not universe-dependent (`route()`
only sees the query vector and the 34 centroids). Titles checked for
plausibility:

```
SB028::c004,c009,c011,c014 -> "Liberty, Prosperity and the Rule of Law for CPAs, CFOs and CEOs"
CA031::c000                -> "Partners in rule of law, constitutionalism, AI"
CD003::c006                -> "20 law grants at P250k, 5 MBA at P500k"
BC001::c003                -> "With Due Respect (Vol. 7) -- Ch. 3: Justice and Love on Valentine's Day"
```

5 of 7 chunks are directly rule-of-law titled. **Plausible result, PASS.**

---

## STEP 5 — stage CE-11 as a parallel, non-frozen query set

### 10. Validate `gold_additions_batch03_2026-09-26.csv`

| Check | Result |
|---|---|
| Same 15 headers, same order, as `gold_reference_set.csv` | **PASS** — identical lists, confirmed by direct comparison |
| 14 rows, qids A41–X54, no collision with frozen 40 | **PASS** — 14 rows: A41,A42,A43,B44,A45,A46,C47,C48,X49,X50,X51,X52,X53,X54; zero overlap with the 40 frozen qids |
| Every `gold_source_docs` id (excl. RETIRED/OOS) exists in corpus and is not retired | **PASS** — 0 problems across all entries, including multi-doc rows (X50: BD010;BA032, X51: BC017;BC018) |
| Every `routed_topic` in the live 34 `topic_ids` | **PASS** — all 14 resolve (supreme_court_history, judicial_activism_and_political_question, death_penalty_and_echegaray, economic_governance_and_business_law, constitutional_doctrine, with_due_respect_persona, faith_journey ×3, lawyer_ethics_initiative). This directly confirms the P3.3 recovery was necessary for this phase — these labels don't exist under the collapsed 3-topic set. |
| `retrieved_docs` and `model_answer` empty in all 14 | **PASS** — confirmed empty in every row |

**No failure — did not stop.**

### 11. `eval/results/ce11_queries_2026-09-26.json` — written

Shape matches `draft_queries_v1.json` (`{"meta": {...}, "queries": [...]}`).
Meta:

```json
{
  "version": "ce11-batch03",
  "frozen": false,
  "n": 14,
  "sha256_of_queries": "f7f796c4278594957ff11cce1cc2422708bb92c8445adf95bdf1f78fec02eb03",
  "sha256_canonicalization": "sha256( '\\n'.join(sorted(query_strings)).encode('utf-8') )",
  "created": "2026-09-26",
  "embed_regime": "BAAI/bge-base-en-v1.5/768d/cuda_fp32/pilot_subset_frozen_v4",
  "universe": "v4 allowlist (95 docs / 826 chunks)",
  "note": "CE-11 diagnostic set for correction batch-03. NOT part of the frozen 40 and NOT a promotion comparator - there is no baseline for these queries.",
  "grading_reference": "eval/results/gold_additions_batch03_2026-09-26.csv"
}
```

`sha256_of_queries` computed with the exact recipe `draft_queries_v1.json`
records for itself, applied to the 14 CE-11 query strings.

Each of the 14 query objects carries **only** `id`, `query`, `theme`, `type`,
`expected_grounding_doc_ids` — verified programmatically that no forbidden
measured field (`routed_topic`, `routed_cos`, `top_chunk_ids`, `grounded`,
`n_after_cutoff`, `top_score`, `top5_scores`, `kept_doc_ids`) leaked in from
the CSV. Sentinel handling confirmed correct:

```
X52 -> []   (RETIRED)
X53 -> []   (RETIRED)
X54 -> []   (OOS)
X50 -> ['BD010', 'BA032']   (multi-doc split correctly)
X51 -> ['BC017', 'BC018']   (multi-doc split correctly)
```

### 12. Confirm the two frozen references are byte-unchanged

```
gold_reference_set.csv sha256:      37259902530d92efab33d0c8620cdf0fa830b25cfff8579d2bb55a11a9a1bca5
  (matches the value recorded in Phase 2's report exactly)

draft_queries_v1.json sha256 (this repo):   a35556fa37f5be05e7bc452063c056a010492c863c81d3e527159af35c6e5c04
draft_queries_v1.json sha256 (source repo): a35556fa37f5be05e7bc452063c056a010492c863c81d3e527159af35c6e5c04
  (identical — the copy in Step 1 did not alter it)
```

**Both confirmed unchanged.**

---

## Summary of files touched this session

**New (copied in, all sha256-verified):**
```
reports/pilot-eval subset/  (27 files)
scripts/run_ops2_c1.py
scripts/verify_v4_transition.py
```

**Renamed (archived), not deleted:**
```
data/index/pilot_dense.npy       -> data/index/_fullcorpus_2026-09-26_pilot_dense.npy
data/index/pilot_dense_meta.json -> data/index/_fullcorpus_2026-09-26_pilot_dense_meta.json
```

**Newly written:**
```
data/index/pilot_dense.npy        (826, 768) — the 95-doc pilot subset, v4-comparable universe
data/index/pilot_dense_meta.json  (95 docs / 826 chunks / pilot_subset_frozen_v4.csv)
eval/results/ce11_queries_2026-09-26.json
```

**Read-only (no writes into `C:\Reachy Mini Project 2026` at any point).**

## FLAG list — final status

| Flag condition | Fired? |
|---|---|
| Centroids still at 3 topics | No — 34, confirmed at the top |
| FROZEN_SHA not matching | No — exact match |
| Allowlist resolving to anything other than 95 documents | No — exactly 95 / 826 chunks |
| Any retired ID | No — checked in runtime index doc_ids and CE-11 gold_source_docs |
| Any hash change to `gold_reference_set.csv` or `draft_queries_v1.json` | No — both confirmed byte-identical |
| Any need to edit a copied script | No — all copies verbatim |
| Anything that would spend tokens | No — $0 throughout, no composer, no API call |

**Additional finding, not on the original flag list:** amendment B's claim
about `make_runtime_dense_index.py` being patched for the console-encoding
issue does not hold under direct inspection — the `--allowlist` feature is
real, the encoding fix is not. Flagged above under Amendment B; not fixed
(no `.py` file was edited this session).

## What this enables next

Per the source document's "What this changes downstream" section: CE-12 is
now `scripts/run_ops2_c1.py C2_post_batch03` — $0, retrieval-only, graded
against the v4.2 canonical numbers (0.588 / 0.882 / 0.941 / 0.971) and the
3/3 health-gate anchors recorded under Amendment D above. Not run in this
phase.
