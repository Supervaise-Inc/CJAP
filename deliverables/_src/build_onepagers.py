"""Four single-A4-page one-pagers for the CJAP handover."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand as B
from docx import Document
from docx.shared import Pt, Inches

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "deliverables")
COMMIT = "pi/deployment-snapshots @ 2545882"

REPO_SRC = ("CJAP repo " + COMMIT + " — app/.env.example, "
            "deploy/pi/systemd/supervaise.service.d/wakeword.conf, "
            "deploy/pi/PROJECT_NOTES.txt, app/usage_meter.py, corpus/MANIFEST.md")
PILOT_SRC = ("CJP_Pilot_Report_W3_5_FINAL.md, CJP_Latency_Cost_Assessment.md, "
             "CJP_Readiness_Verdict_Brief.md [source: pilot brain repo — "
             "not reproducible from this handover]")


def newdoc(margin=0.55):
    d = Document()
    B.setup_page(d, a4=True, margin=margin)
    return d


def est_height(doc, text_width=7.17, mono_ratio=0.601, prop_ratio=0.478):
    """Printed-height estimate in inches, using real column widths.

    Character width is approximated as ratio * font-size (Consolas is a fixed
    0.60 em; Calibri averages ~0.48 em for mixed-case prose). Line height is
    1.17 * font size. Cell padding is the 40/80 dxa set in brand.cell_margins.
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.ns import qn

    def par_h(p, avail_in, default_size=11.0):
        runs = p.runs
        if runs and any(r.element.findall(qn("w:drawing")) for r in runs):
            for r in runs:                                     # read real extent
                for ext in r.element.iter():
                    if ext.tag.endswith("}extent"):
                        return int(ext.get("cy")) / 914400.0 + 0.12
            return 4.2 * 347 / 2048 + 0.12
        if not p.text.strip():
            return 0.10
        size = max([(r.font.size.pt if r.font.size else default_size) for r in runs]
                   or [default_size])
        mono = any((r.font.name or "") == B.MONO_FONT for r in runs)
        cw = size * (mono_ratio if mono else prop_ratio) / 72.0
        cpl = max(int(avail_in / cw), 8)
        lines = max(1, -(-len(p.text) // cpl))
        sa = (p.paragraph_format.space_after.pt if p.paragraph_format.space_after
              else 4.0)
        sb = (p.paragraph_format.space_before.pt if p.paragraph_format.space_before
              else 0.0)
        return lines * size * 1.17 / 72.0 + (sa + sb) / 72.0

    h = 0.0
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            h += par_h(Paragraph(child, doc), text_width)
        elif child.tag == qn("w:tbl"):
            t = Table(child, doc)
            for row in t.rows:
                widths = []
                for c in row.cells:
                    widths.append(c.width.inches if c.width else
                                  text_width / max(len(row.cells), 1))
                row_h = 0.0
                for c, w in zip(row.cells, widths):
                    inner = max(w - 0.14, 0.4)                 # 80 dxa L+R
                    ch = sum(par_h(p, inner, default_size=9.0) for p in c.paragraphs)
                    row_h = max(row_h, ch)
                h += row_h + 0.056                             # 40 dxa T+B
    return h


# =========================================================== 1. PIPELINE
def pipeline():
    d = newdoc()
    B.onepager_head(
        d, "CJAP — Technical Pipeline",
        "How one visitor question travels through the system as built, and what "
        "each stage falls back to when it fails.")

    diagram = r"""
   VISITOR        ▌ ON-ROBOT · local · $0          ▌ CLOUD · paid per call
 ────────────────▌──────────────────────────────── ▌───────────────────────────
 "Hi Cee-Jap" ──►▌[1] WAKE  openWakeWord           ▌
                 ▌    hi_see_jap.onnx · thr 0.08   ▌
  asks question ►▌[2] CAPTURE  mic → 1.5s silence ─▌─► [3] STT  OpenAI
                 ▌                                 ▌      gpt-4o-mini-transcribe
                 ▌[4] REPAIR + ANSWER GATE  ◄───────▌──────────┘
                 ▌[5] CANNED? ─yes─► cached clip ─► END (zero Claude calls)
                 ▌     │ no                        ▌
                 ▌     ├───────────────────────────▌─► [6] ROUTER  ══ CALL 1
                 ▌     │                           ▌      Claude Haiku 4.5
                 ▌[7] RETRIEVAL  35 topics → docs  ▌      max 160 tokens out
                 ▌     │  context ≤ 5,000 tokens   ▌
                 ▌[8] FILLER plays ────────────────▌─► [9] INFERENCE ══ CALL 2
                 ▌     │      sentence by sentence  ▌      claude-sonnet-4-6
                 ▌     │                           ▌─► [10] TTS  ElevenLabs
                 ▌     │                           ▌      LeM5jaQwKcHJtzmSBNlA
  ◄── PLAYBACK ──▌─────┘  + async Haiku audit      ▌      fails open ► OpenAI
""".strip("\n")
    B.code_block(d, diagram, size=7.0)

    B.para(d, "**Two Claude calls per turn: Call 1 — router**, Claude Haiku 4.5 "
              "(`claude-haiku-4-5-20251001`), capped at 160 output tokens. "
              "**Call 2 — inference**, Claude Sonnet 4.6 (`claude-sonnet-4-6`), streamed. "
              "The dynamic filler and the fidelity audit are two further Haiku calls, both "
              "off the critical path.", size=9, space_after=3)

    rows = [
        ["Stage", "Component / API (verbatim)", "Fallback behaviour"],
        ["1–2 Wake + capture · local",
         "openWakeWord `app/wake/models/hi_see_jap.onnx`; `CJ_MIC_TRAILING_SILENCE_S=1.5`",
         "Operator force-listen from `/maintain`; captures under `CJ_VAD_MIN_SPEECH_S=0.4` discarded"],
        ["3 STT · **API**", "OpenAI `gpt-4o-mini-transcribe`",
         "No failover. A local backend exists as a config switch (`LOCAL_STT_MODEL`), never wired"],
        ["4–5 Gates + canned · local",
         "`app/postprocess.py`, `app/answer_gate.py`, `canned_answers.json`",
         "Both fail open; no canned match → normal path"],
        ["6 Router · **API**", "Claude Haiku 4.5",
         "Truncated JSON → anchor routing; keep `CJ_ROUTER_MAX_TOKENS` ≥ ~140"],
        ["7 Retrieval · local", "`corpus/voice/topic_map.json` → whole `.md` + `.json`",
         "Zero docs but in scope → theme-level fallback documents"],
        ["8 Filler · local + API", "`~/fillers` clips + Haiku sentence",
         "Silent-open — canned clips keep playing"],
        ["9 Inference · **API**", "Claude Sonnet 4.6, streamed",
         "`INFERENCE_MODEL` switchable to Haiku; credit or network loss → in-voice degraded line"],
        ["10 TTS · **API**", "ElevenLabs clone `LeM5jaQwKcHJtzmSBNlA`",
         "Fails open to OpenAI TTS; repeats free from `~/.voice_cache`"],
        ["11 Audit · **API**", "Claude Haiku, asynchronous",
         "Fails open (all-false); the composer is the primary safety surface"],
    ]
    B.table(d, rows, size=7.3, widths=[1.32, 2.45, 3.33])

    B.para(d, "Offline, `~/fillers_bail/not_connected.wav` plays instead of an answer. "
              "Piper appears only in `app/.env.example` under “Legacy laptop-only settings "
              "(unused on the robot; harmless)” — not in the live path.",
           size=8.2, space_after=2)

    B.sources_status(
        d, REPO_SRC,
        "**Confirmed:** every component, model ID and fallback above is read from the "
        "repository at the stated commit. **Open:** on-robot per-stage latency is logged "
        "to `/maintain` but has never been summarised — `[TO CONFIRM: p50/p95 per stage on "
        "the robot | owner: Pao]`.")
    return d, "CJAP_OnePager_Pipeline.docx"


# ================================================== 2. COST AND CORPUS
def cost():
    d = newdoc()
    B.onepager_head(
        d, "CJAP — Cost, Tokens & Knowledge Base",
        "What one turn costs, what is metered, and what the curated corpus actually "
        "contains in this repository.")

    rows = [
        ["Stage", "Model / Service", "Avg tokens in/out", "Metered?",
         "Cost per turn", "Target vs. Measured"],
        ["Wake", "openWakeWord (on-device)", "n/a", "No", "$0", "**Measured** — local"],
        ["STT", "OpenAI `gpt-4o-mini-transcribe`", "n/a (audio)",
         "Yes — `stt_calls`, `stt_seconds`", "`[TO CONFIRM]`",
         "**Measured** latency 1.2–1.6 s; cost never converted"],
        ["Router", "Claude Haiku 4.5", "~1,000 in / few dozen out",
         "Yes — 4 buckets", "≈$0.001 **derived**", "**Measured** tokens"],
        ["Retrieval", "`topic_map.json` + whole docs", "≤5,000 context", "No", "$0",
         "**Measured** config ceiling"],
        ["Filler", "Claude Haiku", "≤60 out", "Yes", "≈$0.001 **derived**",
         "**Measured** 3–4 s generation"],
        ["Inference", "Claude Sonnet 4.6", "~5,000–9,000 in / ≤260 out",
         "Yes — 4 buckets", "≈$0.023 **derived**", "**Measured** tokens"],
        ["TTS", "ElevenLabs clone", "~300–450 credits (fresh); repeats free",
         "Yes — `chars`, `cache_hits`", "`[TO CONFIRM]`",
         "**Measured** in credits, not dollars"],
        ["Audit", "Claude Haiku (async)", "`[TO CONFIRM]`", "Yes",
         "≈$0.001 (“~0.1 cents”)", "**Measured**"],
        ["**TOTAL**", "**Anthropic only**", "—", "—", "**≈$0.025 derived**",
         "Against a **Target** of ≤$0.02/turn"],
    ]
    B.table(d, rows, size=7.3, widths=[0.62, 1.32, 1.45, 1.08, 1.02, 1.6])

    B.callout(d, "**The blended per-turn cost is `[TO CONFIRM: convert OpenAI STT seconds "
                 "and ElevenLabs characters to USD and add to the $0.025 Anthropic figure | "
                 "owner: Pao]`.** The $0.025 above is Anthropic only, derived from the logged "
                 "tally in `deploy/pi/PROJECT_NOTES.txt` (8 composer calls / 79,760 tokens ≈ "
                 "$0.20). All three providers are metered in `app/usage_meter.py`; none of the "
                 "non-Anthropic meters has been priced. Do not quote a total turn cost to the "
                 "client until this is closed.", size=8.6)

    B.heading(d, "Knowledge base in this repository", level=3, space_before=5)
    B.para(d, "**79 documents curated and ingested** — 64 *With Due Respect* columns and 15 "
              "speeches, each a paired `.md` (YAML front-matter + canonical text) and `.json` "
              "(routing, entities, stances, signature phrases, anecdotes). One biography row "
              "(`GC001`) was deliberately skipped: no single publication date, and the spec "
              "forbids placeholder dates. The curation pipeline read a 15-column schema from "
              "`data/csv/`, matched source text from `data/text/`, and emitted "
              "`reports/generation_report.json`. **Topic map: 35 curated topics** across four "
              "tiers in `corpus/voice/topic_map.json`, with per-document `topic_paths` "
              "backfilled.", size=9.3, space_after=3)

    B.table(d, [
        ["Volume (turns/month)", "100", "1,000", "10,000"],
        ["Anthropic only, at $0.025/turn **derived**", "≈$2.50", "≈$25", "≈$250"],
        ["Pilot brain v4.2, measured $0.0177–$0.031", "≈$1.80–$3.10", "≈$18–$31", "≈$180–$310"],
        ["Blended (incl. STT + ElevenLabs)", "`[TO CONFIRM]`", "`[TO CONFIRM]`", "`[TO CONFIRM]`"],
    ], size=7.8, widths=[2.9, 1.3, 1.3, 1.5])

    B.sources_status(
        d, REPO_SRC + " · " + PILOT_SRC,
        "**Confirmed:** 79 documents, 35 topics, per-stage token counts, Anthropic pricing "
        "table. **Open:** blended per-turn cost; ElevenLabs credit-to-dollar conversion. "
        "The 1,109-document / 9,865-chunk corpus belongs to the pilot brain repo and is "
        "**not** in this handover.")
    return d, "CJAP_OnePager_Cost_and_Corpus.docx"


# ================================================ 3. ROBOT OPERATION
def robot():
    d = newdoc()
    B.onepager_head(
        d, "CJAP — Runtime & Operating Cycle",
        "The robot's turn cycle with its timeout, barge-in and error path at each step — "
        "and the untethered-runtime gap.")

    B.heading(d, "Operating cycle", level=3, space_before=2)
    rows = [
        ["Step", "Enters when", "Timeout / barge-in / error path", "Duration"],
        ["Idle", "Boot, or previous turn ended",
         "Alive gesture every 10 s. No timeout. Service auto-starts at boot",
         "**Measured** — indefinite"],
        ["Wake detected", "openWakeWord score ≥ `CJ_WAKE_OWW_THRESHOLD=0.08` in a 2.5 s window",
         "Cooldown `CJ_WAKE_COOLDOWN_S=0.1`. Miss → operator force-listen from `/maintain`",
         "**Measured** 0.33–0.6 s to “SPEAK NOW”"],
        ["Listening", "Immediately after wake",
         "Closes after `CJ_MIC_TRAILING_SILENCE_S=1.5` of silence. Captures with "
         "< `CJ_VAD_MIN_SPEECH_S=0.4` of speech are discarded",
         "**Measured** 1.6–3.1 s of real speech"],
        ["Transcribing", "Mic closes; sub-second “Ah.” acknowledgment plays",
         "No automatic STT failover. Network loss → `~/fillers_bail/not_connected.wav`",
         "**Measured** 1.2–1.6 s"],
        ["Routing", "Transcript passes the gate",
         "Truncated router JSON → anchor-routing fallback. Canned match skips this entirely",
         "`[TO CONFIRM: router seconds on robot | owner: Pao]`"],
        ["Generating", "Topics resolved; filler already playing",
         "Filler holds up to `CJ_FILLER_FIRST_WAIT_S=1.2`. Credits exhausted → in-voice "
         "degraded line, no real answer",
         "`[TO CONFIRM: composer TTFT on robot | owner: Pao]`"],
        ["Speaking", "First sentence composed",
         "**Barge-in:** wake phrase at `CJ_STOP_OWW_THRESHOLD=0.01` cuts playback and returns "
         "to sleep. TTS failure → OpenAI TTS fallback",
         "**Measured** first audio 4.9–6.2 s after transcript; first-sentence synth 1.7–2.5 s"],
        ["Return to idle", "Answer completes or is stopped",
         "`CJ_FOLLOWUP_WINDOW_S=0` — follow-up window disabled; next question needs a fresh wake",
         "**Measured** — immediate"],
    ]
    B.table(d, rows, size=7.4, widths=[0.78, 1.65, 3.0, 1.65])

    B.para(d, "**End-to-end, measured:** 4.9–6.2 s from transcript to first spoken audio "
              "(2026-08-21, after the latency-v3 changes; was 15–20 s before streaming). "
              "**Target** in `README.md` is ≤4 s end-to-end — not yet met on the robot.",
           size=9, space_after=3)

    B.heading(d, "Untethered runtime", level=3, space_before=4)
    B.callout(
        d,
        "`[TO CONFIRM: untethered runtime never measured — requires a timed discharge test | "
        "owner: hardware]`\n"
        "No battery capacity, runtime-on-full-charge, recharge time, or idle-vs-active power "
        "figure exists anywhere in the repository. A repository-wide search for battery, "
        "charge, discharge, mAh, watt and power-draw terms returned only corpus prose — no "
        "measurement, no specification, no test record. These figures are deliberately left "
        "blank rather than inferred from component datasheets: a datasheet figure would not "
        "account for the mic array, the wake model running continuously, Bluetooth audio, or "
        "the motors. **Closing this needs one timed discharge test** — full charge, run the "
        "normal turn cycle to shutdown, log wall-clock runtime and turn count, then a timed "
        "recharge.",
        size=8.8, fill="FDE9E9", edge="C00000")

    B.sources_status(
        d, REPO_SRC,
        "**Confirmed:** every threshold, timeout and env var above is verbatim from "
        "`wakeword.conf`; the durations marked Measured are from `PROJECT_NOTES.txt`. "
        "**Open:** router and composer timings on the robot; the entire untethered-runtime "
        "section.")
    return d, "CJAP_OnePager_Robot_Operation.docx"


# ==================================================== 4. UI DESIGN
def ui():
    d = newdoc()
    B.onepager_head(
        d, "CJAP — Application & Maintenance UI",
        "The two operator-facing surfaces: the Streamlit conversation app and the on-robot "
        "maintenance dashboard.")

    wire = r"""
 A. CONVERSATION APP  app/dashboard.py        B. MAINTENANCE DASHBOARD
    Streamlit · laptop · wide layout             deploy/pi/dashboard · :8080 / :8443
 ┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
 │ [sidebar ◄ collapsed]  ⚖ With Due    │    │ /maintain?key=cjap    (key-gated)    │
 │  Settings                 Respect    │    ├──────────────────────────────────────┤
 │  ☑ Voice response                    │    │ ┌Health──────┐ ┌System─────────────┐ │
 │  ☐ TTS chunks (debug)                │    │ │ services   │ │ temp · disk · net │ │
 │  🧹 Clear conversation               │    │ └────────────┘ └───────────────────┘ │
 │  Router / Inference / STT / TTS ids  │    │ ┌Current turn────┐ ┌Stage latency──┐ │
 │  Topics loaded: 35                   │    │ │ cost ¢ · total │ │ gate·route·TTS│ │
 ├──────────────────────────────────────┤    │ └────────────────┘ └───────────────┘ │
 │  ┌ assistant ─────────────────────┐  │    │ ┌Recent turns (tracking)───────────┐ │
 │  │ streamed answer, token by      │  │    │ │ question │ route │ cost │ secs   │ │
 │  │ token (st.write_stream)        │  │    │ └──────────────────────────────────┘ │
 │  │ ▶ ──────────── audio player    │  │    │ ┌Conversation (raw vs corrected)───┐ │
 │  │ ▼ 📚 Sources — rule_of_law     │  │    │ │ NER corrections (P0)             │ │
 │  └────────────────────────────────┘  │    │ └──────────────────────────────────┘ │
 ├──────────────────────────────────────┤    │ ┌Claude┐ ┌OpenAI STT┐ ┌ElevenLabs─┐ │
 │  ⏺ Press to start talking  ⏹ stop    │    │ └──────┘ └──────────┘ └───────────┘ │
 │  … or type your question (fallback)  │    │ ┌Controls┐ ┌Manual actions────────┐ │
 └──────────────────────────────────────┘    │ │ mute   │ │ force listen · say   │ │
                                             │ └────────┘ └──────────────────────┘ │
   other robot pages: /  (troubleshooting)   └──────────────────────────────────────┘
   /audience  /avatar  /event (= /phone)  /notes  /canned-qa  /backup
""".strip("\n")
    B.code_block(d, wire, size=6.6,
                 title="Wireframe from source — not a screenshot. The app cannot be "
                       "launched in this environment: `app/.env` is absent and "
                       "`app/dashboard.py` calls `st.stop()` when `ANTHROPIC_API_KEY` is "
                       "unset. Layout above is read from `app/dashboard.py` and "
                       "`deploy/pi/dashboard/ui_page_maintenance.py`.")

    B.para(d, "**A — Conversation app** (`app/dashboard.py`, Streamlit). *Purpose:* hold a "
              "voice or text conversation in the Chief Justice's persona. *Users:* demo "
              "presenter, reviewer, engineer. *Screens:* one wide page plus a collapsed "
              "settings sidebar. *Actions:* record from the mic (`st.audio_input`); type a "
              "fallback question (`st.chat_input`); watch the answer stream token by token; "
              "replay inline audio; open the **Sources** expander to see routed topics, "
              "confidence, router reasoning and the documents used; toggle voice response "
              "and TTS-chunk debug; clear the conversation. Note this surface synthesises "
              "through **OpenAI TTS**, not the ElevenLabs clone — the sidebar help text "
              "documents it at ~$0.003–$0.005 per turn.", size=8.8, space_after=3)

    B.para(d, "**B — Maintenance dashboard** (`deploy/pi/dashboard/`, a standard-library HTTP "
              "server, not Streamlit). It **does exist as a distinct surface** — "
              "`ui_page_maintenance.py`, 44 KB, served at `/maintain?key=cjap` behind a key "
              "gate. *Purpose:* run and diagnose the robot without a terminal. *Users:* FLP "
              "operations staff and Supervaise engineers. *Cards:* Health · System · Current "
              "turn · Recent turns (tracking) · Stage latency · Conversation (raw vs "
              "corrected) · NER corrections (P0) · Claude (Anthropic) · OpenAI "
              "(speech-to-text) · ElevenLabs (cloned voice) · Controls · Manual actions. "
              "*Actions:* mute, force-listen, make the robot say text, edit the entity "
              "dictionary, adjust tuning, pair a Bluetooth speaker, read live wake and "
              "stop-word meters, download a checkpoint. Sibling pages: `/` troubleshooting, "
              "`/audience`, `/avatar`, `/event` (alias `/phone`), `/notes`, `/canned-qa`.",
           size=8.8, space_after=2)

    B.sources_status(
        d, "CJAP repo " + COMMIT + " — app/dashboard.py, deploy/pi/dashboard/"
           "{ui_routes,ui_page_maintenance,ui_common}.py, deploy/pi/README.md",
        "**Confirmed:** both surfaces exist; every screen, card and action above is read "
        "from source. **Open:** no screenshots — `[TO CONFIRM: capture live screenshots of "
        "both surfaces on a keyed robot | owner: Pao]`. Visual styling, spacing and colour "
        "are not represented in the wireframe.")
    return d, "CJAP_OnePager_UI_Design.docx"


for fn in (pipeline, cost, robot, ui):
    doc, name = fn()
    B.page_number_footer(doc, f"{B.COMPANY} — CJAP handover · {COMMIT}")
    path = os.path.join(OUT, name)
    doc.save(path)
    words = sum(len(p.text.split()) for p in doc.paragraphs)
    print(f"{name:42s} est_height={est_height(doc):5.2f}in  prose_words≈{words}")
