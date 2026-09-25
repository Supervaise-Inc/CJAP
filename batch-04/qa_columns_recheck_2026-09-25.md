# Columns — re-check against the B4 standard, 25 September 2026

An addendum to `qa_columns.md` (the C2 run of 23 Sep), not a replacement. The books B4 run surfaced a failure mode C2 was not looking for — **a name the text never gives, supplied from general knowledge** — so the same two passes were re-run over the 18 column rows: the mechanical script used on the books, and a fresh read of every column against its row.


**Subject:** `batch-04/columns_enriched_normalized.xlsx` · **Evidence:** `batch-04/data_text/<ID>.md`


## Verdict

**The columns hold up. 18 of 18 rows clear the semantic check with 0 errors (4 warnings). One mechanical failure, in one cell.**


The failure mode that cost the books 13 rows is **absent here**. Every person in all 18 rows is named in the column itself, and the three places where the temptation was strongest are clean: CA530 and CA531 refer only to "the President" and the rows do not name him; CA533 refers to "the Vice President" and the row leaves it unnamed. (CA535 names Sara Duterte — so does its column.) 128 `entities.people` entries checked, 0 supplied from outside.


## 1. Mechanical checks

| Check | Result |
|---|---|
| Header is the 15 fields in pinned order | PASS |
| Row count == manifest column rows (18) | PASS |
| Article Codes unique, regex-valid, none retired, all in the manifest | PASS |
| Every Article Code has a `data_text/<ID>.md` | PASS |
| Every Date is text `YYYY-MM-DD` and equals the manifest | PASS |
| Every Title equals the manifest | PASS |
| Every JSON cell parses (180 cells) | PASS |
| List fields, `entities` keys, `stances` shape, `confidence` values | PASS |
| `one_paragraph_summary` is a single paragraph (mean 293 words) | PASS |
| Every `entities.people` name present in the text (128 entries) | PASS |
| Normalised vs un-normalised: content identical apart from punctuation | PASS |
| **252 signature phrases verbatim** | **FAIL (251/252)** |

### The one failure — CA538

`signature_phrases` holds:

```
justice is administered by fallible human institutions and by fallible--if not scheming--individuals
```

The column has **em dashes**, not double hyphens:

```
...by fallible—if not scheming—individuals.
```

C2 passed this because its comparison treated `—` and `--` as equivalent. The books check folds an em dash to a **single** hyphen, matching what P5 measured in the pinned sheets, so `--` matches neither the source nor the sheet convention. **Fix:** write the phrase with the em dashes as printed and let P5 fold it (the columns sheet carries no em dashes, so it will become `fallible-if not scheming-individuals`). One cell.


Worth noting for the pipeline, not just this row: the two verbatim checks disagreed. The folding rule should live in one place that C1, B3 and P5 all use, or this recurs quietly.


## 2. Semantic check — 0 errors, 4 warnings

| doc_id | field | offending text | why |
|---|---|---|---|
| CA536 | `notable_anecdotes` | The precise age rule: a child is 15 at midnight of the birth date and over 15 after the next midnight. | The column states this only as a general rule of age computation ('children are deemed to be 15 years of age at midnight of their birth date'), not as an incident or episode that h |
| CA540 | `sub_topics` | Literal reading of Article XI, Section 3(6) | The column quotes the clause 'No person shall be convicted without the concurrence of two-thirds of all the Members of the Senate' but never identifies it as Article XI, Section 3( |
| CA541 | `stances` | The 2025 Extradition Rules codified what Purganan held: ex parte issuance of arrest warrants, bail as discretion rather  | The column ties only the ex parte warrant and the discretionary-bail points back to Purganan; the termination of appeals at the Court of Appeals is presented as a new feature, 'in  |
| CD030 | `one_paragraph_summary` | the BSP's 125th-anniversary banknote and coin | The column says the capsule held "the BSP banknote and coin commemorating the Court's 125th anniversary" -- the 125th anniversary is the Supreme Court's, not the BSP's (the same ro |

None blocks a row. `CD030` is the one worth a glance: the summary and `primary_topics` phrase it as "the BSP's 125th-anniversary banknote", where the column has the BSP issuing a banknote for the **Supreme Court's** 125th. The row's anecdote and events fields state it correctly.


## 3. Why the columns did better than the books

Not luck, and worth keeping in mind for the next batch:

- A column is ~900 words on one subject, read whole in one pass. A book chapter averages 2,729 words and often reproduces other people's opinions at length — far more room to blur who said what.

- The columns were pasted from the live Inquirer pages, so the text is clean. The book sources are OCR, with clauses missing (**D-14**) — and a gap in the text is exactly where a reader reaches for outside knowledge to fill in.

- C1 wrote each column's `.md` and its row in one step from the same paste. B3 enriched from a `.md` produced two steps earlier, with the chapter's neighbours in view — which is how BC025 picked up Citibank from BC024.


## 4. What the columns still need

1. The CA538 phrase corrected, then P5 re-run for the columns.

2. The signed 10-row spot check from the 23 Sep C2 run (`spot_check_columns.xlsx`) — still outstanding.

3. The same corpus-wide decision the books raise on name expansion, so C1 and B3 agree.


`CA529` is not in scope: it was removed from the manifest on 23 Sep once the Inquirer page confirmed "Rule of, or by, law" is by Michael L. Tan, not CJP. The ID stays void.
