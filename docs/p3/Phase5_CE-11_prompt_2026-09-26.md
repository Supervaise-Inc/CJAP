# CE-12 assessment, and Phase 5 — the CE-11 diagnostic. **$0**

**26 Sep 2026.** CE-12 is done and the recommendation holds. Phase 5 has a trap in it that would have
produced a fake catastrophic result; the guard is now written into the runner.

## CE-12 — verified, and CC found something the instrument hid

Read straight from `eval/results/ops2_c1_drift.json`:

```
C1_post_ops2      @1 0.588 · @3 0.882 · @5 0.882 · @10 0.971 · @sent 0.941   live_vs_replay 40/40 exact
C2_post_batch03   @1 0.588 · @3 0.853 · @5 0.882 · @10 0.971 · @sent 0.941   live_vs_replay 40/40 exact
```

`delta_vs_C1 = 0.000` on all four headline metrics. `delta_vs_v4 @1 = −0.03`, exactly the July B11/BM25
figure, as predicted. **Batch-03 is retrieval-neutral on the gate criteria.**

**The @3 catch is the valuable part of that run.** The script's printed summary reports only
@1/@5/@sent/@10 — @3 lives in the recall dict and never reaches the console. CC read the dict anyway,
found 0.882 → 0.853, and traced it to a single query. The arithmetic confirms it: 0.882 × 34 = 30,
0.853 × 34 = 29. **Exactly one query** out of 34 dropped out of the top-3 window. Finding a metric the
tool doesn't print, then attributing it to one query, one document and one rank move, is the standard
this whole sequence has been trying to hold.

### One refinement to the attribution

CC attributed the move to `BB002` rising rank 8 → 2 and credited it as "directly among the 18 corrected
pilot docs". True, but the mechanism matters, and the content argues against a content-driven cause:

| | |
|---|---|
| C18 | *"Looking back, what are you most proud of?"* — `qtype stance`, `gold_confidence: low`, gold `SC010;CC008` |
| BB002 | *With Due Respect (Vol. 7) — Ch. 7: **Understanding China*** |
| BB002 in the Centenary merge? | **No** — it was changed by one of the smaller corrections, not a content addition |

A chapter on understanding China rising to rank 2 on a question about personal pride is not a document
that got more relevant. It is a **rank shuffle**. The likely mechanism is the one CC already identified
for D21: the sparse index was rebuilt over 9,804 chunks instead of 9,865, which moves IDF for every
term and perturbs RRF ranks corpus-wide, including for documents nobody touched. That is the **same
family as the B11 loss** batch-02 produced and the project already accepted.

That reading makes the finding smaller, not larger: one low-confidence query, at one k, from generic
IDF drift, with @5 and @10 unmoved. **Promote.** Record the @3 number and the C18 mechanism in the
promotion note so nobody rediscovers it as a mystery later, and let CE-13 decide whether BM25 tuning is
ever worth opening.

## Phase 5's trap, found before it could waste a run

**None of the nine CE-11 gold documents is in the 95-document v4 allowlist:**

```
BA031 BA032 BA036 BA037 BA039 BB006 BC017 BC018 BD010   -> in v4 allowlist: NONE
```

They are all book chapters; the pilot subset is columns and speeches. Running CE-11 against the current
826-chunk universe would score every grounding row zero **by construction** — and a 0/11 result reads as
total failure rather than as a universe mismatch.

So Phase 5 runs in two parts, and the order is not optional:

**5a — restore the full-corpus universe and label it.** This is the measurement that was always owed:
the 95 → 1,104 widening, on its own, against the same instrument.
**5b — the CE-11 diagnostic**, against that full-corpus universe.

`scripts/run_ce11_diag.py` is committed (sha16 `e3a0739c10cf60bc`). It is retrieval-only, reads the
staged `ce11_queries_2026-09-26.json` and the additions CSV, grades grounding rows on hit@1/3/5/10,
passes RETIRED rows only when no retired id appears, reports OOS rows rather than hard-grading them —
and **refuses to run, naming the missing documents, if any expected grounding document is outside the
live universe.** That guard is the trap above, made impossible to walk into.

---

## The prompt

```
Phase 5 — restore the full-corpus universe, then run the CE-11 diagnostic. $0 THROUGHOUT.
NO API CALLS, NO TOKENS, NO COMPOSER. Interpreter:
  set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe"    — use %PY% for every command.
If any step would compose an answer or contact the Anthropic API, STOP.

BOUNDARIES
- Write only: data\index\pilot_dense.npy + pilot_dense_meta.json (and their backups),
  eval\results\ops2_c1_drift.json, eval\results\ce11_diag_*.json, and the report.
- Do NOT edit any .py file. Do NOT modify gold_reference_set.csv, draft_queries_v1.json,
  ce11_queries_2026-09-26.json, or gold_additions_batch03_2026-09-26.csv.
- Do NOT rebuild the dense, sparse or date indexes. Do NOT run build_centroids.py. Do NOT edit
  voice_card.md. Do NOT merge batch-04.
- The C2_post_batch03 result is final. Nothing in this phase may overwrite or re-derive it.

PART 5a — widen the universe, as its own labelled measurement

1. Record the current state before changing anything: pilot_dense_meta.json n_docs / n_chunks /
   allowlist_version (expect 95 / 826 / pilot_subset_frozen_v4.csv) and sha256 of pilot_dense.npy.
2. %PY% scripts\make_runtime_dense_index.py --force
   NO --allowlist this time. Expect n_docs 1104, n_chunks 9804. The script is now encoding-fixed
   (sha16 94c6a43a6647e8fa), so a non-zero exit is a REAL failure — report it and STOP.
   It takes its own timestamped backup of the 826-row pair; report the paths it prints.
3. Verify: pilot_dense.npy (9804, 768); meta n_docs 1104, n_chunks 9804,
   len(chunk_ids) == len(doc_ids) == 9804, allowlist_version reading "full-corpus ...", and no retired
   ID (BA040, BC009, BC010, BD018, SA085) in doc_ids.
4. %PY% scripts\run_ops2_c2.py C3_full_corpus_universe
   This grades the SAME frozen 40 against the SAME v4 gold, changing only the universe. Report the
   recall line and compute delta vs C2_post_batch03 — that delta is the cost or benefit of widening
   from 95 documents to 1,104, isolated at last.
   Report the full recall dict, INCLUDING @3. The printed summary omits @3; CE-12 showed why that
   matters.
5. Interpretation, in the report: a fall at @1 is expected and not automatically bad — the same query
   now competes against 1,104 documents instead of 95, and the v4 gold was authored for the 95-document
   universe. Report the numbers and name the mechanism; do NOT tune anything.

PART 5b — the CE-11 diagnostic

6. %PY% scripts\run_ce11_diag.py ce11_full_corpus
   It refuses to run if any expected grounding document is outside the universe. After step 2 all nine
   should be present; if it still refuses, report its message verbatim and STOP — that means the
   widening did not take.
7. Report the printed table and, from eval\results\ce11_diag_ce11_full_corpus.json, per row:

   GROUNDING rows — is the expected document retrieved, and at what rank?
     A41 BA032  the Centenary-chair bracket, post-merge text only
     A42 BA036  Estrada v. Desierto, 2 Mar 2001, Puno — post-merge
     A43 BA037  the death-penalty self-citation — post-merge
     B44 BB006  IPRA / "only the race owns the land" — post-merge
     A45 BA039  Bengson — the C-6 truncation repair
     A46 BA031  first Inquirer column — the C-5 back-matter repair
     C47 BC017  grandson Miggy — the OCR repair
     C48 BC018  the Invocation — the C-7 truncation repair
     X49 BA039  EXACT IDENTIFIER "G.R. No. 142840". This is the sparse arm's proof of life: dense
                retrieval alone cannot find a docket number. Report BA039's rank explicitly. If it is
                outside the top 3, say so — that is a finding about the phrase dictionary.
     X50 BD010;BA032  and  X51 BC017;BC018  — the normalised dates
   RETIRED rows — X52, X53 must PASS: no retired id anywhere in the selection.
   OOS row — X54: report route cosine against OUT_OF_SCOPE_THRESHOLD and in_scope. It is REPORTED, not
                graded — the real out-of-scope behaviour is a composer decline and costs tokens.

8. C48 is EXPECTED to be weak on the honoree's name. That is C-11, the stale BC018 curated row, logged
   and deferred to P6 — not a retrieval failure. Say which it is from the evidence rather than assuming.
9. Confirm the retired-ID sweep is clean across every row.

REPORT — docs\p3\phase5_ce11_diagnostic_2026-09-26.md
10. Part 5a: before/after universe values, the backup paths, the C3 recall line with the full dict
    including @3, and delta vs C2 with the mechanism named.
    Part 5b: the per-row table from step 7, X49's rank called out separately, the retired sweep, and a
    short verdict on whether the batch-03 repairs are actually reachable by retrieval.
11. State plainly which of the 14 rows cannot be settled without a composer run, so the cost of that
    decision is visible if anyone wants to take it.

FLAG, DO NOT FIX
- make_runtime_dense_index.py exiting non-zero · n_docs != 1104 after step 2 · run_ce11_diag.py
  refusing after the widening · any retired ID anywhere · X49 missing BA039 entirely (not merely
  ranked low) · any urge to tune a knob, rebuild an index, or edit a gold file to improve a number.
```

---

## After Phase 5

**Which universe to keep is then a decision, not a default.** C2 (95 docs) and C3 (1,104 docs) will be
directly comparable on the same gold and the same instrument. Whatever the numbers say, the answer
pipeline is meant to serve the whole corpus, so the likely outcome is keeping the full corpus and
recording the recall cost honestly rather than hiding it behind a subset.

**Then** CE-13/14 · the R-1 voice-card fix as its own change with its own comparison · and P6, which
merges batch-04's 186 rows to 1,290 documents and all 12 works, folding in C-11 and the C-13
enforcement.

**Still open, unchanged:** the orphan floor at 0.68 against a 0.6816 minimum and GC006/CA330 never
caught (CE-8) · the topic prior near-inert at mean pairwise cosine 0.9334 (CE-8) ·
`honors_received` ≡ `robot_identity_meta`, both zero-chunk (CE-8) · `check_date_index.py`'s
NO-REGRESSION GATE needing a bge-base re-baseline (batch-05) · `merge_tag_topics.py` hardening and the
`--force` exit-3 refusal (after CE-12, so now eligible) · C-12 and the ~222 columns from Feb 2007 –
Apr 2011 (batch-05) · pushing `deliverable/2026-09` to `Supervaise-Inc/CJAP`.
