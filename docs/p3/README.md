# docs/p3 — index, and a correction to the naming

**26 Sep 2026.** The files in this folder were produced during the batch-03 correction and carry an
**ad-hoc "Phase 1–7" numbering that is NOT in `CJAP_Robot_Project_Plan_v2.xlsx`.** Two schemes got
conflated while they were written:

- **Project Plan sheet**, P0–P11 — the whole-project phases. **P3** is BUILD THE KNOWLEDGE MODEL,
  **P4** is RETRIEVAL RUNTIME (Done), **P5** is COMPOSITION (Done bar P5.7), **P6** is the
  VALIDITY AND SAFETY GATE (not started).
- **`batch-04/BATCH-04_PROMPTS.md`**, its own P5/P6/P7 — the intake runbook: P5 normalise, P6 merge,
  P7 index/eval/promote.
- **Corpus Expansion sheet**, CE-1…CE-18 — the batch runbook, which is what the batch work actually
  follows.

"Phase 6" in these filenames means **none of those**. Read the table before citing anything here.

## What each file actually was

| File | What it really served | Status |
|---|---|---|
| `P3.2_CE-6_runbook.md` | CE-6 for correction batch-03 | reference; §7 ruling corrected in place |
| `P3.2_claude_code_prompt.md` | CE-6 prompt, first cut | **superseded** |
| `P3_next_phase_claude_code_prompt.md` | CE-6 prompt v2 | **superseded** |
| `P3_rulings_and_run_prompts_2026-09-26.md` | env ruling + CE-6 run prompts | **superseded** (prompts A/A2/B) |
| `p3_env_repair_2026-09-26.md` | evidence — the venv audit | **evidence, keep** |
| `p3_2_dense_rebuild_2026-09-25/26.md` | evidence — CE-6 runs | **evidence, keep** |
| `P3.3_centroid_recovery_prompt_2026-09-26.md` | centroid-collapse recovery, v1 | **superseded** |
| `P3.3_recovery_prompt_v2_2026-09-26.md` | the recovery that ran | reference |
| `p3_3_recovery_2026-09-26.md` | evidence — the recovery run | **evidence, keep** |
| `P3.3_assessment_and_Phase3_go_2026-09-26.md` | assessment + amendments | reference |
| `p3_eval_harness_import_2026-09-26.md` | evidence — closed the D-5 eval sync gap | **evidence, keep** |
| `CJAP_remaining_work_claude_code_prompts.md` | my six-phase scheme | **superseded — invented numbering** |
| `Phase3_CE-11_and_comparator_fix_2026-09-26.md` | CE-11 staging + comparator fix | reference |
| `phase3_ce11_staging_2026-09-26.md` | evidence | **evidence, keep** |
| `Phase4_CE-12_prompt_2026-09-26.md` / `_v2_` | **CE-12** for batch-03 | v2 is the one that ran |
| `ce12_promotion_2026-09-26.md` | **evidence — CE-12 result, batch-03 promoted** | **keep, this is the record** |
| `Phase5_CE-11_prompt_2026-09-26.md` | **CE-11** diagnostic for batch-03 | reference |
| `phase5_ce11_diagnostic_2026-09-26.md` | evidence — the 14-row diagnostic | **evidence, keep** |
| `Phase6_prompt_2026-09-26.md` | C3 universe measurement + findings | **superseded — see note below** |
| `phase6_c3_and_findings_2026-09-26.md` | evidence — C3, date-index test, X49 sizing | **evidence, keep** |
| `Phase7_prompt_2026-09-26.md` | universe adjudication + P3 gap sizing | **NOT RUN, and not to be run** |
| `phase7_universe_adjudication_2026-09-26.md` | evidence, if it exists | evidence |
| `voice_card_header_proposed_2026-09-25.md` | **R-1**, staged fix for P3.6 | **live, still unapplied** |

## The part that went wrong, stated plainly

After CE-12 passed for batch-03, the work should have gone to **CE-4 for batch-04**. Instead it went
into the C3 universe measurement, an adjudication of the 95-vs-1,104 retrieval universe, and sizing the
X49 sparse-arm defect. That is P8 (evaluate and tune) territory and partly re-opens P4, which the plan
records as Done across all eight rows.

**`Phase7_prompt_2026-09-26.md` should not be run.** Its Part D was about to re-derive a topic-map
decision that the Corpus Expansion sheet already owns: **CE-7** (orphan census) → **CE-8** (DECIDE —
retag only / expand / rebuild) → **CE-9** (expansion proposal) → **CE-10** (rebuild centroids from
scratch). CE-8 is marked *(human decision — no CC prompt)*.

The current task is **`batch-04/CE-4_to_CE-7_batch04_prompt.md`**.

## Nothing needs reverting

Audited 26 Sep. The one genuinely wrong state — the 34→3 centroid collapse — was already reverted, and
the restore is byte-exact against the v4.2 anchor (`50600bdd34836db7`). Everything else is either
correct, inert, or about to be replaced by CE-6:

| State | Now | Action |
|---|---|---|
| `pilot_dense.npy` | 1,104 docs / 9,804 chunks, full corpus | none — CE-6 archives and replaces it at 1,290 |
| `topic_centroids.npy` | (34, 768), `merge_cosine 1.01`, `merged_pairs 0` | none — this IS the restored state |
| `corpus_dense` / sparse | 9,804 chunks, bge-base | none — CE-6 rebuilds both |
| `config.py` | `DATE_INDEX_ENABLED False`, `TOPIC_MERGE_COSINE 0.95` | none — both untouched defaults; every override was per-process |
| `ops2_c1_drift.json` | C0, C1, C2, **C3** | keep. C2 is batch-03's promotion record. C3 measured a configuration we are not keeping — leave it as append-only evidence, do not delete |
| `_collapsed_*`, `_fullcorpus_*`, `_prebatch04_*`, `_archived_*` | archives | keep — the rollback trail |

## The four scripts added, and which survive batch-04

| Script | Verdict |
|---|---|
| `make_runtime_dense_index.py` | **Keep and use** — CE-6 step 14 depends on it; `build_corpus_dense.py` does not write the runtime index when no prior one exists |
| `run_ce11_diag.py` | **Keep** — repurposable for batch-04's CE-11; it already carries the universe guard that stops a gold-set/universe mismatch scoring zero by construction |
| `run_ops2_c2.py` | archive — a v4-era, 95-doc-allowlist harness; the v4 gold does not survive batch-04 |
| `run_ops2_c3.py` | archive — same |

`run_ops2_c1.py` was never modified and remains the instrument that produced C0 and C1.
