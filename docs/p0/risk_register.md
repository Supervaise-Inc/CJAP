# P0.4 — Risk register and abort conditions

Opened 25 Sep 2026. Every risk here is **evidenced from something actually found in this project**, not
imagined. Likelihood and impact are the owner's to revise; the evidence column is not.

Scale: likelihood L/M/H · impact L/M/H · a trigger is the observable event that moves the risk from
watched to acted on.

## Live risks

| ID | Risk | L | I | Owner | Trigger | Evidence / state |
|---|---|:-:|:-:|---|---|---|
| **R-1** | **The composer's system prompt describes an architecture that no longer exists.** `voice_card.md` tells the model Haiku has already routed the question and that there are "no embeddings, no similarity search, no chunking — documents arrive whole". Haiku was removed at W1.8; retrieval is dense+sparse over 9,804 chunks. It sits in the cached prefix, so it ships with **every answer** | H | M | Member 1 | Already true | `corpus/voice/voice_card.md` lines 4–14; loaded at `app/answer_pipeline.py:534` |
| **R-2** | **The voice card was written for a ~79-document Phase 1 corpus** and is titled as such. The corpus is 1,104 | H | M | Member 2 | Already true | `voice_card.md` line 1 |

| **R-4** | **The consent behind the persona is undocumented.** CJ Panganiban wants the robot to say it is him — the decision is his and it is settled — but nothing in the folder records it. Disclosure now rests on P7.8 signage and the interaction script, which have not been reviewed in that light | M | M | Member 3 | First unattended public session, or any venue where signage is absent | `docs/p0/persona_brief.md` §4; decisions register D-042 — evidence pending |

| **R-6** | **A document by the wrong author reached staging.** CA529 was by Michael L. Tan, caught only by QA | L | **H** | Member 2 | Any new batch without an authorship check | `batch-04/_rejected/CA529_REJECTED.md` |
| **R-7** | **D-14 — the book sources are OCR-damaged at origin.** Clauses dropped mid-sentence in the publishers' `.docx`. 420 suspect spans across 96 of 168 chapters; not repairable without a re-scan | **H** | M | Member 2 | P6 merge proceeds without a re-scan plan | `batch-04/d14_rescan_list.json`; `correction_round_2026-09-25.md` §4 |
| **R-8** | **The index is stale against the corpus.** batch-03 regenerated 156 documents and re-chunked; the dense and sparse indexes are pre-correction until CE-6 runs | **H** | M | Member 1 | Any demo or eval run before CE-6 | `batch-03_run_report_2026-09-25.md` — "corpus authoritative, index stale" |
| **R-9** | **D-6 — September's corpus work is uncommitted.** Generator guard, retirements, source fixes, batch-03, batch-04 all exist only in the working folders | M | **H** | Member 1 | Disk loss, or a second machine needing the work | tracker CM-2 "uncommitted — D-6" |
| **R-10** | **The validity and safety gate (P6) does not exist.** No sentence-level checks, no envelope audit, no recovery path, no validity record. Fabrication control today rests on retrieval quality and the composer prompt | M | **H** | Member 1 | Public operation | Project Plan P6.1–P6.5, no evidence |
| **R-11** | **Two AMBER KPIs carried into GO.** The payload/threshold sweep (P8.4) and fusion tuning (P8.5) were deferred to DEPLOY-1 | M | M | Member 1 | DEPLOY-1 opens | tracker W3.3, W3.4 DEFERRED |
| **R-12** | **Live TTFA ~4s, STT-dominant.** Measured, diagnosed, not yet fixed | M | M | Member 1 | Visitor-facing timing target set | tracker N-2 |
| **R-13** | **The wake phrase is ratified but not in config.** "Hey Cee Jap" agreed 2026-07-27; WAKE-CFG-1 still pending, and public materials still say the old phrase | M | L | Member 1 | Bench session or any signage print | tracker WW-2, WW-6 |
| **R-14** | **Single-machine dependency.** The embedding stack and model cache exist only in one Windows venv; the model cannot be fetched from the Linux workspace (huggingface.co blocked, 403) | M | M | Member 1 | That machine unavailable when a re-embed is needed | today's CE-6 attempt |
| **R-15** | **Three components carry their own punctuation-folding rules** (C1, B3, P5), which is how a signature phrase passed one verbatim check and failed another | M | L | Member 1 | Next intake batch | CA538; `format_consistency_audit_2026-09-25.md` §4 |

## Risks that have been closed

| Was | Closed by |
|---|---|
| **R-3** — no consent on file for corpus, voice or likeness | **Counsel approval, 25 Sep 2026.** Residual: the approval document is not yet filed in `docs/p0/` |
| **R-5** — third-party writing inside CJP-attributed documents (Salonga, the SC APJR summary, the PDI editor's notes) | **Counsel approval, 25 Sep 2026** — nothing excluded on rights grounds |
| Retired documents still answerable through the index (27 chunks) | batch-03 re-chunk, 25 Sep |
| Corpus dates unreadable by the generator (`2003.0`, `Childhood,`) | C-3 / C-9, 25 Sep — all 1,109 rows now text `YYYY-MM-DD` |
| Source YAML leaking into corpus bodies | C-1 + regenerate |
| "Frozen corpus" unverifiable | `verify_pin.py`, PASS |

## Abort conditions

Written now, while nobody is under pressure.

**Stop the public release** — not the project — if any of these is true at the time of release:

1. The consent behind the persona is undocumented, or the exhibit carries no signage explaining what it is (R-4, P7.8).
3. The index does not match the corpus (R-8).
4. Fabrication is non-zero on the gold set at the current baseline.

**Stop the project and escalate to the Sponsor** if:

5. Consent is **withdrawn** by the subject or the Foundation.
6. Counsel finds the corpus cannot be cleared for this use.
7. A public answer is found to have fabricated a ruling, a vote count or a quotation attributed to him.

**Roll back rather than patch forward** (CE-16) if a corpus change moves any pre-existing document outside
its declared changed-doc set, or if corpus verification fails at any point. Backups for every change made
this week are in `batch-03/` and `batch-04/`.

| | Name | Date | Signature |
|---|---|---|---|
| Register reviewed | Member 3 | | |
| Abort conditions agreed | Sponsor | | |
