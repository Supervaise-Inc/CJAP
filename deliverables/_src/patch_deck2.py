"""Second trim pass: bring every slide to <=40 body words."""
import io, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_deck.py")
s = io.open(p, encoding="utf-8").read()
R = []

# slide 2 -----------------------------------------------------------------
R.append((
    '''   "A desktop robot that answers visitors' questions as the Chief Justice, "
   "grounded only in his published writing.", size=22, bold=True, color=DARK)''',
    '''   "A desktop robot that answers questions as the Chief Justice, "
   "from his published writing.", size=23, bold=True, color=DARK)'''))
R.append((
    '''tb(s, Inches(0.9), Inches(5.05), Inches(11.5), Inches(0.6),
   "Two paid Claude calls per turn. The voice is his own, cloned.",
   size=15, color=DARK)
footer(s, 2)''',
    '''footer(s, 2)'''))
R.append((
    '''notes(s, "The voice is a clone of the Chief Justice's own, licensed through ElevenLabs.''',
    '''notes(s, "Two paid Claude calls per turn. The voice is a clone of the Chief Justice's "
         "own, licensed through ElevenLabs.'''))

# slide 5 -----------------------------------------------------------------
R.append((
    '''s = slide("Knowledge base", "79 documents · 35 topics · hand-curated, not searched")''',
    '''s = slide("Knowledge base", "79 documents · 35 topics · curated")'''))
R.append((
    '''    "**64 columns + 15 speeches = 79 documents**",
    "**35 curated topics**, four tiers",
    "Paired **.md** text and **.json** metadata",
    "**No vector search** — the router names a topic, code fetches the documents",
], size=17, gap=22)''',
    '''    "**64 columns + 15 speeches = 79 documents**",
    "**35 curated topics**, four tiers",
    "**No vector search** — curated lookup, not similarity",
], size=18, gap=26)'''))
R.append((
    '''notes(s, "Curated from a 15-column spreadsheet with source text matched per document.''',
    '''notes(s, "Each document is a paired .md text file and .json metadata file. "
         "Curated from a 15-column spreadsheet with source text matched per document.'''))

# slide 7 -----------------------------------------------------------------
R.append((
    '''        "No battery, runtime, recharge or power-draw figure exists in this repository.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.9), Inches(4.25), Inches(11.4), Inches(2.1), [
    "A repository-wide search returned **only corpus prose** — no test record",
    "**Not inferred from datasheets**",
    "**To close it:** one timed discharge, one timed recharge",
], size=17, gap=18)''',
    '''        "No battery or power figure exists here.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.9), Inches(4.3), Inches(11.4), Inches(2.0), [
    "**Repository search found nothing**",
    "**To close it:** one timed discharge, one timed recharge",
], size=19, gap=26)'''))
R.append((
    '''notes(s, "The search covered battery, charge, discharge, mAh, watt and power-draw terms and "''',
    '''notes(s, "No battery capacity, runtime on a full charge, recharge time or idle-versus-"
         "active power figure exists anywhere in the repository. Figures here are not "
         "inferred from datasheets. "
         "The search covered battery, charge, discharge, mAh, watt and power-draw terms and "'''))

# slide 10 ----------------------------------------------------------------
R.append((
    '''    "**Actions:** mic · text fallback · streamed answer · replay · **Sources** panel",
    "**One screen** plus a settings sidebar",
    "Speaks through **OpenAI TTS**, not the clone",
], size=15, gap=18)''',
    '''    "**Actions:** mic · text fallback · streamed answer · replay · **Sources** panel",
    "Speaks through **OpenAI TTS**, not the clone",
], size=16, gap=22)'''))
R.append((
    '''notes(s, "The app cannot be launched in the handover environment:''',
    '''notes(s, "It is one screen plus a collapsed settings sidebar. "
         "The app cannot be launched in the handover environment:'''))

# slide 11 ----------------------------------------------------------------
R.append((
    '''s = slide("Maintenance dashboard", "deploy/pi/dashboard — on the robot at :8080, key-gated")''',
    '''s = slide("Maintenance dashboard", "on the robot at :8080, key-gated")'''))
R.append((
    '''    "**It exists** — a key-gated page, not Streamlit",
    "**Used by:** FLP operations staff and engineers",
    "**Actions:** mute · force-listen · say text · edit entities · live meters",
    "**Siblings:** /audience · /avatar · /event · /notes",
], size=15, gap=18)''',
    '''    "**A key-gated page**, not Streamlit",
    "**Used by:** FLP operations staff and engineers",
    "**Actions:** mute · force-listen · say text · edit entities",
], size=17, gap=24)'''))
R.append((
    '''notes(s, "Card inventory read from deploy/pi/dashboard/ui_page_maintenance.py,''',
    '''notes(s, "Live wake and stop meters are on the same page. Sibling pages are /audience, "
         "/avatar, /event, /notes and /canned-qa. "
         "Card inventory read from deploy/pi/dashboard/ui_page_maintenance.py,'''))

# slide 12 ----------------------------------------------------------------
R.append((
    '''    "**Start:** it boots itself — run the health check",
    "**26 checks**, one pass line",
    "**Run:** /maintain for cost and timings",
    "**Shut down:** stop services, then power off",
], size=17, gap=22)''',
    '''    "**Start:** run the health check",
    "**26 checks**, one pass line",
    "**Run:** /maintain",
    "**Shut down:** stop services, then power off",
], size=18, gap=24)'''))
R.append((
    '''        "**Never:** share keys · edit the corpus · run offline · change settings in demo week.\\n"
        "**[TO CONFIRM: power-off sequence | owner: Pao]**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=14)''',
    '''        "**Never:** share keys · edit the corpus · run offline.\\n"
        "**[TO CONFIRM: power-off sequence | Pao]**",
        RGBColor(0xFF, 0xF4, 0xCC), AMBER, size=15)'''))
R.append((
    '''notes(s, "The 26 checks cover services, keys, wake model, audio hardware and all three "''',
    '''notes(s, "The robot boots itself; /maintain carries cost and timings. Never change "
         "settings during demo week. "
         "The 26 checks cover services, keys, wake model, audio hardware and all three "'''))

# slide 15 ----------------------------------------------------------------
R.append((
    '''        "**The pilot “brain” is a different repository and is not part of this handover.**\\n"
        "It holds 1,109 documents and a hybrid retrieval engine. You are receiving the "
        "robot: 79 documents, hand-curated topics.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=16)
bullets(s, Inches(0.8), Inches(3.6), Inches(11.7), Inches(2.6), [
    "**Verified:** no pilot commits here, and **no git tags** at all",
    "**Effect:** the robot declines questions he did in fact write about",
], size=18, gap=22)''',
    '''        "**The pilot “brain” is a different repository, not part of this handover.**\\n"
        "You are receiving the robot: 79 documents, hand-curated topics.",
        RGBColor(0xFD, 0xE9, 0xE9), RED, size=17)
bullets(s, Inches(0.8), Inches(3.5), Inches(11.7), Inches(2.7), [
    "**Verified:** no pilot commits, **no git tags**",
    "**Effect:** it declines questions he did write about",
], size=19, gap=26)'''))
R.append((
    '''notes(s, "The pilot engine is bge-base embeddings plus BM25 keyword matching, fused, over "''',
    '''notes(s, "That repository holds 1,109 documents and a hybrid retrieval engine. "
         "The pilot engine is bge-base embeddings plus BM25 keyword matching, fused, over "'''))

# slide 16 ----------------------------------------------------------------
R.append((
    '''s = slide("Sources and evidence", "Every figure in this deck traces to one of these")''',
    '''s = slide("Sources and evidence", "Every figure traces to one of these")'''))
R.append((
    '''    "**Corpus and tests** — MANIFEST.md · TS-006 · smoke_test_summary.json",''',
    '''    "**Corpus and tests** — MANIFEST.md · TS-006",'''))
R.append((
    '''notes(s, "The pilot documents are CJP_Pilot_Report_W3_5_FINAL.md, "''',
    '''notes(s, "Test evidence is reports/smoke_test_summary.json. "
         "The pilot documents are CJP_Pilot_Report_W3_5_FINAL.md, "'''))

missing = [a for a, b in R if a not in s]
if missing:
    print("MISSING %d PATTERN(S):" % len(missing))
    for m in missing:
        print("---", m[:110].replace("\n", " | "))
else:
    for a, b in R:
        s = s.replace(a, b, 1)
    io.open(p, "w", encoding="utf-8").write(s)
    print("patched %d blocks" % len(R))
