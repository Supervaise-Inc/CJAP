> **SUPERSEDED 26 Sep by `docs/p3/Phase4_CE-12_prompt_v2_2026-09-26.md`.** `run_ops2_c1.py:56`
> asserts the pilot matrix is exactly 827 rows; the post-correction slice is 826, so CE-12 would
> abort before measuring. v2 runs `scripts/run_ops2_c2.py`, a copy with that one assert relaxed to
> `len(chunk_ids)` and verified by diff. Use v2.

# Phase 4 — CE-12, the batch-03 promotion eval. **$0**

**26 Sep 2026.** Phase 3 verified complete from disk: runtime index at **95 docs / 826 chunks**
(`allowlist_version: pilot_subset_frozen_v4.csv (95 of 95 documents resolved)`), all 27
`reports/pilot-eval subset/` files present, `run_ops2_c1.py` and `verify_v4_transition.py` copied,
`ce11_queries_2026-09-26.json` staged with 14 queries and `frozen: false`.

This phase spends **nothing**. No composer, no API key, no tokens. It is a retrieval-only drift check.

## The one thing that will be misread if it isn't said first

`run_ops2_c1.py` prints `delta_vs_v4`, computed against `v4_expect` in
`eval/results/ops2_c1_drift.json`:

```
v4_expect            @1 0.618 · @5 0.882 · @chunks_sent 0.941 · @10 0.971
C0_current_artifacts @1 0.588 · @5 0.882 · @chunks_sent 0.941 · @10 0.971   delta_vs_v4 @1 = -0.03
C1_post_ops2         @1 0.588 · @5 0.882 · @chunks_sent 0.941 · @10 0.971   delta_vs_v4 @1 = -0.03
```

That **−0.03 at @1 is already spent**. It is the B11 `hit@1` loss that OPS-2 attributed cleanly to the
batch-02 BM25/IDF rebuild, examined and accepted at the time (`drift_detail.recovery_owner: "separate
BM25-tuning task if ever desired; not required for promotion"`).

**So batch-03's effect is `C2 − C1_post_ops2`, not `delta_vs_v4`.** A clean run prints
`delta_vs_v4 @1 = -0.03` again and that means **no change**. Reading the script's own delta as the
batch-03 result would report a regression that happened in July.

C0 and C1 being identical is also worth carrying: OPS-2's full-corpus re-embed and centroid rebuild cost
nothing measurable. That is the standard batch-03 is being held to.

---

## The prompt

```
Phase 4 / CE-12 — batch-03 retrieval promotion check. $0. NO API CALLS, NO TOKENS.
Interpreter: set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe" — use %PY% throughout.
If any step would compose an answer or contact the Anthropic API, STOP.

BOUNDARIES
- Write only eval\results\ops2_c1_drift.json (the script appends its own label) and the report.
- Do NOT modify gold_reference_set.csv, draft_queries_v1.json, ce11_queries_2026-09-26.json, or any
  index. run_ops2_c1.py asserts the gold set is exactly 40 rows with 34 scope_gold == "in"; if that
  assert fires, something edited the file and you must STOP rather than adjust it.
- Do NOT run build_centroids.py. Do NOT edit voice_card.md. Do NOT merge batch-04.
- Do NOT rebuild any index. Everything this phase reads was built and verified in P3.2-P3.5.
- Do NOT run the CE-11 set in this phase. That is Phase 5 and it needs its own decision.

PRE-FLIGHT — report every value, STOP on any mismatch
1. The four artifacts run_ops2_c1.py reads:
     data\index\pilot_dense.npy       -> expect (826, 768); meta n_docs 95, n_chunks 826,
                                          allowlist_version naming pilot_subset_frozen_v4.csv
     data\index\topic_centroids.npy   -> expect (34, 768); meta n_topics 34, merged_pairs empty,
                                          merge_cosine 1.01
     data\index\pilot_sparse.pkl      -> meta n_chunks 9804
     data\index\corpus_dense_meta.json-> model BAAI/bge-base-en-v1.5, dim 768, n_chunks 9804
   The sparse index covering 9,804 while the dense runtime index covers 826 is CORRECT — the sparse arm
   is allowlist-filtered at query time, the dense arm by the index itself. Do not "fix" it.
2. eval\results\gold_reference_set.csv: 40 rows, 34 with scope_gold == "in". Report its sha256 and
   confirm it is unchanged from the Phase 2 value 37259902530d92efab33d0c8620cdf0fa830b25cfff8579d2bb55a11a9a1bca5.
3. %PY% scripts\verify_pin.py must exit 0.
4. Read eval\results\ops2_c1_drift.json and report the existing labels and their recall blocks
   (anchor, v4_expect, C0_current_artifacts, C1_post_ops2). Confirm C1_post_ops2 reads
   @1 0.588 / @5 0.882 / @chunks_sent 0.941 / @10 0.971. C1 IS THE COMPARATOR FOR BATCH-03.

HEALTH GATE — the three anchors, before the full run
5. eval\results\arch_baseline_v4_2_provenance.json -> health_gate_machine_verified.anchors records
   3/3 PASS for: A1 rule-of-law (n_selected=7), D21 museum-of-liberty (route
   museum_for_liberty_and_prosperity, n_selected=7), E28 roe-v-wade (n_selected=16).
   Run those three queries through the live retrieval path only — retrieval.run(query, allowlist) with
   the allowlist built from pilot_dense_meta.json's doc_ids, exactly as in the Phase 3 smoke test. No
   composition. Report route and n_selected for each and compare to the recorded values.
   A changed n_selected is NOT automatically a failure — batch-03 re-chunked 18 of these 95 documents,
   so counts can legitimately move. Report the numbers and say which of the 156 corrected documents
   could explain any change. Only a crash, an empty selection, or a wildly different route is a STOP.

RUN
6. %PY% scripts\run_ops2_c1.py C2_post_batch03
   It grades the frozen 40-query set against the 34 in-scope v4 gold rows and merges a new
   C2_post_batch03 label into eval\results\ops2_c1_drift.json. Stream the output.

VERIFY — this is the promotion evidence
7. Report the printed line verbatim: [C2_post_batch03] recall @1/@5/@sent/@10 = ...
8. Compute and report BOTH deltas, clearly labelled:
     delta_vs_v4        (the script's own, against v4_expect @1 0.618) — EXPECT -0.03 at @1.
                        That is the July B11/BM25 loss, already accepted. It is NOT a batch-03result.
     delta_vs_C1        (C2 minus C1_post_ops2) — THIS IS THE BATCH-03 RESULT.
                        Expect 0.000 across @1/@5/@chunks_sent/@10 if the correction is retrieval-neutral.
   State in one sentence which number is the batch-03 finding and why.
9. Per-query: list every query whose hit@1 or whose retrieved doc set changed versus C1_post_ops2. For
   each one, name which of the 156 batch-03-corrected documents plausibly explains it. Attribution is
   the entire point — a delta with no named cause is an unfinished finding.
10. Report live_vs_replay. C0 and C1 both read "40/40 exact"; anything less is a STOP.
11. Confirm no retired ID (BA040, BC009, BC010, BD018, SA085) appears in any retrieved set.
12. Report anything that got WORSE, not only what held or improved. If nothing moved at all, say so
    plainly — "no measurable retrieval change" is a valid and useful promotion result for a correction
    batch, and it is what C0 vs C1 looked like.

REPORT — docs\p3\ce12_promotion_2026-09-26.md
13. Pre-flight values; the health-gate comparison; the verbatim recall line; both deltas with the
    explanation of which is which; the per-query attribution from step 9; live_vs_replay; the retired-ID
    check; and a clear recommendation — promote, promote with noted caveats, or do not promote — with
    the reason. Recommend; do not decide. The decision is the user's.

FLAG, DO NOT FIX
- The gold-set assert firing · verify_pin not exiting 0 · live_vs_replay below 40/40 · any retired ID ·
  any recall metric below C1_post_ops2 · a health-gate anchor crashing or returning nothing ·
  any urge to tune a config knob, rebuild an index, or adjust the gold set to improve a number.
```

---

## What follows, so nothing here forecloses it

**Phase 5 — the CE-11 diagnostic set.** `ce11_queries_2026-09-26.json` is staged and non-frozen.
`run_ops2_c1.py` reads the frozen set and the gold CSV by hard-coded path, so running the 14 rows needs
either a small additive runner (the `make_runtime_dense_index.py` pattern — a new script, nothing
edited) or a compose run. Decide after CE-12, because CE-12's outcome changes what those 14 rows are
worth answering.

**Restoring the full-corpus universe.** `_fullcorpus_2026-09-26_pilot_dense.*` is archived and
reversible: re-run `make_runtime_dense_index.py --force` with no `--allowlist`, then re-run
`run_ops2_c1.py` under a label like `C3_full_corpus_universe`. That measures the 95 → 1,104 widening on
its own, which is how it should have been done in the first place.

**Then** CE-13/14, the R-1 voice-card fix with its own comparison, and P6.
