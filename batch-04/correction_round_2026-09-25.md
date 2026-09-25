# Correction round — books and columns, 25 September 2026

Two decisions were taken and applied: **names follow the text**, and **D-14 gets the repairs that can be
proved, with the rest logged for re-scan**. Everything below is done; the state at the end is verified.

## 1. The naming rule, applied corpus-wide

A row may name a person only as its own document names them.

The B4 readers had flagged 11 errors and 37 warnings of this kind. Rather than work from that sample, a
script checked **every token of every person's name in all 186 rows** against its own source.

| | Books | Columns |
|---|---:|---:|
| `entities.people` entries | 1,226 | 128 |
| Rows carrying a name the text does not give | **54** | **0** |
| Name tokens not in their own source | **134** | **0** |

So the sample had found about a quarter of it. The columns needed nothing — confirming the readers'
verdict by a different method.

**Applied:** 55 book rows changed, **102 field-cells** in all — `entities` 54 · `Keyword/s` 17 ·
`sub_topics` 12 · `one_paragraph_summary` 9 · `notable_anecdotes` 5 · `primary_topics` 3 ·
`target_audience` 2. Where a name was struck, it was struck everywhere in the row, not only from
`entities.people`.

Typical: `Reynato S. Puno` → `Justice Puno` · `Andres R. Narvasa` → `Chief Justice Narvasa` ·
`Hilario G. Davide Jr.` → `CJ Davide Jr.` where that is the form the chapter prints. Where the document
names nobody, the row now says what the document says: BA098 carries `the President (issued EO 464 on
September 28, 2005)`, BD039 `our Chief Justice (recipient of the 2002 Ramon Magsaysay Award…)`, and
BE033 no longer names Dr. Franklin M. Zweig at all.

`Date`, `Title`, `Article Code`, `Link` and all 1,421 signature phrases were untouched.

### One consequence worth knowing

Following the text means the rows now carry the source's spelling, and in five places the source is
OCR-damaged: `Oliver Wendeel Holmes Jr.` (BB025) · `SandovalGutierrez` (BA089) · `John Osmeiia` (BC031) ·
`Didag Piang Dilangalen` (BA086) · `Wood`, printed `[GovernorGeneral] Wood` (BA079). These were **not**
silently corrected — repairing a name by inference is the very habit the rule exists to stop. They are in
the re-scan list below, and source and row should be corrected together when a clean scan exists.

## 2. The six non-name errors

| doc_id | Was | Now |
|---|---|---|
| **BD062** | "thirteen" sponsoring organisations; anecdote dated a decade before he joined the Court | twelve, named; "a decade before this address, when he was still in private practice" |
| **BA070** | Estrada declared the moratorium on 25 March 2000 | the news dailies reported on 25 March that he had declared it the previous day |
| **BA079** | "the May 14, 2001 Philippine elections" | "the Supreme Court's decision in SWS v. Comelec the year before this address" |
| **BA080** | "jueteng protection money" | "illegal-gambling protection money", as the Amended Information is quoted |
| **BA064** | Romero's "rejected draft became a seventeen-page dissent" | the raffle for study and the 17-page dissent, with no rejected draft |
| **BC025** | Citibank among the Eyebank donors | "the local peso donors listed on Page 32 of the Balita" |
| **BB028** | "Robert Jaworski", "Francisco Chavez" as petitioners | dropped; the case captions remain in `entities.cases` |

## 3. The columns

One cell. `CA538` stored `fallible--if not scheming--individuals`; the column prints em dashes. Corrected
to the printed form, which P5 then folds to the sheet's convention.

The underlying problem is worth fixing properly: **C1, B3 and P5 each carry their own idea of how dashes
and quotes fold**, which is why C2 passed this phrase and the books check failed it. One shared folding
function, imported by all three, would close it.

## 4. D-14 — what could be repaired, and what could not

First, the finding that settles the scope: **the damage is in the original `.docx` files, not introduced
by our split.** `Liberty and Prosperity.docx` itself reads *"Upon assuming the chief justiceship of the
immediately vowed to lead a judiciary…"*. Nothing in this pipeline can recover words that were never
scanned.

### Repaired — 20 spans in 14 chapters

Only classes that a vocabulary built from the corpus itself could confirm:

- **15 letter-spacing runs** — `s u b h u m a n` → `subhuman`, `w i t h o u t` → `without`,
  `w o m e n` → `women`, and so on. Joined only when the result is a word the corpus already uses.
- **5 words split by a space** — `Wor ld` → `World` · `Commis sion` → `Commission` ·
  `Carm elo` → `Carmelo` · `Cor poration` → `Corporation` · `w e c o u l d` → `we could`.

The dry run caught one thing worth recording: the first pass proposed 324 "repairs", 309 of which were
`x x x` → `xxx`. That is the Philippine legal ellipsis for omitted text, not damage. The rule now skips
any run of a single repeated letter. Backups of all 14 files are in
`batch-04/backup_pre-d14_2026-09-25/`, and **all 1,421 book and 252 column signature phrases were
re-verified verbatim after the edits**.

### Not repaired — logged

- **13 residual artefacts** the vocabulary could not resolve: `It|he`, `a{cc`, `Ta}ny`, `r e d t h e m`,
  `o f P`. Listed in `batch-04/d14_scan.json`. (`F x L` and `S × P` in CA538 are formula notation, left
  alone.)
- **Dropped text — the real problem.** A higher-precision detector (paragraph ends mid-sentence, next
  paragraph is not a list or heading) flags **420 spans across 96 of the 168 chapters**, in
  `batch-04/d14_rescan_list.json`. Treat it as a ranked triage list, not a defect count: tables and name
  rosters inflate it, and the worst offenders are the chapters that contain long enumerations. The head
  of the list is BD028 (28), BA059, BA063, BA070, BB022, BD036 (14–15 each).
- **The five OCR-damaged proper names** from §1.
- **BA083** remains truncated; **BC027** remains page-scrambled. Both need the source, not a script.

**Recommendation unchanged:** these chapters become the corpus at P6, and P6 is append-only. A clean
re-scan of the worst-affected books is the fix; the priority order is in
`batch-04/book_split/SOURCE_GAPS.md`, now to be extended with the list above.

## 5. State after this round

Both workbooks re-normalised with `scripts/normalise_curated.py` and re-checked.

| Check | Books | Columns |
|---|---|---|
| Rows | 168 | 18 |
| Header, IDs, dates, titles, JSON, list shapes, entity keys, stance shapes, confidence values | PASS | PASS |
| Signature phrases verbatim | **1,421 / 1,421** | **252 / 252** |
| Person names present in their own source | **PASS** | **PASS** |
| Normalised vs un-normalised: content identical apart from punctuation | **PASS** | **PASS** |
| P5 idempotent | PASS | PASS |
| **Errors outstanding** | **0** | **0** |

Files: `books_enriched.xlsx` · `books_enriched_normalized.xlsx` · `columns_enriched.xlsx` ·
`columns_enriched_normalized.xlsx` · `p5_normalise_books_report_2026-09-25.md` ·
`p5_normalise_columns_report_2026-09-25.md` · `d14_scan.json` · `d14_rescan_list.json` ·
backups in `backup_pre-fix_2026-09-25/` and `backup_pre-d14_2026-09-25/`.

## 6. What is left before P6

1. **The signed spot checks** — `spot_check_books.xlsx` (10 rows, seed 4) and `spot_check_columns.xlsx`
   from the 23 Sep run. Both still unsigned; this is now the only thing inside batch-04 that needs a
   person.
2. **Write the naming rule into the prompts** — B3, C1, S1 and G3 — so the next batch does not
   re-litigate it. Same for the shared folding function.
3. **Correction batch-03 must be promoted.** P6 is gated on it, and that gate has not moved.
4. **The standing judgement calls**, unchanged: BA083 (truncated), BA080 and BB024 (mostly Salonga's
   writing), the 21 chapters over 6,000 words kept whole, and whether the richer field sizes should be
   trimmed to match the existing rows.
