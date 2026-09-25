# P3 — Python environment repair for the CJAP dense re-embed: NO REPAIR NEEDED

**Date:** 2026-09-26
**Operator:** Claude Code (Opus 5)
**Outcome:** **No packages were installed, upgraded or downgraded. Nothing was
written outside this report.** The embedding environment is not broken — it was
never on this repo's machine path. A working CUDA venv already exists, and it
passes every VERIFY step in the brief, including the offline model load.

**Recommended interpreter for CE-6:**

```
C:\Reachy Mini Project 2026\.venv\Scripts\python.exe
```

---

## Why the INSTALL step was not run

The brief's premise — "the 3.11.9 venv" needing torch — does not match what is on
disk. Two venvs exist, and they are not the same project:

| Venv | Python | What it is | torch |
|---|---|---|---|
| `C:\Reachy Mini Project 2026\.venv` | **3.12.13** | **The embedding environment.** Created 2026-07-17 — the day the July matrix was built | **2.5.1+cu121, CUDA available** |
| `C:\Reachy Mini Project 2026\wakeword\CJAP\.venv` | **3.11.9** | The **wake-word** venv (PLAN-0008): `openwakeword 0.6.0`, `onnxruntime 1.28.0`, 27 packages total | **absent** |

The only 3.11.9 venv on this machine is the wake-word venv. It has no torch, no
transformers, no pandas, no openpyxl — it is not, and never was, the dense
embedding environment. Installing a ~2.5 GB CUDA torch stack into it would
create a second embedding regime next to a working one, for no gain.

Meanwhile the 3.12.13 venv **already satisfies the brief's install target
exactly**: `torch==2.5.1+cu121`. Its version block matches, byte for byte, what
`data/index/corpus_dense_meta.json` records for the 2026-07-17 build
(`torch 2.5.1+cu121`, `torch_cuda 12.1`, `device_name NVIDIA GeForce GTX 1650`,
`driver 536.67`). This is the machine that built the July matrix.

**Running step 4 as written would have been a regression, not a repair:**

| Package | Installed now | Brief's pin | Effect |
|---|---|---|---|
| `torch` | 2.5.1+cu121 | 2.5.1+cu121 | no-op ("already satisfied") |
| `transformers` | **5.12.1** | 4.44.2 | **downgrade 5.x → 4.x** |
| `sentence-transformers` | **5.6.0** | 3.0.1 | **downgrade 5.x → 3.x** |
| `huggingface_hub` | **1.21.0** | — | forced **1.21.0 → <1.0** by transformers 4.44.2 |
| `tokenizers` | **0.22.2** | — | forced **0.22.2 → 0.19.x** by transformers 4.44.2 |

That cascade would roll back a stack that currently loads the model and encodes
correctly. It would also contradict the repo's own code: `app/embeddings.py:96`
branches on `get_embedding_dimension` vs `get_sentence_embedding_dimension`
specifically to support **sentence-transformers ≥ 5** — the version installed.
Per FLAG-DO-NOT-FIX, I stopped rather than executing it.

---

## PRE-FLIGHT

### 1. Python version, venv path, activation

| | |
|---|---|
| **Embedding venv** | `C:\Reachy Mini Project 2026\.venv` |
| **Python** | **3.12.13** — *not* 3.11.9 as the brief expected |
| Created by | `C:\Users\ASUS\.local\bin\python.exe -m venv` (uv CPython 3.12.13), `include-system-site-packages = false` |
| Venv dir mtime | 2026-07-17 21:21 |
| **Activated?** | **No.** No venv is active in this shell. `python` on PATH resolves to `C:\Users\ASUS\.local\bin\python.exe` (uv 3.12.13 base, **no torch**) — which is exactly why the previous session concluded the environment was gone. Every command in this report invoked the venv interpreter by absolute path instead of activating it. |
| 3.11.9 venv | `C:\Reachy Mini Project 2026\wakeword\CJAP\.venv` (wake-word; `home = ...\Programs\Python\Python311`; created from a `C:\Users\ASUS\OneDrive\Desktop\CJAP` path per its `pyvenv.cfg`) |

Bare interpreters on the machine, for completeness (`py -0p`): 3.14.0 (default),
3.11.9, uv 3.12.13 — the last two carry **torch 2.11.0+cpu**, which is the CPU-only
torch the previous session found. No conda.

### 2. `pip show` — embedding venv (`C:\Reachy Mini Project 2026\.venv`)

| Package | Version | Location |
|---|---|---|
| `torch` | **2.5.1+cu121** | `C:\Reachy Mini Project 2026\.venv\Lib\site-packages` |
| `sentence-transformers` | **5.6.0** | same |
| `transformers` | **5.12.1** | same |
| `numpy` | **2.5.0** | same |
| `pandas` | **3.0.3** | same |
| `openpyxl` | **3.1.5** | same |

Also present and relevant: `huggingface_hub 1.21.0`, `tokenizers 0.22.2`,
`safetensors 0.8.0`, `scikit-learn 1.9.0`, `scipy 1.18.0`, **`pyarrow 21.0.0`**
(the last matters — `app/embeddings.py` imports pyarrow before torch as a
deliberate DLL-order guard against the 2026-07-17 exit-139 segfault family; the
guard is satisfied here).

For contrast, the 3.11.9 wake-word venv: `numpy 2.4.6`, `scikit-learn 1.9.0`,
`scipy 1.17.1`, `onnxruntime 1.28.0`, `openwakeword 0.6.0` — **no torch, no
transformers, no sentence-transformers, no pandas, no openpyxl**.

### 3. `nvidia-smi` — **PASS**

```
name, driver_version, memory.total, memory.free, memory.used
NVIDIA GeForce GTX 1650, 536.67, 4096 MiB, 3949 MiB, 0 MiB
```

Driver 536.67 (CUDA 12.2 runtime) drives cu121 fine on Turing / sm_75. GPU idle,
3,949 MiB of 4,096 MiB free.

---

## INSTALL — not run

Prescribed, **NOT EXECUTED**:

```
pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.5.1+cu121
pip install transformers==4.44.2 sentence-transformers==3.0.1
```

Reason: the first is already satisfied at the exact pinned version; the second
would downgrade a working stack (table above). No pip install, uninstall or
upgrade command was run in this session. No network fetch of any kind was
attempted — no PyPI, no download.pytorch.org, and no huggingface.co.

---

## VERIFY

### 5. torch / CUDA — **PASS**

```
torch 2.5.1+cu121 | version.cuda 12.1 | is_available True
device NVIDIA GeForce GTX 1650
VRAM free/total 2818 / 4095 MiB   (free measured from inside a live CUDA context)
torch.__file__  C:\Reachy Mini Project 2026\.venv\Lib\site-packages\torch\__init__.py
```

All four expected values hold: **2.5.1+cu121, 12.1, True, GTX 1650**. `torch.__file__`
confirms the venv's own torch is in use, not the system 2.11.0+cpu.

### 6. Offline model load smoke test — **PASS**

Run with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, against
`C:\Reachy Mini Project 2026\models\bge-base-en-v1.5`, `device='cuda'`:

```
SHAPE (1, 768)   DTYPE float32
SQNORM 1.0
MODULES ['Transformer', 'Pooling', 'Normalize']
```

Expected (1, 768) and squared norm 1.0 — **both exact**. Load took seconds
(199 weight shards, ~1,900 it/s).

**On the `2_Normalize` concern:** confirmed that `modules.json` lists a
`2_Normalize` module whose directory is **absent** (the model dir contains only
`1_Pooling/` plus a nested `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a/` copy).
**It is not a problem under sentence-transformers 5.6.0** — `Normalize` carries no
configuration, so it is constructed without reading its directory. The module
list above shows all three modules loaded, and the unit squared norm proves the
Normalize stage ran. Nothing was created and `modules.json` was not edited.

**Bonus check — the repo's own path, which is what CE-6 actually calls.** Same
venv, same offline flags, run from the repo root against `app/embeddings.py`:

```
[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; cache-snapshot)
DIM 768 | EMBED_DIM 768 | device cuda:0
query (768,) float32 norm 1.0
doc   (1, 768) float32 norm 0.9999999403953552
cosine 0.6302887797355652     ("What did he say about the rule of law?" vs
                               "The rule of law is the bedrock of a free society.")
load_count 1
```

Note the resolution line: **`cache-snapshot`**. With `CJ_EMBED_MODEL_PATH` unset,
`get_model()` resolves to
`C:\Users\ASUS\.cache\huggingface\hub\models--BAAI--bge-base-en-v1.5\snapshots\a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`
— the **same snapshot id** as the `C:\Reachy Mini Project 2026\models` copy, so the
two are the same weights by a different route. The `EMBED_DIM` guard passes, the
vectors are unit-norm, the cosine is sane, and it all worked with the hub
disabled. **No hub access is needed for CE-6.**

### 7. numpy before/after — **unchanged (nothing was installed)**

| Package | Before | After | Changed by torch? |
|---|---|---|---|
| `numpy` | **2.5.0** | **2.5.0** | No — no install ran |
| `pandas` | **3.0.3** | **3.0.3** | No |
| `openpyxl` | **3.1.5** | **3.1.5** | No |

No major-version move, no downgrade. Pickles and xlsx written under these
versions are unaffected.

---

## Final versions

| Package | Version |
|---|---|
| `torch` | 2.5.1+cu121 (CUDA 12.1, `is_available() == True`) |
| `transformers` | 5.12.1 |
| `sentence-transformers` | 5.6.0 |
| `numpy` | 2.5.0 |

---

## Flags

1. **The brief's "3.11.9 venv" is the wake-word venv, not the embedding venv.**
   The embedding venv is Python **3.12.13**. Confirm you want CE-6 run on 3.12.13
   before it proceeds — it is the interpreter that built the July matrix.
2. **Executing INSTALL step 4 would downgrade a working stack** (transformers
   5.12.1 → 4.44.2, sentence-transformers 5.6.0 → 3.0.1, dragging
   `huggingface_hub` below 1.0 and `tokenizers` to 0.19.x). Not done.
   `app/embeddings.py` is written for sentence-transformers ≥ 5.
3. **The embedding environment is outside this repo**, at
   `C:\Reachy Mini Project 2026\.venv`, and is **not on PATH**. Any CE-6 command
   must call that interpreter by absolute path (or activate the venv first);
   a bare `python scripts/...` silently lands on the uv 3.12 base interpreter,
   which has no torch. This is what made the environment look destroyed.
4. **No 3.11.9 path to CUDA was created.** If policy requires the re-embed to run
   on 3.11.9 specifically, that is a fresh ~2.5 GB install and a new decision —
   say so and I will scope it.
5. Nothing from the "do not fix" list occurred: CUDA is available, no `+cpu`
   torch was resolved, the model loads, numpy did not move, and no hub download
   was attempted or suggested.

## Still open from the CE-6 pre-flight (unchanged by this session)

The blocker recorded in [`p3_2_dense_rebuild_2026-09-25.md`](p3_2_dense_rebuild_2026-09-25.md)
that is **not** environmental still stands: with `pilot_dense.npy` and
`pilot_dense_meta.json` both absent, `scripts/build_corpus_dense.py` leaves
`new_pilot = None` and writes **no** pilot index, so that run book's VERIFY 12
cannot pass with the script unmodified. That needs a ruling before CE-6 runs.
The rollback backup taken then is still in place:
`data/index/_archived_precorrection_2026-09-22_corpus_dense{.npy,_meta.json}`.
