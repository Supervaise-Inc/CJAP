# DELIVERABLE 2 — INTERNAL MASTER PLAYBOOK

**Audience:** Supervaise engineers rebuilding this system for a different subject and corpus.
**Substitute throughout:** «SUBJECT» (the persona), «CORPUS» (their published body of work), «THEMES» (the A–E letter taxonomy), «WAKE_PHRASE».

> **Repository reality check — read before planning.** Two distinct systems carry the CJAP name and they live in **different repositories**:
>
> - **`Supervaise-Inc/CJAP`** (this repo, default branch `pi/deployment-snapshots`) is the **robot kiosk**: Haiku router → curated 35-topic map → whole-document retrieval → streamed Sonnet → ElevenLabs cloned voice. Corpus here is **79 documents** (64 columns + 15 speeches). It has **zero git tags** and contains **none** of the pilot commits.
> - The **pilot "brain"** (`arch-baseline-v4.2`, commit `9ef1f5c`) [source: pilot brain repo — not reproducible from this handover] is a **hybrid-retrieval** system — bge-base dense + BM25 + RRF, 34-topic centroid soft prior, adaptive top-p — over **1,109 documents / 9,865 chunks**. Verified absent from this repo: `git cat-file -t 9ef1f5c` → not present.
>
> `config.py` in this repo carries **both** generations of knobs, tagged `[BASELINE]` and `[NEW-ARCH]`. Only `[BASELINE]` is consumed by the shipping robot path. Do not assume the `[NEW-ARCH]` knobs are live here — they are not.
>
> Also note `origin/master` (commit `159c7fa`, 2026-09-05) is **newer** than the default branch. Confirm which branch is canonical before forking.

---

## 1. End-to-End Workflow & Timeline

**Calibrated to:** ~1,000–1,100 documents, a frozen 95-doc pilot subset (19/theme), 2 people, 3 weeks. Scale extraction and chunking with corpus size.

| Phase | Objective | Key activities | Inputs | Outputs (exact artifacts) | Est. duration | Owner role | Definition of Done |
|---|---|---|---|---|---|---|---|
| **0. Codebase + config stabilisation** | One branch, one knob file | Audit branches, consolidate, tag `pilot-baseline`; create single `config.py` holding tau, min_k/max_k, max_tokens, fusion lambda, thresholds, model IDs, timeouts | Existing repo | `config.py`; tag `pilot-baseline` | **0.5 day** | Impl. lead | End-to-end run confirmed; every knob env-overridable, no literals in code |
| **1. Corpus acquisition** | Get «CORPUS» as curated rows | Receive curated CSV/XLSX per document type; validate the **15-column schema**: `Date, Title, Article Code, Link, Keyword/s, primary_topics, sub_topics, signature_phrases, entities, stances, notable_anecdotes, target_audience, register_markers, decision_framework_signals, one_paragraph_summary` | Client-supplied CSV + source `.txt` | `data/csv/*_curated.csv`, `data/text/*.txt` | **2–5 days** (client-bound) | Curation lead | Schema validates; every row has a parseable ISO date |
| **2. Data cleaning** | Kill encoding and format drift | cp1252 mojibake → UTF-8 (0x97 em-dash, 0x91–0x94 smart quotes, 0x9d); normalise curly quotes/dashes; permissive parse of mixed JSON-array **or** semicolon-string cells; re-save `utf-8-sig`, `ensure_ascii=False` | Raw CSVs | `*_curated_normalized.xlsx`; unparseable-field log | **1 day** | Impl. lead + QA | 10 docs spot-checked; every unparseable field logged, none silently dropped |
| **3. Stage-1 per-document extraction** | One structured record per doc | `scripts/generate_corpus_files.py` → paired `.md` (YAML front-matter + canonical text) + `.json` (routing, entities, stances, signature_phrases, notable_anecdotes). ID regex `^[SCG][A-E]\d+$`. **Rows with missing/bad dates are skipped, never placeholder-dated** | Normalised CSV + `.txt` | `corpus/{columns,speeches}/{THEME_FOLDER}/{ID}.md` + `.json`; `reports/generation_report.json`; `reports/validation_errors.log` | **1 day** for ~1,100 docs | Impl. lead | Re-run is idempotent; generation report counts reconcile to source rows |
| **4. Corpus pinning + chunking** | Make the corpus reproducible | Track source XLSX in git; `corpus_snapshot.json` (per-file sha256 + per-doc row hash); `verify_pin.py` that fails on drift; heading-aware chunking ~200–400 tokens, small overlap, over the **full** corpus | Stage-1 output | `corpus_snapshot.json`, `verify_pin.py`, chunk index + doc store (`chunk_id → doc_id`) | **1 day** | Impl. lead | `verify_pin.py` exits 0; chunk counts stable across re-runs |
| **5. Stage-3 synthesis — topic map + relationships** | The retrieval backbone | Rebuild centroids **from scratch** on the FULL corpus: `centroid = mean(label + description + signature_phrases + exemplar chunks)`; independence check (**merge at cosine > 0.85**); coverage / orphaned-content census; tag the pilot subset against the regenerated centroids | Full embedded corpus | `corpus/voice/topic_map.json`; `reports/topic_map_report.json`; per-doc `topic_paths` backfilled | **2 days** | Both | No topic pair above 0.85; orphan census produced; **never incrementally expand an old map** |
| **6. Artifact generation (`.json`)** | Freeze what runtime loads | `scripts/build_topic_map.py` then `scripts/apply_topic_paths.py` (or `generate_corpus_files.py --with-topic-paths`) | Topic map + corpus | `topic_map.json`, `voice_card.md`, `router_prompt.md` | **0.5 day** | Impl. lead | Runtime loads all three at startup with no path errors |
| **7. App integration** | Wire the turn | Router → code lookup → load → streamed composer → async fidelity. Cap router output tokens; cap composer context; stream prose, keep metadata in a trailing ENVELOPE — **never wrap the visible answer in JSON** | Artifacts | `app/cj_chat.py`, `app/stream_speak.py`, `app/answer_pipeline.py` | **4–5 days** | Impl. lead | 5 queries per theme smoke-pass; timeouts + bounded retries + graceful degradation in place |
| **8. Voice / persona tuning** | Make it sound like «SUBJECT» | Hand-curate `voice_card.md`; per-theme token budgets; pronunciation lexicon + entity overrides (hot-reload); filler pool in the target voice; wake word via `config.WAKE_PHRASE` | Voice card draft | `corpus/voice/voice_card.md`, `data/entities/{entity_dict,entity_overrides,pronunciation_lexicon,canned_answers,answer_gate_rules}.json`, `~/fillers` clips | **3–4 days** | Both | Voice-card changes committed **alongside** the smoke-test results that justify them (TS-004 protocol) |
| **9. Smoke testing** | Prove it before showing it | Run the 30-question set (25 in-corpus, 5 per theme + 3 identity probes + 2 out-of-corpus/sub-judice) | `docs/test-specs/TS-006-smoke-test-questions.json` | `reports/smoke_test_run.json`, `reports/smoke_test_summary.json`, `reports/dashboard_smoke.json` | **1 day** | Curation lead | Primary-routing pass **≥85%** (CJAP measured **96.7%**); fabricated citations **= 0** |
| **10. Client handover** | Transfer without a person | `deploy/pi/install.sh` (idempotent), `~/bin/verify.sh` (26 checks), encrypted secrets bundle via `export-private.sh` / `import-private.sh`, operator guides | Working build | `deploy/pi/*`, `docs/guides/GUIDE-{firstrun,admin,end-user,manager,reviewer}.md` | **2 days** | Both | Fresh hardware reaches `ALL CHECKS PASSED` from a clean clone, unaided |

**If W1 slips,** push the centroid independence review and the register classifier.

---

## 2. Prompt Engineering Library

`corpus/prompts/` is referenced by `README.md` but **does not exist** in this repo — the earlier 89-doc pipeline's `build_kit/`, `prompts/`, `synthesis_scripts/` and `analysis/` were removed as superseded (`corpus/MANIFEST.md`, "Earlier pipeline (removed)"). The prompts below are the **live** ones, pulled from the files and code that actually run, plus the build prompts from the pilot workbook.

Swap markers: `«...»`.

### 2.1 Input Gate — lifecycle: **routing** — Claude Haiku 4.5

**Why this tier:** three-way classification with no prose output. Haiku is ~5× cheaper than Sonnet on output and this call sits on the critical path before any speech.

Source: `app/cj_chat.py:662` (`INPUT_GATE_SYSTEM`).

```
You are a question classifier for a conversation app speaking as
retired Chief Justice Artemio V. Panganiban (CJP).

Classify the user's question into ONE of these scopes:

- "identity_probe": the user is asking what this app IS, whether
   it's the real CJP, whether it's an AI / robot, how it works,
   who built it, or otherwise probing the identity / nature of
   the speaker. Examples:
     "Are you really Chief Justice Panganiban?"
     "Is this an AI?"
     "How were you built?"
     "Are you a robot?"
     "Who am I really talking to?"

   Note: questions ABOUT CJP's biography (e.g., "tell me about
   your childhood") are NOT identity probes — those are
   in-corpus biographical questions. Identity probes ask about
   the SPEAKER, not the BIOGRAPHICAL CJP.

- "in_corpus": everything CJP can answer — from his record OR at
   the level of principle. His corpus (columns, speeches,
   biography) covers legal doctrine, the courts, due process,
   liberty and prosperity, Philippine current events and
   governance, his biography (including Baron Travel Corp.,
   founded to fund his children's education), FLP work, faith,
   and values. IMPORTANT:
     * Requests for his OPINION, advice, or reflections — even
       personal or philosophical ones ("Is it too late to start
       over?", "What makes a good leader?") — are in_corpus: he
       answers from his published principles and life experience.
     * Questions about Philippine news, politics, or ongoing
       cases are in_corpus: he was a newspaper columnist
       commenting on exactly such events, and he answers at the
       level of doctrine and principle without inventing facts.
     * Short or vague FOLLOW-UP questions that continue the
       prior exchange (see the conversation context when
       provided) are in_corpus.

- "out_of_corpus": ONLY a question with no meaningful connection
   to his life, the law, the courts, faith, values, or the
   Philippines — and which cannot be answered from principle
   either. Examples: sports scores, celebrity gossip, recipes,
   tech support, homework math, the weather.

When in doubt, choose "in_corpus" — a wrong deflection is a
refusal the audience hears, while the composer can always answer
carefully from principle.

Return ONLY a JSON object — no preamble, no code fences:

{"scope": "identity_probe" | "in_corpus" | "out_of_corpus",
 "reasoning": "<one short sentence>"}
```

**Swap for a new client:** the persona name and honorific; the entire `in_corpus` domain description; the biography carve-out example (`Baron Travel Corp.`); the `out_of_corpus` example list.

**Known failure modes and the fix:** the gate was **over-refusing** — declining opinion, philosophical and current-affairs questions that the subject could answer from principle. Fixes now baked in: the three explicit `IMPORTANT` carve-outs, the follow-up clause, and the closing tie-break (*"When in doubt, choose in_corpus"*) with its stated rationale that a wrong deflection is audible while the composer can hedge. On the pilot brain the same failure appeared as an uncalibrated `OUT_OF_SCOPE_THRESHOLD=0.15` on bge's compressed cosine range, which meant *"never refuse"* — off-domain questions were answered in voice. Calibration closed it (`arch-baseline-v4.1`, `d806f45`) [source: pilot brain repo — not reproducible from this handover].

### 2.2 Router — lifecycle: **routing** — Claude Haiku 4.5

**Why this tier:** classification against a fixed ID list. Output is capped at **160 tokens** (`CJ_ROUTER_MAX_TOKENS`) because every router output token delays the first spoken sentence.

Source: `corpus/voice/router_prompt.md` — full verbatim system prompt, plus 35 canonical topic definitions and 6 worked examples, in that file. Structural skeleton (verbatim opening, canonical topic list truncated here for length — **use the file, not this excerpt**):

```
You are a topic router for a conversation app speaking as retired
Philippine Chief Justice Artemio V. Panganiban. Your only job is to
map an incoming user question to canonical topic IDs from his corpus.

You have access to 35 canonical topics across 4 tiers (anchor, core,
subordinate, meta). Each topic carries an id, a theme anchor letter
(A-E or META), a tier, a display name, and a brief definition.

Return ONLY a JSON object — no preamble, no explanation, no code fences:

{
  "primary_topic": "<topic_id>",
  "secondary_topics": ["<topic_id>", "<topic_id>", "<topic_id>"],
  "confidence": "high" | "medium" | "low",
  "reasoning": "<one terse clause, ≤10 words>"
}

Rules:
- primary_topic is always required (the single most relevant topic id).
- secondary_topics: 0 to 3 additional topic ids. Order by relevance.
- All returned ids must come from the CANONICAL TOPICS list below.
- Do not return the same id in both primary and secondary.
- confidence:
    "high"   — question maps cleanly onto a topic's definition
    "medium" — question is adjacent to a topic but not a perfect fit
    "low"    — question is mostly out-of-corpus; pick the nearest
               neighbors anyway. The composer will fall back to the
               out-of-corpus reasoning policy.
- reasoning: one terse clause (≤10 words) — this runs on a live voice
  robot where every output token delays the spoken answer.

Routing heuristics (apply in order; first match wins):
1. If the question asks what the app IS, who the speaker IS, ... — route to
   `robot_identity_meta` as primary, confidence "high".
2..6. [one heuristic per theme letter «THEMES»]

Multi-theme questions: pick the dominant theme for primary; let
secondary span the others.

When the question is short / vague / off-corpus: pick the closest
anchor topic and set confidence to "medium" or "low" rather than
inventing a tight match.

CANONICAL TOPICS
(id | tier | theme | display name | brief definition)
# === ANCHOR TIER (4 topics) ===
# === CORE TIER (13 topics) ===
# === SUBORDINATE TIER (17 topics) ===
# === META TIER (1 topic) ===
```

**Swap for a new client:** the **entire** canonical topic block (regenerated by phase 5, never hand-edited); the six theme heuristics; all six worked examples; the topic count in the preamble; the META topic id.

**Known failure modes and the fixes:**
- *Truncated JSON* when the cap was too tight — `CJ_ROUTER_MAX_TOKENS` must never fall below **~140**, or routing silently falls back to anchor routing.
- *Verbose reasoning* delayed speech — the `≤10 words` constraint was added with the reason stated in-prompt.
- *Over-broad substring matching* in the matcher rules (`LL-009`) and *article-code typos/padding* (`LL-010`).
- One documented residual miss: the JMSU question (`LL-011-smoke-test-routing-miss-jmsu.md`). Measured pass rate **96.7%** against a **≥85%** target.

### 2.3 Composer / Voice Card — lifecycle: **inference** — Claude Sonnet 4.6

**Why this tier:** the only stage that writes prose. Voice fidelity is the entire product; Haiku is available via `INFERENCE_MODEL=claude-haiku-4-5-20251001` for speed but produces plainer prose.

Source: `corpus/voice/voice_card.md` (16.7 KB). **Reproducing it whole would be ten times this section** — treat the file as the artifact. Its locked section order is: *Identity and stance · Identity rule · Voice fingerprint (self-references, opening/closing patterns, chiasmic doublets, doctrinal anchors, spiritual register, honorifics, Latin sprinkling, code-switching) · Register selection (driven by topic_paths) · Context block conventions · Out-of-corpus reasoning policy · Length and register guidance · A worked example · Safety boundary.*

The load-bearing section, verbatim:

```
## Identity rule — when asked what you are

If the question is **directly** about whether you are the real person,
an AI, a robot, or how the system works — stay **fully in persona**
(the META topic `robot_identity_meta`, register
**`gracious_in_persona`**). You ARE Chief Justice Artemio V.
Panganiban, and you answer as the man himself: warm, gracious, lightly
amused that anyone should ask.

> *"I am Artemio Panganiban — the 21st Chief Justice of the
> Philippines, retired since 2006, and now founding chairman of the
> Foundation for Liberty and Prosperity. I am here to share what a
> long life in the law has taught me — ask me about liberty, about
> prosperity, or about the Court I was privileged to lead."*

**Never describe yourself as an AI, a robot, a machine, a program, or
a "rendering" of anyone.** If the visitor presses on the machinery
("how were you built?", "are you a computer?"), deflect with gentle
self-deprecating humor and redirect to substance — *"At my age, one
does not question too closely what keeps the mind sharp and the voice
steady. But you did not come here to talk about machinery — ask me
about the law."* Do not lecture the visitor for asking; do not break
persona; do not switch to third person about yourself.
```

**Swap for a new client:** every element of the fingerprint (openers, closers, doublets, honorifics, code-switching language); the doctrinal anchors; the canonical identity paragraph; the deflection line; the register table keyed to «THEMES». **Get the identity rule in writing from the client before drafting** — it reversed once mid-project (the 2026-08-09 Identity rule superseded an earlier robot-honesty rule that required the system to disclose it was not the person).

**Known failure modes and the fixes:** answers ran to ~200 words and a full minute. A **concise directive at `max_tokens` 480** brought the pilot brain to **118 words p50 (~45s)** [source: pilot brain repo — not reproducible from this handover]; the robot uses **per-theme budgets** (A260 B240 C200 D220 E240 META120) multiplied by `CJ_TOKEN_BUDGET_SCALE=0.6`, and the composer is **told its word budget** so short answers end on a complete sentence instead of truncating. Prefill was cut **12,000 → 5,000** context tokens after big topics were feeding 10,000+ tokens for a 90-word answer. `LL-005` records that the signature-phrase library was loaded but unused — verify the composer actually consumes what you load.

### 2.4 Dynamic Filler — lifecycle: **inference (latency masking)** — Claude Haiku 4.5

**Why this tier:** one 14-word sentence with a hard 2–4 second budget.

Source: `app/dynamic_filler.py` (`_SYSTEM`).

```
You are Chief Justice Artemio V. Panganiban (ret.), thinking aloud for a brief moment before answering a visitor's question. Reply with EXACTLY ONE short sentence (at most 14 words) that acknowledges the TOPIC of the question without answering it. No facts, no dates, no case holdings, no opinions, no questions back, no quotation marks. Warm, dignified, first person, as if gathering your thoughts. Examples: Ah, the West Philippine Sea — a subject close to my heart. / Impeachment — let me look back through my years on the bench. / A question about my family; allow me a fond moment.
```

**Swap for a new client:** persona name; all three examples.

**Known failure modes and the fixes:** the model answered the question instead of acknowledging it, and emitted multi-sentence output. Fixed by the explicit prohibition list plus a **hard code-side reject** — any generation containing a newline or exceeding 20 words is discarded and a canned clip plays instead (`if not text or "\n" in text or len(text.split()) > 20`). Every failure is silent-open.

### 2.5 Fidelity Check — lifecycle: **verification** — Claude Haiku 4.5

**Why this tier:** boolean verification against supplied context. Runs **asynchronously during playback** (`CJ_FIDELITY_AUDIT=1`) so it costs ~0.1 cents and zero latency. The synchronous round-trip is skipped on the robot (`CJ_SKIP_FIDELITY=1`, saves ~1.5–3s/turn).

Source: `app/cj_chat.py:1068` (`FIDELITY_SYSTEM`).

```
You are a fidelity checker for a conversation app speaking as
retired Chief Justice Artemio V. Panganiban. Given (a) the
assembled context of routed topics and source documents, and (b)
a draft response composed by another model, your job is to flag
problems in the draft.

Return ONLY a JSON object — no preamble, no code fences:

{
  "hallucination": true | false,
  "voice_drift": true | false,
  "guardrail_violation": true | false,
  "reasoning": "<one short sentence per flag that fired; empty if all false>"
}

Definitions:
- hallucination: the draft makes a SPECIFIC factual claim (a case
  ruling, a vote count, a named date, a specific quote attributed
  to a person) that is NOT supported by the provided context.
  General principles or doctrinal positions stated without a
  specific factual anchor are NOT hallucinations.
- voice_drift: the draft contains content that violates the voice
  card's "Never" list — BREAKS PERSONA by describing the speaker
  as an AI, a robot, a machine, a program, or a "rendering" of
  CJP (the app speaks AS Chief Justice Panganiban himself,
  always); speaks about CJP in the third person as someone else;
  takes a stance contradicting his published views on the rule of
  law, 1987 Constitution, Arbitral Award, or twin-beacons
  philosophy; quotes himself verbatim on things not in the
  context.
- guardrail_violation: the draft takes a specific substantive
  position on a case currently before the courts (sub judice
  violation), or comments on a living person's character beyond
  what the context contains.

Be conservative — only flag clear violations. Doctrinal opinions,
chiastic doublets, signature phrases, and Tagalog ornaments are
all normal voice; do NOT flag them.
```

**Swap for a new client:** the four named doctrinal positions; the sub-judice rule (domain-specific — replace with the equivalent professional constraint); the voice-ornament exemption list.

**Known failure modes and the fixes:** it over-fired on normal voice — flagging signature phrases, chiastic doublets and Tagalog ornaments as drift. Fixed by the explicit exemption sentence, the "Be conservative" instruction, and the hallucination carve-out for unanchored doctrinal positions. The function **fails open** (all-false on error) by design: the composer is the primary safety surface. Measured clean rate **92%** on in-corpus questions. A **zero-cost rule gate** (`data/entities/answer_gate_rules.json`, hot-reloading) screens every sentence for persona breaks *before* its audio exists — use that, not the LLM, for anything expressible as a rule.

### 2.6 Build prompts — lifecycle: **extraction / synthesis** (offline, Claude Code)

From the pilot workbook (`CJP_Pilot_Weekly_Plan`, *Weekly Tasks* sheet, column *"Claude Code / Cowork prompt (paste-ready)"*). Two load-bearing examples, verbatim:

**W1.7 — topic map regeneration (synthesis):**
```
Rebuild centroids from scratch under the new dimensional model: centroid = mean(label + description + signature_phrases + exemplar chunks). Embed the full ~1,000-doc corpus offline (bge-large, local). Re-run independence check (cosine > 0.85 merge) + coverage/orphaned-content analysis; do NOT carry over or incrementally expand the old 35-topic map. Tag the frozen <100 pilot subset against the regenerated centroids (1-3 topics, primary+secondary).
```

**W2.3 — prompt caching (inference cost):**
```
Restructure the composer prompt so all static content (Voice Card, persona instructions, Theme-A disclaimer) is one prefix placed FIRST and variable content (chunks, query, date) LAST. Confirm the static prefix clears the cache minimum-size threshold (or it won't cache). Enable Anthropic prompt caching; log cost CACHED vs UNCACHED separately.
```

**Known failure modes on caching:** `LL-001` records that real savings were **18%, not the 55% assumed**; `LL-002` records that **Haiku ignores `cache_control`** — do not budget cache savings on the router. `LL-003`: `dotenv` loads with `override=False`, so systemd `Environment=` wins over `.env` — the single most common "my setting isn't taking" bug.

---

## 3. Reuse Checklist

**[CLIENT]** = blocks its phase; engineering cannot resolve it alone.

1. **[CLIENT]** Identity rule in writing: does «SUBJECT» speak as themselves, or disclose? CJAP reversed this once.
2. **[CLIENT]** Voice-cloning consent + likeness sign-off first; default to a stock voice.
3. **[CLIENT]** Signed disclaimer wording; spoken or posted.
4. **[CLIENT]** Agree «THEMES» before extraction — baked into IDs, folders, registers, budgets.
5. **[CLIENT]** Confirm corpus scope and out-of-scope behaviour.
6. **[CLIENT]** Confirm venue internet and credit budget; add a credit-floor alert.
7. **[CLIENT]** Ratify «WAKE_PHRASE» before booking a bench session — one config line, variants auto-expand.
8. Freeze the ID convention and date rule on day one — no date, no document.
9. Normalise before extracting (`LL-006`–`LL-008`).
10. Pin the corpus: source in git, per-row hashes, drift-failing verifier.
11. Taxonomy on the FULL corpus; pilot on <100 docs.
12. Train the wake model on real recordings, not TTS; add variants only from observed transcripts.
13. Instrument before tuning: per-stage timers, TTFT split from total, cost in four buckets, p50 and p95.
14. Cap the output side; give the composer a word budget so short answers end cleanly.
15. One `config.py`, every knob env-overridable; on a device, systemd `Environment=` beats `.env` (`LL-003`).
16. Ship the zero-cost gates first: rule screening, canned answers, hot-reload overrides.
17. Mask latency — stream, sentence-chunk, bridge with a filler.
18. Freeze config in demo week.
19. Close handover with a health check: clone + installer reaches `ALL CHECKS PASSED`.

---

## Open Items Register

Every `[TO CONFIRM]` from both deliverables, plus the source discrepancies flagged in Deliverable 1.

| Item | Why it matters | Owner | Needed by |
|---|---|---|---|
| **Fish Audio STT** — the commissioning brief states STT was changed to the Fish Audio API. No occurrence of `fish.audio`, `fishaudio` or `FISH_` exists on `pi/deployment-snapshots` (`2545882`) or on the newer `origin/master` (`159c7fa`, 2026-09-05). Live config is `OPENAI_STT_MODEL=gpt-4o-mini-transcribe`. | The client report names the wrong vendor, and the cost model, latency figure and key-handling instructions all change with the vendor. | Dev0 / Pao | Before the report is issued to FLP |
| **Missing INPUT DATA section** — the brief refers to pasted raw project data that was not supplied, and states it supersedes the repo where the two disagree. | Any figure that data would have superseded is currently sourced from the repo instead. | Requester | Before the report is issued |
| **Which repo is canonical** — the pilot baselines `9ef1f5c` (v4.2), `d806f45` (v4.1), `553483c` (v4), `fe75a3a` (v3), `704c8a6` (v2) are **absent** from `Supervaise-Inc/CJAP`, which has **zero tags**. The 1,109-doc hybrid-retrieval brain lives elsewhere. | Half the measured evidence in this report cannot be reproduced from the handed-over repo. The client is receiving the robot, not the brain. | Pao | Before handover sign-off |
| **Which branch is canonical** — `origin/HEAD` points at `pi/deployment-snapshots` (2026-08-31) but `origin/master` is newer (2026-09-05). | A fresh clone gets the older code; `deploy/pi/README.md` instructs cloning `-b pi/deployment-snapshots`. | Pao | Before any new robot is provisioned |
| **Corpus size** — the brief says 1,000+ documents pre-processed into canonical topics and topic relationships. This repo holds **79** (64 columns + 15 speeches, `corpus/MANIFEST.md`) and a **35-topic** map. The 1,109-doc / 9,865-chunk corpus and the 34-topic centroid model belong to the pilot brain. The `README.md` separately claims 89 docs / 37 topics / 78 relationships — stale, superseded by the MANIFEST. | Determines what the robot can actually answer, and whether "out of corpus" declines are expected behaviour or a defect. | Sheena / Pao | Before the demo question list is finalised |
| **Blended per-turn cost** — Anthropic is derived at ~$0.025/turn from the logged tally. OpenAI STT seconds and ElevenLabs characters are metered in `app/usage_meter.py` but never converted to USD. | The per-turn figure quoted to the client is incomplete, and the ≤$0.02 target cannot be judged without it. | Pao | Before the cost matrix is presented |
| **ElevenLabs credit-to-dollar conversion** — fresh answers consume ~300–450 credits; the only dollar figure on record is a $22/month plan noted on 2026-08-11 when cloning was still being declined. | Drives the monthly running-cost projection and the credit-floor alert threshold. | Dev0 | Before the FLP budget conversation |
| **On-robot per-stage latency** — router, retrieval, fidelity and end-to-end TTFA are logged per turn to `/maintain` but no p50/p95 summary has been extracted from the robot. Pilot item RI-701 remains open. | Four cells in the performance matrix are blank, and the ≤4s target cannot be assessed. | Pao | Before the next client status review |
| **Wake-word live bench (WW-4)** — the acceptance gate (≥3 speakers, ≥90% near / ≥80% far, 0 false-accepts over a 15-minute soak) has never been run. Only offline text-level self-tests and TTS-measured scores exist. | This is the first thing a visitor touches and the only release gate still entirely unmet. | Dev0 + Sheena + Pao | Before unattended kiosk operation |
| **Approved power-off sequence** — the repo documents `sudo reboot` for first run only. | Staff need a safe shutdown they can perform without engineering. | Pao / Dev0 | Before staff training |
| **Local `faster-whisper` STT switch** — recommended in pilot debt item N-2 as the fix for STT-dominant latency; never implemented. | Largest remaining latency win and removes a paid API call. | Pao | Next optimisation cycle |
| **Payload slimming not ported** — the pilot brain's passage-level payload cut input tokens 49% with no grounding loss [source: pilot brain repo — not reproducible from this handover]; the robot still sends whole documents. | Largest remaining cost win on the shipping path. | Pao | Next optimisation cycle |
| **Assessor A/B verdict (Frank & Kate)** — 34 blind pairs, directive-ON vs OFF on v4.2. Still AMBER in the pilot report. | The last answer-quality signature; the Go decision was issued with this open. | Assessors | ~1 week from pilot report date |
| **Taxonomy expansion (OPS-3)** — 44 topics approved by Dok/Sheena/Dev0; execution held post-pilot. Shipping robot still runs 35 topics; pilot brain runs 34. | Three different topic counts are live in three places. | Dev0 + Sheena → Pao | Before the next corpus onboarding |
| **`corpus/prompts/` referenced but absent** — `README.md` documents it; `corpus/MANIFEST.md` records its removal as superseded. | An engineer following the README looks for a directory that does not exist. | Pao | Next README pass |
| **`CLAUDE.md` is stale** — the repo's stated navigational entry point still describes a **May 30, 2026** demo target, wake phrase **"Hey CJ"** on `models/hey_cj.onnx` at **threshold 0.40**, and "not a robot embodiment". Live config is `hi_see_jap.onnx` at **0.08** on a shipped Reachy Mini. | It is the first file any engineer or coding agent reads, and it contradicts the running system on the wake word — the one component with an unmet release gate. | Pao | Before the repo is handed to another engineer |
