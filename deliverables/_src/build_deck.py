"""CJAP_Handover.pptx — client-facing handover deck, 16:9."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand as B
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "deliverables")
COMMIT = "pi/deployment-snapshots @ 2545882 (2026-08-31)"

DARK = RGBColor(0x2D, 0x2D, 0x2D)
GREEN = RGBColor(0x00, 0xCC, 0x00)
GREY = RGBColor(0x80, 0x80, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
RED = RGBColor(0xC0, 0x00, 0x00)
AMBER = RGBColor(0xBF, 0x90, 0x00)

W, H = Inches(13.333), Inches(7.5)
prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]


def tb(slide, l, t, w, h, text, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT,
       font="Calibri", space_after=4, line=1.0):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.03)
    tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line
        r = p.add_run(); r.text = ln
        r.font.size, r.font.bold, r.font.name = Pt(size), bold, font
        r.font.color.rgb = color
    return box


def bullets(slide, l, t, w, h, items, size=16, color=BLACK, gap=9):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap); p.line_spacing = 1.02
        r0 = p.add_run(); r0.text = "▪  "
        r0.font.size, r0.font.color.rgb, r0.font.name = Pt(size), GREEN, "Calibri"
        # crude bold-marker support: **...**
        parts = it.split("**")
        for j, part in enumerate(parts):
            if not part:
                continue
            r = p.add_run(); r.text = part
            r.font.size, r.font.name = Pt(size), "Calibri"
            r.font.bold = (j % 2 == 1)
            r.font.color.rgb = color
    return box


def rect(slide, l, t, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1.25)
    s.shadow.inherit = False
    s.text_frame.word_wrap = True
    return s


def slide(title, kicker=None):
    s = prs.slides.add_slide(BLANK)
    bar = rect(s, 0, 0, W, Inches(0.92), DARK, shape=MSO_SHAPE.RECTANGLE)
    bar.text_frame.text = ""
    tb(s, Inches(0.55), Inches(0.18), Inches(11.4), Inches(0.5), title,
       size=27, bold=True, color=WHITE)
    if kicker:
        tb(s, Inches(0.55), Inches(0.62), Inches(11.4), Inches(0.3), kicker,
           size=11.5, color=RGBColor(0xC8, 0xE6, 0xC8))
    accent = rect(s, 0, Inches(0.92), W, Inches(0.045), GREEN, shape=MSO_SHAPE.RECTANGLE)
    accent.text_frame.text = ""
    return s


def footer(s, n):
    tb(s, Inches(0.55), Inches(7.06), Inches(9.0), Inches(0.3),
       f"Supervaise Inc. — CJAP handover · repo {COMMIT}", size=8.5, color=GREY)
    tb(s, Inches(12.1), Inches(7.06), Inches(0.75), Inches(0.3), str(n),
       size=9, color=GREY, align=PP_ALIGN.RIGHT)


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def mono(s, l, t, w, h, text, size=10.5, fill=RGBColor(0xF7, 0xF7, 0xF7)):
    bx = rect(s, l, t, w, h, fill, line=RGBColor(0xD0, 0xD0, 0xD0),
              shape=MSO_SHAPE.RECTANGLE)
    tf = bx.text_frame
    tf.margin_left = tf.margin_right = Inches(0.12)
    tf.margin_top = tf.margin_bottom = Inches(0.08)
    tf.word_wrap = False
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = 0; p.line_spacing = 1.0
        r = p.add_run(); r.text = ln
        r.font.size, r.font.name, r.font.color.rgb = Pt(size), "Consolas", BLACK
    return bx


def table(s, l, t, w, h, rows, col_w=None, size=11, head_size=11):
    shp = s.shapes.add_table(len(rows), len(rows[0]), l, t, w, h).table
    if col_w:
        total = sum(col_w)
        for j, cw in enumerate(col_w):
            shp.columns[j].width = Emu(int(w * cw / total))
    for i, row in enumerate(rows):
        shp.rows[i].height = Inches(0.32 if i else 0.36)
        for j, val in enumerate(row):
            c = shp.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.07)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.space_after = 0; p.line_spacing = 0.95
            for k, part in enumerate(val.split("**")):
                if not part:
                    continue
                r = p.add_run(); r.text = part
                r.font.size = Pt(head_size if i == 0 else size)
                r.font.name = "Calibri"
                r.font.bold = (i == 0) or (k % 2 == 1)
                r.font.color.rgb = WHITE if i == 0 else BLACK
            c.fill.solid()
            c.fill.fore_color.rgb = DARK if i == 0 else (
                LIGHT if i % 2 == 0 else WHITE)
    return shp


def callout(s, l, t, w, h, text, fill, edge, size=13, color=BLACK):
    bx = rect(s, l, t, w, h, fill, line=edge, shape=MSO_SHAPE.RECTANGLE)
    tf = bx.text_frame
    tf.margin_left = tf.margin_right = Inches(0.16)
    tf.margin_top = tf.margin_bottom = Inches(0.10)
    tf.word_wrap = True
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5); p.line_spacing = 1.02
        for k, part in enumerate(ln.split("**")):
            if not part:
                continue
            r = p.add_run(); r.text = part
            r.font.size, r.font.name = Pt(size), "Calibri"
            r.font.bold = (k % 2 == 1); r.font.color.rgb = color
    return bx


# ============================================================ 1 TITLE
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, H, DARK, shape=MSO_SHAPE.RECTANGLE).text_frame.text = ""
if os.path.exists(B.BANNER):
    s.shapes.add_picture(B.BANNER, Inches(0.0), Inches(0.0), width=W)
tb(s, Inches(0.9), Inches(2.45), Inches(11.5), Inches(1.2),
   "CJAP — Conversation Robot", size=46, bold=True, color=WHITE)
tb(s, Inches(0.9), Inches(3.45), Inches(11.5), Inches(0.6),
   "Chief Justice Artemio V. Panganiban, in his own voice and corpus",
   size=20, color=RGBColor(0xC8, 0xE6, 0xC8))
rect(s, Inches(0.92), Inches(4.25), Inches(2.2), Inches(0.05), GREEN,
     shape=MSO_SHAPE.RECTANGLE).text_frame.text = ""
tb(s, Inches(0.9), Inches(4.6), Inches(11.5), Inches(1.6),
   "Project handover\n"
   "Supervaise Inc.  →  Foundation for Liberty and Prosperity\n"
   f"Repository: github.com/Supervaise-Inc/CJAP · {COMMIT}\n"
   "20 September 2026",
   size=14, color=WHITE, space_after=6)
tb(s, Inches(0.9), Inches(6.75), Inches(11.5), Inches(0.4),
   f"{B.COMPANY} — {B.TAGLINE}", size=12, color=GREEN)
notes(s, "Handover of the CJAP conversation robot. Everything presented traces to the "
         "repository at the commit on this slide, or to a named pilot document. Figures are "
         "labelled Target or Measured throughout. Slides carrying [TO CONFIRM] are "
         "deliberate: those numbers were never measured and are not estimated here.")

# ============================================== 2 WHAT WAS BUILT
s = slide("What was built", "One sentence, one picture")
tb(s, Inches(0.7), Inches(1.35), Inches(12.0), Inches(0.9),
   "A desktop robot that answers questions as the Chief Justice, "
   "from his published writing.", size=23, bold=True, color=DARK)
y = Inches(2.75)
rect(s, Inches(0.9), y, Inches(2.9), Inches(1.9), RGBColor(0xEF, 0xF7, 0xEF), GREEN)
tb(s, Inches(1.05), Inches(2.95), Inches(2.6), Inches(1.6),
   "REACHY MINI\n\nface · ears · mouth\non-device, offline",
   size=13, color=DARK, align=PP_ALIGN.CENTER)
rect(s, Inches(5.2), y, Inches(2.9), Inches(1.9), LIGHT, GREY)
tb(s, Inches(5.35), Inches(2.95), Inches(2.6), Inches(1.6),
   "CURATED CORPUS\n\n79 documents\n35 topics",
   size=13, color=DARK, align=PP_ALIGN.CENTER)
rect(s, Inches(9.5), y, Inches(2.9), Inches(1.9), RGBColor(0xE8, 0xEF, 0xF9),
     RGBColor(0x4A, 0x6F, 0xA5))
tb(s, Inches(9.65), Inches(2.95), Inches(2.6), Inches(1.6),
   "CLAUDE\n\nHaiku 4.5 routes\nSonnet 4.6 composes",
   size=13, color=DARK, align=PP_ALIGN.CENTER)
for x in (Inches(4.0), Inches(8.3)):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, Inches(3.35), Inches(1.05), Inches(0.5))
    a.fill.solid(); a.fill.fore_color.rgb = GREEN; a.line.fill.background()
    a.shadow.inherit = False
footer(s, 2)
notes(s, "Two paid Claude calls per turn. The voice is a clone of the Chief Justice's "
         "own, licensed through ElevenLabs. The "
         "robot never claims to be a machine and never invents a view he did not publish. "
         "Three parts: the robot is embodiment only; the corpus is the ground truth; Claude "
         "does routing and composition. The persona rule (2026-08-09) is that it answers in "
         "the first person AS the Chief Justice and deflects machinery questions with humour "
         "— it never describes itself as an AI. That is enforced in three places: the voice "
         "card, a zero-cost rule gate before audio exists, and an asynchronous Haiku audit.")

# ============================================ 3 PIPELINE DIAGRAM
s = slide("Pipeline architecture", "One question, end to end · two Claude calls")
mono(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(5.0), r"""
   VISITOR        ▌ ON-ROBOT · local · no cost       ▌ CLOUD · paid per call
 ────────────────▌───────────────────────────────────▌──────────────────────────
 "Hi Cee-Jap" ──►▌ [1] WAKE   openWakeWord           ▌
                 ▌     hi_see_jap.onnx · thr 0.08    ▌
  asks question ►▌ [2] CAPTURE  mic → 1.5s silence ──▌──► [3] STT   OpenAI
                 ▌                                   ▌       gpt-4o-mini-transcribe
                 ▌ [4] NAME REPAIR + ANSWER GATE ◄────▌───────────┘
                 ▌ [5] CANNED? ─yes─► cached clip ─► END  (zero Claude calls)
                 ▌      │ no                         ▌
                 ▌      ├────────────────────────────▌──► [6] ROUTER  ══ CALL 1
                 ▌      │                            ▌       Claude Haiku 4.5
                 ▌ [7] RETRIEVAL  35 topics → docs   ▌       max 160 tokens out
                 ▌      │   context ≤ 5,000 tokens   ▌
                 ▌ [8] FILLER plays ─────────────────▌──► [9] INFERENCE ══ CALL 2
                 ▌      │   sentence by sentence     ▌       claude-sonnet-4-6
                 ▌      │                            ▌──► [10] TTS  ElevenLabs
                 ▌      │                            ▌       LeM5jaQwKcHJtzmSBNlA
  ◄── PLAYBACK ──▌──────┘  + async Haiku audit       ▌       fails open ► OpenAI
""".strip("\n"), size=11.5)
footer(s, 3)
notes(s, "Call 1 is the router (Haiku 4.5, claude-haiku-4-5-20251001), capped at 160 output "
         "tokens because every router token delays speech. Call 2 is the composer (Sonnet 4.6, "
         "claude-sonnet-4-6), streamed sentence by sentence so the robot starts speaking before "
         "the answer is finished. The filler plays during the gap so the visitor never hears "
         "silence. Two more Haiku calls — the dynamic filler and the fidelity audit — sit off "
         "the critical path and add no delay. A canned match short-circuits the whole thing "
         "with zero Claude calls.")

# ============================================ 4 COMPONENT STACK
s = slide("Component stack", "What runs locally, what is a paid API, and what happens when it fails")
table(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(5.3), [
    ["Stage", "Component (verbatim)", "Local / API", "Fallback"],
    ["Wake", "openWakeWord hi_see_jap.onnx", "**Local**", "Operator force-listen from /maintain"],
    ["STT", "OpenAI gpt-4o-mini-transcribe", "**API**", "**None wired.** Local switch exists, unused"],
    ["Gates", "postprocess.py · answer_gate.py", "**Local**", "Fail open — turn proceeds"],
    ["Canned", "canned_answers.json", "**Local**", "No match → normal path"],
    ["Router", "Claude Haiku 4.5", "**API**", "Truncated JSON → anchor routing"],
    ["Retrieval", "topic_map.json → whole documents", "**Local**", "No match → theme-level documents"],
    ["Inference", "Claude Sonnet 4.6, streamed", "**API**", "Credit/network loss → in-voice degraded line"],
    ["TTS", "ElevenLabs clone LeM5jaQwKcHJtzmSBNlA", "**API**", "**Fails open to OpenAI TTS**"],
    ["Audit", "Claude Haiku, asynchronous", "**API**", "Fails open; composer is primary safety"],
], col_w=[1.2, 3.6, 1.3, 4.2], size=11.5, head_size=12)
footer(s, 4)
notes(s, "Read this as the resilience map. Everything local keeps working without internet: "
         "the wake word, the gates, the canned answers, retrieval. Everything marked API stops "
         "without internet or credits. The single weakest link is STT — it has no automatic "
         "failover. A local faster-whisper backend exists as a config switch (LOCAL_STT_MODEL) "
         "and was recommended by the pilot as the main latency fix, but was never wired. "
         "Piper is not in the live path; it appears only as a legacy laptop-only setting.")

# ============================================ 5 KNOWLEDGE BASE
s = slide("Knowledge base", "79 documents · 35 topics · curated")
bullets(s, Inches(0.7), Inches(1.5), Inches(6.2), Inches(4.4), [
    "**64 columns + 15 speeches = 79 documents**",
    "**35 curated topics**, four tiers",
    "**No vector search** — curated lookup, not similarity",
], size=18, gap=26)
rect(s, Inches(7.35), Inches(1.4), Inches(5.35), Inches(2.5), LIGHT, GREY)
tb(s, Inches(7.55), Inches(1.6), Inches(5.0), Inches(2.2),
   "CURATION PIPELINE\n\n"
   "data/csv  +  data/text\n"
   "        ↓  generate_corpus_files.py\n"
   "corpus/**/*.md  +  *.json\n"
   "        ↓  build_topic_map.py\n"
   "corpus/voice/topic_map.json   (35)",
   size=13, color=DARK, font="Consolas")
callout(s, Inches(7.35), Inches(4.15), Inches(5.35), Inches(2.0),
        "Routing accuracy\n**96.7% Measured** against a **Target of ≥85%**.",
        RGBColor(0xEF, 0xF7, 0xEF), GREEN, size=13.5)
footer(s, 5)
notes(s, "Each document is a paired .md text file and .json metadata file. "
         "Curated from a 15-column spreadsheet with source text matched per document. "
         "One biography row was skipped: no single publication date, and placeholders are "
         "forbidden. The 96.7% figure comes from the repository's own 30-question smoke set, "
         "reports/smoke_test_summary.json. The design bet was that a hand-curated index beats statistical search on a small, "
         "dense corpus. The smoke set measured 96.7% primary-routing pass against an 85% "
         "target, with zero fabricated citations. One documented routing miss exists — the "
         "JMSU question — recorded in docs/lessons/LL-011. Keep that question off a live stage. "
         "Note the 1,109-document corpus you may have heard about is a different repository; "
         "see the second-to-last slide.")

# ============================================ 6 OPERATING CYCLE
s = slide("Robot operating cycle", "Every step has a timeout, a barge-in and an error path")
table(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(5.2), [
    ["Step", "Timeout / barge-in / error path", "Duration"],
    ["Idle", "Alive gesture every 10 s · no timeout · service starts at boot", "**Measured** indefinite"],
    ["Wake detected", "Score ≥ 0.08 in a 2.5 s window · miss → operator force-listen", "**Measured** 0.33–0.6 s"],
    ["Listening", "Closes after 1.5 s silence · under 0.4 s of speech is discarded", "**Measured** 1.6–3.1 s"],
    ["Transcribing", "“Ah.” plays · no STT failover · offline → not-connected clip", "**Measured** 1.2–1.6 s"],
    ["Routing", "Truncated JSON → anchor routing · canned match skips it", "**[TO CONFIRM]** on robot"],
    ["Generating", "Filler holds 1.2 s · no credits → in-voice degraded line", "**[TO CONFIRM]** on robot"],
    ["Speaking", "**Barge-in:** wake phrase cuts playback · TTS → OpenAI fallback", "**Measured** first audio 4.9–6.2 s"],
    ["Return to idle", "Follow-up window disabled · next question needs a fresh wake", "**Measured** immediate"],
], col_w=[1.6, 6.6, 2.6], size=11, head_size=12)
footer(s, 6)
notes(s, "The visitor-felt number is 4.9 to 6.2 seconds from the end of their question to the "
         "first spoken word — measured 2026-08-21 after the latency work. Before streaming it "
         "was 15 to 20 seconds. The README target is 4 seconds end to end, so this is close "
         "but not met. Two stages on this slide have never been measured on the robot itself: "
         "routing and generating. They are logged per turn to the maintenance page; nobody has "
         "summarised them. That is an open item with an owner.")

# ============================================ 7 UNTETHERED RUNTIME
s = slide("Untethered runtime", "The honest gap")
callout(s, Inches(0.7), Inches(1.5), Inches(11.9), Inches(2.3),
        "**[TO CONFIRM: untethered runtime never measured — requires a timed discharge "
        "test | owner: hardware]**\n\n"
        "No battery or power figure exists here.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.9), Inches(4.3), Inches(11.4), Inches(2.0), [
    "**Repository search found nothing**",
    "**To close it:** one timed discharge, one timed recharge",
], size=19, gap=26)
footer(s, 7)
notes(s, "No battery capacity, runtime on a full charge, recharge time or idle-versus-"
         "active power figure exists anywhere in the repository. Figures here are not "
         "inferred from datasheets. "
         "The search covered battery, charge, discharge, mAh, watt and power-draw terms and "
         "found nothing but corpus prose. Datasheet figures are refused here because they "
         "cannot account for the mic array, the always-on wake model, Bluetooth audio or the "
         "motors. To close it: full charge, run the normal turn cycle to shutdown, log "
         "wall-clock runtime and turn count, then a timed recharge — one afternoon of work. "
         "This slide is deliberately empty of numbers. Every figure that belongs here would "
         "have been a guess, and a plausible guess on a handover slide is worse than a blank. "
         "If the client plans to run the robot away from mains power — at a museum stand, for "
         "example — this test must happen before that commitment is made. It is cheap: one "
         "timed discharge and one timed recharge.")

# ============================================ 8 COST MODEL
s = slide("Cost model", "Per turn, and at volume")
table(s, Inches(0.55), Inches(1.25), Inches(6.5), Inches(3.5), [
    ["Stage", "Cost per turn", "Basis"],
    ["Router (Haiku)", "≈$0.001", "**Derived**"],
    ["Inference (Sonnet)", "≈$0.023", "**Derived**"],
    ["Filler + audit (Haiku)", "≈$0.002", "**Measured**"],
    ["STT (OpenAI)", "**[TO CONFIRM]**", "metered, never priced"],
    ["TTS (ElevenLabs)", "**[TO CONFIRM]**", "300–450 credits/answer"],
    ["**Anthropic total**", "**≈$0.025**", "vs **Target** ≤$0.02"],
], col_w=[2.6, 2.0, 1.9], size=12, head_size=12)
table(s, Inches(7.35), Inches(1.25), Inches(5.4), Inches(2.2), [
    ["Turns / month", "100", "1,000", "10,000"],
    ["Anthropic only", "≈$2.50", "≈$25", "≈$250"],
    ["Blended", "**[TO CONFIRM]**", "**[TO CONFIRM]**", "**[TO CONFIRM]**"],
], col_w=[2.0, 1.1, 1.1, 1.2], size=11, head_size=11)
callout(s, Inches(7.35), Inches(3.75), Inches(5.4), Inches(2.3),
        "**Do not quote a total turn cost yet.**\n"
        "Only Anthropic is priced. Repeat questions are **free** — audio is cached locally.",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=15)
footer(s, 8)
notes(s, "All three providers are metered in app/usage_meter.py; only Anthropic has been "
         "converted to dollars. Canned answers cost nothing at all. "
         "The $0.025 figure is derived, not measured directly: the robot logged 8 composer "
         "calls across 79,760 tokens at roughly $0.20 in one service session. It is Anthropic "
         "only. The bill is input-heavy by design — every answer carries the persona and the "
         "retrieved documents in with it — and prompt caching already bills cached input at "
         "one tenth. Cost is not the problem here; at a thousand questions a month this is "
         "roughly twenty-five dollars.")

# ============================================ 9 PERFORMANCE
s = slide("Performance", "Target versus measured — and what was never measured")
table(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(3.4), [
    ["Metric", "Target", "Measured", "Verdict"],
    ["Router accuracy", "≥85%", "**96.7%**", "**Met**"],
    ["Fabricated citations", "0", "**0** across all graded runs", "**Met**"],
    ["End-to-end to first audio", "≤4 s", "**4.9–6.2 s**", "**Not met**"],
    ["Cost per turn (Anthropic)", "≤$0.02", "**≈$0.025 derived**", "**Not met**"],
    ["Speech-to-text latency", "—", "**1.2–1.6 s**", "Measured"],
    ["First-sentence synthesis", "—", "**1.7–2.5 s**", "Measured"],
], col_w=[3.4, 1.8, 3.6, 1.6], size=12.5, head_size=12.5)
callout(s, Inches(0.55), Inches(4.95), Inches(12.2), Inches(1.5),
        "**Never measured on the robot:** router latency · retrieval latency · composer "
        "first token · blended cost · untethered runtime. **None is estimated here.**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=15)
footer(s, 9)
notes(s, "Two targets are met and two are missed, and the misses are modest. The latency miss "
         "has a known fix that was recommended and never implemented: move speech-to-text to a "
         "local model, which removes one to one-and-a-half seconds and one paid API call at the "
         "same time. The cost miss is small in absolute terms. What matters more than either is "
         "the list in the amber box — those are the numbers nobody has, and they are named here "
         "rather than filled with plausible guesses.")

# ============================================ 10 CONVERSATION UI
s = slide("Conversation app", "app/dashboard.py — Streamlit, runs on a laptop")
mono(s, Inches(0.55), Inches(1.3), Inches(6.5), Inches(4.7), r"""
┌──────────────────────────────────────────────┐
│ [sidebar ◄]        ⚖  With Due Respect       │
│  Settings                                    │
│  ☑ Voice response                            │
│  ☐ TTS chunks (debug)                        │
│  🧹 Clear conversation                       │
│  Router / Inference / STT / TTS model ids    │
│  Topics loaded: 35                           │
├──────────────────────────────────────────────┤
│  ┌ assistant ──────────────────────────────┐ │
│  │ answer streams token by token           │ │
│  │ ▶ ───────────────  audio player         │ │
│  │ ▼ 📚 Sources — rule_of_law (high)       │ │
│  └─────────────────────────────────────────┘ │
├──────────────────────────────────────────────┤
│  ⏺ Press to start talking      ⏹ stop        │
│  … or type your question (fallback)          │
└──────────────────────────────────────────────┘
""".strip("\n"), size=10.5)
bullets(s, Inches(7.4), Inches(1.5), Inches(5.35), Inches(4.2), [
    "**Used by:** presenter, reviewer, engineer",
    "**Actions:** mic · text fallback · streamed answer · replay · **Sources** panel",
    "Speaks through **OpenAI TTS**, not the clone",
], size=16, gap=22)
tb(s, Inches(0.55), Inches(6.2), Inches(12.2), Inches(0.4),
   "Wireframe from source — not a screenshot.", size=12, color=GREY)
footer(s, 10)
notes(s, "It is one screen plus a collapsed settings sidebar. "
         "The app cannot be launched in the handover environment: app/.env is absent and "
         "dashboard.py calls st.stop() when ANTHROPIC_API_KEY is unset, so no screenshots are "
         "included. The Sources panel shows routed topics, confidence and the documents used. "
         "This is the laptop demo surface, not the robot. It is the fallback if robot audio "
         "fails on the day — same pipeline, answer read from the screen. The Sources expander "
         "is the trust feature: it shows which topics the router picked, how confident it was, "
         "and which of the Chief Justice's documents the answer came from. No screenshots are "
         "included because the application needs three live API keys that are correctly kept "
         "out of the repository.")

# ============================================ 11 MAINTENANCE UI
s = slide("Maintenance dashboard", "on the robot at :8080, key-gated")
mono(s, Inches(0.55), Inches(1.3), Inches(6.5), Inches(4.7), r"""
 /maintain?key=cjap
┌──────────────────────────────────────────────┐
│ ┌Health──────────┐ ┌System──────────────────┐│
│ │ services up    │ │ temp · disk · network  ││
│ └────────────────┘ └────────────────────────┘│
│ ┌Current turn────┐ ┌Stage latency───────────┐│
│ │ cost ¢ · total │ │ gate · route · synth   ││
│ └────────────────┘ └────────────────────────┘│
│ ┌Recent turns (tracking)───────────────────┐ │
│ │ question │ route │ cost │ seconds        │ │
│ └──────────────────────────────────────────┘ │
│ ┌Conversation (raw vs corrected)───────────┐ │
│ │ NER corrections (P0)                     │ │
│ └──────────────────────────────────────────┘ │
│ ┌Claude──┐ ┌OpenAI STT─┐ ┌ElevenLabs──────┐  │
│ └────────┘ └───────────┘ └────────────────┘  │
│ ┌Controls┐ ┌Manual actions────────────────┐  │
│ │ mute   │ │ force listen · say text      │  │
│ └────────┘ └──────────────────────────────┘  │
└──────────────────────────────────────────────┘
""".strip("\n"), size=10.5)
bullets(s, Inches(7.4), Inches(1.5), Inches(5.35), Inches(4.2), [
    "**A key-gated page**, not Streamlit",
    "**Used by:** FLP operations staff and engineers",
    "**Actions:** mute · force-listen · say text · edit entities",
], size=17, gap=24)
tb(s, Inches(0.55), Inches(6.2), Inches(12.2), Inches(0.4),
   "Wireframe from source — not a screenshot.", size=12, color=GREY)
footer(s, 11)
notes(s, "Live wake and stop meters are on the same page. Sibling pages are /audience, "
         "/avatar, /event, /notes and /canned-qa. "
         "Card inventory read from deploy/pi/dashboard/ui_page_maintenance.py, a 44 KB page "
         "served behind a key gate. Operators can also adjust tuning, pair a Bluetooth "
         "speaker, and reach the troubleshooting root page and /canned-qa. "
         "This is where an operator lives during a session. The two cards that matter most on "
         "a demo day are Health — is everything running — and Current turn, which shows what "
         "the last question cost in cents and the running total. Stage latency is the card that "
         "already holds the per-turn timings nobody has summarised; the open item on the "
         "performance slide is reading this card systematically, not building anything new.")

# ============================================ 12 OPERATIONS
s = slide("Operations", "Start · run · shut down")
bullets(s, Inches(0.7), Inches(1.5), Inches(5.9), Inches(4.6), [
    "**Start:** run the health check",
    "**26 checks**, one pass line",
    "**Run:** /maintain",
    "**Shut down:** stop services, power off",
], size=18, gap=24)
mono(s, Inches(7.0), Inches(1.4), Inches(5.75), Inches(1.5),
     "$ ~/bin/verify.sh\n\n"
     "ALL CHECKS PASSED — say \"Hi Cee-Jap\"\n"
     "                     to the robot.", size=12)
mono(s, Inches(7.0), Inches(3.2), Inches(5.75), Inches(0.95),
     "$ sudo systemctl stop \\\n"
     "      supervaise pi-dashboard", size=12)
callout(s, Inches(7.0), Inches(4.45), Inches(5.75), Inches(1.9),
        "**Never:** share keys · edit the corpus · run offline.\n"
        "**[TO CONFIRM: power-off sequence | Pao]**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=15)
footer(s, 12)
notes(s, "The robot boots itself; /maintain carries cost and timings. Never change "
         "settings during demo week. "
         "The 26 checks cover services, keys, wake model, audio hardware and all three "
         "providers. /audience is the visitor display. Also never let the credit balance "
         "reach zero: the robot degrades to a polite in-voice line and gives no real answer. "
         "The health check is the whole operations story: one command, 26 checks, and a single "
         "pass line. Its exit code equals the number of failures, so it can be scripted. If it "
         "prints anything other than ALL CHECKS PASSED, do not start the session. On shutdown: "
         "the repository documents a reboot for first-run setup but never specifies an approved "
         "power-off sequence for this hardware, so that is carried as an open item rather than "
         "guessed at.")

# ============================================ 13 TROUBLESHOOTING
s = slide("Troubleshooting", "The five faults an operator will actually meet")
table(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(4.9), [
    ["Symptom", "Likely cause", "Fix", "Escalate if"],
    ["Robot does not wake", "Mic sensitivity, or wake model not resident",
     "Check the wake meter on /maintain; re-run verify.sh",
     "Three speakers fail at 1 m"],
    ["Wakes at the wrong moment", "Threshold is low; “chief justice” can trigger it",
     "Raise CJ_WAKE_OWW_THRESHOLD toward 0.4",
     "Raising it starts causing missed wakes"],
    ["Stops itself mid-answer", "Mic hears the speaker; Bluetooth has no echo cancellation",
     "Raise CJ_STOP_OWW_THRESHOLD, or disable the stop word",
     "It happens on the internal speaker"],
    ["Answers but no sound", "Bluetooth dropped, or audio routing overwritten",
     "Re-pair from the dashboard; re-run verify.sh",
     "The routing check fails after every reboot"],
    ["“Unable to answer just now”", "Credits exhausted, or venue internet down",
     "Check provider status and credit balance on /maintain",
     "Credits are funded and it still fails"],
], col_w=[2.5, 3.2, 3.5, 3.0], size=11, head_size=11.5)
footer(s, 13)
notes(s, "Four of these five are audio or network, not AI. The wake threshold is the one real "
         "tuning trade-off: it currently sits low at 0.08, which means the phrase “chief "
         "justice” spoken at a sleeping robot can wake it. The configuration file documents the "
         "remedy and the direction to move in either case. The barge-in issue is physics — "
         "echo cancellation covers the internal speaker only, so a Bluetooth speaker will "
         "sometimes let the robot hear itself.")

# ============================================ 14 OPEN ITEMS
s = slide("Open items and owners", "Carried forward, not closed")
table(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(5.2), [
    ["Item", "Why it matters", "Owner", "Needed by"],
    ["Blended per-turn cost", "The quoted cost excludes STT and TTS", "Pao", "Before the budget conversation"],
    ["On-robot per-stage latency", "Two stages unmeasured; the 4 s target cannot be judged", "Pao", "Next status review"],
    ["Untethered runtime", "No battery figure exists at all", "Hardware", "Before any un-mained deployment"],
    ["Wake-word live bench", "The only release gate still entirely unmet", "Dev0 + Sheena + Pao", "Before unattended operation"],
    ["ElevenLabs credits in dollars", "Drives the monthly running cost", "Dev0", "Before the budget conversation"],
    ["Approved power-off sequence", "Staff need a safe shutdown", "Pao / Dev0", "Before staff training"],
    ["Live UI screenshots", "Both surfaces documented from source only", "Pao", "Before the next revision"],
], col_w=[3.1, 4.5, 2.2, 2.7], size=11.5, head_size=11.5)
footer(s, 14)
notes(s, "Seven items, every one with a named owner and a deadline tied to a real event rather "
         "than a date. The full register in the written deliverables has fifteen rows including "
         "documentation drift and repository questions; these seven are the ones that affect "
         "what the client can do with the robot. None of them blocks operating it today with "
         "an attendant present and mains power.")

# ============================================ 15 NOT INCLUDED
s = slide("What this handover does not include", "And why it matters")
callout(s, Inches(0.6), Inches(1.35), Inches(12.1), Inches(1.75),
        "**The pilot “brain” is a different repository, not part of this handover.**\n"
        "You are receiving the robot: 79 documents, hand-curated topics.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.8), Inches(3.5), Inches(11.7), Inches(2.7), [
    "**Verified:** no pilot commits, **no git tags**",
    "**Effect:** it declines questions he did write about",
], size=19, gap=26)
footer(s, 15)
notes(s, "That repository holds 1,109 documents and a hybrid retrieval engine. "
         "The pilot engine is bge-base embeddings plus BM25 keyword matching, fused, over "
         "9,865 chunks. Any pilot figure quoted in the written deliverables is labelled "
         "'source: pilot brain repo — not reproducible from this handover'. Also not "
         "included: the roughly 150-speech expansion, a web UI, multi-user sessions, and "
         "memory beyond the current conversation. This is the most important slide for setting expectations. If someone has seen the "
         "pilot report — with its 1,109 documents, its 94% recall figure and its two-cent "
         "answers — that system is not what is being handed over. It lives in a separate "
         "repository that was never merged into this one. Confirming which repository is "
         "canonical, and whether the two are meant to converge, is a decision for the project "
         "owners, not an engineering task.")

# ============================================ 16 SOURCES
s = slide("Sources and evidence", "Every figure traces to one of these")
bullets(s, Inches(0.7), Inches(1.6), Inches(11.9), Inches(4.4), [
    "**Repository** — Supervaise-Inc/CJAP, " + COMMIT,
    "**Config** — app/.env.example · wakeword.conf",
    "**Runtime notes** — PROJECT_NOTES.txt · usage_meter.py",
    "**Corpus and tests** — MANIFEST.md · TS-006",
    "**Pilot documents** — separate repository, **version unconfirmed**",
], size=16, gap=20)
footer(s, 16)
notes(s, "Test evidence is reports/smoke_test_summary.json. "
         "The pilot documents are CJP_Pilot_Report_W3_5_FINAL.md, "
         "CJP_Latency_Cost_Assessment.md, CJP_Readiness_Verdict_Brief.md and the pilot "
         "workbook Weekly Tasks sheet, 2026-08-22 copy. Written companions to this deck are "
         "CJAP_Client_Turnover.docx, CJAP_Internal_Playbook.docx and the four one-page "
         "summaries. Nothing in this deck was estimated. Where a number was never measured it says "
         "[TO CONFIRM] with an owner, and where a figure comes from the separate pilot "
         "repository it is labelled as not reproducible from this handover. The pilot workbook "
         "copy used is dated 2026-08-22; its version number could not be confirmed because the "
         "file on disk carries a system-generated name rather than a version.")

prs.save(os.path.join(OUT, "CJAP_Handover.pptx"))
print(f"CJAP_Handover.pptx  slides={len(prs.slides.__iter__.__self__._sldIdLst)}")
