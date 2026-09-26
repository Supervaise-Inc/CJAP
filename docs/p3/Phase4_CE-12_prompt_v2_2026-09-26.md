# Phase 4 / CE-12 (v2) — the batch-03 promotion check. **$0**

**26 Sep 2026. Supersedes `docs/p3/Phase4_CE-12_prompt_2026-09-26.md`.** Phase 3 is complete. Two things
changed since that prompt was written: my encoding patch has now actually landed, and a **hard blocker
in `run_ops2_c1.py`** was found that would have stopped CE-12 before it measured anything.

## Phase 3 assessment — complete, and one flag of mine was right to fire

Every step verified independently: 27 pilot-eval files copied sha-matched, `FROZEN_SHA` exact, the
comparator determined by reading the files rather than taking my word, the full-corpus index archived
and re-sliced to **95 docs / 826 chunks**, CE-11 staged as 14 non-frozen queries with no fabricated
fields, and both frozen references byte-unchanged. $0 throughout.

**Amendment B was right and I was wrong.** The encoding patch I claimed was applied was not in the file.
I asserted it on the strength of a tool reporting success without reading the file back — exactly the
failure mode I have spent this whole sequence telling Claude Code to guard against, caught by CC doing
precisely that. It is now genuinely landed and verified by reading the device file:

```
scripts/make_runtime_dense_index.py   sha256[:16] 94c6a43a6647e8fa
  reconfigure present · zero U+2016 · two ASCII "abs(norm-1)" strings
  whole file encodes to cp1252 · syntax OK
```

CC's handling was correct either way: it verified the Step 4 write by direct file inspection
(2,537,600 bytes = 826 × 768 float32 + header) instead of trusting the exit code, which is why the
re-slice is sound despite the crash.

**CC's read of the NO-REGRESSION GATE is also exactly right.** `check_date_index.py:38` loads
`arch_baseline_v2.json` directly. That is the bge-large / 827-chunk baseline, so a bge-base live
retrieval mismatches all 40 queries by construction. Not a regression, and not fixable without
re-baselining that gate — a batch-05 item.

## The blocker: `run_ops2_c1.py` pins 827 rows and will abort on 826

Line 56, before any measurement happens:

```python
assert mat.shape == (827, config.EMBED_DIM) and cen.shape[0] == 34
```

The runtime index is now **(826, 768)** — one chunk fewer, because batch-03 re-chunked 18 of the 95
pilot documents. That difference is the signal CE-12 exists to measure, and the assert would kill the
run before it starts. The 827 is a **pin on the pre-correction state**, not a measurement.

`scripts/run_ops2_c2.py` is committed: a copy with **exactly one code line changed**, verified by diff —

```
40c40
<     assert mat.shape == (827, config.EMBED_DIM) and cen.shape[0] == 34
---
>     assert mat.shape == (len(chunk_ids), config.EMBED_DIM) and cen.shape[0] == 34
```

This keeps the check's real intent — the matrix agrees with its own meta — without pinning a count the
correction legitimately moved. Same gold set, same `service._allowlist("v4")`, same grading, same output
file and label scheme. `run_ops2_c1.py` stays untouched so the instrument used for C0 and C1 remains
auditable.

## The number that will be misread if it isn't said first

The script prints `delta_vs_v4` against `v4_expect @1 0.618`, but both prior labels already sit lower:

```
v4_expect             @1 0.618 · @5 0.882 · @sent 0.941 · @10 0.971
C0_current_artifacts  @1 0.588 · @5 0.882 · @sent 0.941 · @10 0.971   delta_vs_v4 @1 = -0.03
C1_post_ops2          @1 0.588 · @5 0.882 · @sent 0.941 · @10 0.971   delta_vs_v4 @1 = -0.03
```

That −0.03 is the B11 `hit@1` loss OPS-2 attributed to the batch-02 BM25/IDF rebuild and accepted in
July. **Batch-03's result is `C2 − C1_post_ops2`, not `delta_vs_v4`.** A clean run prints −0.03 again and
that means *no change*. C0 and C1 being identical is the bar: OPS-2's own full-corpus re-embed and
centroid rebuild cost nothing measurable.

---

## The prompt

```
Phase 4 / CE-12 — batch-03 retrieval promotion check. $0. NO API CALLS, NO TOKENS, NO COMPOSER.
Interpreter: set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe" — use %PY% throughout.
If any step would compose an answer or contact the Anthropic API, STOP.

BOUNDARIES
- Write only eval\results\ops2_c1_drift.json (the script appends its own label) and the report.
- Do NOT edit any .py file, including run_ops2_c1.py and run_ops2_c2.py.
- Do NOT modify gold_reference_set.csv, draft_queries_v1.json, ce11_queries_2026-09-26.json, or any
  index. run_ops2_c2.py asserts the gold set is 40 rows with 34 scope_gold == "in"; if that fires,
  something edited the file — STOP rather than adjust it.
- Do NOT rebuild any index, run build_centroids.py, edit voice_card.md, or merge batch-04.
- Do NOT run the CE-11 set. That is Phase 5 and needs its own decision.

STEP 0 — the two things that changed since the last prompt
1. scripts\make_runtime_dense_index.py: report sha256[:16]. It must be 94c6a43a6647e8fa, with
   "reconfigure" present and zero U+2016 characters. Your Amendment B finding was correct; this is the
   verification that it is now actually fixed. This phase does not run that script — confirm and move on.
2. scripts\run_ops2_c2.py exists. Run and paste:
     diff "scripts\run_ops2_c1.py" "scripts\run_ops2_c2.py"
   Everything outside the leading docstring must be a single line: the 827 assert replaced by
   len(chunk_ids). If the diff shows any other code change, STOP and report it — a second difference
   would make the measurement instrument itself suspect.

PRE-FLIGHT — report every value, STOP on any mismatch
3. data\index\pilot_dense.npy       -> (826, 768); meta n_docs 95, n_chunks 826,
                                        allowlist_version naming pilot_subset_frozen_v4.csv
   data\index\topic_centroids.npy   -> (34, 768); meta n_topics 34, merged_pairs empty, merge_cosine 1.01
   data\index\pilot_sparse.pkl      -> meta n_chunks 9804
   data\index\corpus_dense_meta.json-> BAAI/bge-base-en-v1.5, dim 768, n_chunks 9804
   The sparse arm covering 9,804 while the dense runtime index covers 826 is CORRECT — sparse filters by
   allowlist at query time, dense by the index itself. Do not "fix" it.
4. Report what service._allowlist("v4") returns: the count and the first five doc_ids. It must be the
   95-document v4 allowlist. If it returns anything else, STOP — the universe would not match the index.
5. eval\results\gold_reference_set.csv: 40 rows, 34 in-scope, sha256 unchanged from
   37259902530d92efab33d0c8620cdf0fa830b25cfff8579d2bb55a11a9a1bca5.
6. %PY% scripts\verify_pin.py must exit 0.
7. eval\results\ops2_c1_drift.json: report the existing labels and their recall blocks. Confirm
   C1_post_ops2 reads @1 0.588 / @5 0.882 / @chunks_sent 0.941 / @10 0.971.
   C1_post_ops2 IS THE COMPARATOR FOR BATCH-03. v4_expect is not.

HEALTH GATE — three anchors, retrieval only, before the full run
8. arch_baseline_v4_2_provenance.json records 3/3 PASS: A1 rule-of-law n_selected=7,
   D21 museum-of-liberty route=museum_for_liberty_and_prosperity n_selected=7, E28 roe-v-wade
   n_selected=16. Run those three through retrieval.run(query, allowlist) with the allowlist from
   service._allowlist("v4"). No composition. Report route and n_selected for each.
   A changed n_selected is NOT automatically a failure — 18 of these 95 documents were re-chunked. Report
   the numbers and name which corrected documents could explain any move. Only a crash, an empty
   selection, or a wildly different route is a STOP.

RUN
9. %PY% scripts\run_ops2_c2.py C2_post_batch03
   Stream the output. If it aborts on an assert, report the assert verbatim and STOP — do not edit
   anything to get past it.

VERIFY — this is the promotion evidence
10. Paste the printed line verbatim: [C2_post_batch03] recall @1/@5/@sent/@10 = ...
11. Report BOTH deltas, clearly labelled:
      delta_vs_v4  (the script's own, vs v4_expect @1 0.618) — EXPECT -0.03 at @1. That is the July
                   B11/BM25 loss, already accepted. It is NOT a batch-03 result.
      delta_vs_C1  (C2 minus C1_post_ops2) — THIS IS THE BATCH-03 RESULT. Expect 0.000 across
                   @1/@5/@chunks_sent/@10 if the correction is retrieval-neutral.
    Say in one sentence which is which and why.
12. Per-query: list every query whose hit@1 or retrieved doc set changed versus C1_post_ops2, and for
    each name which of the 156 batch-03-corrected documents plausibly explains it. A delta with no named
    cause is an unfinished finding.
13. Report live_vs_replay. C0 and C1 both read "40/40 exact"; anything less is a STOP.
14. Confirm no retired ID (BA040, BC009, BC010, BD018, SA085) appears in any retrieved set.
15. Report anything that got WORSE, not only what held. If nothing moved, say so plainly — "no
    measurable retrieval change" is a valid and useful result for a correction batch, and it is exactly
    what C0 vs C1 looked like.

REPORT — docs\p3\ce12_promotion_2026-09-26.md
16. Step 0's two verifications including the diff; every pre-flight value; the health-gate comparison;
    the verbatim recall line; both deltas with the explanation; the per-query attribution; live_vs_replay;
    the retired-ID check; and a recommendation — promote, promote with caveats, or do not promote — with
    the reason. Recommend; the decision is the user's.

FLAG, DO NOT FIX
- The diff in step 2 showing more than one code line · the gold-set assert firing · verify_pin not
  exiting 0 · service._allowlist("v4") not returning 95 documents · live_vs_replay below 40/40 · any
  retired ID · any recall metric below C1_post_ops2 · a health-gate anchor crashing or returning
  nothing · any urge to tune a config knob, rebuild an index, or adjust the gold set to move a number.
```

---

## After CE-12, in order

**Phase 5 — the CE-11 diagnostic set.** `ce11_queries_2026-09-26.json` is staged and non-frozen.
Neither `run_ops2_c1.py` nor `c2` can read it — both take the frozen set and the gold CSV by hard-coded
path — so running the 14 rows needs a small additive runner or a compose run. Decide after CE-12,
because its outcome changes what those rows are worth answering.

**Restore the full-corpus universe as its own labelled change.** Everything needed is recorded:

```
archived:  data/index/_fullcorpus_2026-09-26_pilot_dense.npy  (+ _meta.json)
before:    n_docs 1104 · n_chunks 9804 · allowlist_version "full-corpus ..."
sha256:    c11f6784...  (recorded by Phase 3 before the rename)
```

Re-run `make_runtime_dense_index.py --force` with no `--allowlist`, then `run_ops2_c2.py
C3_full_corpus_universe`. That measures the 95 → 1,104 widening on its own, which is how it should have
been done in the first place.

**Then** CE-13/14, the R-1 voice-card fix with its own comparison, and P6 — batch-04's 186 rows, taking
the corpus to 1,290 documents and all 12 works, with C-11 and the C-13 enforcement folded in.

## Open, unchanged

`check_date_index.py`'s NO-REGRESSION GATE needs a bge-base re-baseline (batch-05) · the orphan floor at
0.68 against a 0.6816 minimum, and GC006/CA330 never caught (CE-8) · the topic prior near-inert at mean
pairwise cosine 0.9334 (CE-8) · `honors_received` ≡ `robot_identity_meta`, both zero-chunk (CE-8) ·
`merge_tag_topics.py` hardening (after CE-12) · `make_runtime_dense_index.py`'s `--force` guard
returning exit 3 on a deliberate refusal (after CE-12) · C-11, C-12, C-13 (P6 / batch-05) · the ~222
columns from Feb 2007 – Apr 2011 (batch-05 sourcing) · pushing `deliverable/2026-09`.
