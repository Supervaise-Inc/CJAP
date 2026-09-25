# P3.2 / CE-6 — full-corpus dense re-embed: PRE-FLIGHT HALT

**Date:** 2026-09-25
**Operator:** Claude Code (Opus 5)
**Script:** `scripts/build_corpus_dense.py` — **not run, not modified**
**Outcome:** **STOPPED at PRE-FLIGHT 6.** The embed did not start. No embedding
artefact was written or overwritten. The only write into `data/index/` is the
PRE-FLIGHT 7 rollback backup (a byte-identical copy, verified by sha256).

---

## Verdict

Two independent blockers. Either one alone is a stop; together they mean the
embedding environment that produced the July matrix no longer exists on this
machine.

| # | Blocker | Detail |
|---|---|---|
| **B1** | **CUDA is not available to Python** | Every interpreter on this box has **torch 2.11.0+cpu**. `torch.cuda.is_available()` → `False`, `torch.version.cuda` → `None`. The GPU itself is fine and idle (see PF6). The July run recorded `torch 2.5.1+cu121`; that install is gone. |
| **B2** | **`sentence_transformers` is not installed in any interpreter** | `app/embeddings.get_model()` imports it on the first batch. The run cannot reach the first embedding call regardless of backend. |

### Hazard found while reading the script — read before any retry

`scripts/build_corpus_dense.py` wraps its body in:

```python
except Exception as e:
    for p in out:                      # out = [CORPUS_DENSE_PATH, CORPUS_DENSE_META_PATH]
        Path(p).unlink(missing_ok=True)
```

In the current environment the run raises `ModuleNotFoundError:
sentence_transformers` **inside** that `try`, so launching it as-is would
**delete `data/index/corpus_dense.npy` and `corpus_dense_meta.json` before
failing** — i.e. it would destroy the rollback matrix and produce nothing. The
PRE-FLIGHT 7 backup below was taken for exactly this reason and is now the
protection against that path. Do not launch the script until B1/B2 are resolved.

---

## PRE-FLIGHT results

### 1. Config — **PASS**

Read from `config.py` with **no `CJ_*` environment overrides set** (verified:
no `CJ_` variables in the environment), so every value below is the ratified
default:

| Key | Value | Expected | |
|---|---|---|---|
| `EMBED_MODEL_ID` | `BAAI/bge-base-en-v1.5` | `BAAI/bge-base-en-v1.5` | PASS |
| `EMBED_DIM` | `768` | `768` | PASS |
| `EMBED_NORMALIZE` | `True` | `True` | PASS |
| `EMBED_BACKEND` | `cuda_fp32` | `cuda_fp32` (default) | PASS (but see PF6) |
| `EMBED_BATCH_SIZE` | `8` | `8` | PASS |
| `EMBED_DEVICE` | `cuda` | — | — |
| `EMBED_MODEL_PATH` | `''` (empty) | — | — |
| `EMBED_QUERY_PREFIX` | `Represent this sentence for searching relevant passages: ` | — | — |
| `EMBED_DOCUMENT_PREFIX` | `''` (empty) | — | — |

Nothing in config was changed.

### 2. Chunk set — **PASS**

`corpus/index/chunk_index.json` → `stats`:

```
n_docs             1104      (by_doc has 1104 entries — cross-checked)
n_chunks           9804
avg_tokens         313.7     min 11   max 459
anecdote_chunks    1330      docs_with_anecdotes 1104
chunk_band         [200, 400]   overlap_tokens 40
```

`wc -l corpus/index/chunks.jsonl` → **9804**. Both read 9,804; neither reads
8,887 nor 9,865. Chunk index mtime 2026-09-25 15:59.

`source_snapshot.doc_id_count` is **1109** (vs 1,104 chunked docs) — 5 pinned
doc rows produced no chunks. Noted, not acted on; `verify_pin` is keyed to the
1,109 and passes.

### 3. `scripts/verify_pin.py` — **PASS (exit 0)**

```
[verify_pin] PASS — 1109 docs across 4 source files match corpus_snapshot.json.
EXIT=0
```

Run with **Python 3.11** (`C:\Users\ASUS\AppData\Local\Programs\Python\Python311\python.exe`).
Worth recording: the interpreter first on `PATH` (`C:\Users\ASUS\.local\bin\python.exe`,
uv CPython 3.12.13) has **no `openpyxl`**, so a bare `python scripts/verify_pin.py`
exits 1 with `ModuleNotFoundError: openpyxl` — an interpreter fault, not corpus
drift. The corpus **is** in its pinned state.

### 4. `data/index/pilot_dense.npy` absent — **PASS, with a caveat that makes VERIFY 12 unreachable**

`pilot_dense.npy` → **does not exist**. `pilot_dense_meta.json` → **also does not
exist**. Both remain archived as
`_archived_precorrection_2026-07-17_pilot_dense.npy` (2,540,672 B = 827 × 768
float32) and `_archived_precorrection_2026-07-17_pilot_dense_meta.json`. Nothing
was restored.

The parity gate will therefore be skipped as intended. **However**, the brief's
expectation that the script "derives a fresh pilot slice from the new matrix"
does not match the code. In `build_corpus_dense.py`:

```python
sanity = "skipped (no prior pilot index)"
new_pilot = None
if Path(config.DENSE_INDEX_PATH).exists():        # <- false; block skipped
    ...
    new_pilot = np.stack([matrix[pos[c]] for c in sub_ids])
...
if new_pilot is not None:                          # <- false; nothing written
    np.save(config.DENSE_INDEX_PATH, new_pilot)
```

With `pilot_dense.npy` absent, `new_pilot` stays `None` and **no pilot index is
written**. The slice also needs `pmeta["chunk_ids"]` from
`pilot_dense_meta.json`, which is likewise absent — so the pilot slice cannot be
derived from the archived `.npy` alone either. **VERIFY step 12 ("pilot_dense.npy
has been regenerated as a slice of the full matrix") cannot pass with the script
unmodified.** Flagged, not fixed — the script was not touched. Ruling needed:
accept a run with no pilot index, or supply the archived pilot meta / amend the
verify list.

### 5. Model resolution — **PASS, resolves locally; no hub download**

`EMBED_MODEL_PATH` is empty, so `app/embeddings.get_model()` falls to the HF
cache branch, which resolves:

```
RESOLUTION = cache-snapshot ->
  C:\Users\ASUS\.cache\huggingface\hub\models--BAAI--bge-base-en-v1.5\
  snapshots\a5beb1e3e68b9ab74eb54cfd186867f64f240e1a
```

Weights are really on disk (not dangling symlinks): `model.safetensors`
437,955,512 B, `tokenizer.json` 711,396 B, `vocab.txt` 231,508 B, plus
`config.json`, `modules.json`, `1_Pooling/config.json`, dated 2026-07-16. The
`blobs/` directory is empty — normal for a Windows cache, where snapshot entries
are copies rather than links. `HF_HOME` is unset. **No network fetch would be
needed for the model.**

### 6. Backend / device — **FAIL → this is the stop**

**GPU at the OS level is healthy and idle:**

```
NVIDIA-SMI 536.67   Driver 536.67   CUDA Version: 12.2
GPU 0: NVIDIA GeForce GTX 1650 (WDDM)   0 MiB / 4096 MiB used   0% util   P8 / 2W
```

**But no Python on this machine can reach it:**

| Interpreter | torch | `cuda.is_available()` | `torch.version.cuda` | `sentence_transformers` |
|---|---|---|---|---|
| `...\Python311\python.exe` (3.11.9) | **2.11.0+cpu** | **False** | **None** | **missing** |
| `...\Python314\python.exe` (3.14.0) | **2.11.0+cpu** | **False** | **None** | **missing** |
| `...\.local\bin\python.exe` (uv 3.12.13, first on PATH) | **not installed** | — | — | **missing** |

`py -0p` lists exactly these three; there is no conda installation and no
project venv (`.venv/`, `venv/`, `env/` all absent). A depth-8 search of the
user profile found no `sentence_transformers` package anywhere.

For contrast, `data/index/corpus_dense_meta.json` records what the July run used:

```json
"version_block": {"backend":"cuda_fp32","torch":"2.5.1+cu121","torch_cuda":"12.1",
                  "cudnn":90100,"device_name":"NVIDIA GeForce GTX 1650","driver":"536.67"}
```

Same GPU, same driver — but `torch 2.5.1+cu121` has been replaced by a CPU-only
`2.11.0`, and `sentence_transformers` is gone with it.

**Not falling back to CPU, as instructed.** Even setting aside that
`sentence_transformers` is missing, `cpu_fp32` at the benchmarked ~0.27 chunks/s
would be **≈ 10.1 hours** for 9,804 chunks, and the resume checkpoint is keyed on
`EMBED_BACKEND` — a CPU run could not later be resumed on GPU, it would have to
start over. Awaiting your call before any fallback.

### 7. Rollback backup — **DONE, verified**

Both files copied (not moved) with timestamps preserved. Named by their mtime
date, `2026-09-22`, per the brief:

| Archived path | Bytes | sha256 (identical to source) |
|---|---|---|
| `data/index/_archived_precorrection_2026-09-22_corpus_dense.npy` | 30,305,408 | `df5ca465c954e2181ca8a15f9036acfbf4d2b57790924d8f860ce303a5ec55a9` |
| `data/index/_archived_precorrection_2026-09-22_corpus_dense_meta.json` | 197,886 | `465ba344146be81a5d1f3edee87f84e1d2ac0b06c940011a682a944d191362b2` |

Sources (untouched, still in place):

| Path | mtime | Bytes |
|---|---|---|
| `data/index/corpus_dense.npy` | 2026-09-22 23:00:59 +0800 | 30,305,408 |
| `data/index/corpus_dense_meta.json` | 2026-09-22 23:00:59 +0800 | 197,886 |

**Naming note:** the filesystem mtime is **2026-09-22** (when the files were
copied into this checkout), but the matrix's own `build_date` is **2026-07-17**
and it is the July artefact the brief calls the rollback. The archive is named
`2026-09-22` because the brief specified the mtime date; if the convention
should instead follow the existing `_archived_precorrection_2026-07-17_pilot_dense*`
pair (named by build date), rename before this is relied on.

**What the rollback contains:** `model_id BAAI/bge-base-en-v1.5`, `dim 768`,
`backend cuda_fp32`, `normalize true`, `batch_size 8`, **`n_chunks 9865`**,
`build_date 2026-07-17`, `chunk_index_sha256 d8a5b7ba…7acedd`,
`pilot_parity_sanity "min_cosine(old_cpu vs new_cuda)=1.000000 over 827 rows"`.
Its 9,865 rows are the pre-batch-03 chunk set — which is precisely why CE-6
exists: the live corpus is now 9,804 chunks, so the shipped matrix is 61 rows
stale and keyed to a different `chunk_index` hash.

---

## RUN — not attempted

Step 8 was not executed. Wall-clock, chunks/s, and VERIFY steps 9–13 are all
**not applicable**: no run, no new matrix, no new meta, no spot-check.

## What is needed to unblock

1. **Reinstall the CUDA embedding environment** — `torch==2.5.1+cu121` (the
   version the July matrix was built with; cu121 runs fine under driver 536.67 /
   CUDA 12.2) plus `sentence_transformers`, into one interpreter, and confirm
   `torch.cuda.is_available()` is `True` on the GTX 1650. Python 3.11.9 is the
   natural host: it already carries `openpyxl`, `pyarrow 24.0.0` and `numpy`.
   Note `app/embeddings.py`'s DLL-order guard — pyarrow must import before
   torch; it already does.
2. **Decide the pilot question from PF4** — with the script unmodified, a run
   that starts from no `pilot_dense.npy` writes no pilot index at all. VERIFY 12
   needs either an amended acceptance list or the archived pilot **meta**
   restored alongside a decision on the parity gate.
3. Then re-run this pre-flight from the top and proceed to step 8.

Nothing else in the brief's FLAG list fired: the chunk set is 9,804 as expected,
the model resolves to a local snapshot with no hub download, the corpus pin is
intact, and no embedding output was created, so there are no norms or parity
values to report yet.
