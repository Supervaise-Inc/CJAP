# P3 — rulings, and the corrected run prompts

**26 Sep 2026.** Prompt 0 is **done** and returned the right answer: no repair was needed. This file
answers the two questions that report ended on and replaces Prompts A / A2 / B in
`docs/p3/P3_next_phase_claude_code_prompt.md`. Prompt 0 in that file should not be run again.

---

## Ruling 1 — Python 3.12.13 and `C:\Reachy Mini Project 2026\.venv` are approved

**Claude Code was right to stop, and my Prompt 0 was wrong.** The "3.11.9" in it was the wake-word
venv — `wakeword\CJAP\.venv`, created from `Python311` for PLAN-0008, with no torch. It is a different
project. Running the install against it would have put a 2.5 GB CUDA stack into the wrong environment;
running it against the embedding venv would have rolled transformers 5.12.1 → 4.44.2 and
sentence-transformers 5.6.0 → 3.0.1, downgrading a stack that had just passed its own smoke test.

Every claim in that report checks out. Verified independently, from disk:

| | |
|---|---|
| `.venv/pyvenv.cfg` | `version = 3.12.13`, uv cpython-3.12 |
| `wakeword/CJAP/.venv/pyvenv.cfg` | `version = 3.11.9`, created at `…\OneDrive\Desktop\CJAP\.venv` |
| `.venv` packages | torch **2.5.1+cu121** · transformers **5.12.1** · sentence-transformers **5.6.0** · numpy **2.5.0** · pandas **3.0.3** · openpyxl **3.1.5** · rank_bm25 **0.2.2** · scikit-learn 1.9.0 · scipy 1.18.0 · huggingface_hub 1.21.0 · tokenizers 0.22.2 |
| `corpus_dense_meta.json.version_block` | `torch 2.5.1+cu121 · cuda 12.1 · cudnn 90100 · GTX 1650 · driver 536.67` — identical to the live venv |
| `app/embeddings.py:95` | `getattr(_MODEL, "get_embedding_dimension", None) or _MODEL.get_sentence_embedding_dimension` — the repo explicitly supports ST ≥ 5 |

So the environment that will run CE-6 is the environment that built the July matrix. **Nothing is to be
installed, upgraded or downgraded.**

## Ruling 2 — the pilot index was already settled; nothing to decide

The report asks to "settle the non-environmental blocker … that runbook's VERIFY 12 can't pass
unmodified". It was settled on 26 Sep, in the same file Prompt 0 came from. VERIFY 12 there already
reads *"CORRECTED 26 Sep: `data/index/pilot_dense.npy` is expected to be ABSENT after this prompt"*, and
**Prompt A2** then runs `scripts/make_runtime_dense_index.py` to build the runtime index from the new
matrix. `P3.2_CE-6_runbook.md` §5 and §7 carry the same correction, dated.

If a VERIFY 12 that demands a regenerated pilot index is still on screen, it is from the superseded
`docs/p3/P3.2_claude_code_prompt.md`, which now carries a SUPERSEDED banner. Read
`docs/p3/P3_next_phase_claude_code_prompt.md` and this file; ignore the other.

## What the report's finding *changes* — four additions

**1. The interpreter is absolute for every command, not just the dense build.** A bare `python` lands
on the uv 3.12 base with no torch. `check_date_index.py` imports `retrieval` → `embeddings` → torch, and
`merge_tag_topics.py` needs numpy. All of Prompts A, A2 and B use `%PY%`.

**2. The model must be pinned, because it currently is not.** The report says the model resolved via
`cache-snapshot` — the HF cache — **not** `C:\Reachy Mini Project 2026\models\bge-base-en-v1.5`, which is
what my earlier prompt assumed. Two copies of these weights exist on this machine, both with a
437,955,512-byte `model.safetensors`, and the `models/` copy carries a snapshot-hash subdirectory
`a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`, so they are probably the same download. *Probably* is not
attributable. Hash both, set `CJ_EMBED_MODEL_PATH` explicitly, and record the hash in the report.

**3. `version_block` pins torch and the driver — and nothing else.** No transformers, no
sentence-transformers, no numpy. Two consequences: the new run's full version set has to be recorded in
the report by hand, and the July rollback matrix was built under an unknown transformers/ST pair, so it
is a rollback, not a comparator. Say so once, in writing.

**4. P3.5 is probably already current.** `data/index/date_index_provenance.json` reads
`n_docs 1104 · dated 1104 · undated 0` at `git_commit 30abf4d`, i.e. rebuilt after batch-03, and its own
provenance says the artifact is deterministic. Expect the rebuild to be a confirmatory no-op with an
identical sha256, and treat a *different* hash as the finding.

---

## Prompt A — P3.2 / CE-6, the full-corpus dense re-embed

```
P3.2 / CE-6 — full-corpus dense re-embed after correction batch-03.
Run scripts/build_corpus_dense.py UNCHANGED. Do not modify it.
Prompt 0 is DONE (docs/p3/p3_env_repair_2026-09-26.md): no repair was needed, nothing was installed,
and the approved interpreter is Python 3.12.13 at

    set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe"

Use %PY% for EVERY python command below. A bare `python` lands on the uv 3.12 base, which has no torch.
Install nothing. Upgrade nothing. Downgrade nothing — transformers 5.12.1 and sentence-transformers
5.6.0 are correct and app/embeddings.py:95 depends on the ST>=5 API.

BOUNDARIES
- Read-only: corpus/, data/text/, data/csv/*.xlsx, corpus_snapshot.json. Never edit them.
- Write only inside data/index/ and a new report at docs/p3/p3_2_dense_rebuild_2026-09-26.md.
- Do NOT run build_centroids.py or build_centroids_fullcorpus.py. Batch-03 is a correction; the topic
  map is not what changed, and rebuilding it in the same run makes CE-12 uninterpretable.
- Do NOT edit corpus/voice/voice_card.md. The staged fix at
  docs/p3/voice_card_header_proposed_2026-09-25.md waits until after CE-12.
- Do NOT restore data/index/_archived_precorrection_2026-07-17_pilot_dense*.
- One encoder, one dimensionality for the whole corpus. If anything forces a different model, dim or
  backend mid-run: STOP.

PRE-FLIGHT — report every value, then stop if any check fails
1. %PY% -c "import sys,torch,transformers,sentence_transformers,numpy; print(sys.version); \
   print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0)); \
   print(transformers.__version__, sentence_transformers.__version__, numpy.__version__)"
   Expect 3.12.13 · 2.5.1+cu121 · 12.1 · True · GTX 1650 · 5.12.1 · 5.6.0 · 2.5.0.
   Record all of it: corpus_dense_meta's version_block captures torch and the driver only, so this line
   is the ONLY record of the transformers/ST/numpy set the matrix was built under.
2. config: EMBED_MODEL_ID == "BAAI/bge-base-en-v1.5", EMBED_DIM 768, EMBED_NORMALIZE True,
   EMBED_BACKEND cuda_fp32, EMBED_BATCH_SIZE 8. Ratified at P3.1. Do not change them.
   (EMBED_NORMALIZE=True on a model whose modules.json already ends in Normalize is intentional and
   idempotent. Do not "fix" it.)
3. corpus/index/chunk_index.json: expect 1,104 documents and 9,804 chunks; cross-check that
   corpus/index/chunks.jsonl has 9,804 lines. If either reads 8,887 or 9,865 you are on an old chunk
   set — STOP.
4. %PY% scripts/verify_pin.py must exit 0 before you start. Run it from the repo root; it inserts the
   root on sys.path itself. If it does not exit 0, STOP: the corpus is not in its pinned state.
5. data/index/pilot_dense.npy must NOT exist. It was built 17 July, before batch-03 changed 18 of the
   95 pilot-subset documents. With it absent the script records
   sanity = "skipped (no prior pilot index)" and writes NO pilot index at all, because new_pilot stays
   None (build_corpus_dense.py:155-192). Its closing line "pilot sliced+overwritten" is wrong in that
   case. Expect NO pilot index after this prompt — Prompt A2 creates it. If it has reappeared, move it
   aside; do not delete it.
6. PIN THE MODEL. It currently resolves via the HF cache, not the models/ directory, and two copies
   exist on this machine. Do this:
     a. Report the sha256 of the resolved cache snapshot's model.safetensors AND of
        "C:\Reachy Mini Project 2026\models\bge-base-en-v1.5\model.safetensors".
     b. If they match, set  CJ_EMBED_MODEL_PATH="C:\Reachy Mini Project 2026\models\bge-base-en-v1.5"
        so the run resolves via config-path, and confirm app/embeddings.py prints how == "config-path".
     c. If they DIFFER, STOP and report both hashes. Two different sets of weights on one machine is
        the finding, and picking one silently would make the matrix unattributable.
   Record the chosen sha256 in the report either way.
   Also set HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1. huggingface.co returns 403 here; a silent hub
   fallback would waste the run.
7. Report torch.cuda.is_available(), device name and free VRAM from nvidia-smi. Expect ~3.9 GB free on
   the GTX 1650. If CUDA is not available, STOP and ask — cpu_fp32 is ~0.27 chunks/s on this machine
   (about ten hours) and the resume checkpoint is keyed on the backend, so a CPU run cannot later be
   resumed on GPU.
8. MANDATORY BACKUP. Copy data/index/corpus_dense.npy and corpus_dense_meta.json to
   data/index/_archived_precorrection_2026-07-17_* BEFORE anything runs. This is not housekeeping:
   build_corpus_dense.py ends with `except Exception: for p in out: unlink(p)` and `out` includes
   CORPUS_DENSE_PATH, so a late failure DELETES the existing matrix. Report the exact backup paths.
   Note in the report that this July matrix is a ROLLBACK, not a comparator: its transformers/ST
   versions were never recorded, so it cannot be used to validate the new one.

RUN
9. %PY% scripts/build_corpus_dense.py
   Stream progress. On a GTX 1650 at batch 8 this should be tens of minutes, not hours — if the rate
   implies more than ~2 hours, stop and report the chunks/s, because that suggests it is on CPU.
   If interrupted, the checkpoint resumes — do not change the model, backend or normalize flag between
   attempts or the checkpoint is discarded and the run starts over.

VERIFY — all must hold
10. data/index/corpus_dense_meta.json:
       model_id == "BAAI/bge-base-en-v1.5" · dim == 768 · n_chunks == 9804
       backend  == cuda_fp32
       pilot_parity_sanity == "skipped (no prior pilot index)"
       version_block torch == 2.5.1+cu121
11. corpus_dense.npy shape == (9804, 768), dtype float32, every row unit-norm
    (max |‖v‖ − 1| < 1e-5). Report the actual max deviation.
12. The chunk_ids in the meta match corpus/index/chunks.jsonl exactly — same set, same order.
13. data/index/pilot_dense.npy is expected to be ABSENT. Confirm that it is. If it exists, something
    re-created it and the two indexes may disagree — STOP.
14. Spot-check semantics, not shapes. Embed "What did he say about the rule of law?" with
    config.EMBED_QUERY_PREFIX, take the top 5 chunks by cosine against the new matrix, print their
    doc_ids and titles. They should be plausibly about the rule of law. If they look random, the prefix
    or the normalisation is wrong — STOP.
15. Confirm none of BA040, BC009, BC010, BD018, SA085 owns any chunk in the meta's chunk_ids.

REPORT — write docs/p3/p3_2_dense_rebuild_2026-09-26.md
16. Every pre-flight value including the full version set from 1 and the model sha256 from 6; backend
    and device; wall-clock and chunks/s; verify results 10-15; the exact backup paths; and the one-line
    note that the July matrix is a rollback, not a comparator.

FLAG, DO NOT FIX
- Any failed pre-flight · the two model copies disagreeing · CUDA unexpectedly absent · the model
  resolving to "hub" · n_chunks != 9804 · any non-unit-norm row · a parity value other than
  "skipped (no prior pilot index)" · any retired ID present.
Report and stop. Do not rebuild the topic map, re-chunk, or edit the corpus.
```

---

## Prompt A2 — P3.2b, restore the runtime dense index

```
P3.2b — make the runtime dense index from the new full-corpus matrix.
Precondition: docs/p3/p3_2_dense_rebuild_2026-09-26.md exists and every check passed. If not, STOP.
Use %PY% ("C:\Reachy Mini Project 2026\.venv\Scripts\python.exe") for every command.

WHY: app/embeddings.load_dense_index() reads config.DENSE_INDEX_PATH (data/index/pilot_dense.npy), not
corpus_dense.npy, and app/retrieval.py:54 reads meta["chunk_ids"] AND meta["doc_ids"]. P3.2 wrote no
pilot index, so retrieval is offline right now. Pointing CJ_DENSE_INDEX_PATH at corpus_dense.npy does
NOT work — that meta has no doc_ids key and retrieval raises KeyError. Do not try it. This is the ruling
recorded in P3.2_CE-6_runbook.md §7.

BOUNDARIES
- Run scripts/make_runtime_dense_index.py as it is. Do not edit it, do not hand-write an index.
- Write only data/index/pilot_dense.npy, data/index/pilot_dense_meta.json, their backups, and the
  report. Nothing else. No re-embedding.

STEPS
1. %PY% scripts/make_runtime_dense_index.py
   It verifies before it writes: shape vs chunk_ids, dim vs EMBED_DIM, model_id vs config, unit norms,
   every chunk_id resolvable in chunks.jsonl, no extra chunks, no retired doc_id present. On any
   failure it writes nothing and exits non-zero. If it exits non-zero, STOP and report the message
   verbatim — it is telling you the matrix and the chunk store disagree.

VERIFY
2. data/index/pilot_dense_meta.json: n_docs == 1104, n_chunks == 9804, dim == 768,
   model_id == "BAAI/bge-base-en-v1.5", len(chunk_ids) == len(doc_ids) == 9804,
   allowlist_version reads "full-corpus (no allowlist; supersedes pilot_subset_frozen_v4)".
3. None of BA040, BC009, BC010, BD018, SA085 appears in doc_ids.
4. End-to-end smoke test through the real code path, not numpy directly:
     %PY% -c "import sys; sys.path.insert(0,'app'); import retrieval; \
       print(retrieval.run('What did he say about the rule of law?', set()))"
   Report what comes back. A KeyError 'doc_ids' means the meta is wrong. An error from the centroids is
   expected-ish — they are stale until P3.3 retags — so note it and continue to Prompt B.

REPORT — append a "P3.2b runtime index" section to the same docs/p3/ report
5. The counts from 2, the retired-ID check from 3, the smoke-test output, the backup paths the script
   printed.
6. State plainly, in one line, that the runtime retrieval universe has moved from the frozen
   95-document pilot subset (827 chunks) to all 1,104 documents (9,804 chunks), and that this needs an
   entry in the decisions register. It is a change of behaviour, not a repair.

FLAG, DO NOT FIX
- The script exiting non-zero · any retired ID present · n_docs != 1104 · retrieval raising anything
  other than the known stale-centroid case.
```

---

## Prompt B — P3.4, P3.5, P3.3

```
P3.4, P3.5 and P3.3 — the remaining index builds on the new dense matrix.
Precondition: Prompt A2 finished and the runtime index verifies. If not, STOP.
Use %PY% ("C:\Reachy Mini Project 2026\.venv\Scripts\python.exe") for every command. Note step 3 imports
app/retrieval, which loads the runtime dense index — it cannot run before A2.

Dependencies are already present in that venv and must not be installed or changed:
rank_bm25 0.2.2, openpyxl 3.1.5, numpy 2.5.0, scipy 1.18.0, scikit-learn 1.9.0.
build_sparse_index.py reads the curated xlsx through openpyxl directly, not pandas, so pandas 3.0.3 is
not in the path.

BOUNDARIES — as before. Read-only corpus/, data/text/, data/csv/. Write only data/index/ and the
report. Do NOT rebuild centroids. Do NOT edit voice_card.md. Do NOT change any config flag.

BEFORE YOU START
0. Record the current data/index/pilot_sparse_meta.json (n_chunks, n_phrases,
   n_phrases_by_provenance, keyword_cell_parse_modes) and the current
   data/index/date_index_provenance.json sha256. These are the before-values for the diffs below.

STEPS
1. %PY% scripts/build_sparse_index.py     # P3.4 — BM25 + atomic-phrase dictionary
2. %PY% scripts/build_date_index.py       # P3.5
3. %PY% scripts/check_date_index.py       # P3.5 verification — must pass
4. %PY% scripts/merge_tag_topics.py       # P3.3 / CE-7 — RETAG ONLY against the existing 34
                                          # centroids. Never build_centroids.py.

VERIFY
5. Sparse: n_chunks must now read 9804. It read 9,865 before — that was the pre-correction chunk set,
   including the 27 chunks of the 5 retired IDs. Diff n_phrases and keyword_cell_parse_modes against
   the before-values from step 0 and report the deltas; the phrase dictionary is built from the curated
   xlsx, which batch-03 changed, so some movement is expected and a large swing is worth a look. Report
   any chunk with no terms. The file is named "pilot_" for historical reasons but has always covered
   the full corpus.
6. Dates: report n_docs, dated and undated. Expect 1,104 / 1,104 / 0 — every corpus document now
   carries a text YYYY-MM-DD date. NOTE: date_index_provenance.json ALREADY reads 1104/1104/0 at
   git_commit 30abf4d, and the artifact is deterministic by its own provenance, so expect the rebuilt
   sha256 to be IDENTICAL to the before-value. If it differs, that is the finding — report both hashes
   and what moved. DATE_INDEX_ENABLED is false in config; building does not enable it, and enabling it
   is a separate decision. Do not flip the flag.
7. Retag: report the orphan census — documents whose best centroid cosine falls below the config floor
   — and the count per topic, diffed against the previous tagging. Do NOT act on it. CE-8 is a human
   decision and for a correction batch the answer is already "retag only".
8. Re-run the A2 smoke test now that the centroids are retagged:
     %PY% -c "import sys; sys.path.insert(0,'app'); import retrieval; \
       print(retrieval.run('What did he say about the rule of law?', set()))"
   It should now return sensibly with no centroid error. Report the top doc_ids.

REPORT — append to the same docs/p3/ report: counts, timings, the sparse and date diffs from 5-6, the
retag diff from 7, and the smoke-test result from 8.

FLAG, DO NOT FIX
- Any script that wants to rebuild centroids · sparse coverage below 9,804 · any document with no date ·
  a date-index sha256 that changed · any prompt to change a config flag · any retired ID in any index.
```

---

## After Prompt B

CE-11 is already drafted: `eval/results/gold_additions_batch03_2026-09-26.csv`, 14 rows, copy in
`batch-03/`. Then CE-12, the promotion eval. Only after CE-12 does the staged voice-card fix (R-1) get
applied.

**One thing worth doing before CE-6 runs**, because it is cheap now and expensive later: **C-11**.
`BC018`'s curated row was never re-derived after the C-7 repair — it still says "short fragment" and
"Unnamed honoree" where the restored text names *Justice Regino C. Hermosisima, Jr.* That summary is
appended to the `.md` and therefore chunked and embedded. Fixing it after the embed means embedding
again.


---

## Why 1,104 and not ~1,290 — the counts in Prompt B are correct

Asked 26 Sep. **1,104 is right for this run.** Nothing is missing; batch-04 is not merged yet, and it
must not be merged during this run.

### The arithmetic, measured from disk 26 Sep

| | Now | Batch-04 adds | After P6 |
|---|---:|---:|---:|
| Columns | 785 | 18 | **803** |
| Book chapters | 131 | 168 | **299** |
| Speeches | 153 | 0 | 153 |
| Biography chapters | 35 | 0 | 35 |
| **Active corpus documents** | **1,104** | **186** | **1,290** |
| Retired IDs (rows kept, no corpus file) | 5 | 0 | 5 |
| Rows in the four pinned sheets | 1,109 | 186 | 1,295 |

Chunks track documents: **9,804 now**, and roughly 12,000–13,000 after P6. So Prompt A's 9,804 and
Prompt B's 1,104 / 9,804 are the correct expected values today, and a script reporting 1,290 during this
run would mean batch-04 leaked into the pinned corpus — which is the failure, not the goal.

### "12 books" counts works; "10 books" counts volumes. Both numbers are right

This is the whole source of the confusion. *With Due Respect* is one work in seven volumes.

**In the corpus now — 10 volumes, 4 works:** With Due Respect Vol. 1–7 · A Centenary of Justice ·
Justice and Faith · The Bio-Age Dawns on the Judiciary.

**Batch-04 brings 8 new works** (168 chapters): Liberty and Prosperity 35 · Transparency, Unanimity &
Diversity 24 · Love God, Serve Man 22 · Judicial Renaissance 21 · Reforming the Judiciary 20 · Leveling
the Playing Field 20 · Leadership by Example: The Davide Standard 14 · Battles in the Supreme Court 11 ·
plus 1 into A Centenary of Justice (BA108, Ch. 20, superseding retired BA040).

**4 + 8 = 12 works** — which is exactly the "all 12 books" target. As volumes it is 18.

### Why batch-04 is not merged yet — CE-17

Batch-03 is a **correction**. Its promotion eval (CE-12) measures the corrections against the standing
baseline. Merging 186 new documents into the same run would make any movement in the eval
uninterpretable: nobody could say whether the numbers moved because the repairs worked or because 186
new documents arrived. CE-17 is the rule that a correction runs as its own batch, never mixed with new
material.

Order: finish P3 on 1,104 → CE-11 → CE-12 → CE-13/14 → **P6 merges batch-04** → re-chunk, re-embed,
re-index at 1,290 → eval again.

**The cost of doing it in this order has collapsed, which is worth noticing.** The reason to fear two
embed passes was the ~10-hour CPU estimate. On the GTX 1650 in the approved venv a full pass is tens of
minutes. Two clean, attributable runs now cost about an hour of GPU time — so there is no longer a
performance argument for cutting the corner.

### The one number that is genuinely short: columns

Even after P6 it is **803 columns, not ~1,000.** Measured coverage: 2011:36 · 2012–2025 at 51–53 each ·
2026:20, running 17 Apr 2011 – 18 May 2026 with **no missing year inside that range**. The column began
**11 Feb 2007** (BA031 is his first Inquirer column). Feb 2007 – Apr 2011 at roughly weekly cadence is
**~222 columns that were never sourced**. 803 + ~222 ≈ 1,025 — which is where "almost 1,000 columns"
comes from.

That gap is a **sourcing task, not a pipeline task**: nothing in P3, P6 or the eval will produce those
documents. It is described in `docs/p1/source_inventory.md` and belongs in a batch-05 intake against the
Inquirer archive.

### No change to Prompt B

Run it as written. Add one line to its report: the expected counts for this run are 1,104 documents and
9,804 chunks, and they become ~1,290 / ~12–13k only after P6.
