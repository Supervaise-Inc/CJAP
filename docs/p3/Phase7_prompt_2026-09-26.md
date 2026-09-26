# Phase 6 assessment, and Phase 7 — adjudicate the universe, then two sized fixes

**26 Sep 2026.** Phase 6 A and B are excellent work. One conclusion in it is understated, and the
understatement matters, because it feeds a recommendation I think is wrong for a reason that has nothing
to do with the measurement.

## What Phase 6 got right

**C3 ran clean** — `live_vs_replay 40/40 exact`, the divergence fully resolved, C0/C1/C2 byte-unchanged,
only C3 appended. The diff was verified rather than assumed, including the line ordering I had got
wrong on the first cut.

**The date-index test is a model of how to settle a question.** Env override only, flag confirmed
reverted, and the full 14-row diff rather than just the two rows I asked about: **exactly one row moves**
— X51 FAIL → PASS at rank 5, X50 already passing and untouched, nothing else changes. That is a clean,
zero-collateral result.

**X49 got sharper than Phase 5 left it.** BA039's own text writes **"GR No. 142840"** — no periods,
footnote style — while the query and the competitor chunks use **"G.R."**, and CC confirmed against the
real tokenizer that `gr` and `g.r.` are *distinct tokens*. Plus: only 2 chunks contain `142840` at all,
and 0 of 8 G.R. phrase-dictionary entries carry a bare docket number. That is no longer "citation-dense
competitors crowd it out" — it is a specific tokenization gap with a bounded fix.

## Where I read the C3 result differently

CC characterised the 47-point drop as "largely a scope-mismatch artifact — the gold set can't credit
answers it was never shown", on the strength of 8 spot-checked hit@1 flips. I ran all 34 from the
`per_query` records, and the picture splits in two.

First, what `retrieved_docs` actually is: the **top 15 documents of the full fused ranking**
(`run_ops2_c1.py` dedupes the ranked chunk list to documents and caps at 15) — not the selected nucleus.
So "absent" means below rank 15 of 1,104, not absent from the corpus.

```
gold document present in the top 15   C2: 33/34      C3: 23/34
rank of first gold when present       C3: median 4, mean 4.9, max 11
C3 top-1 outside the 95-doc subset    28/34 (82%)
```

**Two distinct effects, not one.** For the 23 queries where gold survives, CC's mechanism is exactly
right: median rank 4, outranked by plausible full-corpus alternatives that the gold list cannot credit.
Pure measurement artefact. But for **11 queries the gold document falls out of the top 15 entirely** —
in C2 that happened once. Those are not reorderings, and calling the whole drop an artefact papers over
them.

What the 11 cannot tell us on their own is whether they are *failures*. Look at what replaced them:

| query | gold | C3 top-4 |
|---|---|---|
| C13 | BC001 | BC008, BA035, BC017, BC018 — sibling chapters of the same book |
| E28 | CE007 | CA189, CA142, CA376, CA078 |
| B9 | CB006;CB005;CB007 | GC034, CD003, CC028, SB085 |

Document IDs cannot settle that. **Whether the full-corpus universe is acceptable is a question about
answer quality, and it can only be settled by reading what actually came back.** Recall against a gold
list authored for a 95-document universe is structurally unable to answer it.

## And the recommendation I'd change

CC recommends keeping the 95-document universe as "the validated state". That is the right instinct
about evidence and the wrong answer about the product. **The pipeline is specified to serve the whole
corpus** — all 12 works, the columns, the speeches, the biography. A robot answering from 95 of 1,104
documents (8.6%) is not shippable, whatever its recall against a subset-authored gold.

So the decision is not "95 or 1,104". It is **what has to be true for 1,104 to be measurable**, and the
honest answer is: a gold set that was authored against the full corpus, or at minimum an adjudication of
the queries where the subset-era gold and the full-corpus retrieval disagree. That is CE-13's real
content, and it is the actual blocker to shipping — bigger than the voice card, which is why Part C is
deferred again below.

Meanwhile the live index is the widened one, which is correct for the product and differs from the
"validated" C2 state. Leave it; note the divergence in the record.

---

## The prompt

```
Phase 7 — adjudicate the universe question, then size two fixes. $0 THROUGHOUT.
NO API CALLS, NO TOKENS, NO COMPOSER. Interpreter:
  set PY="C:\Reachy Mini Project 2026\.venv\Scripts\python.exe"
If any step would compose an answer or contact the Anthropic API, STOP.

BOUNDARIES
- Do NOT edit any .py file. Do NOT edit config.py. Do NOT rebuild any index.
- Do NOT run build_centroids.py. Do NOT merge batch-04. Do NOT touch voice_card.md.
- Do NOT modify gold_reference_set.csv, draft_queries_v1.json, the CE-11 files, or any C0-C3 record.
- Leave the runtime index as it is (full corpus, 1,104 / 9,804). Do not revert it.

PART A — adjudicate the 11 displaced queries. This is the decision-relevant evidence.

1. From ops2_c1_drift.json C3_full_corpus_universe.per_query, confirm my list: the in-scope queries
   whose gold document appears NOWHERE in the top-15 are
     A2, A4, B8, B9, C13, C14, C17, C18, D24, E28, X40
   Report the list you derive; if it differs from mine, yours wins — say so and use yours.
2. For EACH of those queries, produce a judgement table with:
     - the query text (from gold_reference_set.csv)
     - the gold documents, with their TITLES
     - C3's top-3 documents, with their TITLES and their dates
     - where the gold document actually ranks in C3's full fused ranking, not just "absent from top 15".
       Get this from the live path: retrieval.run(query, allowlist-from-pilot_dense_meta) and walk the
       ranked list. Report the rank number, or "beyond the ranking" if it truly does not appear.
     - your one-line judgement: would C3's top-3 answer the question as well as the gold, better, or
       worse? Judge the CONTENT from the titles and, where the title is not enough, the first 200
       characters of the top chunk. Do not judge from doc IDs.
3. Tally: of the 11, how many are BETTER-or-EQUAL replacements and how many are genuine losses.
   That ratio is the answer to whether the full-corpus universe is acceptable, and it is the number
   this phase exists to produce.
4. Also report, for the 23 queries where gold survived: the rank distribution, and whether any of them
   would fall outside a realistic composer window (the nucleus, not the top-15 grading window).

PART B — the date index, measured where the decision lives

5. The CE-11 test showed one row improving and nothing regressing. Before that can become a default,
   it needs the same test on the frozen 40. With the env override only, and confirmed reverted after:
     set CJ_DATE_INDEX_ENABLED=1
     %PY% scripts\run_ops2_c3.py C4_dateindex_on
     (then unset, and confirm it reads False in a fresh process)
   Report the full recall dict including @3, and the delta against C3_full_corpus_universe. C3 is the
   comparator here, NOT C2 — same universe, one flag different.
6. Report any query whose retrieved set changed, and say whether the date index helped, hurt or did
   nothing. A flag that improves CE-11's X51 but degrades the frozen 40 is a trade, not a win.
   Do NOT change the default in config.py either way.

PART C — size the X49 fix precisely. Read-only.

7. The finding is that BA039 writes "GR No. 142840" while the query says "G.R. No. 142840", and the
   tokenizer treats gr and g.r. as different tokens. Measure the blast radius:
     a. across the whole corpus, how many chunks contain "GR No." (no periods) versus "G.R. No."?
     b. how many distinct documents use each form? Do particular books or formats favour one?
     c. in the phrase dictionary, how many entries contain each form?
     d. how many of the 40 frozen queries and the 14 CE-11 queries contain a citation in either form?
8. State plainly what a fix would be — a normalization in app/sparse.py's shared tokenizer so that
   "g.r." and "gr" fold to one token — and what it would require re-running (the sparse index, and
   therefore a fresh C-label comparison). Do NOT implement it. Sizing is the deliverable.

REPORT — docs\p3\phase7_universe_adjudication_2026-09-26.md
9. Part A's judgement table and the better-or-equal / genuine-loss tally, stated as the recommendation
   on the universe. Part B's frozen-40 date-index delta with a recommendation on the flag. Part C's
   four measurements and the fix description with its re-run cost.
10. State explicitly which questions remain unanswerable without either a full-corpus gold set or a
    composer run, so the cost of each is visible.

FLAG, DO NOT FIX
- Your displaced-query list differing from mine (report both) · the date index degrading the frozen 40 ·
  any urge to edit config.py, app/sparse.py, the phrase dictionary or any gold file · any step that
  would spend tokens.
```

---

## Why the voice card waits again

R-1 still has no comparable baseline — `arch_baseline_v2` is bge-large/827, and v4/v4.2 are
retrieval-only. Establishing a bge-base compose baseline is its own approved spend, and it should be
established on whichever universe survives Phase 7, not on one we are about to change. Doing it now
would mean paying twice.

## The queue after Phase 7

| | |
|---|---|
| **CE-13** | a gold set authored against the full corpus — the real blocker to shipping |
| **X49 tokenizer fix** | `app/sparse.py` normalization + sparse rebuild + a fresh C-label |
| **Date index** | flip the default only if Part B says it is free on the frozen 40 |
| **Compose baseline + R-1** | one approved spend, after the universe is settled |
| **P6 merge** | batch-04's 186 rows → 1,290 documents, all 12 works; C-11 and C-13's enforcement fold in |
| **CE-8** | the orphan floor at 0.68 vs a 0.6816 minimum · the near-inert topic prior (mean pairwise 0.9334) · `honors_received` ≡ `robot_identity_meta`, both zero-chunk |
| **batch-05** | C-12 (CA528 truncated) · the ~222 columns Feb 2007 – Apr 2011 · re-baselining `check_date_index.py`'s NO-REGRESSION GATE off bge-large |
| **Housekeeping** | `merge_tag_topics.py` hardening · `make_runtime_dense_index.py`'s exit-3 refusal · push `deliverable/2026-09` · the 94 staged `eval/results` files still to commit |


---

## PART D — the three P3 acceptance gaps (added 26 Sep, after auditing P3.1-P3.6)

An audit of the P3 block against its own "Done when" bullets found P3.3 and P3.6 short and P3.5 built
but dark. `CJAP_Robot_Project_Plan_v2.xlsx` Status/Evidence has been updated accordingly — P3.2 and P3.4
move up to Done (both rebuilt 26 Sep), **P3.3 moves DOWN from Done to Partial**. Add this part to
Phase 7; it is still $0 and still ends in a report, not a change.

```
PART D — size the three P3 acceptance gaps. $0, READ-ONLY, no index rebuilds, no file edits.

D1. P3.3 gap 1 — tagging covers 95 of 1,104 documents.
    The plan requires "every document tagged with a primary and secondary topic".
    merge_tag_topics.py STEP 5 reads reports\pilot-eval subset\pilot_subset_frozen_v4.csv and tags only
    those 95. Its own doc_affinity() already scans the FULL corpus for the orphan census, so the data to
    tag all 1,104 is computed and then discarded.
    Report: the exact lines that scope the tagging to the pilot list; what a full-corpus tagging pass
    would cost (it is matrix work already done — estimate the added runtime); and whether the output
    file shape (reports\w1_7_pilot_topic_tags.json) would need to change or just grow.
    Do NOT implement it. This is a scope-and-cost answer.

D2. P3.3 gap 2 — the independence check is mis-calibrated, and the degenerate pair is live in the data.
    At TOPIC_MERGE_COSINE 0.95, 220 of 561 centroid pairs merge and 34 topics collapse to 3. We bypass it
    at 1.01. Separately, honors_received and robot_identity_meta are byte-identical zero-chunk centroids
    sharing one gmean fallback — and they are appearing as SECONDARY tags on real documents (sample:
    CA003 -> secondary ['honors_received', 'robot_identity_meta']).
    Report: (a) across the 95 tagged documents, how many carry either of those two as primary, and how
    many as secondary; (b) the threshold at which the merge would produce a sensible number of topics —
    sweep TOPIC_MERGE_COSINE from 0.95 to 0.999 in steps and report the resulting topic count at each,
    computed directly from the centroid matrix, WITHOUT running merge_tag_topics.py; (c) whether
    retiring the two zero-chunk topics would change the answer.
    Do NOT change any threshold or retire anything.

D3. P3.6 — what the voice card still needs.
    Three bullets are unmet. Report, from corpus\voice\voice_card.md:
    (a) confirm the opening block (lines 1-14, above the first ---) still states Haiku routing, "no
        embeddings, no similarity search, no chunking", and whole documents — quote the lines;
    (b) whether any signature-phrase section exists at all, and what the card currently says about
        signature phrases (line 353 is the only hit I found);
    (c) whether any authorship, reviewer or date marker exists anywhere in the 380 lines;
    (d) a list of every OTHER passage in the remaining ~366 lines that assumes a small corpus, whole
        documents, or the removed Haiku router — this is P3.6's outstanding "read-through by someone who
        knows the voice", done mechanically so the SME read starts from a list rather than a blank page.
    Do NOT edit the card. R-1 stays staged until after a compose baseline exists.

REPORT — append a "Part D — P3 acceptance gaps" section to the Phase 7 report with D1's cost answer,
D2's threshold sweep table and tag counts, and D3's four findings including the passage list.
```

**Why these are not fixed in this phase.** D1 changes what `merge_tag_topics.py` writes, which is in the
batch-03 attributable path. D2 is a calibration decision that belongs to CE-8 and needs the sweep before
anyone picks a number. D3's R-1 apply needs a compose baseline that may not exist. All three are sized
here so the decisions are cheap when they come.
