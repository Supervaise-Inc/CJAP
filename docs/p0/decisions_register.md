# P0.5 — Decisions register

Opened 25 Sep 2026, **retrospectively**: the project has been making decisions since May 2026, and this is
the first place they are collected. Rows below are harvested from the 19 ADRs in `docs/decisions/`, the
pilot tracker, and the corpus-maintenance work of September. A decision nobody can find was not made.

Columns: **what** was decided · **why** · **who ratified** · **when** · **revisit** · where the evidence is.
`—` in *who ratified* marks a decision that was taken in the build and never formally ratified; those are
the rows to review first.

## Architecture and platform

| # | Decision | Why | Ratified by | When | Revisit | Evidence |
|---|---|---|---|---|---|---|
| D-001 | Claude, not OpenAI, for inference | — | — | 2026-05 | — | ADR-0001 |
| D-002 | LLM tiering: Haiku router + Sonnet composer | — | — | 2026-05 | **Superseded** by D-011 | ADR-0002 |
| D-003 | Reject embeddings for v1 | Small corpus, full index | — | 2026-05 | **Superseded** by D-012 | ADR-0003 |
| D-004 | Pattern 1 — topic-routed two-stage API | — | — | 2026-05 | Superseded by D-011 | ADR-0004 |
| D-005 | Defer robot embodiment for the 30 May demo | — | — | 2026-05 | Done | ADR-0005 |
| D-009 | Messages API, not a managed agent | — | — | 2026-05 | — | ADR-0009 |
| D-010 | Prompt-cache the Voice Card prefix | Cost | — | 2026-05 | — | ADR-0010; tracker W2.3 |
| **D-011** | **Remove the Haiku router entirely — zero model calls before composition** | Latency and determinism | — | 2026-06 | — | tracker W1.8; `llm_calls_before_composition == 0` |
| **D-012** | **Adopt dense + sparse retrieval over a chunked corpus** | Corpus grew past whole-document routing | — | 2026-06 | — | tracker W1.4–W1.6 |
| **D-013** | **Embedding model: bge-base-en-v1.5 @768d** | 4-candidate bake-off | **Sponsor** | 2026-07 | On any corpus-scale change | ADR ref; `bakeoff_FINAL_for_dok.md` (2ca0255) |
| D-014 | Softmax-temp top-p cutoff replaces flat top-k | −28% tokens, 0 grounding loss | — | 2026-07 | — | tracker W2.8, commit 5750b6e |
| D-015 | Streamlit for both the operator UI and the end-user UI | — | — | 2026-05/06 | — | ADR-0008, ADR-0017 |
| D-016 | STT/TTS: local faster-whisper + Piper, then OpenAI STT/TTS with Claude chat | — | — | 2026-05 → 2026-08 | **Open — no consent basis recorded** | ADR-0006, ADR-0007, ADR-0018 |

## Corpus model

| # | Decision | Why | Ratified by | When | Revisit | Evidence |
|---|---|---|---|---|---|---|
| D-020 | Doc ID format `^[CBSG][A-E]\d{3}$`, never reused, never renumbered | Stable citation across batches | — | 2026-05 | — | ADR-0011 |
| D-021 | Hand-curated taxonomy in Python; topic paths by derivation rules | — | — | 2026-05 | — | ADR-0014, ADR-0015 |
| D-022 | Theme-anchored register selection | — | — | 2026-05 | — | ADR-0016 |
| D-023 | Strict date validation, no placeholders | — | — | 2026-05 | — | ADR-0013 |
| D-024 | Permissive CSV enrichment parsing | — | — | 2026-05 | — | ADR-0012 |
| D-025 | The 15-field curated schema is the contract | — | — | 2026-09 | — | Plan → Data Flow §3 |
| **D-026** | **A numbered chapter stays a chapter, whoever wrote it** — flag `by-another-author` | Numbering gaps must mean the *book* skipped a number | Team | 2026-09-24 | At P6 | ADR-0019 |
| **D-027** | **Retire 5 summary-only/duplicate docs without renumbering** (BA040, BC009, BC010, BD018, SA085) | No usable source / duplicate | Team | 2026-09-22 | BC009 revival is a batch-04 question | `data/csv/retired_doc_ids.csv`; CE-18 |
| **D-028** | **CA529 is void** — "Rule of, or by, law" is by Michael L. Tan | Authorship verified against the Inquirer page | Team | 2026-09-23 | Never reuse the ID | `batch-04/_rejected/CA529_REJECTED.md` |
| **D-029** | **A Centenary of Justice is dated 2001-12-01, month precision** | Book's own Preface (Oct 2000–Oct 2001) + source YAML; no printed day | Team | 2026-09-23 | — | `batch-03/correction_list.md` |
| **D-030** | **A row may name a person only as its own document names them** | Stops outside knowledge entering the corpus — the confabulation path | **User, 25 Sep** | 2026-09-25 | Write into B3/C1/S1/G3 | `correction_round_2026-09-25.md` §1 |
| **D-031** | **D-14: repair only what a corpus-built vocabulary confirms; log the rest for re-scan** | Dropped clauses are damage at origin and cannot be inferred | **User, 25 Sep** | 2026-09-25 | On re-scan | same, §4 |
| **D-032** | **Biography dates take the start of the period**; GC020 (Epilogue) takes 2007-01-01 | The "unknown" values were a 10-char truncation artifact | **User, 25 Sep** | 2026-09-25 | — | `batch-03/biography_dates_applied_2026-09-25.csv` |
| **D-033** | **Apply the Centenary merge** — corpus spine + the book's missing passages and headings, all 19 chapters | Neither source is a superset | **User, 25 Sep** | 2026-09-25 | If a clean scan arrives | `batch-03/centenary_merge_applied_2026-09-25.csv` |
| **D-034** | **C-9: all dates stored as text `YYYY-MM-DD` in every pinned sheet** | 1,109 of 1,109 rows disagreed with the schema; the generator absorbed it by luck | Build, on the user's "make all normalisation the same format" | 2026-09-25 | — | `batch-03/format_consistency_audit_2026-09-25.md` |

## Persona, voice and public presentation

| # | Decision | Why | Ratified by | When | Revisit | Evidence |
|---|---|---|---|---|---|---|
| **D-040** | **Wake phrase "Hey Cee Jap" / "Cee Jap"** | Accent testing | **Sponsor + Counsel** | 2026-07-27 | At DEPLOY-1 | tracker WW-2 — **config change still pending** |
| D-041 | Keep legacy "CJ"/"hey cj" variants through the August demo, prune at DEPLOY-1 | — | Lean on record, **not ratified** | 2026-08 | DEPLOY-1 | tracker WW-5 — OPEN |
| **D-042** | **The robot speaks as CJ Panganiban and does not describe itself as an AI** | **The subject's own wish** — CJ Panganiban wants the robot to say that it is him | **CJ Panganiban (the subject)** | pre-existing, date to be recorded | On any change of venue or audience | `voice_card.md` "Identity rule" matches. **EVIDENCE PENDING** — the consent is not documented in the folder; file it in docs/p0/ and point this row at it |
| D-043 | Sub judice, no comment on living individuals beyond the corpus, no invented rulings | — | — | Phase 1 | — | `voice_card.md` "Safety boundary" |

## Process and gates

| # | Decision | Why | Ratified by | When | Revisit | Evidence |
|---|---|---|---|---|---|---|
| D-050 | A correction runs as its own batch, never mixed with new material (CE-17) | — | Team | 2026-09 | — | Plan → Corpus Expansion §F |
| D-051 | Append-only corpus; corrections and retirements are the only exceptions | — | Team | 2026-09 | — | same |
| D-052 | The Final Project Folder is the base for the online repo | — | User | 2026-09-22 | — | status doc |
| **D-054** | **Counsel cleared the whole corpus, the voice and the likeness** — all six items of the consent inventory | Rights review completed | **Counsel** | 2026-09-25 | On any new source type or venue | `docs/p0/consent_evidence_inventory.md` §4 — **approval document still to be filed** |
| **D-053** | **GO issued with 2 AMBER KPIs** (payload sweep, fusion tuning deferred to DEPLOY-1) | — | **Sponsor** | 2026-09 | DEPLOY-1 | `CJP_Pilot_Report_W3_5_FINAL_r2.docx` |

## What this register makes visible

- **Most of the architecture was decided without a recorded ratifier.** Twelve rows carry `—`. That is
  normal for a build moving fast, and it is exactly what P0.5 exists to stop being invisible.
- **Three superseded decisions were never marked superseded** — D-002, D-003, D-004 describe a system
  that no longer exists, and their ADRs still read as current. The voice card still describes that same
  dead architecture (risk R-1), which is what happens when supersession is not recorded.
- **D-042 is ratified by the subject himself** — CJ Panganiban wants the robot to say it is him — but the
  consent is **not documented anywhere in the folder**. That is the gap now: evidence, not agreement. It
  also moves the disclosure burden onto the exhibit's signage and interaction script (P7.8).
- **D-016 (the synthesis voice)** is covered by D-054, Counsel's clearance of 25 Sep 2026.

## Maintenance

One row per decision, added when the decision is made, not later. Superseded rows are marked, never
deleted. New ADRs continue in `docs/decisions/` and are cross-referenced here.

| | Name | Date | Signature |
|---|---|---|---|
| Register opened and reviewed | Member 3 | | |
| Unratified rows dispositioned | Sponsor | | |
