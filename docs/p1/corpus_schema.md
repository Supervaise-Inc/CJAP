# P1.3 — Corpus schema

The contract a script can validate, not a habit. Mirrors the Project Plan's **Data Flow** sheet; that
sheet and this file must agree. Written 25 Sep 2026 against what the pipeline actually enforces.

Enforced by: `scripts/normalise_curated.py` (P5/CE-2) · `scripts/generate_corpus_from_xlsx.py` ·
`scripts/verify_pin.py`.

---

## 1. Identifier convention

```
^[CBSG][A-E]\d{3}$
```

| Position | Meaning | Values |
|---|---|---|
| 1 | Format | `C` column · `B` book chapter · `S` speech · `G` biography |
| 2 | Theme | `A` liberty and rule of law · `B` prosperity and economic philosophy · `C` biographical and personal · `D` FLP mission and foundation · `E` current events commentary |
| 3–5 | Number within that format+theme series | zero-padded |

**Rules.** An ID is never reused and never renumbered. A retired ID stays retired
(`data/csv/retired_doc_ids.csv`); a replacement takes a new ID and records `superseded_doc_id`. The number
is a position in a series, **not a count** — `CA529` does not mean 529 columns.

Retired to date: `BA040`, `BC009`, `BC010`, `BD018`, `SA085`. Void: `CA529` (wrong author).

## 2. The source file — `data/text/<ID>.md`

```
# <Title, exactly as the pinned sheet has it>
Date:       <YYYY-MM-DD>
Publisher:  <publisher>
Source:     <URL, or "file: <name>">

<body>
```

- UTF-8. **No YAML front matter. No line that is exactly `---`.**
- The H1 must equal the sheet's `Title` — otherwise the generator does not recognise it and leaks it into
  the body (this was defect D-10).
- Body: paragraphs separated by blank lines; his own sub-headings as `## …`; block quotes as `> …`.
- No backslash escapes or stray `__`/`*` left by document conversion.
- One file per document; the filename is the doc ID.

## 3. The curated row — 15 fields, in this order

Sheet: `data/csv/cjp_<columns|books|speeches|biography>_curated_normalized.xlsx`, first sheet.

| # | Field | Type | Notes |
|---:|---|---|---|
| 1 | `Date` | **text** `YYYY-MM-DD` | Never a datetime, never a number. A real calendar date |
| 2 | `Title` | text | Must equal the source file's H1 |
| 3 | `Article Code` | text | The doc ID; unique; matches the regex above |
| 4 | `Link` | text | May be blank |
| 5 | `Keyword/s` | JSON array of strings | names, cases, laws, key phrases; multi-word kept whole |
| 6 | `primary_topics` | JSON array of strings | full sentences: what the document is centrally about |
| 7 | `sub_topics` | JSON array of strings | supporting points, in the order made |
| 8 | `signature_phrases` | JSON array of strings | **verbatim** from the source file, 3–20 words |
| 9 | `entities` | JSON object | keys ⊆ `people`, `institutions`, `places`, `cases`, `laws_treaties`, `events`; each a list of strings |
| 10 | `stances` | JSON array of objects | `{"claim","rhetorical_move","confidence"}` |
| 11 | `notable_anecdotes` | JSON array of strings | first-hand moments; `[]` is valid |
| 12 | `target_audience` | JSON array of strings | |
| 13 | `register_markers` | JSON array of strings | tone, structure, rhetorical habits |
| 14 | `decision_framework_signals` | JSON array of strings | the tests and principles applied |
| 15 | `one_paragraph_summary` | text | one paragraph, no line breaks |

`confidence` is exactly one of: `asserted` · `asserted with evidence` · `hedged` ·
`reported (not his view)`.

### Known deviation
**The biography sheet has 14 columns — it has no `Link`.** Documented here because the data and the
documentation disagreed until 25 Sep. Either add the column or amend this schema; do not leave it
unstated.

## 4. Rules a validator enforces

1. Header is exactly these fields, in this order (14 for biography, pending the decision above).
2. Every `Article Code` matches the regex, is unique in the file, and is not retired.
3. Every `Date` is text `YYYY-MM-DD` and a real date. **Nothing is coerced** — a datetime or a float is
   an error to report, not a value to convert silently.
4. Every JSON field parses, and its shape matches §3.
5. Every `signature_phrase` is found **verbatim** in that document's `.md`, comparing with curly quotes
   and dashes folded.
6. Every claim in a row comes from that document's own text. **A person is named only as that document
   names them** — if the text says "the President", the row says "the President". (Decision D-030.)
7. Mojibake count is zero; a second normalisation pass changes nothing.

## 5. Punctuation

Curly quotes fold to straight. Dash handling is **measured from the pinned sheet at run time**, per type —
and this is a known weakness: the books sheet holds 52 em/en dashes where the other three hold none, so
the same text normalises differently by type.

**To fix:** one shared folding function imported by C1, B3, S1, G3 and P5. Three components currently
carry their own copy, which is how a phrase passed one verbatim check and failed another (CA538).

## 6. What the generator produces

`scripts/generate_corpus_from_xlsx.py` reads the four pinned sheets plus `data/text/<ID>.md` and writes
`corpus/<type>/<theme>/<ID>.md` and `.json`. The `.md` carries generated front matter (`id`, `format`,
`type`, `theme`, `theme_label`, `number`, `title`, `date`, `keywords`, `target_audience`, `word_count`,
`has_body`, `source_xlsx`) followed by the H1 and body. The date is `str(Date)[:10]` — which is why field
1 must be text.

**The three sets must be identical:** active rows in the pinned sheets, files in `data/text/`, documents
in `corpus/`. `verify_pin.py` fails if they are not.
