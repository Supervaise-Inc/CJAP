# Format consistency audit — all four pinned sheets plus batch-04

**Question asked:** does the 131-row date normalisation cover the old columns too, and is every
normalisation in the same format?

**Short answer: no, and no.** The 131 rows touch books and biography only. The old columns are not in it —
but they are not clean either: all 785 of them store the date as an Excel datetime rather than the text
`YYYY-MM-DD` the schema calls for. So do all 154 speeches. Three structural divergences between the sheets
have never been logged at all.

---

## 1. What the 131 rows actually cover

`batch-03/date_normalisation.csv` — 131 rows, all of them books and biography:

| | Rows |
|---|---:|
| Book chapters with an unreadable date (`9/30/2007`, `2003.0`) | 78 |
| A Centenary of Justice chapters carrying the ingestion date `2026-01-12` (defect D-2) | 22 |
| Biography chapters with free text or a bare year (`Childhood,`, `1955-1959`) | 31 |
| **Columns** | **0** |
| **Speeches** | **0** |

## 2. How each sheet actually stores its dates

| Sheet | Live rows | datetime | text `YYYY-MM-DD` | other text | number |
|---|---:|---:|---:|---:|---:|
| `cjp_columns_curated_normalized` | 785 | **785** | 0 | 0 | 0 |
| `cjp_books_curated` | 135 | 57 | 0 | 58 | 20 |
| `cjp_speeches_curated` | 154 | **154** | 0 | 0 | 0 |
| `cjp_biography_curated` | 35 | 4 | 0 | 27 | 4 |
| `batch-04/columns_enriched_normalized` | 18 | 0 | **18** | 0 | 0 |
| `batch-04/books_enriched_normalized` | 168 | 0 | **168** | 0 | 0 |

**Not one of the 1,109 existing rows stores its date the way the schema specifies.** The new batch-04 rows
are the only ones that do — which means that once batch-04 merges, the pinned sheets will hold two
different date representations side by side.

### Why nothing has broken

`scripts/generate_corpus_from_xlsx.py` line 255 writes `str(date)[:10]`. For a datetime that yields
`2025-03-24 00:00:00`[:10] → `2025-03-24`, the right answer by luck. The 105 text-and-number values are the
ones where the trick fails and the corpus shows `2003.0` or `Childhood,` — which is D-7.

So the 785 columns and 154 speeches are **not** a live defect. They are an inconsistency that has been
silently absorbed, and it will become a live defect the first time anything reads the Date column without
stringifying it first.

## 3. Three structural divergences, previously unlogged

- **The biography sheet has 14 columns, not 15 — there is no `Link`.** The schema is described everywhere
  as "the 15 fields". For biography it has never been 15. The G3 prompt asks for a `Link` column that the
  pinned sheet has no home for.
- **The speeches sheet has 26 header cells** — the 15 real ones followed by 11 empty cells. Any strict
  header-equality check fails on it, which is why P5 reads the order from each pinned sheet rather than
  comparing to a constant.
- **Sheet names disagree**: `cjp_columns_curated_normalized` against `cjp_books_curated`,
  `cjp_speeches_curated`, `cjp_biography_curated`.

Also cosmetic: the books and speeches workbooks carry 864 and 845 trailing blank rows in their dimension
records, which is why a naive row count reports 999 for each.

## 4. Punctuation — the convention genuinely differs by sheet

| Sheet | curly quotes | em/en dashes | straight quotes | hyphens | mojibake |
|---|---:|---:|---:|---:|---:|
| columns pinned | 0 | **0** | 264,957 | 111,256 | 0 |
| books pinned | 0 | **52** | 40,995 | 14,448 | 0 |
| speeches pinned | 0 | **0** | 40,603 | 15,660 | 0 |
| biography pinned | 0 | **0** | 13,969 | 11,119 | 0 |
| batch-04 columns | 0 | 0 | 5,479 | 766 | 0 |
| batch-04 books | 0 | **12** | 57,029 | 13,703 | 0 |

Because `normalise_curated.py` measures the convention from each pinned sheet at run time, it folds em
dashes to hyphens for columns, speeches and biography — and **preserves them for books**, because the
books sheet already had 52. That is the script faithfully reproducing an accident. Three sheets out of
four say hyphen.

Quotes and mojibake are consistent everywhere: zero curly, zero mojibake, zero non-breaking spaces. That
part is clean.

## 5. JSON payloads — consistent

Every JSON cell in all 1,109 live rows and all 186 new rows parses. `entities` is an object everywhere,
`stances` a list of objects everywhere, every list field a list of strings. No divergence.

## 6. What I have prepared

`batch-03/date_normalisation_v2.csv` — **1,109 rows, the whole corpus**, replacing the 131-row file:

| Change | Rows | Needs a decision? |
|---|---:|---|
| datetime → text, value unchanged | **978** | No — mechanical and lossless |
| The existing 131-row proposal (D-2 and D-7) | **131** | Yes — already awaiting your sign-off |

Each row carries `stored_as`, `current_value`, `target_text`, `precision`, and whether the change is
"type only" or "value + type".

**The 978 are free.** Because the generator already stringifies and truncates, converting them changes no
corpus file, no chunk and no index — nothing needs re-embedding. They can ride along with batch-03 at no
extra risk.

I have **not** applied anything to the pinned sheets. CE-17 says a correction runs as its own batch, and
batch-03 is that batch and has not been promoted.

## 7. Recommended, in order

1. **Fold the 978 into batch-03** as correction C-9. No corpus change, no re-index, closes the storage
   inconsistency for good.
2. **Sign off the 131** — that is still the gate on batch-03 and therefore on P6.
3. **Pick one punctuation convention corpus-wide.** Three of four sheets already say hyphen; the books
   sheet's 52 dashes are the outlier. Fold them, and stop measuring per sheet.
4. **Replace the per-sheet measurement with one shared folding function** imported by C1, B3, S1, G3 and
   P5. This is the same defect that let CA538 store `--` where the column prints em dashes: two checks
   disagreed because each had its own rule.
5. **Decide the biography `Link` question** — add the column to the pinned sheet, or amend the schema and
   the G3 prompt to say biography is 14 fields. Right now the documentation and the data disagree.
6. **Tidy the speeches header** (drop the 11 empty cells) and align the four sheet names.

Items 3–6 are cheap, but they are changes to pinned sheets, so they belong in a correction batch too —
not mixed into batch-04.
