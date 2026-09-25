> **Prompt 0 is DONE (26 Sep) and needed no repair. Prompts A / A2 / B here are REPLACED by
> `docs/p3/P3_rulings_and_run_prompts_2026-09-26.md`.** The "3.11.9" venv named in Prompt 0 was
> the wake-word environment; the approved interpreter is Python 3.12.13 at
> `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe`. Install nothing. Read the rulings file.

# P3 — next phase: paste-ready Claude Code prompts

**Written 26 Sep 2026. Supersedes `docs/p3/P3.2_claude_code_prompt.md`** (25 Sep), which was written
before Claude Code's pre-flight found the environment broken and before the pilot-index consequence was
understood. Where the two disagree, this file wins.

Four prompts, run in order. Each one **stops and reports**; do not chain them.

| | What | Ends at |
|---|---|---|
| **0** | Repair the Python environment | a working `torch.cuda.is_available()` and a model that loads offline |
| **A** | P3.2 / CE-6 — full-corpus dense re-embed | `corpus_dense.npy` at 9,804 × 768 |
| **A2** | P3.2b — restore the runtime dense index | `pilot_dense.npy` + meta, retrieval live again |
| **B** | P3.4 sparse · P3.5 dates · P3.3 retag | three indexes rebuilt on the new matrix |

Run everything in the **Final Project Folder**
(`C:\Users\ASUS\Projects\Supervaise-Reachy-Mini-Project\Final Project Folder`).

---

## What changed since the 25 Sep prompt — read this before pasting anything

**1. The environment is broken, not merely unconfigured.** The pre-flight found `torch 2.11.0+cpu`, no
`sentence_transformers`, and the GPU invisible to Python. A CPU run of 9,804 chunks benchmarks at
~0.27 chunks/s — about ten hours. Prompt 0 exists so that cost is a choice, not an accident.

**2. `huggingface.co` returns 403 from this network.** Nothing may be downloaded. The model is already on
disk, in full sentence-transformers layout:

```
C:\Reachy Mini Project 2026\models\bge-base-en-v1.5
    config.json  modules.json  config_sentence_transformers.json
    sentence_bert_config.json  tokenizer.json  vocab.txt  special_tokens_map.json
    model.safetensors            437,955,512 bytes
    1_Pooling\config.json
```

Two things to know about it. It was saved by sentence-transformers 2.2.2, and its `modules.json`
declares a third module `2_Normalize` **whose directory is not present**. Modern sentence-transformers
constructs `Normalize` without reading that path, so this is expected to be harmless — but it is exactly
the kind of thing that fails on module load, ten seconds in, so Prompt 0 smoke-tests it rather than
assuming.

**3. The pilot-index finding — the important one.** The 25 Sep prompt claimed that with
`pilot_dense.npy` absent, `build_corpus_dense.py` "derives a fresh pilot slice from the new matrix".
**It does not.** Read `scripts/build_corpus_dense.py` lines 155–192: `new_pilot` is initialised to
`None` and is only assigned inside `if Path(config.DENSE_INDEX_PATH).exists():`. With no prior pilot
index the parity gate is skipped *and the whole pilot write is skipped too*. The closing line still
prints `pilot sliced+overwritten`; in this case that line is false.

That matters because the **runtime reads the pilot index, not the corpus matrix**:

```
app/embeddings.py:133   matrix = np.load(config.DENSE_INDEX_PATH)      # data/index/pilot_dense.npy
app/embeddings.py:134   meta   = json.loads(... DENSE_INDEX_META_PATH)
app/retrieval.py:54     _PILOT = (mat, meta["chunk_ids"], meta["doc_ids"], mat @ cen.T)
```

So after Prompt A succeeds, retrieval is **offline** until Prompt A2 runs.

And the fix proposed in §7 of the runbook — point `CJ_DENSE_INDEX_PATH` at `corpus_dense.npy` — **is
wrong and must not be used.** The corpus meta that `build_corpus_dense.py` writes has no `doc_ids` key,
so `app/retrieval.py:54` raises `KeyError: 'doc_ids'`. Prompt A2 runs
`scripts/make_runtime_dense_index.py` instead, which copies the matrix and writes a meta in the schema
retrieval actually expects. It has been added to the repo and its guards have been tested against the
current stale matrix: it refused and wrote nothing.

**4. The cleanup block is destructive.** `build_corpus_dense.py` ends with
`except Exception: for p in out: <unlink>` where `out` includes `CORPUS_DENSE_PATH`. A late failure
deletes the existing matrix. Backing it up is **mandatory**, not advisory.

**5. Making the runtime universe the full corpus is a real decision.** Today's runtime index is the
frozen 95-document pilot subset (827 chunks). Prompt A2 replaces it with all 1,104 documents / 9,804
chunks. That is what "the answer pipeline should have all the books, columns, biography and speeches"
requires, and it is recorded in the new meta's `allowlist_version`. Say so in the report; it belongs in
the decisions register, not buried in an index file.

---

## Prompt 0 — repair the environment

```
Repair the Python environment for the CJAP dense re-embed. Do not run any index build in this prompt.

BOUNDARIES
- Touch only the virtual environment. Do not edit any .py file in the repo, do not edit config.py,
  do not write anything into data/index/ or corpus/.
- The network cannot reach huggingface.co (403). Do NOT attempt a model download, and do not work
  around the block. The model is already on disk (see step 4).
- Do not upgrade or downgrade numpy, pandas or openpyxl beyond what pip must do to satisfy torch.
  Report the before/after version of each. Other scripts in this repo read pickles and xlsx written
  under the current versions.

PRE-FLIGHT — report every value
1. python --version (must be 3.11.9), the venv path, and whether it is activated.
2. pip show torch sentence-transformers transformers numpy  — report version or "absent" for each.
3. nvidia-smi — driver version, GPU name, total and free VRAM. If nvidia-smi is missing or reports no
   device, STOP and report: there is no GPU path on this machine and the CPU decision is the user's.

INSTALL
4. Into the 3.11.9 venv, in this order:
       pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.5.1+cu121
       pip install transformers==4.44.2 sentence-transformers==3.0.1
   cu121 supports the GTX 1650 (Turing, sm_75). If pip resolves a different torch build, STOP and
   report rather than accepting a +cpu wheel.

VERIFY — all must hold, report each
5. python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(),
   torch.cuda.get_device_name(0))"
   Expect 2.5.1+cu121, 12.1, True, and the GTX 1650. If is_available() is False, STOP and report the
   reason (driver too old for cu121 is the usual one).
6. Offline model load smoke test — this is the check that matters, and it takes seconds:
       set HF_HUB_OFFLINE=1
       set TRANSFORMERS_OFFLINE=1
       python -c "from sentence_transformers import SentenceTransformer as S; \
         m=S(r'C:\Reachy Mini Project 2026\models\bge-base-en-v1.5', device='cuda'); \
         v=m.encode(['rule of law'], normalize_embeddings=True); \
         print(v.shape, float((v[0]**2).sum()))"
   Expect (1, 768) and a squared norm of 1.0. Report the actual numbers.
   The snapshot's modules.json lists a 2_Normalize module whose directory is absent. If the load fails
   on that, report it exactly and STOP — do not create the directory, do not edit modules.json.
7. Re-run pip show for numpy and report whether torch changed it.

REPORT — write docs/p3/p3_env_repair_<YYYY-MM-DD>.md
8. Every value from 1-7, the exact pip commands run, and the final versions of
   torch / transformers / sentence-transformers / numpy.

FLAG, DO NOT FIX
- cuda.is_available() False after install · pip resolving a +cpu torch · the model failing to load ·
  numpy being moved to a major version · any suggestion to download from the hub.
Report and stop.
```

---

## Prompt A — P3.2 / CE-6, the full-corpus dense re-embed

```
P3.2 / CE-6 — full-corpus dense re-embed after correction batch-03.
Run scripts/build_corpus_dense.py UNCHANGED. Do not modify it.
Precondition: docs/p3/p3_env_repair_<date>.md exists and step 5 reported cuda.is_available() True.
If it does not, STOP.

BOUNDARIES
- Read-only: corpus/, data/text/, data/csv/*.xlsx, corpus_snapshot.json. Never edit them.
- Write only inside data/index/ and a new report at docs/p3/p3_2_dense_rebuild_<YYYY-MM-DD>.md.
- Do NOT run build_centroids.py or build_centroids_fullcorpus.py. Batch-03 is a correction; the topic
  map is not what changed, and rebuilding it in the same run makes CE-12 uninterpretable.
- Do NOT edit corpus/voice/voice_card.md. A staged fix exists at
  docs/p3/voice_card_header_proposed_2026-09-25.md and waits until after CE-12.
- Do NOT restore data/index/_archived_precorrection_2026-07-17_pilot_dense*. They were archived on
  purpose — see PRE-FLIGHT 4.
- One encoder, one dimensionality for the whole corpus. If anything forces a different model, dim or
  backend mid-run: STOP.

PRE-FLIGHT — report every value, then stop if any check fails
1. config: EMBED_MODEL_ID == "BAAI/bge-base-en-v1.5", EMBED_DIM 768, EMBED_NORMALIZE True. Ratified by
   the Sponsor at P3.1 (bakeoff_FINAL_for_dok.md). Do not change them.
2. corpus/index/chunk_index.json: expect 1,104 documents and 9,804 chunks; cross-check that
   corpus/index/chunks.jsonl has 9,804 lines. If either reads 8,887 or 9,865 you are on an old chunk
   set — STOP.
3. python scripts/verify_pin.py must exit 0 before you start. If it does not, STOP: the corpus is not
   in its pinned state and nothing built from it would be attributable.
4. data/index/pilot_dense.npy must NOT exist. It was built on 17 July, before batch-03 changed 18 of
   the 95 pilot-subset documents; with it present the parity gate raises RuntimeError AFTER the whole
   embed completes. With it absent the script records
   sanity = "skipped (no prior pilot index)" and — CORRECTED 26 Sep — writes NO pilot index at all,
   because new_pilot stays None. Its closing line "pilot sliced+overwritten" is wrong in that case.
   Expect no pilot index after this prompt; Prompt A2 creates it. If pilot_dense.npy has reappeared,
   move it aside — do not delete it.
5. Model resolution: report which of CJ_EMBED_MODEL_PATH / HF cache / hub will be used, and say so
   explicitly. It must resolve to the local directory
   C:\Reachy Mini Project 2026\models\bge-base-en-v1.5 with HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1
   set. If it would reach the hub, STOP — the network returns 403 and a silent fallback wastes the run.
6. Backend: report EMBED_BACKEND, torch.cuda.is_available(), device name and free VRAM. Default is
   cuda_fp32 with EMBED_BATCH_SIZE 8, sized for a GTX 1650. If CUDA is not available, STOP and ask —
   cpu_fp32 is ~0.27 chunks/s on this machine (about ten hours) and the resume checkpoint is keyed on
   the backend, so a CPU run cannot later be resumed on GPU.
7. MANDATORY BACKUP. Copy data/index/corpus_dense.npy and corpus_dense_meta.json to
   data/index/_archived_precorrection_<their mtime date>_* BEFORE anything runs. This is not
   housekeeping: build_corpus_dense.py ends with `except Exception: for p in out: unlink(p)` and `out`
   includes CORPUS_DENSE_PATH, so a late failure DELETES the existing matrix. That matrix is the
   rollback. Report the exact backup paths.

RUN
8. python scripts/build_corpus_dense.py
   Stream progress. If interrupted, the checkpoint resumes — do not change the model, backend or
   normalize flag between attempts or the checkpoint is discarded and the run starts over.

VERIFY — all must hold
9.  data/index/corpus_dense_meta.json:
       model_id == "BAAI/bge-base-en-v1.5" · dim == 768 · n_chunks == 9804
       backend  == the backend you ran
       pilot_parity_sanity == "skipped (no prior pilot index)"
10. corpus_dense.npy shape == (9804, 768), dtype float32, every row unit-norm
    (max |‖v‖ − 1| < 1e-5). Report the actual max deviation.
11. The chunk_ids in the meta match corpus/index/chunks.jsonl exactly — same set, same order.
12. CORRECTED 26 Sep: data/index/pilot_dense.npy is expected to be ABSENT after this prompt. Confirm
    that it is. If it exists, something re-created it and the two indexes may disagree — STOP.
13. Spot-check semantics, not just shapes. Embed "What did he say about the rule of law?" with
    config.EMBED_QUERY_PREFIX, take the top 5 chunks by cosine against the new matrix, print their
    doc_ids and titles. They should be plausibly about the rule of law. If they look random, the prefix
    or the normalisation is wrong — STOP.

REPORT — write docs/p3/p3_2_dense_rebuild_<date>.md
14. Every pre-flight value, backend and device, wall-clock, chunks/s, verify results 9-13, and the exact
    paths of the archived rollback files.

FLAG, DO NOT FIX
- Any failed pre-flight · CUDA unexpectedly absent · the model resolving to a hub download ·
  n_chunks != 9804 · any non-unit-norm row · a parity value other than "skipped (no prior pilot index)".
Report and stop. Do not rebuild the topic map, re-chunk, or edit the corpus.
```

---

## Prompt A2 — P3.2b, restore the runtime dense index

```
P3.2b — make the runtime dense index from the new full-corpus matrix.
Precondition: docs/p3/p3_2_dense_rebuild_<date>.md exists and every check passed. If not, STOP.

WHY: app/embeddings.load_dense_index() reads config.DENSE_INDEX_PATH (data/index/pilot_dense.npy), not
corpus_dense.npy, and app/retrieval.py:54 reads meta["chunk_ids"] AND meta["doc_ids"]. P3.2 wrote no
pilot index, so retrieval is offline right now. Pointing CJ_DENSE_INDEX_PATH at corpus_dense.npy does
NOT work — that meta has no doc_ids key and retrieval raises KeyError. Do not try it.

BOUNDARIES
- Run scripts/make_runtime_dense_index.py as it is. Do not edit it, and do not hand-write an index.
- Write only data/index/pilot_dense.npy, data/index/pilot_dense_meta.json, their backups, and the
  report. Nothing else.
- No re-embedding. The runtime index is a copy of the corpus matrix so the two stay bit-identical.

STEPS
1. python scripts/make_runtime_dense_index.py
   It verifies before it writes: shape vs chunk_ids, dim vs EMBED_DIM, model_id vs config, unit norms,
   every chunk_id resolvable in chunks.jsonl, no extra chunks, and no retired doc_id present. On any
   failure it writes nothing and exits non-zero. If it exits non-zero, STOP and report the message
   verbatim — it is telling you the matrix and the chunk store disagree.

VERIFY
2. data/index/pilot_dense_meta.json: n_docs == 1104, n_chunks == 9804, dim == 768,
   model_id == "BAAI/bge-base-en-v1.5", len(chunk_ids) == len(doc_ids) == 9804,
   allowlist_version reads "full-corpus (no allowlist; supersedes pilot_subset_frozen_v4)".
3. None of BA040, BC009, BC010, BD018, SA085 appears in doc_ids. (The script checks this; confirm it.)
4. End-to-end smoke test through the real code path, not numpy directly:
       python -c "import sys; sys.path.insert(0,'app'); import retrieval; \
         r=retrieval.run('What did he say about the rule of law?', set()); print(r)"
   Report what comes back. If it raises KeyError 'doc_ids' the meta is wrong; if it raises on the
   centroids, note it and continue to Prompt B — the centroids are stale until P3.3 retags.

REPORT — append a "P3.2b runtime index" section to the same docs/p3/ report
5. The counts from 2, the retired-ID check from 3, the smoke-test output, and the backup paths printed
   by the script.
6. State plainly, in one line, that the runtime retrieval universe has moved from the frozen 95-document
   pilot subset to all 1,104 documents, and that this needs an entry in the decisions register.

FLAG, DO NOT FIX
- The script exiting non-zero · any retired ID present · n_docs != 1104 · retrieval raising anything
  other than the known stale-centroid case.
```

---

## Prompt B — P3.4, P3.5, P3.3

```
P3.4, P3.5 and P3.3 — the remaining index builds on top of the new dense matrix.
Precondition: Prompt A2 finished and the runtime index verifies. If not, STOP.

BOUNDARIES — as before. Read-only corpus/, data/text/, data/csv/. Write only data/index/ and the
report. Do NOT rebuild centroids. Do NOT edit voice_card.md. Do NOT change any config flag.

STEPS
1. python scripts/build_sparse_index.py     # P3.4 — BM25 + atomic-phrase dictionary
2. python scripts/build_date_index.py       # P3.5
3. python scripts/check_date_index.py       # P3.5 verification — must pass
4. python scripts/merge_tag_topics.py       # P3.3 / CE-7 — RETAG ONLY against the existing 34
                                            # centroids. Never build_centroids.py.

VERIFY
5. Sparse: data/index/pilot_sparse_meta.json n_chunks == 9804 (it read 9,865 before — that was the
   pre-correction chunk set, including the 27 chunks of the 5 retired IDs). Report n_phrases and any
   chunk with no terms. Note the file is named "pilot_" for historical reasons but has always covered
   the full corpus.
6. Dates: report how many of the 1,104 documents resolve to a date and list any that do not. Every
   corpus document now carries a text YYYY-MM-DD date after batch-03, so the expected answer is 1,104.
   DATE_INDEX_ENABLED is false in config; building the index does not enable it and whether to enable
   it is a separate decision. Do not flip the flag.
7. Retag: report the orphan census — documents whose best centroid cosine falls below the config floor
   — and the count per topic, and diff the per-topic counts against the previous tagging. Do NOT act on
   it. CE-8 is a human decision, and for a correction batch the answer is already "retag only".

REPORT — append to the same docs/p3/ report, or a sibling file: counts, timings, the sparse and date
coverage numbers, and the retag diff.

FLAG, DO NOT FIX
- Any script that wants to rebuild centroids · sparse coverage below 9,804 · any document with no date ·
  any prompt to change a config flag · any retired ID appearing in any index.
```

---

## After Prompt B

**CE-11 is already drafted.** `eval/results/gold_additions_batch03_2026-09-26.csv` — 14 rows in the
frozen gold set's exact 15-column schema, qids A41–X54, no collisions with the 40 existing rows, and
`retrieved_docs` / `model_answer` deliberately blank for the run to fill. It exercises what batch-03
actually changed: four merged Centenary chapters, the four repaired documents, an exact-identifier query
for the sparse arm, two temporal queries over the normalised dates, two retired-ID probes and an
out-of-scope control. A copy sits in `batch-03/` inside the Final Project Folder.
`gold_reference_set.csv` was not touched.

**Then CE-12**, the promotion eval, against the standing baseline. Only after CE-12 does the staged
voice-card fix (R-1) get applied — changing the composer prefix and the corpus in the same run confounds
the comparison.

## Two defects found while drafting this, not fixed

- **C-11 — `BC018`'s curated row is stale.** C-7 restored the body from 97 to 276 words, but the row was
  never re-derived: `sub_topics` still carries "NOTE: The source file is a short fragment", and
  `entities.people` still says "Unnamed honoree being prayed for" when the restored text names *Justice
  Regino C. Hermosisima, Jr.* The summary is embedded (it is appended to the `.md`), so this text goes
  into the index as-is. Cheap to fix, and cheapest **before** the re-embed.
- **`CA528` "Only the President can" (2011-05-15) is truncated at source** and says so in its own
  `sub_topics`: "full article content beyond 'Why no demurrer?' section not available". The title looks
  cut too. Pre-existing, outside batch-03, unlogged until now — a batch-04 item.

A corpus-wide sweep for the same class of defect found only these two plus `SA120`, which is genuinely
lecture notes rather than damage.
