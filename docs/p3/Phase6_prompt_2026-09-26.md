# Phase 5 assessment, and Phase 6 — close C3, decide the universe, then the voice card

**26 Sep 2026.** Phase 5b is the strongest diagnostic work in this sequence. Phase 5a hit a real
harness limitation that CC correctly refused to work around; the fix is now committed.

## Phase 5 — assessment

**5a: the universe widened cleanly** — `pilot_dense_meta.json` reads 1,104 documents / 9,804 chunks. The
**C3 measurement did not happen**, and CC's root cause is exactly right, traced by reading the script
rather than guessing:

`run_ops2_c1/c2` restrict the *live* path to `service._allowlist("v4")` (95 documents), but their
`replay_ranked()` self-check ranks **every row of `mat`** with no allowlist filter. While the matrix was
pre-sliced to those same 95 documents, "rank every row" and "rank within the allowlist" were the same
operation and the check passed silently. Against a 9,804-row matrix they diverge on all 40 queries and
the harness aborts before writing anything. **That is the harness protecting itself, not a retrieval
defect** — and refusing to hand-roll a substitute was the right call.

`scripts/run_ops2_c3.py` is committed (sha16 `2de1f1de0b466172`). One code line differs from c2:
`allow = service._allowlist("v4")` → `allow = set(doc_ids)`, taken from the index meta so live and
replay cover the same universe. I moved the assignment below where `doc_ids` is defined — my first cut
referenced it before it existed and would have died on `NameError`; AST-verified now (`doc_ids` line 62,
`allow` line 69).

**5b: 8 PASS, 3 FAIL, 2 retired probes clean** — and every miss carries a named mechanism.

**X49 is the finding of the run.** "G.R. No. 142840" returns BA039 at **rank 31 of 9,804** fused, 13th on
the sparse arm alone. CC established why, and it is not what I expected:

- the literal string `"G.R. No. 142840"` appears **nowhere** in BA039's text;
- the phrase dictionary carries the citation only as one atomic phrase anchored to the full case name
  (`"bengson v. house of representatives electoral tribunal gr 142840"`), which a bare docket number
  cannot match;
- BA039 is outranked by **BD020** and **BA041** — *"Selected Quotations from Ponencias and Opinions"*
  chapters — which contain no "142840" at all and win purely on the raw frequency of the generic tokens
  `g.r.` and `no.`

So the sparse arm is alive but the phrase dictionary indexes citations at the wrong granularity, and
citation-dense chapters act as an attractor for any docket-shaped query. That is a concrete, fixable
defect in `build_sparse_index.py`, and it would never have surfaced from a pass/fail table.

**X51 is a capability that is switched off, not a defect.** Three of the five retrieved documents are
genuinely dated 1997 (BD020, BC020, BA041). `DATE_INDEX_ENABLED = False`. The deterministic temporal
filter built for exactly this query shape is dark. That is now cheap to test.

**A41 is an ordinary near-miss** among sibling Centenary chapters — BA032 is live with 97 chunks; five
shorter siblings crowded it out. No action.

**Verdict: the batch-03 repairs are reachable.** Seven of eight repaired/merged documents retrieve their
own content, including all four C-5/C-6/C-7/OCR repairs.

---

## The prompt

```
Phase 6 — close the C3 measurement, settle the universe, then the voice card.
Interpreter: set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe" — use %PY% throughout.
PARTS A and B are $0. PART C spends tokens and STOPS for approval first.

BOUNDARIES
- Do NOT edit any .py file. Do NOT edit config.py.
- Do NOT rebuild the dense, sparse or date indexes. Do NOT run build_centroids.py.
- Do NOT merge batch-04. Do NOT modify gold_reference_set.csv, draft_queries_v1.json,
  ce11_queries_2026-09-26.json, or gold_additions_batch03_2026-09-26.csv.
- C2_post_batch03 is final and must not be overwritten or re-derived.

PART A — the C3 measurement. $0.

1. scripts\run_ops2_c3.py exists. Paste:
     diff "scripts\run_ops2_c2.py" "scripts\run_ops2_c3.py"
   Outside the docstring, exactly one code line changes — the allowlist — plus its comment block.
   Confirm `allow = set(doc_ids)` appears AFTER `chunk_ids, doc_ids = pm[...]`; my first cut had it
   before and would have raised NameError. If the diff shows any other code change, STOP.
2. Confirm the universe is still 1,104 / 9,804 and that topic_centroids is (34, 768).
3. %PY% scripts\run_ops2_c3.py C3_full_corpus_universe
   Expect live_vs_replay 40/40 exact now. If it still aborts on live-vs-replay, the divergence has
   another cause — report it verbatim and STOP.
4. Report the FULL recall dict including @3, and the delta against BOTH C1_post_ops2 and
   C2_post_batch03. C2 vs C3 isolates the 95 -> 1,104 widening: same queries, same v4 gold, bigger
   haystack. A fall at @1 is expected and not automatically bad — the gold was authored for the
   95-document universe. Report and explain; tune nothing.
5. Confirm C0/C1/C2 are byte-unchanged in ops2_c1_drift.json and only C3 was appended.

PART B — two cheap questions the Phase 5 findings opened. $0.

6. DATE_INDEX_ENABLED, tested rather than argued. Without editing config.py, run the CE-11 diagnostic
   once with the flag set for that process only:
     set CJ_DATE_INDEX_ENABLED=1
     %PY% scripts\run_ce11_diag.py ce11_dateindex_on
   Then unset it. Report X50 and X51 specifically: does BC017/BC018 surface for "Which of your Justice
   and Faith reflections date from 1997?" Compare against ce11_diag_ce11_full_corpus.json row by row and
   report EVERY row that changed, not only the two.
   First confirm the flag is env-overridable in config.py (report the line). If it is not, say so and
   skip this step — do not edit config.py to force it.
   This is evidence for a decision, not the decision. Leave the flag off afterwards and confirm it is off.

7. X49, characterised one step further — still $0, still read-only. Report:
     a. how many chunks in the corpus contain the literal token "142840";
     b. how many phrase-dictionary entries contain a bare docket number with no case name attached;
     c. BD020's and BA041's raw counts of "g.r." and "no." in their top-ranked chunks, versus BA039's.
   That turns "citation-dense chapters act as an attractor" from a hypothesis into a measured claim, and
   sizes the fix. Do NOT change build_sparse_index.py or the dictionary.

REPORT PARTS A AND B — docs\p3\phase6_c3_and_findings_2026-09-26.md — then STOP and wait.
8. The diff; the C3 recall dict with both deltas and the mechanism; the date-index comparison row by
   row; the X49 measurements; and a recommendation on which universe to keep, with the numbers behind it.
   Recommend; the decision is the user's.

PART C — the voice card. DO NOT START WITHOUT EXPLICIT APPROVAL. SPENDS TOKENS.

9. Precondition: the user has read Parts A and B and has said go. If not, STOP.
10. Before anything: establish whether a bge-base COMPOSE baseline exists at all. arch_baseline_v2.json
    is bge-large / 827-chunk; arch-baseline-v4 and v4.2 are retrieval-only. Search eval\results\ and the
    repo root for any compose run made under bge-base and report what you find.
    If none exists, say so plainly and STOP: the R-1 change would have nothing to be compared against,
    and the honest sequence is to establish a compose baseline on the CURRENT corpus first, as its own
    approved spend, before changing the prompt. Do not proceed on the assumption that one exists.
11. Only if a comparable baseline exists: back up corpus\voice\voice_card.md, apply
    docs\p3\voice_card_header_proposed_2026-09-25.md to lines 1-14 — the block above the first --- and
    nothing else — and re-run the same compose harness. The corpus is held fixed; this is its own change
    with its own comparison. Report grounding and decline-rate deltas.
    The "Identity rule" section is CORRECT and stays: CJ Panganiban consented to the robot saying it is
    him (decision D-042).

FLAG, DO NOT FIX
- The step-1 diff showing more than one code change · C3 still aborting on live-vs-replay · any change
  to C0/C1/C2 · DATE_INDEX_ENABLED not being env-overridable · any urge to edit config.py,
  build_sparse_index.py or the phrase dictionary · starting Part C without approval or without a
  comparable baseline.
```

---

## What the Phase 5 findings become

| Finding | Owner | Why not now |
|---|---|---|
| **X49** — phrase dictionary indexes citations only as full-case-name atomic phrases; bare docket numbers lose to citation-list chapters on generic `g.r.`/`no.` frequency | **CE-13/14**, a `build_sparse_index.py` change | Rebuilding the sparse index mid-promotion re-opens the comparison that just closed |
| **X51** — `DATE_INDEX_ENABLED` is dark; the temporal filter exists for exactly this query shape | a config decision, evidence gathered in Part B | Flipping a flag during a correction batch confounds it; measure now, decide after |
| **A41** — near-miss among sibling Centenary chapters | none | Ordinary retrieval behaviour |
| **C48** — BC018's stale curated row | **P6 merge** (C-11) | Editing a pinned workbook breaks `verify_pin.py` |

## Then, in order

**P6 proper** — batch-04's 186 rows merge to 1,290 documents, 803 columns, all 12 works. That repeats
the whole of P3 on the larger corpus and is where C-11 and the C-13 enforcement fold in. About an hour
of GPU time.

**Still open:** the orphan floor at 0.68 against a 0.6816 minimum and GC006/CA330 never caught (CE-8) ·
the topic prior near-inert at mean pairwise cosine 0.9334 (CE-8) · `honors_received` ≡
`robot_identity_meta`, both zero-chunk (CE-8) · `check_date_index.py`'s NO-REGRESSION GATE still
comparing against the bge-large `arch_baseline_v2.json` (batch-05) · `merge_tag_topics.py` hardening and
the `--force` exit-3 refusal (now eligible) · C-12 and the ~222 columns from Feb 2007 – Apr 2011
(batch-05) · pushing `deliverable/2026-09` to `Supervaise-Inc/CJAP`.
