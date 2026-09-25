"""Trim deck slides to the <=40 body-word rule; detail moves into speaker notes."""
import io, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_deck.py")
s = io.open(p, encoding="utf-8").read()
R = []

# ---------------- slide 2
R.append((
    '''   "A desktop robot that answers visitors' questions as retired Chief Justice "
   "Panganiban, grounded only in his published writing.", size=22, bold=True, color=DARK)''',
    '''   "A desktop robot that answers visitors' questions as the Chief Justice, "
   "grounded only in his published writing.", size=22, bold=True, color=DARK)'''))
R.append((
    '''   "REACHY MINI\\n\\nface · ears · mouth\\nwake word + mic + speaker\\non-device, offline",''',
    '''   "REACHY MINI\\n\\nface · ears · mouth\\non-device, offline",'''))
R.append((
    '''   "CURATED CORPUS\\n\\n79 documents\\n35 topics\\nread from disk, no search",''',
    '''   "CURATED CORPUS\\n\\n79 documents\\n35 topics",'''))
R.append((
    '''   "CLAUDE\\n\\nHaiku 4.5 routes\\nSonnet 4.6 composes\\ntwo paid calls per turn",''',
    '''   "CLAUDE\\n\\nHaiku 4.5 routes\\nSonnet 4.6 composes",'''))
R.append((
    '''tb(s, Inches(0.9), Inches(5.0), Inches(11.5), Inches(0.9),
   "The voice is a clone of the Chief Justice's own, licensed through ElevenLabs. "
   "The robot never claims to be a machine — and never invents a view he did not publish.",
   size=14, color=DARK)
footer(s, 2)
notes(s, "Three parts''',
    '''tb(s, Inches(0.9), Inches(5.05), Inches(11.5), Inches(0.6),
   "Two paid Claude calls per turn. The voice is his own, cloned.",
   size=15, color=DARK)
footer(s, 2)
notes(s, "The voice is a clone of the Chief Justice's own, licensed through ElevenLabs. The "
         "robot never claims to be a machine and never invents a view he did not publish. "
         "Three parts'''))

# ---------------- slide 5
R.append((
    '''bullets(s, Inches(0.7), Inches(1.35), Inches(6.2), Inches(4.8), [
    "**64 columns + 15 speeches** = 79 documents ingested",
    "Each is a paired **.md** (text) and **.json** (entities, stances, signature phrases)",
    "**35 curated topics** across anchor, core, subordinate and meta tiers",
    "Curated from a 15-column spreadsheet; source text matched per document",
    "**No vector search.** The router names a topic; code looks up the documents",
    "One biography row skipped — no single publication date, and placeholders are forbidden",
], size=15.5, gap=13)''',
    '''bullets(s, Inches(0.7), Inches(1.5), Inches(6.2), Inches(4.4), [
    "**64 columns + 15 speeches = 79 documents**",
    "**35 curated topics**, four tiers",
    "Paired **.md** text and **.json** metadata",
    "**No vector search** — the router names a topic, code fetches the documents",
], size=17, gap=22)'''))
R.append((
    '''        "Routing accuracy\\n**96.7% Measured** on the repository's own 30-question smoke set "
        "(reports/smoke_test_summary.json), against a **Target of ≥85%**.",''',
    '''        "Routing accuracy\\n**96.7% Measured** against a **Target of ≥85%**.",'''))
R.append((
    '''notes(s, "The design bet was that a hand-curated index''',
    '''notes(s, "Curated from a 15-column spreadsheet with source text matched per document. "
         "One biography row was skipped: no single publication date, and placeholders are "
         "forbidden. The 96.7% figure comes from the repository's own 30-question smoke set, "
         "reports/smoke_test_summary.json. The design bet was that a hand-curated index'''))

# ---------------- slide 7
R.append((
    '''callout(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(2.35),
        "**[TO CONFIRM: untethered runtime never measured — requires a timed discharge "
        "test | owner: hardware]**\\n\\n"
        "No battery capacity, runtime on a full charge, recharge time, or idle-versus-active "
        "power figure exists anywhere in the repository.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.9), Inches(4.05), Inches(11.4), Inches(2.4), [
    "A repository-wide search for battery, charge, discharge, mAh, watt and power-draw "
    "returned **only corpus prose** — no measurement, no specification, no test record",
    "These figures are **left blank rather than inferred from datasheets**: a datasheet "
    "cannot account for the mic array, the always-on wake model, Bluetooth audio or the motors",
    "**To close it:** full charge → run the normal turn cycle to shutdown → log wall-clock "
    "runtime and turn count → timed recharge. One afternoon of work",
], size=14.5, gap=11)
footer(s, 7)
notes(s, "This slide is deliberately empty of numbers.''',
    '''callout(s, Inches(0.7), Inches(1.5), Inches(11.9), Inches(2.3),
        "**[TO CONFIRM: untethered runtime never measured — requires a timed discharge "
        "test | owner: hardware]**\\n\\n"
        "No battery, runtime, recharge or power-draw figure exists in this repository.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.9), Inches(4.25), Inches(11.4), Inches(2.1), [
    "A repository-wide search returned **only corpus prose** — no test record",
    "**Not inferred from datasheets**",
    "**To close it:** one timed discharge, one timed recharge",
], size=17, gap=18)
footer(s, 7)
notes(s, "The search covered battery, charge, discharge, mAh, watt and power-draw terms and "
         "found nothing but corpus prose. Datasheet figures are refused here because they "
         "cannot account for the mic array, the always-on wake model, Bluetooth audio or the "
         "motors. To close it: full charge, run the normal turn cycle to shutdown, log "
         "wall-clock runtime and turn count, then a timed recharge — one afternoon of work. "
         "This slide is deliberately empty of numbers.'''))

# ---------------- slide 8
R.append((
    '''        "**Do not quote a total turn cost yet.**\\n"
        "All three providers are metered in app/usage_meter.py. Only Anthropic has been "
        "converted to dollars. Repeat questions are **free** — ElevenLabs audio is cached "
        "locally and canned answers cost nothing at all.",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=13)
footer(s, 8)
notes(s, "The $0.025 figure is derived''',
    '''        "**Do not quote a total turn cost yet.**\\n"
        "Only Anthropic is priced. Repeat questions are **free** — audio is cached locally.",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=15)
footer(s, 8)
notes(s, "All three providers are metered in app/usage_meter.py; only Anthropic has been "
         "converted to dollars. Canned answers cost nothing at all. "
         "The $0.025 figure is derived'''))

# ---------------- slide 9
R.append((
    '''        "**Never measured on the robot:** router latency · retrieval latency · composer "
        "time-to-first-token · blended per-turn cost including STT and TTS · untethered runtime.\\n"
        "All five are logged or loggable. None is estimated anywhere in this handover.",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=13.5)''',
    '''        "**Never measured on the robot:** router latency · retrieval latency · composer "
        "first token · blended cost · untethered runtime. **None is estimated here.**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=15)'''))

# ---------------- slide 10
R.append((
    '''bullets(s, Inches(7.4), Inches(1.4), Inches(5.35), Inches(4.4), [
    "**Used by:** demo presenter, reviewer, engineer",
    "**Actions:** record from mic · type a fallback question · watch the answer stream · "
    "replay audio · open **Sources** for routed topics, confidence and documents used",
    "**One screen** plus a collapsed settings sidebar",
    "This surface speaks through **OpenAI TTS**, not the ElevenLabs clone",
], size=14, gap=12)
tb(s, Inches(0.55), Inches(6.15), Inches(12.2), Inches(0.5),
   "Wireframe from source — not a screenshot. The app cannot launch here: app/.env is absent "
   "and dashboard.py stops when ANTHROPIC_API_KEY is unset.", size=11, color=GREY)
footer(s, 10)
notes(s, "This is the laptop demo surface''',
    '''bullets(s, Inches(7.4), Inches(1.5), Inches(5.35), Inches(4.2), [
    "**Used by:** presenter, reviewer, engineer",
    "**Actions:** mic · text fallback · streamed answer · replay · **Sources** panel",
    "**One screen** plus a settings sidebar",
    "Speaks through **OpenAI TTS**, not the clone",
], size=15, gap=18)
tb(s, Inches(0.55), Inches(6.2), Inches(12.2), Inches(0.4),
   "Wireframe from source — not a screenshot.", size=12, color=GREY)
footer(s, 10)
notes(s, "The app cannot be launched in the handover environment: app/.env is absent and "
         "dashboard.py calls st.stop() when ANTHROPIC_API_KEY is unset, so no screenshots are "
         "included. The Sources panel shows routed topics, confidence and the documents used. "
         "This is the laptop demo surface'''))

# ---------------- slide 11
R.append((
    '''bullets(s, Inches(7.4), Inches(1.4), Inches(5.35), Inches(4.4), [
    "**It does exist** as a distinct surface — a 44 KB page behind a key gate, not Streamlit",
    "**Used by:** FLP operations staff and Supervaise engineers",
    "**Actions:** mute · force-listen · make the robot speak text · edit the entity "
    "dictionary · adjust tuning · pair a Bluetooth speaker · read live wake and stop meters",
    "**Sibling pages:** / troubleshooting · /audience · /avatar · /event · /notes · /canned-qa",
], size=13.5, gap=11)
tb(s, Inches(0.55), Inches(6.15), Inches(12.2), Inches(0.5),
   "Wireframe from source — not a screenshot. Card inventory read from "
   "deploy/pi/dashboard/ui_page_maintenance.py.", size=11, color=GREY)
footer(s, 11)
notes(s, "This is where an operator lives''',
    '''bullets(s, Inches(7.4), Inches(1.5), Inches(5.35), Inches(4.2), [
    "**It exists** — a key-gated page, not Streamlit",
    "**Used by:** FLP operations staff and engineers",
    "**Actions:** mute · force-listen · say text · edit entities · live meters",
    "**Siblings:** /audience · /avatar · /event · /notes",
], size=15, gap=18)
tb(s, Inches(0.55), Inches(6.2), Inches(12.2), Inches(0.4),
   "Wireframe from source — not a screenshot.", size=12, color=GREY)
footer(s, 11)
notes(s, "Card inventory read from deploy/pi/dashboard/ui_page_maintenance.py, a 44 KB page "
         "served behind a key gate. Operators can also adjust tuning, pair a Bluetooth "
         "speaker, and reach the troubleshooting root page and /canned-qa. "
         "This is where an operator lives'''))

# ---------------- slide 12
R.append((
    '''bullets(s, Inches(0.7), Inches(1.35), Inches(5.9), Inches(5.0), [
    "**Start:** the robot starts itself at boot. Run the health check and read the last line",
    "**Expected:** ALL CHECKS PASSED — say “Hi Cee-Jap” to the robot",
    "**26 checks** cover services, keys, wake model, audio hardware, and all three providers",
    "**Run:** open /maintain?key=cjap for cost and timings; /audience for the visitor display",
    "**Shut down:** stop the services, then power down normally",
], size=15, gap=13)''',
    '''bullets(s, Inches(0.7), Inches(1.5), Inches(5.9), Inches(4.6), [
    "**Start:** it boots itself — run the health check",
    "**26 checks**, one pass line",
    "**Run:** /maintain for cost and timings",
    "**Shut down:** stop services, then power off",
], size=17, gap=22)'''))
R.append((
    '''        "**Never:** share the three API keys · hand-edit the corpus · run a session without "
        "internet · change settings during demo week · let the credit balance reach zero.\\n"
        "**[TO CONFIRM: approved power-off sequence | owner: Pao / Dev0]**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=12.5)
footer(s, 12)
notes(s, "The health check is the whole operations story''',
    '''        "**Never:** share keys · edit the corpus · run offline · change settings in demo week.\\n"
        "**[TO CONFIRM: power-off sequence | owner: Pao]**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=14)
footer(s, 12)
notes(s, "The 26 checks cover services, keys, wake model, audio hardware and all three "
         "providers. /audience is the visitor display. Also never let the credit balance "
         "reach zero: the robot degrades to a polite in-voice line and gives no real answer. "
         "The health check is the whole operations story'''))

# ---------------- slide 15
R.append((
    '''        "**The pilot “brain” is a different repository, and it is not part of this handover.**\\n"
        "It holds a 1,109-document corpus (9,865 chunks) and a hybrid retrieval engine — "
        "bge-base embeddings plus BM25 keyword matching, fused. What you are receiving is the "
        "robot: 79 documents and a hand-curated topic map.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=15)
bullets(s, Inches(0.8), Inches(3.4), Inches(11.7), Inches(3.0), [
    "**Verified:** none of the pilot baseline commits exist in this repository, and it "
    "carries **no git tags** at all",
    "**Consequence:** any pilot figure quoted in these documents is labelled "
    "**[source: pilot brain repo — not reproducible from this handover]**",
    "**Consequence:** the robot will honestly decline questions the Chief Justice has in "
    "fact written about, because those documents are in the other repository",
    "**Also not included:** the ~150-speech expansion · a web UI · multi-user sessions · "
    "memory beyond the current conversation",
], size=14, gap=11)
footer(s, 15)
notes(s, "This is the most important slide''',
    '''        "**The pilot “brain” is a different repository and is not part of this handover.**\\n"
        "It holds 1,109 documents and a hybrid retrieval engine. You are receiving the "
        "robot: 79 documents, hand-curated topics.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=16)
bullets(s, Inches(0.8), Inches(3.6), Inches(11.7), Inches(2.6), [
    "**Verified:** no pilot commits here, and **no git tags** at all",
    "**Effect:** the robot declines questions he did in fact write about",
], size=18, gap=22)
footer(s, 15)
notes(s, "The pilot engine is bge-base embeddings plus BM25 keyword matching, fused, over "
         "9,865 chunks. Any pilot figure quoted in the written deliverables is labelled "
         "'source: pilot brain repo — not reproducible from this handover'. Also not "
         "included: the roughly 150-speech expansion, a web UI, multi-user sessions, and "
         "memory beyond the current conversation. This is the most important slide'''))

# ---------------- slide 16
R.append((
    '''bullets(s, Inches(0.7), Inches(1.4), Inches(11.9), Inches(5.0), [
    "**This repository** — github.com/Supervaise-Inc/CJAP, " + COMMIT,
    "**Configuration** — app/.env.example · deploy/pi/systemd/supervaise.service.d/wakeword.conf",
    "**Measured runtime notes** — deploy/pi/PROJECT_NOTES.txt · app/usage_meter.py",
    "**Corpus and tests** — corpus/MANIFEST.md · docs/test-specs/TS-006 · reports/smoke_test_summary.json",
    "**Pilot documents (separate repository)** — CJP_Pilot_Report_W3_5_FINAL.md · "
    "CJP_Latency_Cost_Assessment.md · CJP_Readiness_Verdict_Brief.md · pilot workbook "
    "Weekly Tasks sheet, 2026-08-22 copy, **version unconfirmed**",
    "**Written companions** — CJAP_Client_Turnover.docx · CJAP_Internal_Playbook.docx · "
    "four one-page summaries",
], size=14.5, gap=12)
footer(s, 16)
notes(s, "Nothing in this deck was estimated.''',
    '''bullets(s, Inches(0.7), Inches(1.6), Inches(11.9), Inches(4.4), [
    "**Repository** — Supervaise-Inc/CJAP, " + COMMIT,
    "**Config** — app/.env.example · wakeword.conf",
    "**Runtime notes** — PROJECT_NOTES.txt · usage_meter.py",
    "**Corpus and tests** — MANIFEST.md · TS-006 · smoke_test_summary.json",
    "**Pilot documents** — separate repository, **version unconfirmed**",
], size=16, gap=20)
footer(s, 16)
notes(s, "The pilot documents are CJP_Pilot_Report_W3_5_FINAL.md, "
         "CJP_Latency_Cost_Assessment.md, CJP_Readiness_Verdict_Brief.md and the pilot "
         "workbook Weekly Tasks sheet, 2026-08-22 copy. Written companions to this deck are "
         "CJAP_Client_Turnover.docx, CJAP_Internal_Playbook.docx and the four one-page "
         "summaries. Nothing in this deck was estimated.'''))

missing = [a for a, b in R if a not in s]
if missing:
    print("MISSING %d PATTERN(S):" % len(missing))
    for m in missing:
        print("---", m[:100].replace("\n", " | "))
else:
    for a, b in R:
        s = s.replace(a, b, 1)
    io.open(p, "w", encoding="utf-8").write(s)
    print("patched %d blocks" % len(R))
