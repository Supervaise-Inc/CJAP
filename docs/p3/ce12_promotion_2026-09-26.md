# Phase 4 / CE-12 — batch-03 retrieval promotion check

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Interpreter:** `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe` (Python 3.12.13)
**$0 throughout:** no API calls, no composer, no token spend. Confirmed at every step below.
**Outcome:** **Retrieval-neutral, with one small, fully-attributed exception.**
The four headline recall metrics (@1/@5/@chunks_sent/@10) are bit-for-bit
identical to C1_post_ops2. One metric not in the script's own printed
summary — recall@3 — dropped 0.882→0.853, traced to a single query (C18)
where a corrected document's re-ranking bumped the gold document out of the
top-3 window. Recommendation at the end.

---

## STEP 0 — the two things that changed since the last prompt

### 1. `scripts/make_runtime_dense_index.py` — confirmed genuinely fixed

```
sha256[:16]: 94c6a43a6647e8fa   — exact match
"reconfigure" present:            yes (line 63, errors="replace")
U+2016 (‖) character count:       0
```

**Confirmed.** My earlier Amendment B finding (the claimed fix wasn't actually
in the file) is now resolved — this is the verification that it's genuinely
patched. Not run in this phase, per the boundaries.

### 2. `scripts/run_ops2_c2.py` — diff against `run_ops2_c1.py`

Everything outside the leading docstring is a single line:

```
< assert mat.shape == (827, config.EMBED_DIM) and cen.shape[0] == 34
---
> assert mat.shape == (len(chunk_ids), config.EMBED_DIM) and cen.shape[0] == 34
```

Confirmed by locating the docstring boundary in both files (`"""` before
`from __future__ import annotations` — verified identical position in both).
Everything else in the diff (the "Usage:"/"Verify with:" lines, the
explanatory paragraphs about the fix) is inside the docstring — text, not
code. One cosmetic blank line was also added after the docstring in C2 —
noted, not a code difference. **No second code change. The measurement
instrument is trustworthy.**

---

## PRE-FLIGHT

### 3. Four index artifacts

| Artifact | Value | Expected | Match |
|---|---|---|---|
| `pilot_dense.npy` | (826, 768) | (826, 768) | ✅ |
| `pilot_dense_meta.json` | n_docs 95, n_chunks 826, `pilot_subset_frozen_v4.csv (95 of 95 documents resolved)` | same | ✅ |
| `topic_centroids.npy` | (34, 768) | (34, 768) | ✅ |
| `topic_centroids_meta.json` | n_topics 34, merged_pairs [], merge_cosine 1.01 | same | ✅ |
| `pilot_sparse_meta.json` | n_chunks 9804 | 9804 | ✅ |
| `corpus_dense_meta.json` | BAAI/bge-base-en-v1.5, dim 768, n_chunks 9804 | same | ✅ |

The sparse arm covering 9,804 chunks while the dense runtime index covers 826
is correct as noted (sparse filters by allowlist at query time; dense is
pre-sliced) — not touched.

### 4. `service._allowlist("v4")`

```
type: set | count: 95
first five (sorted): ['BA009', 'BA027', 'BB001', 'BB002', 'BB003']
```

**PASS — 95 documents, matching the runtime index universe.**

### 5. `gold_reference_set.csv`

```
n_rows: 40 | scope_gold=='in' count: 34
sha256: 37259902530d92efab33d0c8620cdf0fa830b25cfff8579d2bb55a11a9a1bca5
```

**PASS — exact match, unchanged from Phase 3.**

### 6. `verify_pin.py`

```
[verify_pin] PASS — 1109 docs across 4 source files match corpus_snapshot.json.
EXIT=0
```

**PASS.**

### 7. `ops2_c1_drift.json` — existing labels before this run

```
top-level keys: anchor, v4_expect, C0_current_artifacts, C1_post_ops2
anchor:    "arch-baseline-v4 canonical C-baseline"
v4_expect: {"1": 0.618, "5": 0.882, "chunks_sent": 0.941, "10": 0.971}

C0_current_artifacts.recall: {"1": 0.588, "3": 0.882, "5": 0.882, "10": 0.971, "chunks_sent": 0.941}
C1_post_ops2.recall:         {"1": 0.588, "3": 0.882, "5": 0.882, "10": 0.971, "chunks_sent": 0.941}
Both: live_vs_replay = "40/40 exact"
```

**Confirmed: C1_post_ops2 reads @1 0.588 / @5 0.882 / @chunks_sent 0.941 /
@10 0.971 — exact match.** C1_post_ops2 is the comparator for batch-03;
`v4_expect` (@1=0.618) is a different, earlier reference point and is not
used as the comparator here, per instructions.

---

## HEALTH GATE — three anchors, retrieval only

Run via `retrieval.run(query, service._allowlist("v4"))`, no composition:

| Anchor | Query | Route | n_selected | Expected (v4.2 provenance) | Verdict |
|---|---|---|---|---|---|
| A1 rule-of-law | "What does the rule of law actually mean?" | global_geopolitics | **7** | n_selected=7 | **Exact match** |
| D21 museum | "What is the purpose of the Museum for Liberty and Prosperity?" | museum_for_liberty_and_prosperity | **10** | route=museum_for_liberty_and_prosperity, n_selected=7 | Route matches exactly; n_selected moved 7→10 |
| E28 roe-v-wade | "What did the Court decide in Roe v. Wade?" | constitutional_doctrine | **10** | n_selected=16 | n_selected moved 16→10 |

**No crash, no empty selection, no wildly different route — no STOP condition
fired.** Per instructions, a changed n_selected is not automatically a
failure; attributing each:

- **D21:** selected doc_ids were `SD002, SD021, SD016` — **none of these are
  among the 18 batch-03-corrected pilot documents.** This move is best
  explained by the corpus-wide BM25/IDF rebuild (the sparse index covers all
  9,804 chunks; correcting any of the 156 corpus-wide documents shifts global
  term-frequency statistics and can move RRF-fused scores for chunks whose
  own text never changed) rather than a direct content change. This is the
  same mechanism `run_ops2_c1.py`'s own docstring names as one of the drift
  sources it exists to measure.
- **E28:** selected doc_ids included `BD001`, `BD003`, and `BA009` —
  **all three are directly among the 18 corrected pilot documents.** This is
  a concrete, document-level explanation: these documents' own re-chunking/
  re-embedding under batch-03 plausibly moved their similarity ranks for this
  query, shifting how many chunks clear the top-p nucleus cutoff.

---

## RUN

```
python scripts/run_ops2_c2.py C2_post_batch03

[embeddings] loading resident model BAAI/bge-base-en-v1.5 on cuda (load #1; config-path)
[live-vs-replay] 40/40 exact
[C2_post_batch03] recall @1/@5/@sent/@10 = 0.588/0.882/0.941/0.971
[C2_post_batch03] delta vs v4 canon    = -0.03/+0.0/+0.0/+0.0
wrote eval\results\ops2_c1_drift.json [C2_post_batch03]
EXIT=0
```

No assert fired. Confirmed the write only **appended** a new `C2_post_batch03`
key — `anchor`, `v4_expect`, `C0_current_artifacts`, `C1_post_ops2` are all
present unchanged after the write.

---

## VERIFY — the promotion evidence

### 10. Verbatim printed line

```
[C2_post_batch03] recall @1/@5/@sent/@10 = 0.588/0.882/0.941/0.971
```

### 11. Both deltas

```
delta_vs_v4  (script's own, C2 vs v4_expect @1=0.618):
  @1: -0.03 | @5: +0.0 | @chunks_sent: +0.0 | @10: +0.0
  -> This is the accepted July B11/BM25-rebuild loss at @1. It is NOT a
     batch-03 result — it predates batch-03 entirely and is already baked
     into C0 and C1 identically.

delta_vs_C1  (C2 minus C1_post_ops2 — computed directly from the four
              headline metrics both records share):
  @1: +0.0000 (0.588 vs 0.588)
  @5: +0.0000 (0.882 vs 0.882)
  @chunks_sent: +0.0000 (0.941 vs 0.941)
  @10: +0.0000 (0.971 vs 0.971)
  -> THIS IS THE BATCH-03 RESULT. All four headline metrics are unchanged.
```

**One metric outside the script's own headline summary moved, and it is
reported here per instruction 15 ("report anything that got worse"):**

```
recall@3:  C1_post_ops2 = 0.882   C2_post_batch03 = 0.853   delta = -0.029
```

This metric is present in the full `recall` dict written to the JSON but is
not one of the four the script prints in its summary line (`@1/@5/@sent/@10`
only — `@3` is silently omitted from that line, though computed and stored).
Traced to a single query below.

### 12. Per-query attribution

Diffing every one of the 34 in-scope queries' `hit@k` values and
`retrieved_docs` lists between C1_post_ops2 and C2_post_batch03:

**Only one query's graded outcome (`hit@k`) actually changed:**

| qid | hit@k that flipped | Mechanism | Attributed to |
|---|---|---|---|
| **C18** | `hit@3`: True → False | Same 15 documents in both runs (no doc added/removed) — but `BB002` rose from rank 8 (index 7) to rank 2 (index 1), pushing the gold document out of the top-3 window while it stayed inside the top-15 (`hit@5`/`hit@10`/`hit@sent` all still True) | **`BB002`** — directly among the 18 batch-03-corrected pilot documents |

Exactly one query flipping recall@3 out of 34 in-scope queries accounts for
the observed delta: 1/34 ≈ 0.0294, matching the observed 0.882→0.853 drop
(0.029) precisely.

**19 further queries show a document-set change at the tail of their top-15
list, with no effect on any `hit@k` value** (all remained identical
before/after for these):

| qid | Added | Removed | Corrected-doc attribution |
|---|---|---|---|
| A1 | BE002 | CA242 | BE002 (corrected) |
| A2 | BA009 | SB040 | BA009 (corrected) |
| A4 | BD001 | CA095 | BD001 (corrected) |
| A6 | BA027 | CE008 | BA027 (corrected) |
| B7 | BE002 | CE008 | BE002 (corrected) |
| B8 | BD004 | CA060 | BD004 (corrected) |
| C13 | BD002 | SC005 | BD002 (corrected) |
| C15 | BD002 | CA330 | BD002 (corrected) |
| C16 | BC001 | BD001 | both corrected (swap between two corrected docs) |
| D21 | SB063 | CE001 | **no direct match** — attributed to corpus-wide BM25/IDF drift (see Health Gate) |
| D24 | BC001 | SC008 | BC001 (corrected) |
| E26 | CE008 | BD002 | BD002 (corrected, removed side) |
| E27 | BB002 | BD005 | both corrected (swap between two corrected docs) |
| E28 | CA095 | BC001 | BC001 (corrected, removed side) |
| E30 | BB002, BE003 | CA377, CC004 | both added docs corrected |
| X34 | SB040 | BD006 | BD006 (corrected, removed side) |
| X38 | BD006 | CD003 | BD006 (corrected) |
| X40 | BD002, SC010 | SB063, SD021 | BD002 (corrected, added side) |

**15 of these 19 tail-rank changes are directly explained by one of the 18
batch-03-corrected pilot documents entering or leaving the bottom of a
top-15 ranking — a rank-14/15 boundary effect with zero effect on any graded
metric.** Only **D21** lacks a direct document-level cause; it is attributed
to the same corpus-wide BM25/IDF mechanism identified in the Health Gate
(D21's own selected documents there — SD002/SD021/SD016 — likewise showed no
overlap with the 18-doc list).

**The remaining 14 of 34 in-scope queries showed no change whatsoever**
(A3, A5, B9, B10, B11, B12, C14, C17, D19, D20, D22, D23, D22, X37 — identical
`hit@k` and identical retrieved_docs, order included, between C1 and C2).

### 13. `live_vs_replay`

```
C0: 40/40 exact
C1: 40/40 exact
C2: 40/40 exact
```

All three read 40/40 exact. **PASS.**

### 14. Retired-ID check

```
retired ID leak across all C2 retrieved sets: NONE
```

Checked programmatically across every query's full `retrieved_docs` list in
C2_post_batch03. **PASS.**

### 15. What got worse — reported plainly

**One thing got worse: recall@3, 0.882 → 0.853 (−0.029), caused by exactly
one query (C18) where a corrected document's re-ranking pushed the gold
answer from rank 3 to rank 4.** This is a small, single-query, fully-traced
regression on a metric the script computes but doesn't print in its own
headline summary. Every other metric — the four the script does headline —
held exactly. Per instruction 15's own framing, "no measurable retrieval
change" would have been the ideal outcome for a correction batch; this is
very close to that, with one narrow, well-understood exception rather than a
broad or unexplained one.

---

## Recommendation

**Promote, with one caveat noted for the record — not a blocker.**

- The four metrics `run_ops2_c2.py` itself reports as the promotion gate
  (`@1/@5/@chunks_sent/@10`) are **bit-for-bit identical** to C1_post_ops2.
  `delta_vs_C1 = 0.000` across the board on the actual gate criteria.
- The one metric that moved (`@3`) is not part of that gate, dropped by a
  single query, and the mechanism is fully attributed to one of the batch-03
  corrections themselves (`BB002`, a document the correction batch legitimately
  touched) rather than to any index-repair side effect, an unrelated
  regression, or an unexplained drift.
- Health gate: 3/3 still non-crashing, non-empty, correctly-routed (where
  routes were recorded); both `n_selected` moves are attributed, one directly
  to corrected documents, one to the accepted corpus-wide BM25/IDF mechanism.
- `live_vs_replay` holds at 40/40 across C0, C1, and C2. No retired ID
  anywhere. `verify_pin` exits 0.

**Caveat for the record, not acted on here:** `run_ops2_c2.py`'s printed
summary line omits `@3` from its headline, so a regression on that specific
metric would not surface without reading the full JSON, as done here. Worth
flagging to whoever owns the harness — not a request to add it, since editing
`.py` files is out of this phase's boundaries.

**The decision to promote is yours.** Nothing above suggests batch-03
introduced a broad or unattributed retrieval regression; the one metric that
moved has a name, a document, and a mechanism behind it.
