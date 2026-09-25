# Phase 3 (revised) — close the comparator gaps, then stage CE-11

**26 Sep 2026. Supersedes Phase 3 in `CJAP_remaining_work_claude_code_prompts.md`, and corrects
Phase 4's comparator.** Everything here is **$0** — no API calls, no token spend.

## Assessment of the Phase 2 run

Executed correctly and reported well. Three of my errors were caught, all three handled the right way:
copied in full and flagged, rather than silently reconciled.

1. **`eval/results` holds 94 files, not 90.** I counted top level only; there are three subdirectories
   (`incoming/`, `postreboot/`, `stt_bench_clips/`). CC copied all 94.
2. **Step 4's premise was wrong.** `eval/` did not exist in this repo at all, so the additions CSV could
   not "already exist" there. It arrived through the bulk copy because the working repo had it, and CC
   proved it sha-identical to `batch-03/gold_additions_batch03_2026-09-26.csv`
   (`9d085462997965ee…`). Nothing was lost.
3. **`check_date_index.py` had a second missing dependency.** `service.py` was the first blocker and is
   fixed; the NO-REGRESSION GATE then needs `reports/pilot-eval subset/draft_queries_v1.json`. CC
   refused to copy it because it was not on the list, which is exactly right. Coverage and idempotency
   both passed on the way through: **1104 / 1104 / 0**, sha `82a550e69c34` matching the P3.5 build.

Phase 2's own checks are sound: five harness files sha-matched, all eight modules import,
`verify_pin.py` PASS at 1,109 docs, nothing written to the working repo.

## Two things that must be fixed before CE-12, one of them mine

**Phase 1 was skipped.** `data/index/topic_centroids.npy` is still `(3, 768)` with `merged_pairs: 220`
and `merge_cosine: 0.95`. No `_collapsed_2026-09-26_*` archive exists. Phase 3 step 5 checks the CE-11
rows' `routed_topic` values against the live topic list, and with 3 collapsed topics that fails for all
14 rows. **Run the P3.3 recovery first.**

**My Phase 4 named the wrong comparator, and this one would have cost money for nothing.** I told CC
that `arch_baseline_v2.json` was the expected standing baseline. Reading it:

```
arch_baseline_v2.json   run 2026-07-04   verify.parity_A1.universe = 827
```

Every query record in it carries `universe: 827` — the 95-document pilot. The bge-base ratification
happened later (the archived bge-base pilot index is dated 17 July; the bge-large archives are 29 June),
and `eval/results/arch_baseline_v4_retrieval.json` says plainly:

```
"anchor": "arch-baseline-v4 (embedder = bge-base-en-v1.5, ratified by Dok)"
```

So **v2 is a bge-large, 827-chunk, compose-latency baseline.** The lineage that matches the current
regime is **arch-baseline-v4 / v4.2**, and `eval/results/arch_baseline_v4_2_provenance.json` is the
full-corpus promotion gate record from 18 July, with machine-verified numbers:

| | |
|---|---|
| recall@1 · @5 · @chunks_sent · @10 | **0.588 · 0.882 · 0.941 · 0.971** (v4 gold, N=34, scope-aware) |
| Health gate | 3/3 PASS — A1 rule-of-law, D21 museum, E28 roe-v-wade |
| Anchor artifacts | `corpus_dense` (9865, 768) bge-base · `topic_centroids` (34, 768) · `pilot_dense` **(827, 768)** · `pilot_sparse` batch-02 |

And the harness for that comparison already exists: **`scripts/run_ops2_c1.py`** —
*"OPS-2 C1 — **$0 retrieval-only** drift check vs the canonical v4 anchor … grades the live pipeline on
the frozen 40-query set vs v4 gold and RECORDS the recall deltas, so drift … can be measured and
attributed."* It takes a label and merges into `eval/results/ops2_c1_drift.json`. It is exactly the
instrument batch-03 needs, it costs nothing, and it was not on my copy list.

**The compose run is a separate, later question.** CE-12's promotion decision is a retrieval-quality
decision and it is free. Paying Sonnet for 40 compositions against a bge-large baseline would have
measured the encoder, the universe and the corpus change all at once.

### The universe confound — introduced by me in Phase A2

The v4.2 anchor's `pilot_dense.npy` is **(827, 768)**: the 95-document pilot universe. My Phase A2
rebuilt it as **1,104 documents / 9,804 chunks**. Comparing a full-corpus run against a 95-document
anchor measures my universe change, not batch-03.

Widening the universe is right *eventually* — it is what "the answer pipeline should cover all the
books, columns, biography and speeches" means — but it has to be **its own labelled change with its own
before/after**, after CE-12, not folded into the correction batch. Same rule as CE-17, same rule that
keeps `build_centroids.py` banned and batch-04 unmerged.

So `scripts/make_runtime_dense_index.py` now takes `--allowlist <csv>`. Committed and dry-tested against
the live matrix:

```
[runtime-index] allowlist pilot_subset_frozen_v4.csv: 95 documents, 826 chunks
```

826, not 827 — one chunk fewer, because batch-03 re-chunked 18 of those 95 documents. That difference
*is* the signal CE-12 is meant to measure.

### One correction to my own reasoning, for the record

I said appending the CE-11 rows to `gold_reference_set.csv` would break a `FROZEN_SHA` gate. That was
wrong about the mechanism: `FROZEN_SHA = 65492b65…` is computed over the **query strings in
`reports/pilot-eval subset/draft_queries_v1.json`**, not over the CSV. The conclusion is unchanged and
the reason is better — the harness reads its 40 queries from that JSON, so the CE-11 rows need a
*parallel queries JSON* to be runnable at all, and the CSV stays what it is: the human-graded reference.

---

## The prompt

```
Phase 3 (revised) — comparator closure + CE-11 staging. $0 THROUGHOUT.
No API calls. No token spend. If any step would compose an answer, STOP.

HARD PRECONDITION
0. data/index/topic_centroids_meta.json must read n_topics 34 with merged_pairs empty. If it still
   reads 3, STOP and run docs/p3/P3.3_centroid_recovery_prompt_2026-09-26.md first. Phase 3 validates
   routed_topic values against the live topic list and every CE-11 row will fail against 3 topics.
   Report what you found before doing anything else.

BOUNDARIES
- C:\Reachy Mini Project 2026 is READ-ONLY. Copy out of it; write nothing into it.
- Copy files; do not edit them. If a copied file needs a change to run, STOP and report.
- Do NOT modify gold_reference_set.csv or draft_queries_v1.json. Ever. They are the frozen references.
- Do NOT run build_centroids.py. Do NOT edit voice_card.md. Do NOT merge batch-04.
- Do NOT run any composer or eval that spends tokens in this phase.

STEP 1 — finish the eval closure
1. Copy from the working repo, preserving paths, and report sha256 for each source/destination pair:
     reports\pilot-eval subset\    (the WHOLE directory — 27 files at source; this repo has 4)
     scripts\run_ops2_c1.py
     scripts\verify_v4_transition.py
   draft_queries_v1.json lives in that directory and is the frozen 40-query set the gates validate.
2. Re-run %PY% scripts\check_date_index.py. With draft_queries_v1.json present all three sections
   should now run. Report the full output including the NO-REGRESSION GATE.

STEP 2 — validate the frozen query set
3. reports\pilot-eval subset\draft_queries_v1.json: report meta.frozen, meta.n, len(queries), and the
   sha256 of the canonicalised query strings — sha256('\n'.join(sorted(query_strings)).encode('utf-8')),
   the recipe its own meta records. It must equal
   65492b650aec8dda5e76be21c32aaae3faf61f9663c6c58ace02b5a6c4bc9a63 (run_arch_baseline.py FROZEN_SHA).
   If it does not, STOP — the gate would fail and nothing downstream is comparable.
4. Note for the report, do not act on it: that file's meta records embed_regime
   "BAAI/bge-large-en-v1.5/1024d/..." and universe "v4 allowlist (95 docs / 827 chunks)". The QUERY
   STRINGS are regime-independent and are what the gate hashes; the recorded routing fields in it are
   stale and are not a comparator.

STEP 3 — establish the correct comparator, in writing
5. Read and report from eval\results\:
     arch_baseline_v4_retrieval.json          -> anchor string, recall_C_baseline, n
     arch_baseline_v4_2_provenance.json       -> canonical_recall_machine_verified,
                                                 health_gate_machine_verified,
                                                 promoted_artifacts_machine_verified
   State plainly which artifact is the standing comparator for a bge-base run and why
   arch_baseline_v2.json is not (its queries carry universe: 827 and it predates the bge-base
   ratification). Contradict me if the files say otherwise — read them, do not take my word.

STEP 4 — restore the comparable retrieval universe
6. Archive the current full-corpus runtime index, by rename, not delete:
     data\index\pilot_dense.npy       -> data\index\_fullcorpus_2026-09-26_pilot_dense.npy
     data\index\pilot_dense_meta.json -> data\index\_fullcorpus_2026-09-26_pilot_dense_meta.json
   Report their n_docs / n_chunks first so the full-corpus state is on the record and restorable.
7. %PY% scripts\make_runtime_dense_index.py --allowlist "reports\pilot-eval subset\pilot_subset_frozen_v4.csv" --force
   Expect: "allowlist pilot_subset_frozen_v4.csv: 95 documents, 826 chunks".
   826 and not 827 is CORRECT — batch-03 re-chunked 18 of those 95 documents. Do not treat it as an error.
8. Verify the new runtime index: n_docs 95, n_chunks 826, dim 768, model BAAI/bge-base-en-v1.5,
   len(chunk_ids) == len(doc_ids) == 826, allowlist_version naming pilot_subset_frozen_v4.csv, and no
   retired ID (BA040, BC009, BC010, BD018, SA085) in doc_ids.
9. Smoke test on the real path, with the real universe — this replaces the broken set() call:
     %PY% -c "import json,sys; sys.path.insert(0,'app'); import config, retrieval; \
       ids=set(json.load(open(config.DENSE_INDEX_META_PATH,encoding='utf-8'))['doc_ids']); \
       print(len(ids)); print(retrieval.run('What did he say about the rule of law?', ids))"
   Expect 95 doc_ids and a plausible rule-of-law result. Report the routed topic and the top doc_ids.

STEP 5 — stage CE-11 as a parallel, clearly non-frozen query set
10. Validate eval\results\gold_additions_batch03_2026-09-26.csv:
      - same 15 headers, same order, as gold_reference_set.csv
      - 14 rows, qids A41-X54, no collision with the frozen 40
      - every gold_source_docs id (ignoring the RETIRED / OOS sentinels) exists in corpus\ and is not
        in data\csv\retired_doc_ids.csv
      - every routed_topic appears in topic_centroids_meta.json topic_ids (34 topics)
      - retrieved_docs and model_answer empty in all 14
    Report each check. Any failure: report and STOP.
11. Write eval\results\ce11_queries_2026-09-26.json in the SAME SHAPE as draft_queries_v1.json:
      {"meta": {...}, "queries": [...]}
    meta must carry: version "ce11-batch03", frozen FALSE, n 14, created "2026-09-26",
      embed_regime "BAAI/bge-base-en-v1.5/768d/cuda_fp32/pilot_subset_frozen_v4",
      universe "v4 allowlist (95 docs / 826 chunks)",
      note "CE-11 diagnostic set for correction batch-03. NOT part of the frozen 40 and NOT a
            promotion comparator - there is no baseline for these queries.",
      sha256_of_queries computed by draft_queries_v1.json's own recipe,
      grading_reference "eval/results/gold_additions_batch03_2026-09-26.csv"
    Each query carries only the fields that are knowable before a run:
      id (the qid), query, theme, type (the qtype), expected_grounding_doc_ids (gold_source_docs split
      on ';', empty list for the RETIRED and OOS sentinels).
    Do NOT invent routed_topic, routed_cos, top_chunk_ids, grounded or any other measured field. Those
    are outputs, not inputs, and copying them from the CSV would fabricate a result.
12. Confirm by hash that gold_reference_set.csv and draft_queries_v1.json are UNCHANGED by this phase.

REPORT — docs\p3\phase3_ce11_staging_2026-09-26.md
13. Every copy with both hashes; the check_date_index output; the FROZEN_SHA check; the comparator
    determination from step 5 in your own words; the universe change with before/after counts; the
    smoke-test result; the 14-row validation; and the path and sha256 of the new queries JSON.

FLAG, DO NOT FIX
- Centroids still at 3 topics · the FROZEN_SHA not matching · the allowlist resolving to anything other
  than 95 documents · any retired ID · any hash change to gold_reference_set.csv or draft_queries_v1.json
  · any need to edit a copied script · anything that would spend tokens.
```

---

## What this changes downstream

**Phase 4 is replaced.** CE-12 becomes `%PY% scripts\run_ops2_c1.py C2_post_batch03` — **$0,
retrieval-only** — graded against the v4 gold and compared to v4.2's machine-verified
0.588 / 0.882 / 0.941 / 0.971, with the health gate's three anchors. The drift file keys by label, so
batch-03's effect is attributable the same way OPS-2 attributed B11 to the batch-02 BM25 rebuild. Write
that prompt once Phase 3 reports.

**A compose run stays optional and later.** If the team wants answer-quality evidence rather than
retrieval evidence, that is a separate decision with a separate cost, and it needs a bge-base compose
baseline to compare against — which may not exist. Worth establishing before anyone pays for it.

**Widening the universe to all 1,104 documents becomes its own change.** After CE-12: re-run
`make_runtime_dense_index.py` with no `--allowlist`, re-run the same drift check, label it, and report
the delta. Then it is a measured decision instead of a side effect of an index repair.
