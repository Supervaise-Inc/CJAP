# docs/p3 — what is here, and what was cleared out

**Tidied 26 Sep 2026.** This folder held 25 files, most of them superseded prompts written under an
**ad-hoc "Phase 1–7" numbering that is NOT in `CJAP_Robot_Project_Plan_v2.xlsx`**. Thirteen prompt
documents and two dead scripts were deleted; only run evidence and live artifacts remain.

## The naming mistake, so nobody repeats it

Three numbering schemes were in play and two of them got conflated:

- **Project Plan sheet**, P0–P11 — the whole-project phases. **P3** BUILD THE KNOWLEDGE MODEL ·
  **P4** RETRIEVAL RUNTIME (Done, all 8 rows) · **P5** COMPOSITION (Done bar P5.7) ·
  **P6** VALIDITY AND SAFETY GATE (not started).
- **`batch-04/BATCH-04_PROMPTS.md`**, its own P5/P6/P7 — the intake runbook: normalise, merge, index.
- **Corpus Expansion sheet**, CE-1…CE-18 — what batch work actually follows.

"Phase 6" in the deleted filenames meant none of those. **Batch work follows the CE numbers.**

## What went wrong

After CE-12 passed for batch-03, the work should have gone to **CE-4 for batch-04**. Instead it ran a
C3 universe measurement, an adjudication of the 95-vs-1,104 retrieval universe, and a sizing of the X49
sparse-arm defect — P8 territory that partly re-opens P4. A "Part D" was also drafted to re-derive a
topic-map decision the Corpus Expansion sheet already owns:
**CE-7** orphan census → **CE-8** DECIDE (retag / expand / rebuild) → **CE-9** proposal → **CE-10**
rebuild centroids. CE-8 is marked *(human decision — no CC prompt)*.

**Current task: `batch-04/CE-4_to_CE-7_batch04_prompt.md`.**

## What remains here

| File | Why it stays |
|---|---|
| `P3.2_CE-6_runbook.md` | CE-6 runbook — still applies to batch-04's re-embed |
| `voice_card_header_proposed_2026-09-25.md` | **R-1** — live staged fix for P3.6, still unapplied |
| `ce12_promotion_2026-09-26.md` | **the CE-12 record that promoted batch-03** |
| `p3_env_repair_2026-09-26.md` | evidence — the venv audit |
| `p3_2_dense_rebuild_2026-09-25.md` / `_26.md` | evidence — the CE-6 runs |
| `p3_3_recovery_2026-09-26.md` | evidence — the centroid-collapse recovery |
| `p3_eval_harness_import_2026-09-26.md` | evidence — closed the D-5 eval sync gap |
| `phase3_ce11_staging_2026-09-26.md` | evidence — CE-11 staging |
| `phase5_ce11_diagnostic_2026-09-26.md` | evidence — the 14-row diagnostic |
| `phase6_c3_and_findings_2026-09-26.md` | evidence — C3, the date-index test, X49 sizing |
| `phase7_universe_adjudication_2026-09-26.md` | evidence, if the run produced it |

The `phaseN_*` evidence files keep their names so the commit messages and reports that cite them stay
valid. Read them as run records, not as plan phases.

## CE-11 → CE-14: the gate before the robot is demonstrated

**P6 VALIDITY AND SAFETY GATE has a concrete meaning now.** batch-04 (CE-4 → CE-10) rebuilt the corpus
and the taxonomy; Phase 8 (post-batch-04) wired the robot to be *able* to run the retrieval stack behind
`config.CJ_PIPELINE`, default `legacy`. **CE-11 → CE-14 is what has to pass before `CJ_PIPELINE=retrieval`
becomes that default** — validating the retrieval stack against a gold set on the full 1,290-document
corpus, not the 95-document `pilot_subset_frozen_v4` universe several `eval/` scripts still assume. Three
open numbers it has to beat or explain, carried forward from `batch-04/BATCH-04_REPORT.md`:

- **Routing top-1 86.7%** on the 30-dimension taxonomy, with `twin_beacons_doctrine` — the project's
  flagship concept — among the four dimensions that never win their own question.
- **The frozen-40 drift**: 14 of 40 selected result sets changed after the move to the 30-dimension map,
  gold hit@10 down 2.9 points (hit@1/3/5 unchanged).
- **`arch_baseline_v2` is not the comparator** — it carries `universe: 827` and predates bge-base
  entirely. CE-11 needs a fresh baseline taken on the current 1,290-document universe before any
  before/after comparison means anything.

See `docs/architecture/PIPELINES.md` and `docs/architecture/PARITY_MATRIX.md` for what `CJ_PIPELINE=retrieval`
does and does not yet do relative to the pipeline the robot has run for months.

## Deleted (recoverable from git history — all were tracked and committed)

```
P3.2_claude_code_prompt.md              P3.3_centroid_recovery_prompt_2026-09-26.md
P3_next_phase_claude_code_prompt.md     P3.3_recovery_prompt_v2_2026-09-26.md
P3_rulings_and_run_prompts_2026-09-26.md  P3.3_assessment_and_Phase3_go_2026-09-26.md
CJAP_remaining_work_claude_code_prompts.md
Phase3_CE-11_and_comparator_fix_2026-09-26.md
Phase4_CE-12_prompt_2026-09-26.md       Phase4_CE-12_prompt_v2_2026-09-26.md
Phase5_CE-11_prompt_2026-09-26.md       Phase6_prompt_2026-09-26.md
Phase7_prompt_2026-09-26.md             scripts/run_ops2_c2.py   scripts/run_ops2_c3.py
```

`git log --diff-filter=D --name-only` finds them; `git show <commit>^:<path>` restores one.

**`run_ops2_c2.py` / `run_ops2_c3.py`** were v4-era harnesses pinned to the 95-document allowlist and
the v4 gold — neither survives batch-04. `run_ops2_c1.py` was never modified and stays.

## Scripts added during this work that DO survive

| Script | Why |
|---|---|
| `scripts/make_runtime_dense_index.py` | **CE-6 depends on it.** `build_corpus_dense.py` does not write the runtime index when no prior one exists, so the app would have no index without this |
| `scripts/run_ce11_diag.py` | repurposable for batch-04's CE-11; carries the universe guard that stops a gold-set/universe mismatch scoring zero by construction |

## `data/index/` was tidied by MOVING, not deleting

`data/index/` is **not tracked by git**, so a delete there is permanent. 32 archive and bake-off files
were moved into **`data/index/_archive/`** instead. Twelve live files remain at the top level.

Nothing in `app/` or `scripts/` reads the moved paths — checked. Two references are worth knowing:

- `scripts/verify_v4_transition.py:153` records the P3.1 rollback as *"restore
  `data/index/_archived_bgelarge_*` over production names"* — those files are now under `_archive/`.
- `scripts/build_centroids_fullcorpus.py` used to write `_archived_pilotmm_*` at the top level. CE-10 rewrote it: it now
  builds centred centroids from scratch and REFUSES to overwrite existing centroid files (archive first, by moving).

**Do not delete `_archive/`.** It holds the only rollback for the ratified encoder and the promoted
arch-baseline-v4.2 artifacts, all three sha-verified:

```
_archived_precollapse_2026-07-17_topic_centroids.npy   50600bdd34836db7   = v4.2 topic_centroids
_archived_precorrection_2026-07-17_pilot_dense.npy     0ec7d6f64d3c5b14   = v4.2 pilot_dense
_archived_precorrection_2026-09-22_corpus_dense.npy    df5ca465c954e218   = v4.2 corpus_dense
_archived_bgelarge_* · _archived_pilotmm_* · bakeoff_* = P3.1's "archive the alternatives with a
                                                          rollback", which is a Done-when bullet
```

---

## CE-10 (27 Sep 2026) — the build order, recorded because the order is the fix

**map → centroids → tag all 1,290 documents → `apply_topic_paths` → re-pin (`build_corpus_snapshot.py`) → refresh
`chunk_index.json`.** The pin comes LAST. Pinning before the apply step is what wiped the `topic_paths` backfill on every
earlier regeneration and left 0 of 1,104 documents tagged (P3.3); the pin is over the source xlsx, but the regeneration that
follows a re-pin rewrites the corpus JSONs, so anything applied before it is lost. Run in this order, every time the taxonomy
changes:

| # | step | command | what it must show |
|---|---|---|---|
| 0 | corpus mean (once) | `scripts/build_corpus_mean.py` | writes `data/index/corpus_mean.npy`; refuses to overwrite a differing file |
| 1 | archive v1 artifacts | *move* (never delete) into `data/index/_archive/` with a dated prefix | `_v1_pre-CE10_2026-09-27_*` |
| 2 | topic map | `scripts/build_topic_map.py` | `len(load_docs()) == 1290`, `taxonomy_version: 2`, doc_counts = the proposal's Table 1 |
| 3 | centroids, from scratch, centred | `scripts/build_centroids_fullcorpus.py` | meta records the mean's sha256, `n_chunks`, `corpus_dense_build_date` |
| 4 | independence check + tag ALL documents | `scripts/merge_tag_topics.py <date>` | 0 pairs above `TOPIC_MERGE_COSINE`; `n of 1,290` tagged; `reports/topic_tags_full_<date>.json` |
| 5 | per-document `topic_paths` | `scripts/apply_topic_paths.py` (now includes `books/**`, writes LF) | 1,290 of 1,290 files carry `topic_paths` |
| 6 | **re-pin** | `scripts/build_corpus_snapshot.py`, then `scripts/verify_pin.py` | `PASS — 1295 docs` (1,290 + 5 retired ids) |
| 7 | refresh `chunk_index.json` | `scripts/chunk_corpus.py` | `chunks.jsonl` byte-identical; only `source_snapshot` changes; update the four metas that record its sha256 |

**Centring.** Every cosine that touches a centroid is on vectors centred on `data/index/corpus_mean.npy`, loaded only through
`app/centering.py`, which raises if the file is missing or its sha256 disagrees with `corpus_mean.sha256` in
`topic_centroids_meta.json` (three sites: the centroid build, `retrieval._load_pilot()`, `retrieval.route()`; plus the tagger).
There is no fallback to raw. The dense retrieval arm still uses raw vectors. `TOPIC_MERGE_COSINE` (0.75),
`TOPIC_ASSIGN_MIN_COSINE` (0.31) and `OUT_OF_SCOPE_THRESHOLD` (0.12) are centred values; do not compare them with the v1 raw ones.

**Archived by this phase (moved, not deleted):** `data/index/_archive/_v1_pre-CE10_2026-09-27_topic_centroids.npy`,
`..._topic_centroids_meta.json`, `..._topic_centroids_premerge.npy`; the v1 map is kept beside the new one as
`corpus/voice/topic_map_v1_2026-05-25.json`. `data/index/corpus_mean.npy`, `topic_centroids.npy` and `topic_centroids_meta.json`
are force-tracked (the rest of `data/index/` stays git-ignored) because the load-time sha256 check ties the three together.
