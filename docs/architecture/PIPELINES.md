# The two pipelines

There is no other document in this repo that says which pipeline is live. This one does, and it is
meant to stop the next person rediscovering Phase 7's finding the hard way: **the robot has, until
Phase 8, run a pipeline that never touches the corpus rebuild batch-04 spent six phases producing.**

As of Phase 8, both pipelines exist in `app/`, both are committed, and one is selected by
`config.CJ_PIPELINE` (`legacy` | `retrieval`, default **`legacy`**). Neither imports the other.

## The comparison

| | `answer_pipeline.py` (`legacy`, default) | `retrieval.py` + `service.py` (`retrieval`) |
|---|---|---|
| entry point | `main_voice_robot.py` → `_handle_turn_streaming` → `speech_streaming.stream_turn()` | `main_voice_robot.py` → `_handle_turn_retrieval` → `service.answer()` |
| routing | Claude Haiku call, graded against `router_prompt.md`'s system prompt (~2,400 tokens, cached) | local cosine of the query against 30 centred topic centroids — no network, no LLM |
| identity intent | `input_gate()` (Haiku call) flags `identity_probe` → `force_meta_routing()` → `robot_identity_meta`'s persona text, 120-token cap | `retrieval.input_gate()` (a regex, no LLM) flags it → `service._answer_identity()` → the same intent's persona text, the same 120-token cap ([Phase 8] closed this — Phase 7 found it detected but unused) |
| document selection | `_select_source_doc_ids()`: whole documents, by `topic_map.json`'s per-topic `doc_ids` lists (matcher membership only) | `retrieval.retrieve()`: dense (bge-base cosine) + BM25, reciprocal-rank fused, top-p nucleus cutoff over **passages**, not whole documents |
| context given to the composer | up to 3 whole documents' curated fields (summary, stances, anecdotes, signature phrases) — never the raw body | the top-p nucleus of raw passage **text** from `chunks.jsonl` |
| model calls before composition | **1** (the Haiku router; 2 including the Haiku input gate) | **0** |
| composition | Claude Sonnet, one shot, then a Haiku fidelity check | Claude Sonnet, streamed, no fidelity check |
| needs network | yes — every turn, for the router/gate call alone | no, until the single composer call |
| reads `data/index/` | no | yes — `pilot_dense.npy`, `pilot_sparse.pkl`, `sparse_phrase_dict.json`, `topic_centroids.npy`, `corpus_mean.npy` (traced: `batch-04/ph7_analysis/results/runtime_trace.json`) |
| reads the encoder (`models/bge-base-en-v1.5`) | no | yes — one query embedding per turn |
| reads `corpus/**/<id>.json` | yes, always (`CorpusArtifacts.load_raw_doc()`) | only if `config.COMPOSER_SIGNATURE_PALETTE=1` (dark by default) |
| reads `corpus/**/<id>.md` | no — `load_doc_body()` is defined, never called | no |
| reads `corpus/voice/router_prompt.md` | yes (the Haiku router's system prompt) | no |
| out-of-scope handling | a 3-way Haiku classifier (`identity_probe` / `in_corpus` / `out_of_corpus`); `out_of_corpus` skips the router and composer entirely for a canned deflection | no hard classifier; `OUT_OF_SCOPE_THRESHOLD` only re-weights the topic prior toward a uniform fallback, and a system-prompt instruction (`COMPOSER_OOS_DECLINE_TEXT`) asks Sonnet to decline in prose |
| canned answers, fillers, answer/language gates, entity post-processing, speaker ID | present (see `docs/architecture/PARITY_MATRIX.md`) | absent |

## What each costs, measured on this laptop (not the Pi)

**`retrieval` path**, warm (model already resident), five representative queries
(`app/retrieval.py`'s own `run_timed()`, GPU present):

| stage | typical | range observed |
|---|---:|---:|
| query embedding (bge-base, GPU) | ~45 ms | 42–60 ms |
| BM25 sparse search | ~120 ms | 90–164 ms |
| dense search | ~50 ms | 43–64 ms |
| RRF fusion | ~33 ms | 29–39 ms |
| centroid scoring | ~130 ms | 105–203 ms |
| top-p cutoff | ~50 ms | 25–151 ms |
| **retrieval total** | **~470 ms** | 380–596 ms |

The **first** call after process start additionally pays one model load: **~44 s** on this laptop's GPU
(`sentence-transformers` reading `models/bge-base-en-v1.5` and moving it to CUDA). **The Pi has no GPU.**
Both the per-query numbers above and the one-time load will be materially slower there — CE-11's fresh
baseline (Step 6) should include a real Pi measurement, not this laptop's.

**`legacy` path:** no equivalent measurement exists in `eval/results/` (its cost/latency tables —
`cost_per_query.csv`, `compose_latency_per_query.csv` — hold a schema and one `SELFTEST` stub row, not
production data), and it cannot be measured here at all (every turn needs `ANTHROPIC_API_KEY`, which
this environment does not have). What is certain structurally: it makes at least one network round trip
(the router; two counting the input gate) before the composer even starts, where `retrieval` makes none.

## One correction to the batch record

`batch-04/BATCH-04_REPORT.md` said the taxonomy went 35 → 30; earlier batch-04 prompts said 34 → 30. Both
are right about different things: v1 **defined** 35 topics in `topic_map_v1_2026-05-25.json`, but only
**deployed** 34 centroids (`topic_centroids_meta.n_topics` in the v1 build was 34 — `robot_identity_meta`
was already excluded from the centroid matrix even in v1, it just hadn't yet been formally moved to an
`intents` block). v2 defines 30 and deploys 30, with `robot_identity_meta` explicitly an intent. Ten
topic ids survive from v1 to v2 unchanged; twenty are new (`batch-04/BATCH-04_REPORT.md` names both).

## Architecture note, for anyone who finds an older `config.py` comment confusing

`config.py`'s own module docstring already describes this exact fork — "[NEW-ARCH] the develop retrieval
engine that runs TODAY" vs. "[BASELINE] ... Consumed ONLY by the `CJ_ALLOW_LEGACY`-guarded
`app/answer_pipeline.py` path ... NOT by the develop pipeline" — but it is describing a different branch
(`develop`, on a separate, older checkout at `C:\Reachy Mini Project 2026`), not `deliverable/2026-09`,
and `CJ_ALLOW_LEGACY` was never implemented here. `config.CJ_PIPELINE` (this phase) is the real flag on
*this* branch; the docstring's language was aspirational until now.

## When this flips

`legacy` stays the default until **CE-11 → CE-14** validate the retrieval stack against a gold set on
the full 1,290-document corpus. See `docs/p3/README.md` and `batch-04/BATCH-04_REPORT.md` for the three
numbers that gate stayed open.
