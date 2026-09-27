# Batch-04 report

Batch-04 (CE-4 → CE-10, 22–27 September 2026) rebuilt the corpus, retagged it against a taxonomy
derived from the whole thing rather than a 79-document pilot, and delivered two packaged outputs: a
reading copy for the Foundation (`knowledge-base/`, Phase 6) and a data bundle for the robot
(`deploy/pi/bundle/`, Phase 7). All work is on `deliverable/2026-09`; the final commit of this batch is
Phase 7's.

## What grew

| | before (22 Sep) | after (27 Sep) |
|---|---:|---:|
| documents | 1,104 | 1,290 |
| columns | 785 | 803 |
| speeches | 153 | 153 |
| biography | 35 | 35 |
| books — chapters | 131 | 299 |
| books — works | 4 (*A Centenary of Justice*, *Justice and Faith*, *The Bio-Age Dawns on the Judiciary*, *With Due Respect* as one 7‑volume series) | 12 (the 4 above unchanged, 8 more added; 18 distinct titles if *With Due Respect*'s 7 volumes are counted individually) |
| chunks (`corpus/index/chunks.jsonl`) | 9,804 | 13,549 |
| taxonomy dimensions | 35 | 30 |

The taxonomy figure needed a direct check: batch-04's own prompts cite 34; the committed v1 file
(`corpus/voice/topic_map_v1_2026-05-25.json`) has 35. 35 → 30 is what is actually on disk. Of the 30,
**10 ids survive from v1** unchanged (`asean_law_association`, `bar_exam_and_legal_education`,
`death_penalty_and_echegaray`, `faith_journey`, `foundation_for_liberty_and_prosperity`,
`impeachment_accountability`, `international_law_disputes`, `jbc_discernment_and_appointment`,
`judicial_reform`, `twin_beacons_doctrine`) and **20 are newly derived** from the full corpus.

## The raw-to-centred cosine change

Raw cosine in this embedding space sits on a noise floor: two independent random 30-document groups
already score 0.984 cosine (`taxonomy_v2_PROPOSAL.md` §1) — almost indistinguishable from a real
topical match. That is what collapsed the v1 taxonomy from 34 candidate merges down to 3 surviving
topics at `TOPIC_MERGE_COSINE = 0.95` (P3.3): the merge threshold could not tell a real duplicate from
two unrelated document sets. CE-10 centres every centroid cosine on the corpus mean
(`app/centering.py`; `data/index/corpus_mean.npy`) before comparing, which removes the shared
component every chunk has and restores separation — the independence check on the new 30 dimensions
tops out at 0.6935 between the closest pair, comfortably under the 0.75 merge line.

**P3.3's two failing bullets are now met:** every document is tagged (route_source `matcher` 1,045 +
`affinity` 227 + `orphan` 18 = 1,290 — see [`knowledge-base/MANIFEST.md`](../knowledge-base/MANIFEST.md)
for the full breakdown), and the tags survive a from-scratch regeneration
(`scripts/apply_topic_paths.py` reproduces the same route_source split byte-for-byte against the
committed corpus).

## Defects found and fixed along the way

- **Newline defects** — `scripts/generate_corpus_files.py` and `scripts/chunk_corpus.py` wrote corpus
  `.md`/`.json` and `chunk_index.json` in the platform newline instead of LF (`8ede4bf`, `fa36356`).
- **`load_docs()` never read a book chapter** — `scripts/build_topic_map.py`'s document loader globbed
  `columns/**`, `speeches/**` and `biography/**` and stopped there; the topic map (and everything built
  on it, including `apply_topic_paths.py`) was blind to 299 of 1,290 documents until the `books/**` glob
  was added (`cf5950a`, 991 → 1,290 documents seen).
- **The router prompt and its fail-safe route were still on v1 topic ids** — `router_prompt.md` named
  topics that no longer existed post-CE-10, and the router's fail-safe fallback pointed at `rule_of_law`,
  an id CE-10 removed. Both were moved to v2 ids, and `robot_identity_meta` — which has no centroid and
  cannot be reached by cosine — was kept reachable as an intent (`1a795f6`, `5d38812`).

## Phase 6 and Phase 7 outputs

- **`knowledge-base/`** (Phase 6): 3,879 files, 62.4 MB, the Foundation's reading copy — source text,
  enriched CSVs, the corpus cards, the topic map. Built and validated by
  `scripts/build_knowledge_base.py`.
- **`deploy/pi/bundle/`** (Phase 7): 1,315 files, 516 MB, the data the robot's retrieval pipeline reads
  — the chunk store, the four search indexes, the corpus cards (no per-document `.md` — see below), and
  a 419 MB sentence encoder. Built and validated by `scripts/build_robot_bundle.py`. See
  [`deploy/pi/bundle/MANIFEST.md`](../deploy/pi/bundle/MANIFEST.md) for the file-by-file reasoning and
  [`batch-04/ph7_analysis/`](ph7_analysis/) for the traces and measurements behind it.

## Open items, plainly

- **Two pipelines exist, and this bundle serves the one that is not yet wired to the robot.** The
  systemd unit the robot actually runs (`main_voice_robot.py --wake`) calls `app/answer_pipeline.py` —
  a Claude Haiku router + Claude Sonnet composer that needs a live API key for every turn, including
  identity-probe detection, and touches none of `data/index/` or `models/`. The pipeline this bundle
  serves — `app/service.py` + `app/retrieval.py`, a deterministic dense+BM25+centroid retrieval with
  zero LLM calls before composition, and the reason this batch built an 838 MB-then-419 MB encoder
  bundle at all — is what config.py calls the architecture that "runs TODAY", but **`app/service.py`
  itself is not committed to git** (present on disk, dated 18 July, never checked in). Landing it on
  `pi/deployment-snapshots` and pointing the systemd unit at it is a prerequisite for this bundle to do
  anything on a real robot; it is a code change, not a data one, and is outside this batch's scope.
- **The identity intent does not yet route to itself in the new pipeline.** `app/retrieval.py`'s local,
  no-LLM `input_gate()` correctly *detects* an identity probe ("Are you an AI?" → `identity_probe`), but
  `app/service.py`'s `answer()` never consumes that signal — an identity question is scored against the
  30 topic centroids like any other and lands wherever its low cosine (≈0.15–0.20, near the 0.12
  out-of-scope floor) happens to point, not at the `robot_identity_meta` persona treatment the deployed
  (`answer_pipeline.py`) pipeline gives it. The *data* the persona treatment needs — the
  `intents.robot_identity_meta` node's definition text — is present in `topic_map.json` and in the
  bundle; the code path to use it in the new pipeline does not exist yet. Confirmed on 2 identity
  probes in `batch-04/ph7_analysis/results/runtime_trace.json`.
- **Routing top-1 86.7%, four dimensions never win their own question** — `judiciary_milestones_and_tributes`,
  `public_funds_budget_and_bank_evidence`, `ill_gotten_wealth_and_the_pcgg`, and **`twin_beacons_doctrine`
  — the flagship concept — which the router sends to `international_law_disputes`.** Top-3 is 86.7%
  short-form / 100% on 60 longer descriptive questions. Full numbers and the pre-registered question set
  are in [`knowledge-base/README.md`](../knowledge-base/README.md) §7 and
  [`batch-04/ph6_analysis/results/routing_check.json`](ph6_analysis/results/routing_check.json).
- **The frozen-40 retrieval set drifted**: 14 of 40 selected result sets changed after the move to the
  30-dimension map, and gold hit@10 fell 2.9 points (hit@1/3/5 unchanged).
- **Biography chunks never won the top-selected chunks in 22 test queries** — including two questions
  built directly from biography chapter titles (`GC012`, `GC020`). This does not change what the bundle
  ships (`chunks.jsonl` carries every format's text regardless of what any one query selects), but it is
  a retrieval-quality gap worth a look alongside the routing numbers above.
  (`batch-04/ph7_analysis/results/runtime_trace.json`.)
- **18 orphaned documents** carry no topic at all (11 columns, 2 books, 3 speeches, 2 biography —
  `GC015`, `GC018`), and a further 22 keep a keyword-matcher route despite sitting below the 0.31
  affinity floor.
- **~222 Inquirer columns from February 2007 – April 2011 remain unsourced.** They are outside this
  batch, not lost by it.
- **`CE-11 → CE-14` are the gate before the robot is demonstrated** — this batch measured routing, it
  did not validate it end to end, and did not touch the router.
