# CJAP — the remaining work, as sequential Claude Code prompts

**26 Sep 2026.** Everything left between here and a promoted batch-03, in order. Six phases, each one
stops and reports. Do not chain them. Phase 4 is the only one that spends money and it has its own gate.

Interpreter for every command, in every phase:

```
set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe"
```

Python 3.12.13, torch 2.5.1+cu121, CUDA True. **Install nothing.** A bare `python` has no torch.

## Where things stand

| | |
|---|---|
| **Done** | P3.1 encoder · P3.2 dense (9,804 chunks) · P3.2b runtime index (1,104 docs) · P3.4 sparse (9,804) · P3.5 dates (1,104/1,104/0) |
| **Broken** | P3.3 — live centroids are the collapsed `(3, 768)` set |
| **Blocked on P3.3** | CE-11 · CE-12 · CE-13/14 · P3.6 · the R-1 voice-card fix |
| **Not in scope until P6** | C-11 (BC018's stale row) · batch-04's 186 rows · the ~222 missing 2007–2011 columns |

### Why C-11 is not fixed here, having been urged before the embed

Fixing `BC018`'s curated row means editing a **pinned** workbook. `verify_pin.py` hashes those four
sheets against `corpus_snapshot.json`, so touching one now invalidates the pin and makes every index
built this week unattributable. The cheap window — before CE-6 — has closed. It now rides with the P6
merge, where the sheets are re-pinned and everything re-embeds anyway. Gold row **C48** already flags it
so a wrong answer there is not misread as a retrieval failure.

---

## Phase 1 — close P3.3

The full text is in `docs/p3/P3.3_centroid_recovery_prompt_2026-09-26.md`. Paste that file's prompt
block. In one line: archive the collapsed centroids and the two `reports/w1_7_*` files, rename the stale
bge-large `topic_centroids_premerge.npy` aside, restore
`_archived_precollapse_2026-07-17_topic_centroids.*`, then run `merge_tag_topics.py` with
`CJ_TOPIC_MERGE_COSINE=1.01` so nothing merges. Expect `0 pair(s) > 1.01 ... -> 34 -> 34 topics`.

**Do not start Phase 2 until that run reports 34 topics and centroid drift below 1e-6.**

---

## Phase 2 — bring the eval harness into the Final Project Folder

```
Phase 2 — copy the evaluation harness into this repo. No eval is run in this phase.

WHY: the Final Project Folder has no eval code at all. run_arch_baseline_v2.py, run_arch_baseline.py,
run_baseline.py, eval_instrumentation.py and app/service.py exist ONLY in C:\Reachy Mini Project 2026.
That is the same sync gap that made check_date_index.py fail on "No module named 'service'" — a missing
file, not a repo defect. It also means CE-12 cannot run here yet, and must NOT be run over there,
because the working repo's indexes are the pre-correction July ones.

BOUNDARIES
- The working repo C:\Reachy Mini Project 2026 is READ-ONLY in this phase. Copy out of it; write
  nothing into it.
- Copy files; do not edit them. If a copied file needs changing to import, STOP and report instead.
- Do not copy anything not on the list below.

STEPS
1. Copy into this repo, preserving paths:
     app\service.py
     scripts\run_baseline.py
     scripts\run_arch_baseline.py
     scripts\run_arch_baseline_v2.py
     scripts\eval_instrumentation.py
   Report the sha256 of each source and destination and confirm they match.
2. Copy the whole of eval\results\ (90 files) into this repo's eval\results\, including
   gold_reference_set.csv. Report the file count and the sha256 of gold_reference_set.csv.
3. Copy the standing baselines from the working repo root into this repo root:
     baseline.json  arch_baseline.json  arch_baseline_v2.json
   (and their .jsonl siblings if present). Report which exist and their sizes.
4. eval\results\gold_additions_batch03_2026-09-26.csv already exists here from CE-11 drafting. Confirm
   it survived the copy in step 2 and was NOT overwritten. If it was, restore it from
   batch-03\gold_additions_batch03_2026-09-26.csv, which is the same file.

VERIFY — imports only, no eval, no API call
5. %PY% -c "import sys; sys.path.insert(0,'app'); sys.path.insert(0,'scripts'); \
     import config, retrieval, embeddings, service; \
     import run_baseline, run_arch_baseline, run_arch_baseline_v2, eval_instrumentation; \
     print('imports OK')"
   Anything that fails to import is the finding — report the exact traceback and STOP.
6. %PY% scripts\check_date_index.py
   This failed last run only because service.py was missing. It should now run. Report its output.
   If it still fails, report the traceback; do not fix it.
7. %PY% scripts\verify_pin.py must still exit 0. Nothing in this phase touches the corpus, so a
   failure here means something else moved — STOP.

REPORT — docs\p3\p3_eval_harness_import_2026-09-26.md: every file copied with both hashes, the import
result, the check_date_index output, and verify_pin's exit code.

FLAG, DO NOT FIX
- Any hash mismatch · any import failure · verify_pin not exiting 0 · any need to edit a copied file ·
  anything that would write into the working repo.
```

---

## Phase 3 — CE-11: stage the gold additions, do not merge them

```
Phase 3 — stage the CE-11 additions as a SEPARATE run set. $0, no API calls.

CRITICAL: do NOT append the 14 new rows to eval\results\gold_reference_set.csv. Two reasons, both hard:
run_arch_baseline.py carries a FROZEN_SHA gate over that file and a 40-row / 17-column expectation, so
adding rows makes the gate fail and the promotion comparison incomparable; and that file already has an
incident history (eval\results\gold_incident_reconciliation.md). The frozen 40 is the comparator. The 14
additions are diagnostic evidence about batch-03 and are run separately in Phase 5.

STEPS
1. Confirm eval\results\gold_reference_set.csv is byte-identical to the copy in the working repo —
   report both sha256. If they differ, STOP.
2. Validate eval\results\gold_additions_batch03_2026-09-26.csv:
     - same 15 column headers, same order, as gold_reference_set.csv
     - 14 rows, qids A41-X54, no collision with the frozen 40
     - every gold_source_docs id (ignoring the RETIRED / OOS sentinels) exists in corpus\ and is not in
       data\csv\retired_doc_ids.csv
     - every routed_topic appears in the restored 34-topic topic_centroids_meta.json topic_ids
     - retrieved_docs and model_answer are empty in all 14 rows
   Report each check. Any failure: report and STOP.
3. Create eval\results\ce11_run_set_2026-09-26.csv as a copy of the additions file. This is what Phase 5
   runs against, so the additions file itself stays a clean draft.

REPORT — append to the Phase 2 report. No files outside eval\results\ are touched.

FLAG, DO NOT FIX
- gold_reference_set.csv differing from the working repo's · any validation failure · any temptation to
  merge the two files.
```

---

## Phase 4 — CE-12: the promotion eval. **Two stages, and stage two spends money**

```
Phase 4 STAGE ONE — gates only. $0. No tokens are spent in this stage.

run_arch_baseline_v2.py runs gates G1/G2/G3 first and exits before any token spend on failure. Use that.

PRE-FLIGHT — report, then stop on any failure
1. Confirm an API key is available WITHOUT printing it: report only whether ANTHROPIC_API_KEY is set in
   the environment, and whether a .env file exists. Neither repo has a .env today, so if the variable is
   unset, STOP and report — that is the user's to supply, not yours to find, create or guess.
2. Report which baseline file is the standing comparator for this eval (arch_baseline_v2.json is the
   expected answer given the harness version), its build date, and the pipeline settings it records.
   Do not assume; read it and say what it says.
3. Confirm the indexes the eval will read are the corrected ones:
     corpus_dense_meta.json     n_chunks 9804, build_date 2026-09-26
     pilot_dense_meta.json      n_docs 1104, n_chunks 9804
     pilot_sparse_meta.json     n_chunks 9804
     topic_centroids_meta.json  n_topics 34, merged_pairs empty
   Any of these wrong means the eval would measure the wrong thing — STOP.

RUN STAGE ONE
4. %PY% scripts\run_arch_baseline_v2.py --gates-only
   Report every gate's result verbatim, and the harness's own estimate of query count and cost if it
   prints one.

THEN STOP. Do not run the full eval. Report:
5. The gate results, the standing baseline you identified, and your estimate of the token cost of the
   full run (40 queries, Sonnet 4.6 at $3/MTok in, $15/MTok out, per eval_instrumentation.py's RATES).
   The user decides whether to spend it.

FLAG, DO NOT FIX
- Any gate failing · no API key · any index reading a pre-correction value · the harness wanting to
  write to gold_reference_set.csv.
```

Stage two runs only after the user says go:

```
Phase 4 STAGE TWO — the full promotion eval over the frozen 40. THIS SPENDS API TOKENS.
Precondition: stage one's gates all passed AND the user has explicitly approved the spend. If either is
missing, STOP.

STEPS
1. %PY% scripts\run_arch_baseline_v2.py
2. Report actual cost and wall-clock from the run's own output.

VERIFY
3. Diff the new results against the standing baseline, per query and in aggregate: grounding, scope
   decisions, retrieved_docs overlap, decline rate, latency, cost.
4. Call out every query whose retrieved_docs changed, and say which of the 156 batch-03-corrected
   documents is responsible where you can tell. That attribution is the point of the whole exercise.
5. Report any query that got worse, not only the ones that improved.

REPORT — docs\p3\ce12_promotion_eval_2026-09-26.md: the per-query diff, the aggregate movement, the cost,
and a plain statement of whether the corrected corpus should be promoted. Recommend; do not decide.

FLAG, DO NOT FIX
- Any regression · any query where the model answered from a retired ID · cost materially above the
  stage-one estimate · any urge to tune a config knob to improve a number.
```

---

## Phase 5 — the CE-11 supplementary run

```
Phase 5 — run the 14 CE-11 rows as a labelled diagnostic set. Spends tokens; needs the same approval.
Precondition: Phase 4 stage two completed. If not, STOP.

These 14 rows test what batch-03 changed: the merged Centenary chapters, the four repaired documents,
one exact-identifier query for the sparse arm, two temporal queries, two retired-ID probes and an
out-of-scope control. They are NOT part of the promotion comparison — there is no baseline for them.

STEPS
1. Run the same composer path over eval\results\ce11_run_set_2026-09-26.csv, writing results to
   eval\results\ce11_results_2026-09-26.csv. If the harness cannot take an alternative input file
   without being edited, STOP and report — do not edit it.

VERIFY, row by row
2. A41-A43, B44: does the answer use text that only exists post-merge? Name the passage.
3. A45, A46, C47, C48: do the repaired documents answer correctly? C48 is expected to fail on the
   honoree's name — that is the known stale row C-11, not a retrieval fault. Confirm which it is.
4. X49: does G.R. No. 142840 retrieve BA039 in the top 3? This is the sparse arm's proof of life.
5. X50, X51: correct dates, no invented third chapter.
6. X52, X53: a decline, and NO retired ID (BA040, BC009, BC010, BD018, SA085) anywhere in retrieved_docs
   for ANY row of this run or Phase 4's.
7. X54: a warm decline with no legal advice and no firm named.

REPORT — append a CE-11 section to the Phase 4 report, row by row, with a PASS/FAIL and the evidence.

FLAG, DO NOT FIX
- Any retired ID retrieved · X49 missing BA039 · any row that cannot be run without editing the harness.
```

---

## Phase 6 — after CE-12 only

```
Phase 6 — the two changes that were deliberately held until after the promotion eval.
Precondition: CE-12 is reported and the user has accepted or rejected promotion. If not, STOP.

1. R-1, the voice card. Apply docs\p3\voice_card_header_proposed_2026-09-25.md to lines 1-14 of
   corpus\voice\voice_card.md — the block above the first ---, nothing else. Back up the original first.
   The current text tells the model that Haiku routed the question, that there are no embeddings and no
   chunking, and that it received whole documents. All three stopped being true at W1.8, and this block
   is sent with every answer.
   Then re-run the frozen 40 and diff against the Phase 4 results. This is its OWN change with its OWN
   comparison — the corpus is held fixed. Expect a small difference in grounding and decline rate; a
   large one is itself the finding. This spends tokens: get approval first.
2. P3.6, the rest of the voice card. The remaining ~366 lines were written against a 79-document Phase-1
   corpus. Read them and list every passage that assumes a small corpus, whole documents, or the Haiku
   router. Report the list; change nothing beyond item 1. The card's "Identity rule" section is CORRECT
   and stays — CJ Panganiban consented to the robot saying it is him (decision D-042).

FLAG, DO NOT FIX
- Any line of the voice card outside 1-14 · any change bundled with the corpus · spending tokens without
  approval.
```

---

## Not in these phases, and why

| Item | Why it waits |
|---|---|
| **C-11** — BC018's stale curated row | Editing a pinned workbook breaks `verify_pin.py` and makes this week's indexes unattributable. Rides with P6. |
| **C-12** — CA528 truncated at source | Needs the missing text or a retirement decision. Batch-05. |
| **C-13** — the unenforced schema enums | 93% of documents carry a non-enum `stances.confidence`. Neither field reaches an index. Amend the schema now, enforce at P6. |
| **P6** — batch-04's 186 rows | CE-17: a correction runs as its own batch. Merging 186 new documents mid-eval makes CE-12 unreadable. |
| **The ~222 columns, Feb 2007 – Apr 2011** | A sourcing job against the Inquirer archive, not a pipeline job. Batch-05. |
| **`merge_tag_topics.py` hardening** | Make the backup unconditional and refuse input already carrying `merged_from`. After CE-12 — the script is in this batch's attributable path. |
| **`build_centroids.py`** | Banned until after CE-12. Rebuilding the topic map and the corpus together makes the eval unreadable. |
| **Push to `Supervaise-Inc/CJAP`** | Committed on `deliverable/2026-09`, not pushed. The user's call. |

## After all six phases

P6 merges batch-04 → 1,290 documents, 803 columns, all 12 works. That repeats the whole of P3 on the
larger corpus: re-chunk, re-embed, re-index, re-retag, re-eval. On this GPU that is about an hour, not a
day. C-11 and C-13's enforcement fold into it.
