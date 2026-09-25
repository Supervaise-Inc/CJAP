# Repo reconciliation — working repo ↔ Final Project Folder (23 Sep 2026)

Working repo: `C:\Reachy Mini Project 2026` · Base repo: `C:\Users\ASUS\Projects\Supervaise-Reachy-Mini-Project\Final Project Folder`

## 1. DONE — corpus sources: `data/text` is now identical in both (1,104 files)

126 files in the working repo were behind the Final Project Folder and were replaced with the fixed versions:

| Fix | Files | What changed |
|---|---|---|
| D-9 (markup cleanup) | 15 (GC021–GC035) | BOM, ~2,770 `\` escapes and 123 `__bold__` runs removed |
| D-10 (book title in H1) | 111 (40 BA · 8 BB · 18 BC · 20 BD · 25 BE) | H1 is now "# \<Book\> -- Ch. N: …" |

Checks before copying: for every one of the 126 files the alphanumeric word sequence is unchanged apart from the intended H1 title line and the stripped markup — no body text was altered. After copying, 0 of the 1,104 files differ between the repos.

Backups of the working repo's previous versions, plus `change_log.csv` with before/after sha256 for each file, are in
`C:\Reachy Mini Project 2026\backup_data_text_2026-09-23_pre_reconcile\`.

`data/csv` (9 files), `data/index` (29 files) and `data/retired` were already identical in both repos.

## 2. DONE — D-5 (partly): the retrieval and index code is now in the Final Project Folder

Copied from the working repo (all 10 were absent here, so nothing was overwritten):

- `app/embeddings.py`, `app/retrieval.py`, `app/sparse.py`
- `scripts/build_dense_index.py`, `scripts/build_sparse_index.py`, `scripts/build_corpus_dense.py`
- `scripts/build_centroids.py`, `scripts/build_centroids_fullcorpus.py`
- `scripts/check_date_index.py`, `scripts/merge_tag_topics.py`

Checks: each file is byte-identical to the working repo's copy and parses as valid Python. Every `config.*` name they use exists in this folder's `config.py`, so they should run here. **Not yet executed** — the indexes have not been rebuilt.

## 3. OPEN — same file name, different content (needs a human decision; nothing was overwritten)

The Final Project Folder's copies are all dated 20 Sep 2026 (the Pi deployment); the working repo's are from Jun–Aug 2026.

| File | Working (lines, date) | Final (lines, date) | Diff (− / +) |
|---|---|---|---|
| `config.py` | 750, 2026-08-04 | 800, 2026-09-20 | 23 / 73 |
| `app/app.py` | 1,392, 2026-07-19 | 1,920, 2026-09-20 | 153 / 681 |
| `app/cj_chat.py` | 1,345, 2026-07-16 | 1,689, 2026-09-20 | 77 / 421 |
| `app/voice_io.py` | 540, 2026-07-19 | 876, 2026-09-20 | 117 / 453 |
| `app/wake_word.py` | 434, 2026-08-03 | 97, 2026-09-20 | 378 / 41 |
| `app/dashboard.py` | 1,122, 2026-07-16 | 1,111, 2026-09-20 | 11 / 0 |
| `scripts/build_topic_map.py` | 1,047, 2026-06-29 | 1,037, 2026-09-20 | 26 / 16 |
| `scripts/run_smoke_test.py` | 291, 2026-07-16 | 280, 2026-09-20 | 13 / 2 |
| `scripts/check_paths.py` | 149, 2026-06-20 | 149, 2026-09-20 | 5 / 5 |

`app/wake_word.py` is the one to look at first: the Final Project Folder's version is a quarter the size of the working repo's.

## 4. OPEN — files that exist in only one repo

**Only in the working repo (not copied):** `app/service.py`, `app/filler_route.py`, `app/head_orient.py`, `app/voice_job.py`, `app/voice_stream.py`, `app/wake_listen.py`; and 28 `scripts/` files that are benchmarks, evaluations and one-off runs (`run_w2_*`, `run_w3_2_*`, `run_bakeoff_*`, `run_topp*`, `build_pilot_subset_v3/v4`, `eval_instrumentation`, `reconcile_gold`, `preflight_transport`, `bench_stt_backends`, the clip generators, `verify_filler_v5`, `verify_v4_transition`, `check_expand_on_demand`, `run_arch_baseline*`, `run_baseline`, `run_latency_retrieval`, `run_ops2_*`).

**Only in the Final Project Folder:** the voice/answer stack added for the Pi deployment — `app/answer_canned.py`, `answer_filler.py`, `answer_gate.py`, `answer_pipeline.py`, `canned_answers.py`, `cj_voice_cloud.py`, `dynamic_filler.py`, `lang_gate.py`, `main_voice_robot.py`, `postprocess.py`, `speaker_id.py`, `speech_engines.py`, `speech_streaming.py`, `speech_tempo.py`, `stream_speak.py`, `text_entities.py`, `text_language_gate.py`, `usage_meter.py`, `voice_identity.py`, `voice_vad.py`, `wake_test.py`; and `scripts/backfill_alignments.py`, `export_canned_qa.py`, `prerender_canned.py`, `run_dashboard_smoke.py`.

Decide per file whether the evaluation and benchmark scripts belong in the published repo. The two app stacks are different branches of work, not stale copies of each other, so they should be merged deliberately, not overwritten.

## 5. Next

1. Decide the 9 files in §3 (start with `wake_word.py` and `config.py`).
2. Decide which of §4's working-repo-only scripts to bring over.
3. Then D-3 (drop the 27 retired-doc chunks) is unblocked here, since the index builders are now present.
4. The corpus regenerate for D-1 and D-10 still runs in batch-03, followed by re-chunk and re-index.
