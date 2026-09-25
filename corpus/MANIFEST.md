# corpus/ — MANIFEST

The runtime corpus: **1,104 documents** (snapshot 22 Sep 2026), generated from the four
pinned sheets in `data/csv/*_curated_normalized.xlsx` plus the source texts in `data/text/<ID>.md`
by `scripts/generate_corpus_from_xlsx.py`. The full procedure is on the Data Flow and
Corpus Expansion sheets of `CJAP_Robot_Project_Plan_v2.xlsx` (repo root).

## Subdirectories

| Path | Contents |
|---|---|
| `columns/` | 785 *With Due Respect* columns — paired `<ID>.md` + `<ID>.json`, by theme folder |
| `books/` | 131 book chapters from 10 books |
| `speeches/` | 153 speeches |
| `biography/` | 35 chapters of Reginald T. Yu's *Liberty and Prosperity* (GC001–GC035) |
| `index/` | `chunks.jsonl` + `chunk_index.json` — heading-aware chunks (`scripts/chunk_corpus.py`) |
| `voice/` | `topic_map.json`, `voice_card.md`, `router_prompt.md` — the Pi deployment versions (Aug 2026) |

Theme folders: `A_liberty_rule_of_law`, `B_prosperity_economic_philosophy`, `C_biographical_personal`,
`D_flp_mission_foundation`, `E_current_events_commentary`.

## IDs

`^[CBSG][A-E]\d{3}$` — format (C column, B book, S speech, G biography) + theme + three digits.
IDs are never reused or renumbered. Retired IDs are listed in `data/csv/retired_doc_ids.csv`
(BA040, BC009, BC010, BD018, SA085); their files are in `data/retired/corpus/`.

## Regenerating

```
python scripts/generate_corpus_from_xlsx.py --dry-run   # counts, retired + stripped-YAML report
python scripts/generate_corpus_from_xlsx.py             # writes corpus/<type>/<theme>/
python scripts/build_corpus_snapshot.py && python scripts/verify_pin.py
python scripts/chunk_corpus.py
```

## Known state (see Data Flow sheet, section 6)

- `index/chunks.jsonl` and `data/index/*` were built BEFORE the 22 Sep changes: they still hold the
  5 retired docs (27 chunks) and the leaked YAML header in 22 *A Centenary of Justice* chapters.
  Both clear at the next rebuild (correction batch-03).
- The index-build scripts (dense, sparse, centroids) and the retrieval modules
  (`app/embeddings.py`, `app/retrieval.py`, `app/sparse.py`) are in the working repo
  (`C:\Reachy Mini Project 2026`) and not yet in this folder.
- The Phase-1 pilot (80 `.txt` sources + the 79-doc tree) is in `archive/phase1/`, with an old-ID → live-ID map.
  `generate_corpus_files.py`, `build_topic_map.py` and `apply_topic_paths.py` belong to that path — do not use.
