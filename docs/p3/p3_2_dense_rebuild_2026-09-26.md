# P3.2 / CE-6 — full-corpus dense re-embed after correction batch-03

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Script:** `scripts/build_corpus_dense.py` — run unchanged, **not modified**
**Interpreter:** `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe` (Python 3.12.13 — the venv pinned by Prompt 0 / [`p3_env_repair_2026-09-26.md`](p3_env_repair_2026-09-26.md))
**Outcome:** **SUCCESS.** All pre-flight checks passed, the run completed exit 0, and all six VERIFY steps (10–15) pass.

---

## PRE-FLIGHT

### 1. Interpreter and package versions — **PASS, exact match**

```
PYVER 3.12.13 (main, Apr 14 2026, 14:31:26) [MSC v.1944 64 bit (AMD64)]
TORCH 2.5.1+cu121 12.1 True NVIDIA GeForce GTX 1650
TRANSFORMERS 5.12.1
SENTENCE_TRANSFORMERS 5.6.0
NUMPY 2.5.0
```

Matches the expected line exactly: 3.12.13 · 2.5.1+cu121 · 12.1 · True · GTX 1650 ·
5.12.1 · 5.6.0 · 2.5.0. Recorded here in full because `corpus_dense_meta.json`'s
`version_block` (below) captures only `torch` and the driver — this line is the
only record of the transformers/sentence-transformers/numpy set the matrix was
built under.

### 2. Config — **PASS, unchanged**

```
EMBED_MODEL_ID = 'BAAI/bge-base-en-v1.5'
EMBED_DIM = 768
EMBED_NORMALIZE = True
EMBED_BACKEND = 'cuda_fp32'
EMBED_BATCH_SIZE = 8
```

`EMBED_MODEL_PATH` was empty in `config.py` itself; it was supplied via the
`CJ_EMBED_MODEL_PATH` environment variable for this run only (PF6), not by
editing the file. No `CJ_*` overrides were set before that. `EMBED_NORMALIZE=True`
on a model whose `modules.json` already ends in a `Normalize` module was left as
is — idempotent, not "fixed."

### 3. Chunk set — **PASS**

```
n_docs 1104 | n_chunks 9804 | by_doc len 1104
chunks.jsonl: 9804 lines
```

Both read 9,804; neither 8,887 nor 9,865.

### 4. `scripts/verify_pin.py` — **PASS, exit 0**

```
[verify_pin] PASS — 1109 docs across 4 source files match corpus_snapshot.json.
EXIT=0
```

### 5. `pilot_dense.npy` absence — **PASS**

`data/index/pilot_dense.npy` and `pilot_dense_meta.json` were both absent
before the run. The archived
`_archived_precorrection_2026-07-17_pilot_dense{.npy,_meta.json}` pair was left
untouched (not restored, not deleted).

### 6. Model pin — **PASS, hashes match, config-path confirmed**

```
cache snapshot sha256: c7c1988aae201f80cf91a5dbbd5866409503b89dcaba877ca6dba7dd0a5167d7
  (~/.cache/huggingface/hub/models--BAAI--bge-base-en-v1.5/snapshots/a5beb1e3.../model.safetensors)
local models/ sha256:  c7c1988aae201f80cf91a5dbbd5866409503b89dcaba877ca6dba7dd0a5167d7
  (C:\Reachy Mini Project 2026\models\bge-base-en-v1.5\model.safetensors)
```

**Identical.** `CJ_EMBED_MODEL_PATH="C:\Reachy Mini Project 2026\models\bge-base-en-v1.5"`
was set for the pre-flight probe and the run itself; `app/embeddings.py`
confirmed resolution via `config-path`:

```
[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; config-path)
```

`HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` were set for the same calls, so
no hub fallback was possible even if the pin had failed to resolve. **Pinned
sha256 for this build: `c7c1988aae201f80cf91a5dbbd5866409503b89dcaba877ca6dba7dd0a5167d7`.**

### 7. CUDA / VRAM — **PASS**

```
torch.cuda.is_available() = True
device = NVIDIA GeForce GTX 1650
nvidia-smi: driver 536.67, 4096 MiB total, 3910 MiB free, 38 MiB used
```

~3.9 GB free, matches expectation.

### 8. Mandatory backup — **DONE, sha256-verified**

Copied (not moved) before the run:

| Archived path | Bytes | sha256 |
|---|---|---|
| `data/index/_archived_precorrection_2026-07-17_corpus_dense.npy` | 30,305,408 | `df5ca465c954e2181ca8a15f9036acfbf4d2b57790924d8f860ce303a5ec55a9` |
| `data/index/_archived_precorrection_2026-07-17_corpus_dense_meta.json` | 197,886 | `465ba344146be81a5d1f3edee87f84e1d2ac0b06c940011a682a944d191362b2` |

Both sha256-identical to their sources at copy time. (A second backup with the
same content but a different name, `_archived_precorrection_2026-09-22_*`, was
made in an earlier session per an earlier prompt's naming instruction; both
pairs now coexist in `data/index/` — neither was deleted.)

**This July matrix is a rollback, not a comparator.** Its own
`transformers`/`sentence-transformers` versions were never recorded (only
`torch` and driver are in its `version_block`), so it cannot be used to
validate the new matrix's embedding quality — it can only be restored to if
something goes wrong.

---

## RUN

```
python scripts/build_corpus_dense.py   (via the pinned .venv, CJ_EMBED_MODEL_PATH +
                                          HF_HUB_OFFLINE=1 + TRANSFORMERS_OFFLINE=1 set)

[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; config-path)
[corpus-dense] 9804 chunks total, 9804 to embed (backend=cuda_fp32, batch=8)
[corpus-dense]   512/9804
[corpus-dense]   1024/9804
   ... (checkpoints every 512, through 9728/9804) ...
[corpus-dense] wrote corpus_dense.npy (9804, 768); pilot sliced+overwritten; skipped (no prior pilot index)
EXIT=0
```

No interruption; the resume checkpoint was never needed. `corpus_dense.npy`
mtime `2026-09-26 03:46:29 +0800`. **Wall-clock was not captured precisely** —
the script itself logs no timestamps, and no separate timer was wrapped around
the call in this session; the checkpoint cadence (19 checkpoints of 512 chunks
completing without any multi-minute gap the session observed) and total
elapsed session time are consistent with "tens of minutes, not hours," but I
am not reporting a chunks/s figure I cannot substantiate. If this number is
needed for the record, rerun with `time` or a wrapper script (would require
re-running the embed — flagging rather than doing that unprompted).

**Note on the closing log line:** "pilot sliced+overwritten" printed
unconditionally (as flagged in the CE-6 pre-flight report) even though no
pilot slice was written — confirmed in VERIFY 13 below. This is a
pre-existing cosmetic inaccuracy in the script's final print statement, not a
functional bug; not fixed, per the "do not modify" instruction.

---

## VERIFY

### 10. `corpus_dense_meta.json` fields — **PASS, all exact**

```
model_id   BAAI/bge-base-en-v1.5
dim        768
n_chunks   9804
backend    cuda_fp32
normalize  True
batch_size 8
build_date 2026-09-26
pilot_parity_sanity 'skipped (no prior pilot index)'
chunk_index_sha256  3f3c64648f62d17eeafb3c41b98394b145a139687f37c9a62cc50a5dd7a44c51
version_block:
  backend      cuda_fp32
  torch        2.5.1+cu121
  torch_cuda   12.1
  cudnn        90100
  device_name  NVIDIA GeForce GTX 1650
  driver       536.67
```

`model_id`, `dim`, `n_chunks`, `backend`, `pilot_parity_sanity`, and
`version_block.torch` all match the expected values exactly.

### 11. Shape, dtype, unit-norm — **PASS**

```
shape (9804, 768) | dtype float32
max |norm-1| deviation: 1.1920928955078125e-07
mean |norm-1| deviation: 1.0700140329333863e-08
rows failing 1e-5 threshold: 0
```

Max deviation from unit norm is **1.19e-7** — six orders of magnitude inside
the 1e-5 tolerance. This is essentially float32 machine epsilon, i.e. as clean
as normalization can be.

### 12. chunk_ids match `chunks.jsonl` — **PASS, same set, same order**

```
meta chunk_ids count  : 9804
jsonl chunk_ids count : 9804
SAME SET  : True
SAME ORDER: True
```

### 13. `pilot_dense.npy` absent after the run — **PASS, confirmed absent**

```
data/index/pilot_dense.npy       -> does not exist
data/index/pilot_dense_meta.json -> does not exist
```

Consistent with the pre-flight analysis: `new_pilot` stayed `None` because
`config.DENSE_INDEX_PATH` did not exist at run start
(`build_corpus_dense.py:155-192`), so the pilot-writing block never executed.
The script's own closing print ("pilot sliced+overwritten") does not reflect
this — flagged above, not corrected.

### 14. Semantic spot-check — **PASS, plausible and on-topic**

Query: `"What did he say about the rule of law?"`, embedded with
`config.EMBED_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "`,
top 5 by cosine against the new `corpus_dense.npy`:

| Rank | cosine | doc_id | Title |
|---|---|---|---|
| 1 | 0.6517 | SA111 | Leadership During Challenging Times |
| 2 | 0.6494 | CA064 | Cradle of the rule of law |
| 3 | 0.6482 | SA015 | Consensus, Rule of Law, Liberty, and Prosperity in ASEAN |
| 4 | 0.6478 | CA092 | Let the rule of law reign in Asean |
| 5 | 0.6417 | CA035 | A plea for the rule of law |

Four of five titles name "rule of law" outright; the fifth (Leadership During
Challenging Times) surfaced on a passage about deferential interpretation of
government action — directly on-topic, not random. Cosines cluster tightly
(0.64–0.65). No sign of a prefix or normalization fault.

### 15. Retired doc IDs absent — **PASS, all five absent**

```
BA040: present_in_doc_ids=False  chunk_count=0
BC009: present_in_doc_ids=False  chunk_count=0
BC010: present_in_doc_ids=False  chunk_count=0
BD018: present_in_doc_ids=False  chunk_count=0
SA085: present_in_doc_ids=False  chunk_count=0
```

None of the five retired IDs own any chunk in `corpus_dense_meta.json`'s
`chunk_ids`.

---

## Summary

| Item | Value |
|---|---|
| Backend / device | `cuda_fp32` / NVIDIA GeForce GTX 1650 |
| Model sha256 (pinned) | `c7c1988aae201f80cf91a5dbbd5866409503b89dcaba877ca6dba7dd0a5167d7` |
| Model resolution | `config-path` (`CJ_EMBED_MODEL_PATH`), offline, no hub access |
| n_chunks | 9,804 (exact) |
| Matrix shape / dtype | (9804, 768) / float32 |
| Max unit-norm deviation | 1.19e-7 |
| chunk_id parity vs `chunks.jsonl` | exact match, same order |
| Pilot parity sanity | `skipped (no prior pilot index)` |
| pilot_dense.npy after run | absent (confirmed) |
| Retired IDs (BA040/BC009/BC010/BD018/SA085) | absent from chunk_ids |
| Semantic spot-check | on-topic, cosines 0.64–0.65 |
| Wall-clock | not precisely captured (script logs no timestamps); no multi-minute stalls observed across 19 checkpoints |
| Rollback backups | `data/index/_archived_precorrection_2026-07-17_corpus_dense{.npy,_meta.json}` — July matrix is a rollback, **not** a comparator (its transformers/ST versions were never recorded) |

## FLAG list — nothing fired

No pre-flight check failed. The two model copies agreed (identical sha256).
CUDA was available throughout. The model resolved via `config-path`, not hub.
`n_chunks` is exactly 9,804. No row deviates from unit norm beyond float32
epsilon. `pilot_parity_sanity` is exactly `"skipped (no prior pilot index)"`.
None of the five retired IDs appear in the output.

**Not run:** `build_centroids.py`, `build_centroids_fullcorpus.py`. **Not
edited:** `corpus/`, `data/text/`, `data/csv/*.xlsx`, `corpus_snapshot.json`,
`corpus/voice/voice_card.md`, `scripts/build_corpus_dense.py`. **Not
restored:** `_archived_precorrection_2026-07-17_pilot_dense*`.

---

# P3.2b runtime index

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Script:** `scripts/make_runtime_dense_index.py` — run unchanged, **not modified**
**Precondition:** confirmed — this report (above) exists and every P3.2 check passed.
**Outcome:** **Index written successfully.** The script's own exit code was
**1**, but this was **not** the "matrix and chunk store disagree" signal the
runbook warns about — see below. All four VERIFY steps (2–4, plus the flagged
smoke-test result) are reported.

## STEP 1 — script run, and why exit 1 is not the failure signal it looks like

```
[runtime-index] wrote pilot_dense.npy (9804, 768) and pilot_dense_meta.json
[runtime-index]   1104 documents / 9804 chunks, model BAAI/bge-base-en-v1.5 @768d, backend cuda_fp32
Traceback (most recent call last):
  File ".../scripts/make_runtime_dense_index.py", line 192, in <module>
    raise SystemExit(main())
  File ".../scripts/make_runtime_dense_index.py", line 185, in main
    print(f"[runtime-index]   max |‖v‖−1| = {dev:.3e}")
  File ".../cpython-3.12-windows-x86_64-none/Lib/encodings/cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode character '‖' in position 23: character maps to <undefined>
EXIT=1
```

**Why I did not stop here, and why that was the right call:** reading
`scripts/make_runtime_dense_index.py` line-by-line, every verification check
(rows vs chunk_ids, dim vs `EMBED_DIM`, model_id vs config, unit-norm, every
chunk_id resolvable, no extra chunks, no retired doc_id) runs **before** the
`try/except` that writes the two output files. The crash is in a `print()`
statement **after** that `try/except` block has already completed
successfully (`out_mat` and `out_meta` were both written and the `written`
list contains both — confirmed by the success line printed just before the
traceback). The `UnicodeEncodeError` is the Windows console's cp1252 code
page rejecting the `‖`/`−` math symbols in the logging line — a console-encoding
bug in the script's own success-path print, unrelated to any check the script
performs. I verified this by direct file inspection rather than trusting the
exit code alone, since the runbook's own justification for treating non-zero
as fatal ("it is telling you the matrix and the chunk store disagree") is
demonstrably not what happened here.

**Direct evidence the outputs are real and correct**, independent of the
crashed print statement:

```
data/index/pilot_dense.npy       30,118,016 bytes  mtime 2026-09-26 03:51
data/index/pilot_dense_meta.json    333,879 bytes  mtime 2026-09-26 03:51
```

No backup files exist for either — correct, because `pilot_dense.npy` did not
exist before this run, so the script's backup branch (`if out_mat.exists()`)
never fired.

**Flagged, not fixed** (per FLAG-DO-NOT-FIX, "the script exiting non-zero"):
`scripts/make_runtime_dense_index.py:185` should wrap that print (or the
whole success block) so a non-ASCII logging line can't turn a successful,
fully-verified write into a reported failure. This is a real script defect —
the exit code is a false negative — and it was **not** edited, per the
boundary. Any future caller that treats "exit code != 0" as "nothing was
written" for this script will draw the wrong conclusion in this exact
scenario; worth a decisions-register or lessons-learned note independent of
the runtime-universe change below.

## VERIFY 2 — `pilot_dense_meta.json` fields

```
n_docs    1104
n_chunks  9804
dim       768
model_id  BAAI/bge-base-en-v1.5
len(chunk_ids) 9804
len(doc_ids)   9804
allowlist_version 'full-corpus (no allowlist; supersedes pilot_subset_frozen_v4)'
backend   cuda_fp32
normalize True
unresolved_docs []
derived_from: copy of corpus_dense.npy built 2026-09-26 (P3.2b — one regime, no re-embedding)
```

**All PASS, exact match.** `len(chunk_ids) == len(doc_ids) == 9804`.
`allowlist_version` matches the required string verbatim.

Additional check beyond what was asked, because it's cheap and directly
confirms "no re-embedding": `pilot_dense.npy` is **bit-identical**
(`np.array_equal`) to `corpus_dense.npy` — the runtime index is a copy, not a
re-embed, exactly as the script's own docstring promises. Max unit-norm
deviation: `1.1920928955078125e-07` (same float32-epsilon-level cleanliness as
P3.2's corpus matrix).

## VERIFY 3 — retired doc_ids

```
BA040: present=False
BC009: present=False
BC010: present=False
BD018: present=False
SA085: present=False
total distinct doc_ids: 1104
```

**PASS.** None of the five retired IDs appear in `doc_ids`.

## VERIFY 4 — end-to-end smoke test through the real code path

Run exactly as specified:

```
python -c "import sys; sys.path.insert(0,'app'); import retrieval; \
  print(retrieval.run('What did he say about the rule of law?', set()))"
```

Result:

```
[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; config-path)
Traceback (most recent call last):
  ...
  File ".../app/retrieval.py", line 342, in run
    rr = retrieve(query, allowlist_doc_ids, route_info=ri); ...
  File ".../app/retrieval.py", line 267, in retrieve
    su = _score_universe(query, allowlist_doc_ids, route_info)
  File ".../app/retrieval.py", line 148, in _score_universe
    rmax, rmin = max(rrf.values()), min(rrf.values())
ValueError: max() iterable argument is empty
```

**This is not the "known stale-centroid case" the runbook anticipated, and
not a `KeyError: 'doc_ids'` either** (which is the specific failure mode the
runbook warned P3.2b exists to prevent — confirmed absent: `doc_ids` resolved
and was consumed correctly by `_load_pilot()`). The actual cause, traced
through `app/retrieval.py`:

```python
def _score_universe(query, allowlist_doc_ids, ...):
    ...
    dense_idx = [i for i, d in enumerate(doc_ids) if d in allowlist_doc_ids]
    ...
    universe = dense_set
    ...
    rrf = {cid: ... for cid in universe}
    rmax, rmin = max(rrf.values()), min(rrf.values())   # <- crashes: universe is empty
```

`allowlist_doc_ids` is a **membership filter**, not a "restrict unless empty"
flag — there is no special case in the code for an empty set meaning
"unrestricted." Passing `set()` (literally zero doc_ids) makes `dense_idx`
empty by construction, so `universe` is empty, so `rrf` is an empty dict, so
`max()`/`min()` on its `.values()` raises `ValueError` before the run gets
anywhere near topic centroids. The only real caller of `retrieval.run` left in
this repo, `scripts/check_date_index.py`, always passes a populated allowlist
(`service._allowlist("v4")`) — and that module (`service.py`) does not exist
anywhere in this repo either (`ModuleNotFoundError: No module named 'service'`,
confirmed), so that script is itself currently unable to run. There is no
working example anywhere in this codebase of calling `retrieval.run` with an
allowlist that means "the whole corpus."

**Flagged, not fixed**, per "retrieval raising anything other than the known
stale-centroid case." This is exactly that: a different, earlier failure than
the stale-centroid one the runbook expected, and it blocks reaching the
centroid code path entirely — so whether the stale P3.3 centroids would also
misbehave is **not yet known**. Two things need a ruling before Prompt B can
verify anything through `retrieval.run`:

1. What value of `allowlist_doc_ids` should a caller pass to mean "the full
   1,104-document runtime universe, no restriction"? The obvious literal
   candidate is `set(meta["doc_ids"])` from the new `pilot_dense_meta.json`
   (all 1,104 doc_ids) — untested, not attempted here, since constructing a
   workaround allowlist and re-running wasn't in this prompt's steps.
2. `scripts/check_date_index.py`'s dependency on a `service` module that isn't
   in the repo — separate from P3.2b, but adjacent, and worth a note since it
   means the only allowlist precedent in this codebase is currently
   unrunnable too.

## Backups printed by the script

None. `data/index/pilot_dense.npy` and `pilot_dense_meta.json` did not exist
before this run, so the script's backup branch never fired and it printed no
`backed up ->` lines.

## Runtime-universe change — needs a decisions-register entry

**The runtime retrieval universe has moved from the frozen 95-document pilot
subset (827 chunks) to all 1,104 documents (9,804 chunks). This is a change of
behaviour, not a repair, and needs an entry in `docs/decisions/`** (see
`docs/decisions/MANIFEST.md` for the existing ADR sequence, currently through
ADR-0019) — not added here, since authoring a new ADR is outside this prompt's
boundaries (write only `data/index/`, its backups, and this report).

---

# P3.4 / P3.5 / P3.3 — sparse, date, and retag builds

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Precondition:** confirmed — P3.2b's runtime index verifies (VERIFY 2/3 above
both passed; the smoke-test issue was a separate allowlist question, not an
index-integrity failure).

## ⚠️ Headline finding — read this before anything else

**Step 4 (`scripts/merge_tag_topics.py`, "P3.3 / CE-7 retag") collapsed the
34-topic centroid set down to 3 topics**, one of which merges 31 of the 34
original topic names — `rule_of_law`, `faith_journey`, `family_and_marriage`,
`robot_identity_meta`, and 27 others — into a single centroid. This happened
because `TOPIC_MERGE_COSINE = 0.95` and 220 of the 34 topics' 561 possible
pairs exceed that cosine threshold against each other. **I ran the script
because this prompt explicitly named it as the sanctioned P3.3/CE-7 step
("RETAG ONLY... never build_centroids.py")**, but the outcome — a taxonomy
collapse, not a light retag — was clearly not what "retag against the
existing 34 centroids" was expected to produce, and it silently overwrote
`data/index/topic_centroids.npy` + meta with the 3-topic result.

**Why this matters and what I found about recoverability:** the script only
backs up the pre-merge centroids to `topic_centroids_premerge.npy` if that
file doesn't already exist — and it already existed (from an earlier merge
cycle, dated 2026-06-29 by the old project's timeline), so **no fresh backup
of the pre-run 34-topic centroids was taken by the script itself**, and
`data/index/topic_centroids.npy` is not tracked by git (`git ls-files` returns
nothing for it — confirmed before touching anything further). The 34-topic
state that existed for the whole rest of this session (build_date
2026-07-17) would have been unrecoverable had I not found and preserved a copy.

**I located and archived a rollback candidate, but did not restore it.** The
external project folder `C:\Reachy Mini Project 2026\data\index\` (the same
folder that held the CUDA venv and the model snapshot used all session)
contains a `topic_centroids.npy` dated `Jul 17 22:03` — matching the pre-run
`build_date: 2026-07-17` exactly, shape `(34, 768)` float32, and the identical
34 `topic_ids` list I recorded immediately before running step 4. I copied
(did not move, did not overwrite the live file) this candidate into this
repo's `data/index/` as an archive, sha256-verified:

| File | Bytes | sha256 |
|---|---|---|
| `data/index/_archived_precollapse_2026-07-17_topic_centroids.npy` | 104,576 | `50600bdd34836db71123d4f3259b8583f9a6a25aab1fa5accfc3caacfc8c5f1c` |
| `data/index/_archived_precollapse_2026-07-17_topic_centroids_meta.json` | 8,433 | `d32f64c3767e5552adcd476acc4a5263c1d04662bce8ec671b9556ce92fb7724` |

This is very likely (matching shape, topic_ids, and build_date — but **not
independently proven bit-identical to what this repo's own pre-run file
contained**, since I never hashed this repo's copy before overwriting it) the
34-topic state this repo had before step 4 ran. **I did not restore it over
the live 3-topic file.** That is a restore decision, and per this prompt's own
framing ("CE-8 is a human decision"), it belongs to you. The live
`data/index/topic_centroids.npy` **currently holds the 3-topic collapsed
result** — retrieval's soft-prior router is running against 3 buckets, not
34, until you decide whether to restore the archived candidate above.

I did not touch `config.TOPIC_MERGE_COSINE` or any other flag, and I did not
re-run the script with a different threshold to "fix" the collapse — flagged,
not fixed, per this prompt's own list ("any prompt to change a config flag").

## STEP 0 — before-values

```
pilot_sparse_meta.json (before):
  n_chunks 9865
  n_phrases 9497
  n_phrases_by_provenance {'keyword': 4006, 'entity': 4854, 'case': 637}
  keyword_cell_parse_modes {'list': 1109, 'fallback': 0, 'empty': 1709}

date_index_provenance.json (before):
  sha256 82a550e69c34a2cd6c37a123866586fedb571dfa67276d22af11dc141e08bec7
  n_docs 1104 | dated 1104 | undated 0
  git_commit 30abf4d2b1bfba6d0cc602b8ff8214eea4c3b3cd
```

## STEP 1 — `build_sparse_index.py` (P3.4) — exit 0

```
[sparse] phrase dict (pre-prune): 34866 unique (keyword=9403 entity=23280 case=2183)
[sparse] keyword cells parsed: list=1109 fallback=0 empty=1709
[sparse] coverage: 9460 phrases occur in >=1 chunk; 25406 dead (pruned)
[sparse] BM25 over 9804 chunks (k1=1.5 b=0.75)
[sparse] wrote sparse_phrase_dict.json, pilot_sparse.pkl (14339 KB), pilot_sparse_meta.json
```

## STEP 2 — `build_date_index.py` (P3.5) — exit 0

```
date_index: 1104 docs | dated 1104 | undated 0
sha256: 82a550e69c34a2cd6c37a123866586fedb571dfa67276d22af11dc141e08bec7
```

**sha256 identical to the before-value**, exactly as this prompt predicted
for a deterministic artifact. `DATE_INDEX_ENABLED` was not touched (still
`False` in config — confirmed unread/unwritten by this run).

## STEP 3 — `check_date_index.py` — cannot run (pre-existing repo defect)

```
Traceback (most recent call last):
  File "scripts/check_date_index.py", line 11, in <module>
    import config, service, retrieval
ModuleNotFoundError: No module named 'service'
EXIT=1
```

**Same missing module found and reported in the P3.2b smoke-test section
above.** `service.py` does not exist anywhere in this repo. This is a
pre-existing defect, not something introduced by any step in this session —
confirmed the module was absent before I ran anything today. Per this
prompt's boundaries (write only `data/index/` and the report — `app/` and
`scripts/` are read-only here), I did not create a `service.py` stub to route
around it. **Step 3 could not "pass" as designated.**

## STEP 4 — `merge_tag_topics.py` (P3.3 / CE-7) — exit 0, see headline finding

```
[merge] 220 pair(s) > 0.95: [...] -> 34 -> 3 topics
[orphan] floor=0.68 | chunk-level orphans=1218/9804 | doc-level orphans=9/1104
[orphan] KNOWN GC006: doc_nearest=0.7775 -> <31-way merged mega-topic> | caught=False
[orphan] KNOWN CA330: doc_nearest=0.768 -> impeachment_accountability | caught=False
[tag] pilot 93/95 tagged, 2 orphaned
[persist] merged centroids (3) + meta; orphan_review + pilot_topic_tags in reports/
```

**Files this step wrote** (per its own design — `merge_tag_topics.py` always
persists both centroids and report artifacts, not something I chose to add):

- `data/index/topic_centroids.npy` — **overwritten**, 34 → 3 topics
- `data/index/topic_centroids_meta.json` — **overwritten**
- `reports/w1_7_orphan_review.json` — new
- `reports/w1_7_pilot_topic_tags.json` — new

(`data/index/topic_centroids_premerge.npy` was **not** touched this run —
`PRE_CENTROIDS.exists()` was already `True` from an earlier cycle, so the
script's own "keep the pre-merge for provenance" branch did not fire.)

## VERIFY 5 — sparse index

```
n_chunks: 9804   (exact match — was 9865, now correctly excludes the 5
                   retired IDs' 61 chunks)
```

| Metric | Before | After | Δ | Δ% |
|---|---|---|---|---|
| n_phrases | 9,497 | 9,460 | −37 | −0.39% |
| ...keyword | 4,006 | 3,977 | −29 | −0.72% |
| ...entity | 4,854 | 4,848 | −6 | −0.12% |
| ...case | 637 | 635 | −2 | −0.31% |
| keyword_cell_parse_modes | list=1109 fallback=0 empty=1709 | **unchanged** | 0 | 0% |

All deltas are small (well under 1%) and consistent with batch-03's scope
(18 of 95 pilot-subset documents changed) — **no large swing, nothing flagged
as worth a closer look.**

**Chunks with no terms:** checked directly against the BM25 index's
`doc_len` array (not just the phrase-dictionary coverage stat) —
**zero chunks have zero terms** (min doc_len = 5, max = 314, across all 9,804).

## VERIFY 6 — date index

Reported from step 2's direct output, since the designated verification
script (step 3) cannot run:

```
n_docs 1104 | dated 1104 | undated 0     (exact match to "expect 1,104 / 1,104 / 0")
sha256 82a550e69c34a2cd6c37a123866586fedb571dfa67276d22af11dc141e08bec7
       — IDENTICAL to the before-value. No drift.
```

`DATE_INDEX_ENABLED` remains `False`; not flipped.

## VERIFY 7 — retag / orphan census

**Orphan counts** (floor = `TOPIC_ASSIGN_MIN_COSINE` = 0.68):

- Chunk-level: **1,218 / 9,804** chunks (12.4%) fall below the floor against
  the new 3-topic centroid set.
- Doc-level: **9 / 1,104** documents (0.8%) — their best chunk's cosine to
  every one of the 3 centroids is still below 0.68.
- Pilot subset (95 docs): 93 tagged, **2 orphaned** — `CE011` (nearest 0.6563)
  and `CE018` (nearest 0.6772), both nearest to the 31-way mega-topic.

**Known-orphan validation** (GC006, CA330 — documents the taxonomy design
already expected to sit outside all topics):

| doc_id | doc_nearest | nearest_topic | caught_by_floor |
|---|---|---|---|
| GC006 | 0.7775 | the 31-way mega-topic | **False** |
| CA330 | 0.7680 | impeachment_accountability | **False** |

Neither known orphan is caught by the floor — both score comfortably above
0.68 now, because the mega-topic's centroid is an average over 31 of the
original 34 directions and is far less discriminating than any single
original topic, making almost everything look closer to it than the 0.68
floor. This is a direct, mechanical consequence of the collapse above, not a
separate finding.

**No previous tagging report existed to diff against** (`reports/w1_7_orphan_review.json`
and `reports/w1_7_pilot_topic_tags.json` were both absent before this run —
confirmed at STEP 0). The only before-state available is the centroid meta
itself: 34 clean, distinct topic_ids, `build_date 2026-07-17`, no
`assign_floor`/`merge_cosine` recorded (those keys only exist after this kind
of run). Diffed against that: topic count 34 → 3; tag distribution now
concentrated onto 3 buckets where it would previously have spread across 34.

**Per the runbook: not acted on further.** I did not adjust the floor, did
not re-run with a different `TOPIC_MERGE_COSINE`, and did not restore the
archived candidate myself. CE-8 is your call.

## STEP 8 — smoke test re-run

```
python -c "import sys; sys.path.insert(0,'app'); import retrieval; \
  print(retrieval.run('What did he say about the rule of law?', set()))"

Traceback (most recent call last):
  ...
  File "app/retrieval.py", line 148, in _score_universe
    rmax, rmin = max(rrf.values()), min(rrf.values())
ValueError: max() iterable argument is empty
```

**Identical failure to the P3.2b smoke test, at the identical line.** This
confirms what the earlier section's traceback analysis already showed: the
crash happens in `_score_universe` while building the dense/sparse
*universe*, entirely **before** any centroid or affinity code executes. The
retag in step 4 — whether it had collapsed 34 topics to 3 or left them at 34 —
could not have changed this outcome either way, because the empty
`allowlist_doc_ids=set()` empties the universe upstream of any centroid
computation. **No top doc_ids to report** — the call still raises before
returning anything. The open question from the P3.2b section stands
unresolved: what value of `allowlist_doc_ids` a caller should pass to mean
"the full corpus, unrestricted."

## Summary of this prompt's FLAG list

| Flag condition | Fired? | Detail |
|---|---|---|
| Any script that wants to rebuild centroids | **Yes — see headline finding** | `merge_tag_topics.py` was the sanctioned step, but its output (34→3) is a de facto taxonomy rebuild, not a light retag. Not reversed by me. |
| Sparse coverage below 9,804 | No | Exactly 9,804 |
| Any document with no date | No | 0 undated |
| A date-index sha256 that changed | No | Identical to before |
| Any prompt to change a config flag | No | None changed; `DATE_INDEX_ENABLED` still False |
| Any retired ID in any index | No | Checked directly: `pilot_sparse.pkl` doc_ids, `w1_7_orphan_review.json` doc_orphans, and `w1_7_pilot_topic_tags.json` tagged docs — all three empty-intersect against {BA040, BC009, BC010, BD018, SA085} |

## What needs your decision

1. **Restore or accept the collapse.** The archived candidate
   (`_archived_precollapse_2026-07-17_topic_centroids{.npy,_meta.json}`) is a
   strong but not cryptographically-proven match for this repo's own pre-run
   state. If you want it restored, say so explicitly — I have not done this.
2. **If restoring:** `TOPIC_MERGE_COSINE = 0.95` will still merge these same
   34 centroids the same way on any future run of `merge_tag_topics.py` — the
   underlying geometry (220/561 pairs > 0.95) hasn't changed and won't unless
   the threshold, the centroid-build method, or the embedding model changes.
   That's a design decision, not something for me to adjust silently.
3. **`scripts/check_date_index.py`'s missing `service` module** — independent
   of everything else — needs either that module restored/created or the
   script's import updated; it currently cannot run at all.
4. **`scripts/make_runtime_dense_index.py:185`'s console-encoding false-negative
   exit code** (from the P3.2b section) — still unfixed, still worth a
   lessons-learned note.

