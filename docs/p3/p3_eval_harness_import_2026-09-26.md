# Phase 2 — evaluation harness copy-in

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Outcome:** **Copy complete, all hashes match. Imports pass. `verify_pin.py` still exits 0.
One VERIFY step (6) surfaced a second, previously-unknown missing dependency — reported,
not fixed, not copied (out of scope for this phase's file list).**

Source repo `C:\Reachy Mini Project 2026` was read from only. `git status` confirms
nothing was written there; every change below lands inside this repo.

---

## STEP 1 — five harness files, preserving paths

| File | Source sha256 | Dest sha256 | Match |
|---|---|---|---|
| `app/service.py` | `c2fbfafb615b0654e9284118c2cab4137ebfb97b3b7f0aec6e62893389883ab4` | same | ✅ |
| `scripts/run_baseline.py` | `4bb0711be8fcbfae0b3d7268f10bcc4ba18d8d2c8da49629981dfd211011f28a` | same | ✅ |
| `scripts/run_arch_baseline.py` | `755c96d92df17abeb5efefa3d8ed12af9de631da27f6623446360e5ca477ef6f` | same | ✅ |
| `scripts/run_arch_baseline_v2.py` | `f2259f511f51f2c08421f155bf88e6bb461afab3864ddf69c2e4ae6db3cbf827` | same | ✅ |
| `scripts/eval_instrumentation.py` | `6cdc783b938e87bab0e94aa7944cb91ea6e84dfd7cc4acc9df1a1d003c6d5367` | same | ✅ |

All five copied with `cp -p` (paths preserved), **not edited**. All five hashes match
exactly between source and destination.

## STEP 2 — `eval/results/` wholesale

**Discrepancy from the prompt: source has 94 files recursively, not 90.**

```
top-level files:        87
eval/results/incoming/:      1 file
eval/results/postreboot/:    3 files
eval/results/stt_bench_clips/: 3 files
                              ---
TOTAL:                       94
```

Copied all 94 (whole directory, `cp -Rp`), all 94 now present at
`eval/results/` in this repo. Not reconciled against the stated 90 — flagged
here rather than silently accepted or "corrected."

`gold_reference_set.csv` sha256: `37259902530d92efab33d0c8620cdf0fa830b25cfff8579d2bb55a11a9a1bca5`
— **identical** between source and destination.

## STEP 3 — standing baselines

All six files (3 base names × `.json`/`.jsonl`) existed at source and were
**absent** at this repo's root before this phase — no overwrite risk.

| File | Size (bytes) | Hash match |
|---|---|---|
| `baseline.json` | 1,529 | ✅ |
| `baseline.jsonl` | 5,974 | ✅ |
| `arch_baseline.json` | 46,978 | ✅ |
| `arch_baseline.jsonl` | 31,882 | ✅ |
| `arch_baseline_v2.json` | 113,636 | ✅ |
| `arch_baseline_v2.jsonl` | 45,626 | ✅ |

## STEP 4 — `gold_additions_batch03_2026-09-26.csv`

**Correcting the prompt's premise:** this file did **not** already exist inside
`eval/results/` in this repo before this phase — `eval/` did not exist at all
here until STEP 2's copy created it. The premise "already exists here from
CE-11 drafting" does not hold for `eval/results/` specifically, though the
file genuinely does exist at `batch-03/gold_additions_batch03_2026-09-26.csv`
(dated 2026-09-26 00:15), exactly as the prompt's fallback path names.

What actually happened: the **source** repo's `eval/results/` already
contained `gold_additions_batch03_2026-09-26.csv` (same 2026-09-26 00:15
timestamp), so it arrived in this repo's `eval/results/` via the STEP 2
bulk copy — nothing was overwritten, because nothing was there first.

**Confirmed sha256-identical to the `batch-03/` copy** — "the same file,"
exactly as the prompt states:

```
9d085462997965ee44c1a86579aebc0b35ae0b45fbc49ecea7160aff35b8253e
  eval/results/gold_additions_batch03_2026-09-26.csv
  batch-03/gold_additions_batch03_2026-09-26.csv
```

No restore was needed.

---

## VERIFY 5 — imports only

```
python -c "import sys; sys.path.insert(0,'app'); sys.path.insert(0,'scripts'); \
  import config, retrieval, embeddings, service; \
  import run_baseline, run_arch_baseline, run_arch_baseline_v2, eval_instrumentation; \
  print('imports OK')"

imports OK
EXIT=0
```

**PASS.** All eight modules import cleanly through the pinned venv
(`C:\Reachy Mini Project 2026\.venv\Scripts\python.exe`). No API call, no
eval run.

## VERIFY 6 — `check_date_index.py`

The `service` import now resolves (confirmed — this was the exact failure
from the P3.4/P3.5/P3.3 report, now fixed by this phase's copy). Output:

```
=== COVERAGE ===
docs 1104 | dated 1104 | undated 0
precision: {'day': 1104}
by source-class x precision: {'B:day': 131, 'C:day': 785, 'G:day': 35, 'S:day': 153}
undated doc_ids: []

=== IDEMPOTENCY GATE === rebuild sha == original: True (82a550e69c34)

Traceback (most recent call last):
  File "scripts/check_date_index.py", line 93, in <module>
    raise SystemExit(main())
  File "scripts/check_date_index.py", line 39, in main
    Q = json.loads((ROOT / "reports/pilot-eval subset/draft_queries_v1.json").read_text(...))["queries"]
FileNotFoundError: [Errno 2] No such file or directory:
  '...\\Final Project Folder\\reports\\pilot-eval subset\\draft_queries_v1.json'
EXIT=1
```

**The COVERAGE and IDEMPOTENCY GATE sections both ran and both pass**
(1104/1104/0, sha256 `82a550e69c34...` matches the P3.5 build — confirmed
identical, no drift). The script then fails on its third check ("NO-REGRESSION
GATE"), which needs `reports/pilot-eval subset/draft_queries_v1.json` — **a
second, different missing dependency, not on this phase's copy list.**
Per this phase's boundaries ("Do not copy anything not on the list below"),
I did not copy it, even though it exists at the source
(`C:\Reachy Mini Project 2026\reports\pilot-eval subset\draft_queries_v1.json`,
38,741 bytes, dated Jun 30). **Flagged, not fixed.** The prompt's framing —
"This failed last run only because service.py was missing... it should now
run" — was half right: `service.py` was the first blocker and is now
resolved, but it was not the only one.

## VERIFY 7 — `verify_pin.py`

```
[verify_pin] PASS — 1109 docs across 4 source files match corpus_snapshot.json.
EXIT=0
```

**PASS.** Nothing in this phase touched the corpus; the pin holds.

---

## Summary of files copied into this repo

```
app/service.py
scripts/run_baseline.py
scripts/run_arch_baseline.py
scripts/run_arch_baseline_v2.py
scripts/eval_instrumentation.py
eval/results/  (94 files, including gold_reference_set.csv and
                gold_additions_batch03_2026-09-26.csv)
baseline.json, baseline.jsonl
arch_baseline.json, arch_baseline.jsonl
arch_baseline_v2.json, arch_baseline_v2.jsonl
```

All copies verified byte-identical to source by sha256 (or, for the bulk
`eval/results/` copy, spot-verified via `gold_reference_set.csv` and
`gold_additions_batch03_2026-09-26.csv`, plus a matching recursive file
count). No file was edited. No eval was run. No API call was made.
`C:\Reachy Mini Project 2026` was not written to — confirmed by inspection;
nothing in this phase's operations targeted it as a destination.

## FLAG list — what fired

| Flag condition | Fired? | Detail |
|---|---|---|
| Any hash mismatch | No | All spot-checked hashes matched exactly |
| Any import failure | No | All eight modules import cleanly |
| `verify_pin` not exiting 0 | No | Exit 0, 1109 docs match |
| Any need to edit a copied file | No | All copies verbatim |
| Anything that would write into the working repo | No | Read-only throughout |

**Additional findings not on the original flag list, reported for completeness:**

1. **Source file count is 94, not 90** for `eval/results/` (STEP 2) — copied
   in full regardless, per "copy the whole of."
2. **A second missing dependency** blocks `check_date_index.py`'s third check:
   `reports/pilot-eval subset/draft_queries_v1.json`. This file was not on
   this phase's copy list and was not copied. If the NO-REGRESSION GATE check
   is needed, that's a follow-up decision — not made here.

## Open items carried forward (unchanged by this phase)

- The centroid collapse from the P3.4/P3.5/P3.3 report (34→3 topics) is
  still live; `data/index/topic_centroids.npy` still holds the 3-topic
  result. The archived rollback candidate
  (`_archived_precollapse_2026-07-17_topic_centroids{.npy,_meta.json}`) is
  still in place, unrestored.
- The `retrieval.run(..., set())` empty-allowlist `ValueError` from the
  P3.2b smoke test is unresolved — what value means "the full corpus,
  unrestricted" is still an open question.
- `scripts/make_runtime_dense_index.py:185`'s console-encoding false-negative
  exit code is still unfixed.
