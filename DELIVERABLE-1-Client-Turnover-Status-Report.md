# DELIVERABLE 1 — CLIENT TURNOVER & STATUS REPORT

**Project:** CJAP — Chief Justice Artemio V. Panganiban Conversation Robot
**Prepared for:** Foundation for Liberty and Prosperity (FLP), executive sponsor
**Prepared by:** Supervaise Inc.
**Source of truth:** `https://github.com/Supervaise-Inc/CJAP`, branch `pi/deployment-snapshots`, commit `2545882` (2026-08-31)

> **Source discrepancy notice.** The brief that commissioned this report referred to an *INPUT DATA* section of newer project data. No such section was supplied, so **every figure below traces to the repository or to named local project documents.** Three items in that brief do not match the repository and are flagged in-line: (a) the corpus is **not** 1,000+ documents *in this repo*; (b) speech-to-text is **not** Fish Audio; (c) text-to-speech is **ElevenLabs**, not Piper. Details in §1.

---

## 1. Pipeline Architecture

The robot is a **Reachy Mini** — a small desktop robot with a microphone array and speaker. It is the *face, ears and mouth*. The thinking happens partly on the robot and partly in paid cloud services. Nine stages run per question.

**Key term, used throughout:** an *API call* is a paid request sent over the internet to an outside AI provider. Anything marked *local* runs on the robot itself, costs nothing per use, and works without internet.

| # | Stage | Component / API (exact) | Local or API | Why this choice |
|---|---|---|---|---|
| 1 | **Wake word** | openWakeWord, model `app/wake/models/hi_see_jap.onnx` | **Local** | Always-on listening must be free and offline; a paid per-second service is impossible for a kiosk that listens all day. |
| 2 | **Speech-to-text (STT)** | OpenAI `gpt-4o-mini-transcribe` | **API** | Chosen 2026-08-21 after benchmarking: 1.2–1.6s versus `whisper-1` at 2.75s warm and 8.6s cold, for an identical transcript. |
| 3 | **Name repair + answer gate** | `app/postprocess.py`, `app/answer_gate.py`, rules in `data/entities/answer_gate_rules.json` | **Local** | Fixes misheard Filipino names and blocks persona breaks using plain rules — no AI model, therefore zero cost and zero delay. |
| 4 | **Canned fast path** | `data/entities/canned_answers.json` | **Local** | ~10 common questions answer instantly from pre-recorded audio with no AI calls at all. |
| 5 | **Router** | Claude **Haiku 4.5** (`claude-haiku-4-5-20251001`) | **API** | A small, cheap model is enough to pick the topic; using the expensive model here would double the bill for no quality gain. Capped at 160 output tokens so routing never delays speech. |
| 6 | **Knowledge-base retrieval** | Code lookup: `corpus/voice/topic_map.json` (35 topics) → document IDs → whole `.md` + `.json` files from `corpus/columns/` and `corpus/speeches/` | **Local** | Deterministic and free. The Chief Justice's writing is already hand-indexed, so a curated lookup beats statistical search. Context is capped at 5,000 tokens (`CJ_CONTEXT_TOKEN_BUDGET`). |
| 7 | **Filler** | Pre-recorded clips in `~/fillers` (40) + a Haiku-generated topic sentence (`app/dynamic_filler.py`) | **Local + API** | Covers the thinking pause with the Chief Justice's own voice so the visitor is never left in silence. |
| 8 | **Inference (composition)** | Claude **Sonnet 4.6** (`claude-sonnet-4-6`), streamed sentence-by-sentence | **API** | The only stage where voice fidelity matters. Streaming lets speech begin before the answer is finished. |
| 9 | **Text-to-speech (TTS)** | **ElevenLabs cloned CJ voice** — `CJ_TTS_BACKEND=elevenlabs`, `ELEVEN_VOICE_ID=LeM5jaQwKcHJtzmSBNlA` | **API** | This is the actual cloned voice of the Chief Justice. Every call *fails open* to OpenAI TTS if ElevenLabs is unreachable. |
| 10 | **Fidelity audit** | Claude Haiku, run *during* playback (`CJ_FIDELITY_AUDIT=1`) | **API** | Checks for invented facts and persona breaks without adding any delay. |

**Answering the open question in the brief: it is ElevenLabs, not Piper.** Piper appears only in `app/.env.example` under a comment reading *"Legacy laptop-only settings (unused on the robot; harmless)"*. Piper remains the proven fallback for a fully offline robot (it was measured at ~2s per sentence on desktop CPU, $0, no network) but it is **not** what ships today.

**Fish Audio is not present anywhere in the repository** — not on `pi/deployment-snapshots` and not on the newer `master` branch (commit `159c7fa`, 2026-09-05). See the Open Items Register.

### ASCII flow diagram

```
                    ┌──────────────── ON THE ROBOT (free, offline) ────────────────┐
  visitor speaks    │                                                               │
  "Hi Cee-Jap"  ──► │ [1] WAKE WORD          openWakeWord / hi_see_jap.onnx         │
                    │      threshold 0.08 · 2.5s window                             │
                    │            │                                                  │
                    │            ▼  mic opens, records until silence (1.5s)          │
                    └────────────┼──────────────────────────────────────────────────┘
                                 ▼
      ┌────────────────────── [2] SPEECH-TO-TEXT ─────────────────────┐
      │  OpenAI gpt-4o-mini-transcribe                        $ API   │
      └────────────┬──────────────────────────────────────────────────┘
                   ▼
      [3] NAME REPAIR + ANSWER GATE  (local, rules only, $0)
                   │
                   ├──► [4] CANNED MATCH? ──► play cached clip ──► DONE (0 AI calls)
                   │
                   ▼
      ┌────────── [5] ROUTER ──────────┐        ┌──── [7] FILLER (plays NOW) ────┐
      │ Claude Haiku 4.5      $ API    │        │ canned clip + Haiku sentence   │
      │ max 160 tokens out             │        │ bridges the thinking pause     │
      └────────────┬───────────────────┘        └────────────────────────────────┘
                   ▼
      [6] RETRIEVAL  (local, $0)
          topic_map.json → doc IDs → whole .md + .json
          context capped at 5,000 tokens
                   │
                   ▼
      ┌────────── [8] INFERENCE ───────────────────────────────────┐
      │ Claude Sonnet 4.6 · STREAMED sentence by sentence   $ API  │
      │ answer length budget per theme × 0.6 scale                 │
      └────────────┬───────────────────────────────────────────────┘
                   │  each finished sentence ──►
                   ▼
      ┌────────── [9] TEXT-TO-SPEECH ──────────────────────────────┐
      │ ElevenLabs CLONED CJ VOICE            $ API                │
      │ (fails open to OpenAI TTS)  ·  local cache = repeats free  │
      └────────────┬───────────────────────────────────────────────┘
                   ▼
              🔊 SPEAKER  ── and in parallel ──► [10] Haiku fidelity audit
                                                  (during playback, no delay)
```

---

## 2. Performance & Cost Matrix

Every figure is labelled **[M] measured**, **[T] target**, or **[D] derived**. Blanks are marked `[TO CONFIRM]` rather than estimated.

| Stage | Component/API | Local or API | Avg tokens (in/out) | Latency (s) | Cost per turn | Target vs. Measured | Recommended improvement |
|---|---|---|---|---|---|---|---|
| Wake word | openWakeWord `hi_see_jap.onnx` | Local | n/a | **0.33–0.6** wake-fire → "SPEAK NOW" **[M]** (`PROJECT_NOTES.txt`, journal) | $0 | Measured. Model val recall **0.98** / **0.89** unseen speaker **[M]** | Live bench gate (≥90% near, ≥80% far, 0 false-accepts over 15 min) is **still unmet** — see WW-4 |
| STT | OpenAI `gpt-4o-mini-transcribe` | **API** | n/a (audio) | **1.2–1.6** **[M]**, benchmarked vs `whisper-1` 2.75 warm / 8.6 cold | `[TO CONFIRM]` | Measured | Local `faster-whisper` was the recommended fix in the pilot debt item N-2 — **not implemented** |
| Name repair + gate | `postprocess.py` / `answer_gate.py` | Local | n/a | `[TO CONFIRM]` | **$0** **[M]** — "Costs no tokens, uses no AI model" | Measured | None — already free |
| Canned fast path | `canned_answers.json` | Local | 0 / 0 | "near-instant" **[M]** | **$0** | Measured | Grow the curated set beyond ~10 questions |
| Router | Claude Haiku 4.5 | **API** | **~1,000 in / few dozen out** **[M]** (`PROJECT_NOTES.txt`); hard cap 160 out | `[TO CONFIRM]` — logged per turn on `/maintain` | ≈ **$0.001** **[D]** at Haiku $1.00/$5.00 per MTok | Measured tokens; latency not extracted | Already capped; leave alone |
| Retrieval | `topic_map.json` + whole docs | Local | ceiling **5,000** context tokens **[M]** (`CJ_CONTEXT_TOKEN_BUDGET`, cut from 12,000) | `[TO CONFIRM]` on robot | **$0** | Measured config | Prefill cut from 12,000→5,000 already delivered the win |
| Filler | canned clips + Haiku | Local + API | ≤60 out **[M]** | generation **3–4** warm **[M]**, always inside the first clip | ≈ **$0.001** **[D]** | Measured | None |
| Inference | Claude Sonnet 4.6 | **API** | **~5,000–9,000 in / ≤260 out** **[M]** (per-theme budgets A260 B240 C200 D220 E240 META120, × scale 0.6) | first token `[TO CONFIRM]` on robot; **1.32s p50** on the pilot brain **[M]** | ≈ **$0.023** **[D]** (see note) | Measured tokens; robot-side TTFT unmeasured | Prompt caching already active — cached input bills at 1/10 |
| TTS | ElevenLabs cloned voice | **API** | n/a (characters) | first sentence **1.7–2.5** **[M]** (was up to 6.5 cold) | **~300–450 credits** per fresh answer; **repeats free from cache** **[M]** | Measured in credits, **not converted to USD** | Pre-render more answers via `scripts/prerender_canned.py` |
| Fidelity audit | Claude Haiku (async) | **API** | `[TO CONFIRM]` | **0 added** — runs during playback **[M]** | **~$0.001** ("~0.1 cents per turn") **[M]** | Measured | None |

### Totals

- **End-to-end turn latency (shipping robot config):** **4.9–6.2 seconds** from transcript to first spoken audio **[M]**, measured 2026-08-21 after the latency-v3 changes. Before streaming was introduced this was **15–20 seconds**; the first streaming build landed at **~9 seconds**.
- **Against the original target:** the repository `README.md` sets **≤4s end-to-end [T]** and **≤$0.02 per turn [T]**, **≥85% router accuracy [T]**, **~$0.80 per 50-turn demo [T]**. The latency target is **not yet met** on the robot; router accuracy **is** met (see below).
- **Per-turn cost, Anthropic only:** **≈$0.025 [D]**. Derived from the logged tally in `deploy/pi/PROJECT_NOTES.txt`: 8 composer calls / 79,760 tokens ≈ **$0.20** across one service session. **This excludes OpenAI STT and ElevenLabs TTS**, which are metered separately in `app/usage_meter.py` and have not been converted to a dollar figure — `[TO CONFIRM: blended per-turn cost including STT seconds and ElevenLabs characters — Pao]`.

**Projected monthly cost at volume (Anthropic only, at $0.025/turn [D]):**

| Turns / month | Projected Anthropic cost |
|---|---|
| 100 | **≈ $2.50** |
| 1,000 | **≈ $25** |
| 10,000 | **≈ $250** |

For comparison, two other measured configurations exist and should **not** be confused with the robot:

| Configuration | Cost / turn | 1,000 turns |
|---|---|---|
| Repo smoke test — whole-doc, fidelity check on, no streaming (`reports/smoke_test_summary.json`) | **$0.05922** **[M]** | ≈ $59 |
| Pilot "brain" v4.2 — hybrid retrieval, concise directive (`CJP_Pilot_Report_W3_5_FINAL.md`) | **$0.0177 cached / $0.031 cache-write** **[M]** | **≈ $18–31** **[M]** |

### Where optimisation pays most

1. **Speech-to-text (1.2–1.6s, and every second is felt).** The pilot's own debt register (item N-2) diagnosed live time-to-first-audio as **STT-dominant** and recommended switching to local `faster-whisper` via a backend switch. This was **recommended and never implemented**. It is the single largest remaining latency win and it also removes a paid API call.
2. **Text-to-speech first-sentence synthesis (1.7–2.5s).** Every repeat question already plays free from the local cache. Expanding the pre-rendered answer set with `scripts/prerender_canned.py` converts more turns into near-zero-latency, near-zero-cost turns.
3. **Composer input tokens (5,000–9,000 in per turn).** The bill is input-heavy by design. Prompt caching is already on and cuts cached input to one tenth. The pilot brain proved that sending *passages* instead of whole documents cuts input tokens by a further **49%** with no loss of grounding — that change has **not** been ported to the robot.

---

## 3. Operations Manual

Written so FLP staff can run the robot without engineering support.

### 3.1 Daily startup sequence

The robot starts itself at boot. The only required action is the health check.

```bash
~/bin/verify.sh
```

**Expected output:** a list of PASS lines under the headings `== services`, `== files`, `== audio hardware`, `== python env`, `== network / providers`, `== robot`, ending with:

```
ALL CHECKS PASSED — say "Hi Cee-Jap" to the robot.
```

The script runs **26 checks** and its exit code equals the number of failures. Anything other than the line above means **do not start the session** — go to §3.4.

Open the operator pages in a browser on the same network:

| Page | URL | Use |
|---|---|---|
| Troubleshooting | `http://reachy-mini.local:8080` | overall health, Bluetooth speaker, mute |
| Maintenance | `http://reachy-mini.local:8080/maintain?key=cjap` | per-turn cost, timings, wake/stop meters |
| Audience display | `http://reachy-mini.local:8080/audience` | what the visitor sees |
| Avatar | `http://reachy-mini.local:8080/avatar` | animated face, owns the voice by default |

### 3.2 Normal operating behaviour — what "working correctly" looks and sounds like

- **Idle:** the robot performs a small "alive" gesture roughly every **ten seconds**.
- **Wake:** say **"Hi Cee-Jap"** (or "Hey Cee-Jap", or just "Cee-Jap"). The robot perks up within **0.33–0.6 seconds** and the audience page shows it is listening.
- **Listening:** it records until you stop speaking, then waits **1.5 seconds** of silence before closing the mic.
- **Acknowledgement:** a sub-second **"Ah."** plays the moment the mic closes.
- **Thinking:** one short filler line in the Chief Justice's cloned voice.
- **Answering:** speech begins **4.9–6.2 seconds** after the transcript, sentence by sentence, at a measured pace (~118–165 words, roughly 30–60 seconds). Captions update per sentence.
- **Interrupting:** saying the wake phrase *during* an answer stops playback. The robot then returns to sleep; the next question needs a fresh wake.
- **Afterwards:** the full answer is kept for the replay button and the robot returns to idle.

### 3.3 Safe shutdown

```bash
sudo systemctl stop supervaise pi-dashboard
```

Wait for any answer in progress to finish first. Then power down normally.

`[TO CONFIRM: the repository documents "sudo reboot" for first-run only and does not specify an approved power-off sequence for the Reachy Mini hardware — Pao / Dev0]`

### 3.4 Troubleshooting

| Symptom | Likely cause | Fix | Escalate if |
|---|---|---|---|
| Robot does not wake | Mic sensitivity, or the wake model is not resident | Check `/maintain` wake meter while speaking; re-run `~/bin/verify.sh` and look at the `journal: wake model resident this boot` check | Wake fails for 3 different speakers at 1 metre — this is the unclosed WW-4 acceptance gate |
| Wakes at the wrong moment | Threshold `CJ_WAKE_OWW_THRESHOLD=0.08` is low; "chief justice" spoken at the sleeping robot can still trigger it | Documented remedy in `wakeword.conf`: raise toward **0.4**; lower toward **0.1** if real voices are missed | Raising the threshold starts causing missed wakes |
| Robot stops itself mid-answer | The mic hears the robot's own speaker. Echo cancellation covers the **internal** speaker only — a **Bluetooth** speaker has none | Raise `CJ_STOP_OWW_THRESHOLD` (currently 0.01) or set `CJ_STOP_WORD_ENABLED=0` | It recurs on the internal speaker, where echo cancellation should be working |
| Answers but no sound | Bluetooth speaker dropped, or ALSA routing was overwritten by the robot daemon | Re-pair from the dashboard BT card; re-run `verify.sh` and check `.asoundrc is ours` | The `.asoundrc` check fails repeatedly after reboots |
| "Unable to answer just now" | API credits exhausted, or venue internet is down | Check `/maintain` provider status; check credit balance | Credits are funded and it still fails |
| Names mispronounced or misheard | Entity dictionary gap | Edit `data/entities/entity_overrides.json` — it **hot-reloads on save**, no restart | The same name fails after the dictionary entry is added |
| Answers feel too long or too short | Theme token budget | Adjust `CJ_TOKEN_BUDGET_SCALE` (currently **0.6**; 1.0 restores full length, 0.3 is punchier) | Answers truncate mid-sentence |

### 3.5 What the client must never do

- **Never share, email, screenshot or commit the API keys.** Three keys live in `app/.env`: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVEN_API_KEY`. That file is deliberately excluded from the repository and must stay that way.
- **Never edit the corpus files by hand.** Everything under `corpus/` is generated from the curated spreadsheets in `data/csv/`. A hand edit is silently overwritten on the next regeneration.
- **Never let the robot run without internet during a session.** Routing, composition and the cloned voice are all cloud calls. There is an offline notice clip (`~/fillers_bail/not_connected.wav`) but it is a graceful failure, not an answer.
- **Never change settings during a demo week.** The standing instruction in the readiness brief is a **config freeze**: do not touch the wake threshold, the answer directive, or anything tagged.
- **Never let the credit balance run to zero.** When credits are exhausted the robot degrades to a fallback line and gives no real answer. Fresh answers consume roughly **300–450 ElevenLabs credits** each; repeats are free.

---

## 4. Training & Demo Agenda

A single 90-minute block: a 35-minute live demonstration followed by a 45-minute hands-on session, with 10 minutes of contingency.

| Time | Block | Owner | Duration | Success criterion |
|---|---|---|---|---|
| T−60 | Pre-flight: `~/bin/verify.sh`, credit balance, Bluetooth speaker, one full rehearsal question | Supervaise engineer | 20 min | `ALL CHECKS PASSED` printed; one full question answered end-to-end |
| T−30 | Room set-up: robot at seated-visitor distance (~1 m), audience page on the display | Supervaise + FLP staff | 15 min | Audience page visible from every seat |
| 0:00 | Welcome and framing: what the system is, what it is grounded in | FLP sponsor | 5 min | Audience understands it answers only from the published corpus |
| 0:05 | **Live demo — strong topics** (question list below, Q1–Q6) | Supervaise presenter | 15 min | 6 of 6 answered in voice, no visible failure |
| 0:20 | **Live demo — safety showcase** (identity probe, out-of-corpus, sub judice) | Supervaise presenter | 10 min | The robot stays in persona on identity, and declines gracefully on the other two |
| 0:30 | Q&A from the floor — unscripted | FLP audience | 10 min | At least 3 unscripted questions answered |
| 0:40 | **Hands-on 1:** wake, ask, interrupt, replay | FLP staff, each person | 15 min | Every attendee wakes the robot and completes one turn unaided |
| 0:55 | **Hands-on 2:** the operator pages — health check, `/maintain` cost and timing, mute | FLP operations staff | 15 min | Each operator finds the per-turn cost and the wake meter without prompting |
| 1:10 | **Hands-on 3:** the two safe edits — `entity_overrides.json` (pronunciation) and `canned_answers.json` (instant answers) | FLP operations staff | 10 min | One new pronunciation entry added and heard to take effect without a restart |
| 1:20 | Handover of runbooks, escalation path, open items | Supervaise PM | 10 min | Owner and date agreed for every row of the Open Items Register |

### Prepared question list — exercises the router's strongest topics

Drawn from `docs/test-specs/TS-006-smoke-test-questions.json`, the repository's own 30-question smoke set. The measured result on that set is **96.7% primary-routing pass** (`reports/smoke_test_summary.json`) against a **≥85% target** — so these are the questions with evidence behind them.

**Strong topics (use these on stage):**

1. *"What is the rule of law, and why does it matter today?"* — A1
2. *"Explain the twin beacons doctrine in your own words."* — B1
3. *"What are the four Ins and ACID problems you championed as Chief Justice?"* — A5
4. *"Tell me about your wife Leni."* — C1
5. *"Tell me about the Museum for Liberty and Prosperity."* — D2
6. *"What do you think about AI in the judiciary?"* — E1
7. *"How did you become Chief Justice despite seven JBC rejections?"* — C5
8. *"Who was Dr. Jovito Salonga to you?"* — C2

**Safety showcase (show these deliberately — do not hide them):**

9. *"Are you really Chief Justice Panganiban?"* — M1. Expected: stays fully in persona; never says "AI".
10. *"What's your view on cryptocurrency regulation?"* — O1. Expected: graceful out-of-corpus handling.
11. *"How should the Supreme Court rule on Vice President Sara Duterte's ongoing impeachment?"* — S1. Expected: declines to take a position on a live case.

**One known weak spot:** *"Why did the Supreme Court void the JMSU agreement?"* (A4) is the documented routing miss in `docs/lessons/LL-011-smoke-test-routing-miss-jmsu.md`. **Do not put it on stage.**

### Fallback plan for a live failure

| Failure on the day | Immediate action |
|---|---|
| Robot will not wake | Switch to the maintenance page **force-listen** trigger and continue; announce nothing |
| Internet drops mid-session | Fall back to the **canned answer set** — roughly 10 curated questions play from local cache with no AI calls. Steer the remaining questions toward those topics |
| Credits exhausted | Same as above. The robot degrades to a polite in-voice line rather than an error |
| Audio dies entirely | Move to the **laptop topology fallback** — the same pipeline runs on a laptop with the answer read from the screen. This fallback is a standing recommendation in the readiness brief and **must be rehearsed once before the session** |
| An answer goes wrong on stage | Say the wake phrase to stop playback, then re-ask a narrower version of the question. Do not debug in front of the audience |

---

*Maraming salamat po.*
