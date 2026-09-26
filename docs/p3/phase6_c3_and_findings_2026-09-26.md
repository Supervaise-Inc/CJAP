# Phase 6, Parts A and B — close the C3 measurement, then two findings

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Interpreter:** `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe` (Python 3.12.13)
**$0 throughout Parts A and B:** no API calls, no composer, no token spend.
**Part C: not started.** Per instructions, this report stops here and waits
for explicit approval before any token-spending step.

---

## PART A — the C3 measurement

### 1. Diff `run_ops2_c2.py` → `run_ops2_c3.py`

Outside the docstring (confirmed the docstring spans lines 1–25 by locating
the `"""` markers directly), exactly one code line changes:

```
-    allow = service._allowlist("v4")
+    # C3 variant: the universe IS the index. run_ops2_c1/c2 pin the live path to the
+    # 95-doc v4 allowlist while replay_ranked() ranks every row of mat with no filter.
+    # Those agreed only while mat was pre-sliced to those same 95 documents. Against a
+    # full-corpus index they diverge on every query and the run aborts on live-vs-replay.
+    # Taking the allowlist from the index itself makes both sides cover the same universe,
+    # which is exactly the widened-universe measurement C3 is for.
+    allow = set(doc_ids)
```

**Confirmed the ordering claim directly**, not taken on faith:

```
line 62:  chunk_ids, doc_ids = pm["chunk_ids"], pm["doc_ids"]
line 69:  allow = set(doc_ids)
```

`allow = set(doc_ids)` is at line 69, strictly after `doc_ids` is defined at
line 62 — no `NameError` risk. **No other code change outside the docstring.
The instrument is trustworthy.**

### 2. Universe / centroids confirmed

```
n_docs 1104 | n_chunks 9804
topic_centroids shape (34, 768)
```

Exact match — unchanged from Phase 5's widening.

### 3. Run `run_ops2_c3.py C3_full_corpus_universe`

```
[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; config-path)
[live-vs-replay] 40/40 exact
[C3_full_corpus_universe] recall @1/@5/@sent/@10 = 0.118/0.382/0.529/0.647
[C3_full_corpus_universe] delta vs v4 canon    = -0.5/-0.5/-0.412/-0.324
wrote eval\results\ops2_c1_drift.json [C3_full_corpus_universe]
EXIT=0
```

**`live-vs-replay` reads 40/40 exact — the fix works.** The Phase 5 divergence
is fully resolved; no other cause was in play, exactly as `run_ops2_c3.py`'s
own docstring diagnosed.

### 4. Full recall dict and both deltas

```
C1_post_ops2 recall:          {'1': 0.588, '3': 0.882, '5': 0.882, '10': 0.971, 'chunks_sent': 0.941}
C2_post_batch03 recall:       {'1': 0.588, '3': 0.853, '5': 0.882, '10': 0.971, 'chunks_sent': 0.941}
C3_full_corpus_universe recall: {'1': 0.118, '3': 0.294, '5': 0.382, '10': 0.647, 'chunks_sent': 0.529}
```

**delta_vs_C1 (C3 − C1):**

```
@1:  -0.4700   (0.118 vs 0.588)
@3:  -0.5880   (0.294 vs 0.882)
@5:  -0.5000   (0.382 vs 0.882)
@chunks_sent: -0.4120   (0.529 vs 0.941)
@10: -0.3240   (0.647 vs 0.971)
```

**delta_vs_C2 (C3 − C2) — this isolates the 95→1,104 widening, same queries,
same v4 gold, same batch-03-corrected corpus, only the haystack changes:**

```
@1:  -0.4700   (0.118 vs 0.588)
@3:  -0.5590   (0.294 vs 0.853)
@5:  -0.5000   (0.382 vs 0.882)
@chunks_sent: -0.4120   (0.529 vs 0.941)
@10: -0.3240   (0.647 vs 0.971)
```

**This is a large drop, not a small one** — far beyond what "a fall at @1 is
expected" alone would suggest at face value. Rather than accept that framing
on its own terms, I checked the mechanism directly.

### The mechanism, verified with concrete examples, not asserted

Every one of the 34 in-scope queries' `hit@1` outcomes was diffed between C2
and C3. Spot-checking eight where `hit@1` flipped from true to false, and
looking at exactly what document displaced the gold answer:

| qid | Query | C2 top-1 (in pilot 95) | C3 top-1 (outside pilot 95) |
|---|---|---|---|
| A1 | What does the rule of law actually mean? | CA031 — "Partners in rule of law, constitutionalism, AI" | **CA081** — "The rule of law in the besieged world" |
| B7 | What is the Liberty and Prosperity doctrine? | SB028 — "Liberty, Prosperity and the Rule of Law for CPAs..." | **SA138** — "Striking the Right Balance" |
| B12 | How do you balance liberty and prosperity...? | CB008 — "CPAs as purveyors of liberty and prosperity" | **SA138** — "Striking the Right Balance" |
| B8 | "those who have less in life should have more in law" | SB028 (same as above) | **CD025** — "Resonance" |
| C15 | What does justice mean to you personally? | BC001 — "With Due Respect... Justice and Love on Valentine's Day" | **CA440** — "Filipino justice—from concept to practice" |
| C17 | What qualities did you admire in your colleagues on the bench? | SB042 — "Reminiscences of an Independent Director" | **BD025** — "The Bio-Age Dawns on the Judiciary — Excellence and Ethics..." |
| D20 | Who is eligible for FLP scholarships? | CD001 — "11 LibPros scholars" | **CD020** — "Liberty, prosperity, rule of law" |
| D21 | Purpose of the Museum for Liberty and Prosperity? | SD002 — "Soon, a Futuristic Museum for Liberty and Prosperity" | **CD018** — "FLP expanding into prosperity" |

**All eight new top-1 documents are confirmed outside the 95-document pilot
subset, and all eight are plainly on-topic for their query** — not random
noise, not a broken index. **The mechanism, evidenced rather than assumed:**
`gold_reference_set.csv` was hand-curated *from and for* the 95-document
pilot subset — its "correct" answers are, by construction, always inside
that subset. Widening to the full 1,104-document corpus introduces many more
documents covering the *same* themes (rule of law, liberty and prosperity,
judicial colleagues, FLP scholarships) that the pilot curators never had in
their candidate pool. bge-base embedding similarity has no notion of "this
is the curated gold document" — it finds the topically closest match, and
the full corpus frequently contains one that is at least as good, sometimes
arguably better-titled for the exact query, and it wins the recall-@1 slot
away from the pilot-curated answer.

**This means the C3 recall collapse is very largely a measurement artifact
of grading a full-corpus retrieval against a 95-document-scoped gold set,
not necessarily evidence that end-answer quality actually degraded by this
much.** It is not proof of the opposite either — no composer-quality check
was run (out of scope for $0 Parts A/B) — but the concrete document-level
evidence above does not show retrieval breaking down; it shows retrieval
finding different, still-plausible answers from a pool the gold was never
scoped to credit.

### 5. C0/C1/C2 unchanged — confirmed

```
top-level keys after this run: anchor, v4_expect, C0_current_artifacts,
                                C1_post_ops2, C2_post_batch03, C3_full_corpus_universe
C0 recall: {'1': 0.588, '3': 0.882, '5': 0.882, '10': 0.971, 'chunks_sent': 0.941}
C1 recall: {'1': 0.588, '3': 0.882, '5': 0.882, '10': 0.971, 'chunks_sent': 0.941}
C2 recall: {'1': 0.588, '3': 0.853, '5': 0.882, '10': 0.971, 'chunks_sent': 0.941}
anchor:    "arch-baseline-v4 canonical C-baseline"    (unchanged)
v4_expect: {'1': 0.618, '5': 0.882, 'chunks_sent': 0.941, '10': 0.971}   (unchanged)
```

**All identical to the values recorded in Phase 4. Only `C3_full_corpus_universe`
was appended.**

---

## PART B — two cheap questions

### 6. `DATE_INDEX_ENABLED`, tested rather than argued

**Confirmed env-overridable first**, per instructions, before running anything:

```python
# config.py:511
DATE_INDEX_ENABLED: bool = _env_bool("CJ_DATE_INDEX_ENABLED", False)
```

Ran with the flag set for one process only:

```
set CJ_DATE_INDEX_ENABLED=1
python scripts/run_ce11_diag.py ce11_dateindex_on

[ce11] grounding recall @1/@3/@5/@10 = 0.273/0.636/0.818/0.818 | at-selected 0.818
```

(Compare to flag-off: `0.273/0.636/0.727/0.727`.)

**Full row-by-row diff against `ce11_diag_ce11_full_corpus.json`** (every
field checked, not just X50/X51):

| qid | Changed? | Detail |
|---|---|---|
| A41, A42, A43, A45, A46, B44, C47, C48, X49, X50, X52, X53, X54 | **No change** | Identical verdict, rank, retrieved_doc_ids, routed_topic in both runs |
| **X51** | **CHANGED** | `verdict: FAIL → PASS`; `n_chunks_selected: 7 → 12`; `rank_of_first_gold: None → 5`; `retrieved_doc_ids: [BD020,BC020,CC053,BA041,BC016] → [BD020,BC020,CC053,BA041,BC018,SC007]` (BC016 dropped, **BC018 and SC007 entered**) |

**Only X51 changed.** X50 — which the prompt specifically asked to check —
was already passing at rank 3 without the date filter and is completely
unaffected by enabling it. No other row moved, up or down.

**Flag left off, confirmed** — a fresh process with no override reads
`DATE_INDEX_ENABLED = False`. `config.py` was not edited.

This is real, if narrow, evidence for a decision: enabling the date filter
recovers exactly one CE-11 grounding row without disturbing any other row
in either diagnostic set. Not acted on; reported as evidence only.

### 7. X49, characterised one step further

**a. Chunks containing the literal token "142840":**

```
2 chunks: BA039::c001, BA039::c025
```

**b. Phrase-dictionary entries with a bare docket number, no case name
attached:**

The precise, targeted check — every phrase-dict entry that contains
`"g.r"` or starts with `"gr"`:

```
8 total G.R.-style entries in the phrase dictionary.
All 8 carry a full case name (contain " v.").
0 are a bare docket number with no case name.
```

(A broader, cruder first-pass heuristic — any phrase with a 4–7 digit number
and no "v." — caught 337 entries, but that set is mostly unrelated numeric
phrases: years, R.A. numbers, proclamation numbers, bar-exam years. That
number is reported for transparency but is **not** the answer to (b); the
8-entry G.R.-specific check above is.)

**c. Raw "g.r."/"no." token counts, competitor chunks vs. BA039's own chunks:**

| chunk_id | `g.r.` count | `no.` count | contains "142840" |
|---|---|---|---|
| BD020::c002 (competitor, rank 1 on sparse) | 3 | 3 | No |
| BA041::c030 (competitor) | 2 | 3 | No |
| BA041::c023 (competitor) | 3 | 3 | No |
| BA039::c001 (the actual answer) | **0** | 3 | **Yes** |
| BA039::c025 (the actual answer) | 0 | 0 | **Yes** |

**This sizes the fix precisely and adds a sharper finding beyond what Phase 5
established.** The actual chunk containing "142840" (`BA039::c001`) scores
**zero** on the `g.r.` token — checked why, and found the exact phrasing:

```
"...Thus, under\n1 GR No. 142840, May 7, 2001.\nthe 1935..."
```

BA039 writes the citation as **"GR No."** (footnote style, no periods), not
"G.R. No." (prose style, with periods). Confirmed with the real tokenizer,
not a guess:

```python
sparse.tokenize("GR No. 142840")    -> ['gr', 'no.', '142840']
sparse.tokenize("G.R. No. 142840")  -> ['g.r.', 'no.', '142840']
```

**`"gr"` and `"g.r."` are two distinct tokens in this tokenizer — periods are
not normalised away.** The query "What is G.R. No. 142840 about?" tokenizes
to `g.r.`, which never matches BA039's own footnote spelling `gr`. Combined
with (c)'s counts, the picture is now precise: BA039 loses on the `g.r.`
component of BM25 term overlap not just because competitors are
citation-dense, but because its own citation is written in the one
citation-style variant ("GR" without periods) that doesn't lexically match a
"G.R." (with periods) query — while `no.` and the docket number itself do
match. This is a specific, small-surface tokenization-normalisation gap
(`gr` / `g.r.` / `g.r` / `gr.` treated as distinct tokens), not a broad
defect. Not fixed here, per the boundary against touching
`build_sparse_index.py` or the phrase dictionary.

---

## Recommendation on which universe to keep

**The numbers, plainly:**

- **95-document universe (C2_post_batch03):** the only universe with a
  validated, gate-passing comparison against the ratified v4.2 baseline —
  `delta_vs_C1 = 0.000` on every headline metric, one small, fully-attributed
  @3 regression (Phase 4). This is the state the promotion decision in Phase
  4 was actually made against.
- **1,104-document universe (C3_full_corpus_universe):** a 32–59 point
  headline recall drop against the *same* pilot-scoped gold — evidenced above
  to be substantially a scope-mismatch artifact (the gold can't credit
  answers it was never shown), not a demonstrated quality collapse, but also
  **not validated by any comparably rigorous gate** — no gold set exists that
  was authored with the wider corpus in view, and no composer-quality check
  has been run at this scope either.

**Recommendation: keep the 95-document universe as the validated, gate-passing
state for now; treat full-corpus widening as its own separately-approved,
separately-measured change**, exactly as this project's own methodology has
treated every other change so far (batch-03 correction, centroid retag, and
now this). The current *live* runtime index is the widened, full-corpus one
(9,804 chunks / 1,104 docs) left in place from Phase 5 — I have not reverted
it, since restoring it is a decision, not a default I should make unilaterally.
The 95-doc state remains fully recoverable: `data/index/_archived_2026-09-26_pilot_dense.npy`
/ `_archived_2026-09-26_pilot_dense_meta.json` are the sha256-verified backup
from Phase 5, untouched by anything in this phase.

**This is a recommendation, not a decision — it's yours.**

## Files written this session

```
eval/results/ops2_c1_drift.json           (C3_full_corpus_universe appended; C0/C1/C2 unchanged)
eval/results/ce11_diag_ce11_dateindex_on.json   (new)
```

No `.py` file, `config.py`, gold CSV, or frozen query JSON was touched.
`data/index/pilot_dense.npy` was not modified in this phase (still the
Phase-5 full-corpus state).

## FLAG list — status

| Flag condition | Fired? |
|---|---|
| Step-1 diff showing more than one code change | No |
| C3 still aborting on live-vs-replay | No — 40/40 exact |
| Any change to C0/C1/C2 | No — confirmed byte-identical |
| `DATE_INDEX_ENABLED` not being env-overridable | No — confirmed overridable, tested, left off |
| Any urge to edit `config.py`, `build_sparse_index.py`, or the phrase dictionary | No — none touched |
| Starting Part C without approval or without a comparable baseline | No — Part C not started; waiting here |

---

**Stopping here per instructions. Part C spends tokens and requires explicit
approval before any step, including the baseline-existence check in step 10.**
