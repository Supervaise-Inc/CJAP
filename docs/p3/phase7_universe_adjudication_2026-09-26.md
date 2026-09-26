# Phase 7 — adjudicate the universe question, then size two fixes

**Date:** 2026-09-26
**Operator:** Claude Code (Sonnet 5)
**Interpreter:** `C:\Reachy Mini Project 2026\.venv\Scripts\python.exe` (Python 3.12.13)
**$0 throughout:** no API calls, no composer, no token spend.
**Runtime index:** left as-is (full corpus, 1,104 / 9,804) — not reverted, per instructions.

---

## PART A — adjudicate the 11 displaced queries

### 1. Displaced-query list — confirmed identical

Derived independently from `ops2_c1_drift.json`'s `C3_full_corpus_universe.per_query`,
cross-referenced against `gold_reference_set.csv`'s `gold_source_docs`:

```
A2, A4, B8, B9, C13, C14, C17, C18, D24, E28, X40   (11 queries)
```

**Matches the given list exactly.**

### 2–3. Judgement table

For each query: gold documents with titles, C3's top-3 with titles and dates,
the gold document's true rank in C3's full fused ranking (via
`retrieval._score_universe`, walking the complete 1,104-document ranked
list — not just the top-15 grading window), and a content-based judgement
(titles plus, where needed, actual chunk text, not doc IDs).

| qid | Query | Gold (titles) | Gold's true rank (full ranking) | C3 top-3 (titles, dates) | Judgement |
|---|---|---|---|---|---|
| **A2** | Why is an independent judiciary important in a democracy? | BD001 "How the SC Decides Cases"; BD002 "Chief Justice of the Philippines" | BD001: 31, BD002: 49 | CE020 "Democracy is more than having an election" (2025); **BA005 "Bequeathing an Independent Court"** (2009, same *With Due Respect Vol. 2* as gold, adjacent chapter); SA145 "Safeguarding the Liberty..." (2006) | **Better-or-equal** — BA005 is a near-perfect topical match, same book, explicit "independent court" framing |
| **A4** | What is your view on judicial activism? | CA377 "CBCP and same-sex marriage" | 986 (of 1,104 — essentially unfound) | **CA112 "Origin of judicial activism"** (2023); **CA111 "Judicial activism in the Philippines"** (2023); CA376 "Reactions to comments..." | **Better** — checked CA377's actual text: it substantively discusses judicial restraint/activism via Obergefell, but never uses the literal phrase "judicial activism" (confirmed). CA112/CA111 are explicit, direct, title-perfect treatments of the named concept |
| **B8** | 'those who have less in life should have more in law' | SA011 "Human Rights, Libertarianism and Prosperity"; SB028 "Liberty, Prosperity and Rule of Law for CPAs..." | SA011: 82, SB028: 84 | CD025 "Resonance" (2016, LibPros essays); BB007 "Ang Bagong Bayani-OFW Labor Party v. Comelec — Party-List, a Social Justice Tool" (2001); BD021 "Advice for Aspiring Attorneys" (1995) | **Genuine loss** — the replacements are thematically adjacent (social justice, liberty/prosperity) but less precisely on-message than gold's direct triad language |
| **B9** | How does the law help small entrepreneurs and MSMEs? | CB006 "Unleashing entrepreneurial ingenuity"; CB005 "Merging law and economics"; CB007 "SC decisions on the economy" | CB006: 59, CB005: 132, CB007: 239 | GC034 "Ch.14: Liberty and Prosperity" (2006); **CD003 "20 law grants at P250k, 5 MBA at P500k"** (2025, FLP MSME/legal-education grants — directly on-topic); CC028 "A brilliant executive but God's servant first" (2024, off-topic obituary) | **Roughly equal** — CD003 is a strong, direct answer; CC028 is a clear miss, but 1-of-3 on-target keeps this from being a real loss |
| **C13** | How has your faith shaped your work as a justice? | BC001 "Justice and Love on Valentine's Day" | 97 | **BC008 "Justice Is God's Work"** (2001); BA035 "E-Values for Lawyers" (2001); BC017 "Offering to the Father" (1997) | **Better-or-equal** — BC008's title is arguably a more direct statement of the exact question than the gold |
| **C14** | What lessons did your years on the Supreme Court teach you? | BC001; SA011 "Human Rights..."; CC002 "Jovito R. Salonga, my guru and surrogate father" | BC001: 202, SA011: 88, CC002: 34 | SC032 "Lessons for Young and Not-so-young Couples" (2021, **off-topic** — marriage advice, spurious "Lessons" keyword match); BC014 "Faith in God and in Ourselves" (1997, tangential); **BD025 "Excellence and Ethics in Appellate Practice"** (2003, directly relevant) | **Genuine loss** — one strong hit (BD025) but a clearly off-topic top pick (SC032) and a tangential third; weaker overall than gold's mentor-eulogy angle |
| **C17** | What qualities did you most admire in your colleagues on the bench? | CC002 "Jovito R. Salonga..."; SB042 "Reminiscences of an Independent Director" | CC002: 216, SB042: 144 | **BD025 "Excellence and Ethics in Appellate Practice"** (2003, directly relevant); GC015 "The Bench" (his own SC appointment story, biographical, not about admiring colleagues); BD024 "The Essentials of Legal Education" (2003, tangential) | **Better-or-equal** — BD025 is a strong direct answer despite the other two being weaker |
| **C18** | Looking back, what are you most proud of? | SC010 "My Three Outstanding and Adorable 'Apos'"; CC008 "Keep doing my best, let God do the rest" | SC010: 183, CC008: 75 | BC014 "Faith in God and in Ourselves" (1997, tangential); SD148 "Rising to the Challenge" (2006, honorary doctorate address); SB079 "Safeguard Liberty, Conquer Poverty..." (2014, alumni speech) | **Genuine loss** — none hits the specific personal-pride framing (grandchildren, "keep doing my best") as squarely as gold |
| **D24** | Why did you establish the foundation? | SB050 "Dr. George S. K. Ty..." eulogy; SD035 "Organizing the FLP Scholars Society"; SD016 "From an Imbedded Legal Lore to a Practical Reality" | SB050: 67, SD035: 47, SD016: 34 | SC130 "Why I Am Who I Am Now" (2007, personal biography, could touch founding but not FLP-specific by title); CC111 "Blessings and thanks" (2011, New Year reflection, off-topic); BC013 "Faith Brought Me to the Supreme Court" (1995, off-topic — SC appointment, not FLP) | **Genuine loss** — none directly addresses the founding rationale as squarely as any of the three gold documents |
| **E28** | What did the Court decide in Roe v. Wade? | CE007 "Liberalism vs conservatism" | 79 | **CA189 "Libertarian struggle through jurisprudence"**; **CA142 "Scotus conservatives flex muscles"**; CA376 "How cases are decided" | **Better-or-equal** — checked directly: CA142 and CA189 both quote the actual Roe holding near-verbatim ("...7-2... statutes criminalizing abortion are void because they violate a woman's constitutional right..."), essentially the same substantive content as the gold document (CE007 also discusses Roe with the same content) |
| **X40** | Advice for a young lawyer just starting out? | CC002 "Jovito R. Salonga..."; SB028 "Liberty, Prosperity and Rule of Law..." | CC002: 333, SB028: 45 | BD025 "Excellence and Ethics in Appellate Practice" (2003, advice-oriented); **CA110 "Welcome to the new attorneys — With Due Respect"** (2023, literally about welcoming new bar-passers); BC001 "Justice and Love on Valentine's Day" (2010, tangential) | **Better-or-equal** — CA110 is an explicit, arguably better match, directly addressing new attorneys |

### Tally

**7 of 11 (64%) are better-or-equal replacements: A2, A4, B9, C13, C17, E28, X40.**
**4 of 11 (36%) are genuine content-level losses: B8, C14, C18, D24.**

None of the 11 is a catastrophic or nonsensical miss — every displaced query's
top-3 replacement is at minimum topically adjacent, and a clear majority
substantively answer the question as well as or better than the pilot-curated
gold. **This is the number Part A exists to produce.**

### 4. The 23 "surviving" queries — rank distribution, and a further finding beyond the top-15 window

Walked the full fused ranking (via the live `retrieval.run()` path, not the
replay) for every one of the 23 in-scope queries whose gold document *is*
present somewhere in the top-15 grading window:

```
A1: rank 10 in top15 | nucleus n=13 | gold IN nucleus
A3: rank 1  | nucleus n=4  | gold IN nucleus
A5: rank 1  | nucleus n=4  | gold IN nucleus
A6: rank 1  | nucleus n=5  | gold IN nucleus
B10: rank 4 | nucleus n=10 | gold IN nucleus
B11: rank 11| nucleus n=9  | gold NOT in nucleus
B12: rank 5 | nucleus n=5  | gold NOT in nucleus
B7: rank 7  | nucleus n=6  | gold NOT in nucleus
C15: rank 6 | nucleus n=6  | gold NOT in nucleus
C16: rank 1 | nucleus n=4  | gold IN nucleus
D19: rank 4 | nucleus n=10 | gold IN nucleus
D20: rank 2 | nucleus n=4  | gold IN nucleus
D21: rank 2 | nucleus n=6  | gold IN nucleus
D22: rank 9 | nucleus n=6  | gold NOT in nucleus
D23: rank 7 | nucleus n=5  | gold NOT in nucleus
E25: rank 3 | nucleus n=9  | gold IN nucleus
E26: rank 3 | nucleus n=6  | gold IN nucleus
E27: rank 6 | nucleus n=11 | gold IN nucleus
E29: rank 3 | nucleus n=4  | gold IN nucleus
E30: rank 6 | nucleus n=4  | gold NOT in nucleus
X34: rank 2 | nucleus n=10 | gold IN nucleus
X37: rank 9 | nucleus n=7  | gold NOT in nucleus
X38: rank 9 | nucleus n=6  | gold NOT in nucleus
```

**A finding beyond what "23 survived" suggests: 9 of these 23 (B11, B12, B7,
C15, D22, D23, E30, X37, X38) have their gold document present in the
top-15 grading window — enough to count as a `hit@10`-style success — but
NOT inside the actual nucleus (top-p cutoff) selection that would reach a
composer.** The nucleus size for each of these queries (5–9 chunks) is
simply too small to reach where the gold document sits in the ranking
(ranks 5–11).

**Combining this with the 11 fully displaced queries: 20 of 34 in-scope
queries (59%) would not have their gold document available to a composer
under the widened universe — a substantially more sobering number than the
top-15-based "23/34 survived" framing on its own would suggest.** This does
not mean 59% of answers would be wrong (Part A's content judgement shows most
displaced-query replacements are still good answers), but it does mean the
top-15 recall metric alone materially overstates how often the *specific
gold document* would actually reach an answer-generation step.

### Recommendation on the universe

**Content-wise, the full-corpus universe holds up reasonably well** — a
majority (7/11) of fully-displaced queries get an equal-or-better answer from
elsewhere in the corpus, and the mechanism is well-understood (a hand-curated
95-doc gold set structurally cannot credit a wider corpus's equally-good
alternatives). **But the nucleus-window finding is a real, separate concern**:
even where the gold document is technically retrievable, it frequently
doesn't survive into the actual composer-bound selection at this scale.
**Recommendation: the full-corpus universe is not disqualified by content
quality, but before adopting it as the default, the real question to answer
is answer quality via a composer run against a full-corpus-aware gold set
(or at minimum, a broader nucleus-window sanity check) — not further
retrieval-only analysis.** This is stated as a recommendation; the decision
is not made here.

---

## PART B — the date index, tested where the decision lives

### 5. `run_ops2_c3.py C4_dateindex_on` — could not complete, for a reason in the same family as the original C3 blocker

```
set CJ_DATE_INDEX_ENABLED=1
python scripts/run_ops2_c3.py C4_dateindex_on

[live-vs-replay] 39/40 exact — MISMATCH ['E25']
STOP: live path diverges from replay; grading would be unsound.
EXIT=2
```

**Confirmed nothing was written**: `ops2_c1_drift.json` still holds exactly
`anchor, v4_expect, C0_current_artifacts, C1_post_ops2, C2_post_batch03,
C3_full_corpus_universe` — no `C4_dateindex_on` key.

**Confirmed reverted after**: a fresh process with no override reads
`config.DATE_INDEX_ENABLED = False`.

**Root cause, traced rather than assumed**: `retrieval.run()`'s live path
includes a `[W2.4]` temporal-intent filter/reorder step (`_date_select()`)
that fires only when `config.DATE_INDEX_ENABLED` and the query carries
detected temporal intent. `run_ops2_c3.py`'s replay logic re-implements
scoring but does not model this post-nucleus step — the two were only ever
guaranteed to agree while the flag defaulted off (dark). Confirmed
`retrieval.temporal_intent()` detects intent for exactly one of the 40
frozen queries: **E25** (`{'type': 'year', 'years': [2016]}`) — the query
that diverged. **A `run_ops2_c4.py` analog to `run_ops2_c3.py` would be
needed to measure this cleanly; not created, per the boundary against
editing `.py` files.**

**A full recall delta against C3 cannot be produced through the sanctioned
harness. Not substituted with a private re-implementation of the grading
logic** — that would reintroduce exactly the kind of unaudited measurement
this project has been careful to avoid at every prior step.

### 6. What can be reported directly: a concrete regression on the one eligible query

Since only 1 of 40 frozen queries is even eligible to be affected by this
flag, its actual effect was observed directly through the real
`retrieval.run()` production path (not a re-implementation) for that single
query:

```
E25: "What was the significance of the 2016 South China Sea arbitral award?"
Gold: CA010, CA009

Flag OFF — selected docs: CA335, CA313, CA010, CA014, CA009, CA082, CA314
  (both gold documents present)

Flag ON  — selected docs: CA335, CA339, CA341, CA340, CA343, CA338
  (NEITHER gold document present — both dropped entirely)
```

**Traced why**: the gold documents are *retrospective* columns —
`CA010` dated 2019-08-04, `CA009` dated 2021-06-13 — discussing the
significance of a 2016 ruling years after the fact. The date filter's
literal year-match logic restricts candidates to documents *dated* 2016
(confirmed: `CA335`, `CA338`–`CA343` are all dated 2016-06 through
2016-09), which are plausibly contemporaneous news/commentary but are not
the documents the gold set credits. **This is a genuine, evidenced
regression on the one frozen-40 query the flag can touch — not a wash.**

**Combined verdict**: the CE-11 test (Phase 6) showed the flag helping one
row (X51) with zero collateral damage across CE-11's 14 rows. This phase
shows the flag directly breaking one frozen-40 query (E25) that was
previously fully correct. **This is a trade, exactly as anticipated, not a
free win. Recommendation: leave `DATE_INDEX_ENABLED` at its default (False)**
until the underlying year-match logic is revised to also credit documents
that discuss a dated event retrospectively, not only documents published in
the named year. Not changed here — `config.py` was not edited, and the flag
is confirmed off.

---

## PART C — sizing the X49 fix

### 7. Four measurements

**a. Chunks containing each citation form, corpus-wide:**

```
"GR No." (no periods):    41 chunks
"G.R. No." (with periods): 54 chunks
```

**b. Distinct documents using each form:**

```
"GR No." only:    12 distinct documents  (prefixes: BA×5, SA×2, CE×1, BB×1, BD×1, +others)
"G.R. No." only:   8 distinct documents  (prefixes: BA×3, CA×1, BD×1, GC×1, +others)
Documents using BOTH forms: 2
```

No single book or format cleanly owns one spelling — book-chapter documents
(`BA`/`BB`/`BD` prefixes) appear on both sides of the split, and even 2
documents mix both forms internally. The most that can be said cleanly: `BA`
(book chapters, mostly footnote-derived citations) is the single largest
contributor to the no-period "GR" form, consistent with footnote-style
abbreviation, but it is not exclusive to that form.

**c. Phrase-dictionary entries using each form:**

```
Bare "gr" token entries: 2
"g.r." token entries:    8
```

The dictionary itself mirrors the corpus's own skew — it is not internally
inconsistent, just built from an already-inconsistent source.

**d. Query-side blast radius, checked against both current test sets:**

```
Frozen 40:  0 queries contain a G.R./GR-style citation in either form.
CE-11 14:   1 query (X49) contains one, in the "G.R." (with periods) form.
```

**This sizes the fix's current, measurable value precisely: zero impact on
the frozen 40 (no query there is even eligible to trigger this path), and
exactly one CE-11 row.** The underlying corpus-side inconsistency (95 chunks
across 18 documents, split roughly 43/57 between the two spellings) is real
and could matter for future citation-style queries not yet in either test
set, but today's evidence bounds its proven value to one row.

### 8. What the fix would be, and its cost

**The fix**: a normalization step in `app/sparse.py`'s shared tokenizer so
that citation-marker variants — `"g.r."`, `"gr"`, `"g.r"`, `"gr."` — fold to
one canonical token before BM25 indexing and before query tokenization.
Confirmed via direct testing that the tokenizer currently treats these as
distinct strings (`tokenize("GR No. 142840")` → `['gr', ...]` vs
`tokenize("G.R. No. 142840")` → `['g.r.', ...]`), so this is a targeted,
well-scoped change, not a rewrite.

**What it would require re-running**: `build_sparse_index.py` would need a
full rebuild (the BM25 index and the phrase dictionary are both derived from
the current tokenization, corpus-wide, not just the 18 affected documents),
and — per this whole project's own precedent (every prior index change has
required a fresh, separately-labelled comparator run before being trusted —
CE-6 through C3) — a fresh C-label comparison against the frozen 40 and a
fresh CE-11 diagnostic run would be needed to confirm the change doesn't
regress anything elsewhere in the BM25 ranking (a token-normalization change
touches every chunk's term-frequency vector, not just the 18 documents with
G.R. citations). **Not implemented here — sizing was the deliverable.**

---

## What remains unanswerable without a full-corpus gold set or a composer run

1. **Whether the full-corpus universe's 7 better-or-equal / 4 genuine-loss
   split, and the 9 nucleus-lost queries, actually produce worse *answers* —
   not just different retrieved documents — requires a composer run.**
   Retrieval-only judgement (this report) can assess whether a *document*
   plausibly answers a question; it cannot confirm what a composed answer
   built from it would actually say, especially for the 9 nucleus-lost
   queries where the gold document exists but wouldn't be sent forward.
2. **Whether a broader gold set, authored with the full 1,104-document corpus
   in view, would credit many of the "genuine loss" cases (B8, C14, C18,
   D24) as acceptable** — right now there is no such gold set, so every
   full-corpus recall number is measured against a set that structurally
   cannot credit anything outside the original 95 documents. This is a
   real, not a rhetorical, gap: building or extending a gold set for the
   full corpus is its own project, not a $0 read of existing artifacts.
3. **Whether the date-index year-match logic, if revised to credit
   retrospective discussion of a dated event (not just documents published
   in that year), would recover E25 without introducing a different
   regression** — this is a design change, not something answerable by
   reading current artifacts; it would need its own implementation and its
   own C-label test.
4. **Whether the X49 tokenizer-normalization fix, once implemented, changes
   anything for the 43 pilot-scope or wider-corpus queries not in either
   current test set** — bounded above at "0 frozen-40 impact, 1 CE-11 row"
   only because those are the only queries currently measured; unproven for
   any future query phrased with either citation style.

## Files touched this session

```
eval/results/ops2_c1_drift.json   — unchanged content-wise (C4 write never happened;
                                     confirmed still holds exactly anchor/v4_expect/C0/C1/C2/C3)
docs/p3/phase7_universe_adjudication_2026-09-26.md   — this report
```

No `.py` file, `config.py`, gold CSV, frozen query JSON, CE-11 file, or any
C0–C3 record was modified. The runtime index was left exactly as Phase 5/6
left it (full corpus, 1,104 / 9,804) — not reverted.

## FLAG list — status

| Flag condition | Fired? |
|---|---|
| Displaced-query list differing from the given one | No — identical, independently derived |
| Date index degrading the frozen 40 | **Yes — reported in full above (E25).** A real, evidenced regression, not a hypothesis |
| Any urge to edit `config.py`, `app/sparse.py`, the phrase dictionary, or any gold file | No — none touched |
| Any step that would spend tokens | No — $0 throughout |
