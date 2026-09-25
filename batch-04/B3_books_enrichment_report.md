# B3 / CE-1b — enrichment of the batch-04 book chapters

**Run date** 24 September 2026 · **Output** `batch-04/books_enriched.xlsx` (sheet `cjp_books_curated`)
**Runbook** CJAP_Robot_Project_Plan_v2.xlsx → Corpus Expansion CE-1b; prompt B3 in `BATCH-04_BOOKS_PROMPTS.md`

## Result

**168 of 168 book chapters enriched. 0 errors.**

| | |
|---|---|
| Rows written | 168 (one per `material_type = book chapter` row in `intake_manifest.csv`) |
| Header | the 15 fields, in the pinned schema order |
| Date cells | all text, all `YYYY-MM-DD`, all equal to the manifest |
| JSON cells | 1,680 list/object cells — every one parses |
| Signature phrases | 1,421 phrases, **100% found verbatim** in their own `data_text/<ID>.md` |
| Article Codes | 168 unique; every one has a `.md`; none reused, none retired |
| `confidence` values | all four are from the allowed set (asserted 391 · asserted with evidence 299 · reported, not his view 49 · hedged 28) |

### By book

| Book | Chapters | ID range | Source words | Manifest date |
|---|---:|---|---:|---|
| A Centenary of Justice | 1 | BA108 | 2,867 | 2001-12-01 |
| Battles in the Supreme Court | 11 | BA053–BD030 | 48,746 | 1998-11-01 |
| Leadership by Example: The Davide Standard | 14 | BA059–BD034 | 52,405 | 1999-10-01 |
| Transparency, Unanimity & Diversity | 24 | BA066–BD037 | 93,260 | 2000-11-01 |
| Reforming the Judiciary | 20 | BA077–BD045 | 71,677 | 2002-12-01 |
| Leveling the Playing Field | 20 | BA084–BE034 | 73,891 | 2004-12-01 |
| Judicial Renaissance | 21 | BA093–BD058 | 80,019 | 2005-11-01 |
| Liberty and Prosperity | 35 | BA097–BD071 | 84,945 | 2006-07-01 |
| Love God, Serve Man | 22 | BA051–BE030 | 45,314 | 1990-07-12 |
| **Total** | **168** | | **553,124** | |

### Field sizes actually produced

| Field | min | median | max | reference rows (BA001 · BD010 …) |
|---|---:|---:|---:|---:|
| Keyword/s | 19 | 30 | 54 | 20 |
| primary_topics | 3 | 4 | 6 | 4 |
| sub_topics | 6 | 16 | 32 | 8–10 |
| signature_phrases | 5 | 8 | 15 | 5–6 |
| stances | 3 | 4 | 8 | 2–3 |
| notable_anecdotes | 0 | 5 | 8 | 4 |
| target_audience | 3 | 3 | 4 | 3 |
| register_markers | 5 | 6 | 8 | 5 |
| decision_framework_signals | 4 | 7 | 12 | 3–5 |
| one_paragraph_summary | 286 w | 348 w | 449 w | ~300 w |

The rows sit above the reference medians because the reference rows are *With Due Respect* chapters —
reprinted newspaper columns of roughly 1,000 words — while these are full book chapters with a median of
2,729 words (69 of them over 3,000, 21 over 6,000). B3 instructs scaling up so the whole chapter is
represented. **Judgement call for the team:** if you would rather these matched the existing rows
field-for-field, say so and the counts can be trimmed; nothing else changes.

---

## Flags — reported, not fixed

### 1. OCR corruption in the source `.md` files — NEW DEFECT (proposed **D-14** — D-11 is already the BA031 colophon)

The single most common finding. The book sources were scanned, and the damage survived B0/B2 into
`data_text/`. A machine sweep finds a detectable artefact in **57 of the 168 files**; reading found more,
because the commonest form — a clause silently dropped mid-sentence — leaves no signature.

Three kinds, with examples taken from the files:

- **Dropped clauses.** BD060 opens *"Upon assuming the chief justiceship of the immediately vowed to lead
  a judiciary…"*; BA091's constitutionality section starts mid-thought; BC028 jumps from *"I learned all
  too early"* straight to *"ticket. I was embittered."*; BD048 has a truncated *"no continuance or
  adjournment po[licy]"*.
- **Garbled words and numbers.** *"lis moa"* for *lis mota*; *"Marvos v. Manglapus"*; *"Tajsiada v.
  Angara"*; BA078's *"a unanimous vote of all its 51 members"* (15); BD044's *"more than 05 centenary
  activities"* (50); BE032 dating the dismantling of the Soviet Union to *"1089"*.
- **Letter-spacing and stray glyphs.** `w e c o u l d`, `s u b h u m a n`, `coni fidence`,
  `jurispruden tialcontrov ersies`.

No signature phrase in the workbook is drawn from a damaged span — every one was verified verbatim — but
**the corpus text itself will carry these errors into retrieval** unless they are cleaned. Recommendation:
add D-14 to the Data Flow defect list and schedule a clean-up pass over `batch-04/data_text/` **before**
P6 merge, since merging is append-only and these files are the corpus.

### 2. Mixed authorship inside chapters

These are CJP's books, but several chapters reproduce other people's text at length. Treated as
`reported (not his view)` in `stances`, with signature phrases taken only from his own prose:

| ID | What is reproduced |
|---|---|
| **BA080, BB024** | Most of each chapter is an article **by Jovito R. Salonga**, reprinted with permission and bylined in the text |
| **BD038** | About 75% is the Supreme Court's **APJR Executive Summary**, an institutional document |
| BB033, BB034, BB035, BA082, BB022, BA070, BB025, BB026, BA064 | Long verbatim opinions of other justices (Carpio, Tinga, Puno, Mendoza, Romero, Vitug and others) |
| BC023, BC024, BC025, BA051, BA052, BB010, BB011 | Open with an **editor's note by Isagani Yambot** |
| BC023 | Reproduces the Prayer of St Francis in full |
| BA096 | Closes with a poem, *"A.V.P."*, by Atty. Noel Mapili |
| BD046 | A compiled Q&A; the answers came from a panel (Quisumbing, Carpio, Azcuna and court administrators), not from CJP alone |

**BA080 and BB024 are the two that matter for the robot's voice.** They are registered as CJP book
chapters but read mostly as Salonga's writing. Worth a decision before merge: keep with a flag, or hold
back as the two `by-another-author` chapters already were.

### 3. Truncated or scrambled sources

- **BA083** (Reforming the Judiciary Ch. 22) — confirmed truncated: the file ends after numbered
  pronouncement 9 with no close, and an earlier block quotation is never terminated. Enriched from the
  6,201 words present, flagged, nothing inferred. **Decision still open: hold back until the rest of the
  chapter is supplied, or merge as-is with the flag.**
- **BC027** — page-scrambled rather than truncated: the closing block sits at lines 73–75, *before*
  material that belongs earlier. The row reconstructs the intended order; the `.md` should be re-ordered.
- **BB029**, **BA070** — one sentence each breaks off mid-word.
- **BD062** announces "five key areas" and lists four; **BD027** skips item 7; **BA078** is missing a
  heading number.

### 4. Dates inside the text that post-date the manifest date

The manifest date for a book chapter is the book's publication date, so a speech delivered before it is
normal. These run the other way and are worth a look:

| ID | What the text says | Manifest |
|---|---|---|
| **BD064** | the APJR was hailed at a conference of **28–30 November 2006**, past tense | 2006-07-01 |
| BD052, BD053 | Davide's 13 Dec 2005 lecture and 20 Dec 2005 retirement described as still to come; a ceremony "next week, on December 15" | 2005-11-01 |
| BC044, BC045, BD059 | oath taken "21 December 2005", a conference of Nov 2005 called "two months ago", a retirement party dated "December 19, 2006" | 2006-07-01 |
| BB011 | dated 28 Feb 1988 but reports full-year 1988 figures and 1989–91 targets | 1988-02-28 |

None was changed. If the team wants delivery dates rather than publication dates for the speech-derived
chapters, that is a manifest correction, not a B3 one.

### 5. Thin chapters — scaled down, not padded

BC044 (418 w), BD032 (566 w), BB010 (639 w), BC033 (715 w), BC035 (712 w), BC032 (404 w), BD047 (837 w),
BE033 (890 w), BC037 (918 w), BD030 (977 w), BA103 (984 w), BE030 (988 w), BD040 (993 w).
**BD040** is the only row with an empty `notable_anecdotes` — it is a ten-point exposition containing no
scene, story or recollection anywhere.

### 6. Internal contradictions left as written

BA094 (a dropped negation reverses his stated position), BA096 (his HRET start date conflicts with the
chapter's own opening), BA092 (a statistics table that does not add up), BB020 (ratification "two days
later" on an earlier date), BB040 (RA 7042 vs RA 7942), BB026 (Eusebia vs Eugenia Galzote),
BD063 (APJR used for two different bodies in the same chapter).

---

## What happens next

1. **B4 QA** — independent re-check of every row against its `.md` plus the signed 10-row spot check
   (`qa_books.md`, `spot_check_books.xlsx`).
2. **D-14 clean-up** of `batch-04/data_text/` — recommended before merge, since the merge is append-only.
3. **P5** — run `scripts/normalise_curated.py` on `books_enriched.xlsx`
   (it already produced `columns_enriched_normalized.xlsx` cleanly: 18 rows, 0 cells changed).
4. **P6 onwards** stays blocked until correction batch-03 is promoted.

Open decisions carried forward: BA083 (truncated), BA080/BB024 (Salonga authorship), the 21 chapters over
6,000 words kept whole, and the field-size judgement above.
