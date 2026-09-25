# Batch-04 — prompt index and the shared merge steps

Batch-04 has four intake tracks that end in the same merge:

| Track | File | Steps |
|---|---|---|
| **Books** | `BATCH-04_BOOKS_PROMPTS.md` | B0 split → B1 intake → B2 `.md` → B3 enrich → B4 QA |
| **Columns** (pasted from inquirer.net) | `BATCH-04_COLUMNS_PROMPTS.md` | C0 session → C1 paste per column → C2 QA |
| **Speeches** (files or pasted from cjpanganiban.com) | `BATCH-04_SPEECHES_PROMPTS.md` | S0 session → S1 per speech → S2 QA |
| **Biography** (books about him, GC series) | `BATCH-04_BIOGRAPHY_PROMPTS.md` | G0 split → G1 intake → G2 `.md` → G3 enrich → G4 QA |
| **Merge (all tracks)** | this file | P5 normalise → P6 merge + generate + re-pin → P7 index + eval + promote → P8 records |

Run P5 once the tracks you are using have passed their QA (it takes each enriched workbook separately, so it can also run per track).
**P6 onwards only after correction batch-03 is promoted.** Paths are relative to the Final Project Folder.
The runbook is CJAP_Robot_Project_Plan_v2.xlsx → Corpus Expansion; formats are on its Data Flow sheet.

---

## P5 · CE-2 — Normalise and validate  (Claude Code, in the Final Project Folder)

```
CE-2 — write scripts/normalise_curated.py (the W1.2 normaliser is not in either repo — defect D-4)
and run it on batch-04

BOUNDARIES
- Do NOT modify data/csv/*_curated_normalized.xlsx, data/text/, corpus/ or any existing script.
- New file: scripts/normalise_curated.py. Every knob (encodings, schema width, ID regex) from config.py
  — CURATED_SCHEMA_COLUMNS, DOC_ID_REGEX_PADDED, FILE_ENCODING, JSON_ENSURE_ASCII. No new literals.
- Input batch-04/{columns,books,speeches,biography}_enriched.xlsx (whichever exist) → output
  batch-04/<same name>_enriched_normalized.xlsx.
  Never overwrite the input.

STEPS
1. Validate the header: exactly the 15 columns in schema order. STOP on any difference.
2. Per row:
   - Article Code matches DOC_ID_REGEX_PADDED and is not in corpus/ or retired_doc_ids.csv.
   - Date is text YYYY-MM-DD and a real calendar date. Convert NOTHING silently — a datetime,
     float or other string is an error, not something to coerce.
   - Repair cp1252 mojibake (e.g. 'â€™' → '’', 'â€”' → '—'); normalise curly quotes and dashes the same
     way the existing pinned sheets do (sample 20 existing rows first and report what they use).
   - Parse every JSON field (json first, then ast.literal_eval); check the types in the Data Flow
     sheet §3; entities keys ⊆ {people, institutions, places, cases, laws_treaties, events}.
   - Strip whitespace in list items; drop empty strings; keep original case (the existing sheets are
     NOT casefolded — report this difference from the old W1.2 spec rather than casefolding).
3. Write the normalized workbooks: dates as text, JSON re-serialised with ensure_ascii from config.
4. Report: rows in/out, cells changed per column with before → after examples, every unparseable or
   invalid field (row, column, value).

SELF-CHECKS (must pass)
- mojibake count in output = 0 (search for 'â€', 'Ã', '\ufffd').
- Re-running the script on its own output changes 0 cells (idempotent).
- Assert on a known multi-byte string that UTF-8 survives the round trip.

FLAG, DO NOT FIX
- Any schema violation (STOP) · an invalid date · an ID collision · a JSON cell that does not parse.
```

---

## P6 · CE-4 — Merge, generate, re-pin  (Claude Code — ONLY after batch-03 is promoted)

```
CE-4 — append batch-04 to the pinned sheets, move the sources, regenerate, re-pin

BOUNDARIES
- Precondition: batch-03 is promoted and tagged. If not, STOP.
- Append-only: existing rows in data/csv/*_curated_normalized.xlsx must stay byte-for-byte equal
  in content. Existing data/text/*.md and corpus/ files must not change.
- Use scripts/generate_corpus_from_xlsx.py unchanged. Do not hand-edit corpus/.

STEPS
1. Snapshot before: sha256 of every data/text/*.md and every corpus/*/*/*.md|.json (CRLF-normalised),
   and a per-row hash of each pinned sheet.
2. Append the rows of each batch-04/<type>_enriched_normalized.xlsx to the matching pinned sheet
   data/csv/cjp_<columns|books|speeches|biography>_curated_normalized.xlsx
   (first sheet, after the last row). Write Date as text.
3. Copy batch-04/data_text/*.md to data/text/ (cp -n; STOP if a name already exists).
4. python scripts/generate_corpus_from_xlsx.py --dry-run → expect total = 1,104 + n, summary-fallback 0,
   retired 5, no bad codes or duplicates. STOP otherwise. Then run it for real.
5. Content-aware diff against step 1: the ONLY changes allowed are n new rows, n new data/text files and
   2n new corpus files. STOP if any pre-existing file or row changed.
6. python scripts/build_corpus_snapshot.py && python scripts/verify_pin.py → must PASS.
7. Report counts before/after per type and the exact list of new IDs.

SELF-CHECKS
- IDs in active xlsx rows == data/text/*.md == corpus docs (the three sets are identical).
- verify_pin exits 0.

FLAG, DO NOT FIX
- Any pre-existing hash that moved (STOP and restore) · generator warnings · a new doc with no body.
```

---

## P7 · CE-5 … CE-14 — Chunk, index, topic map, eval, promote  (Claude Code)

```
CE-5…CE-14 for batch-04 — follow the Corpus Expansion sheet rows in order; this prompt only fixes the order and gates.

BOUNDARIES
- The dense/sparse/centroid build scripts and app/embeddings.py, app/retrieval.py, app/sparse.py are
  currently only in C:\Reachy Mini Project 2026. Until the code is reconciled into the Final Project
  Folder, run CE-5…CE-14 there, on a copy of the Final Project Folder's data/ and corpus/, and bring the
  outputs back.
- One encoder, one dimensionality (bge-base-en-v1.5 @768d) for the WHOLE corpus. STOP on any mismatch.

STEPS (each is the paste-ready prompt in its Corpus Expansion row)
CE-5 chunk new docs only → CE-6 full re-embed + sparse + date index → CE-7 orphan census →
CE-8 human decision (retag / expand / rebuild) → CE-9/10 only on those branches →
CE-11 add gold questions for the new material of every track (≥1 grounding, 1 exact-identifier, 1 temporal,
1 out-of-scope) → CE-12 promotion eval (fabrication 0; no regression on pre-existing gold) →
CE-13 threshold re-check → CE-14 provenance, rollback note, attestation, then tag.
```

---

## P8 · CE-15 — Update the records  (Cowork)

```
CE-15 — refresh every quoted number and the trackers after batch-04 is promoted

STEPS
1. Changelist (file · old text · new text) of every place that quotes the corpus / chunk / topic count
   or the next free IDs: CJAP_Robot_Project_Plan_v2.xlsx (Data Flow §4 register and totals),
   CJAP_Pilot_Tracker_v10.xlsx (CM-5, CM-6), corpus/MANIFEST.md, the client one-pagers in deliverables/,
   and the handover deck. Apply only after review.
2. Mark CM-5 and CM-6 Done with evidence paths; add the batch-04 row to the decisions register (CE-8 branch).
3. Update the project note claude/CJAP_corpus_data_flow_status.md.
```

---

### Known issue to clear in batch-03 first (D-7, found 22 Sep 2026)
109 existing corpus documents have no clean `YYYY-MM-DD` date. In the pinned sheets, 58 book dates are
text like `9/30/2007`, 20 are numbers like `2003.0`, and 31 biography dates are free text or a bare year.
The generator writes the first 10 characters, so the corpus shows values like `2003.0` or `Childhood,`.
That's why B1, B3, C1 and P5 insist on text `YYYY-MM-DD` plus a precision column.
