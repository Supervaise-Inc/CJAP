# archive/phase1 — the Phase-1 pilot corpus (May 2026)

Kept for history only. Nothing in the pipeline reads this folder.

| Path | What it is |
|---|---|
| `data_text/` | The 80 original source texts (`.txt`): 64 columns, 15 speeches and the whole biography in one file (GC001). Formerly `data/text/*.txt`. |
| `corpus/` | The 79-document corpus the first demo app used (64 columns, 15 speeches, paired `.md` + `.json`). Formerly `corpus/_legacy_phase1/`. |
| `id_map_phase1_to_live.csv` | Where each Phase-1 document lives in the current corpus. |

## Old IDs are not live IDs

In June the corpus was rebuilt from the four curated spreadsheets (`data/csv/*_curated_normalized.xlsx`), and some documents were renumbered.
An old ID can therefore name a **different** article in the live corpus. Always go through `id_map_phase1_to_live.csv`.

- 53 documents kept their ID.
- 25 were renumbered (e.g. CA001 → CA092, CA002 → CA120).
- The biography (GC001, one file) is now GC001–GC035, one document per chapter.
- **CA016 "Rule of, or by, law" (Inquirer, 2 Feb 2018) is NOT in the live corpus, and must not be added.**
  Checked on 23 Sep 2026 against the article page: it is by **Michael L. Tan**, column **"Pinoy Kasi"** — not a
  *With Due Respect* column. Phase 1 stored it as CA016 by mistake; the June 2026 rebuild correctly dropped it.
  It was briefly staged for batch-04 as CA529 and has been withdrawn; see `batch-04/_rejected/CA529_REJECTED.md`.
  The ID **CA529 is void** — never reuse it. Its text stays here as `data_text/CA016.txt` for reference only.

## The live corpus

1,104 documents: `data/text/<ID>.md` (sources) → `data/csv/*_curated_normalized.xlsx` (enriched rows) → `corpus/` (generated), via `scripts/generate_corpus_from_xlsx.py`.
The Phase-1 scripts (`generate_corpus_files.py`, `build_topic_map.py`, `apply_topic_paths.py`) read the files that are now in this archive and are not used for the live corpus.
