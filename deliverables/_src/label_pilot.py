"""Add the mandated pilot-provenance label to every pilot-sourced figure in
Deliverable 1, writing a labelled copy for conversion. The original .md at the
repo root is left untouched.
"""
import io, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))
SRC = os.path.join(ROOT, "DELIVERABLE-1-Client-Turnover-Status-Report.md")
DST = os.path.join(ROOT, "deliverables", "_src", "DELIVERABLE-1-labeled.md")
LBL = "[source: pilot brain repo — not reproducible from this handover]"

s = io.open(SRC, encoding="utf-8").read()
R = [
    # matrix row: STT improvement column
    ("Local `faster-whisper` was the recommended fix in the pilot debt item N-2 — "
     "**not implemented**",
     "Local `faster-whisper` was the recommended fix in pilot debt item N-2 "
     f"{LBL} — **not implemented**"),
    # matrix row: inference TTFT
    ("**1.32s p50** on the pilot brain **[M]**",
     f"**1.32s p50** on the pilot brain **[M]** {LBL}"),
    # comparison table row
    ('| Pilot "brain" v4.2 — hybrid retrieval, concise directive '
     "(`CJP_Pilot_Report_W3_5_FINAL.md`) |",
     '| Pilot "brain" v4.2 — hybrid retrieval, concise directive '
     f"(`CJP_Pilot_Report_W3_5_FINAL.md`) {LBL} |"),
    # optimisation item 1
    ("The pilot's own debt register (item N-2) diagnosed live time-to-first-audio",
     f"The pilot's own debt register {LBL} (item N-2) diagnosed live "
     "time-to-first-audio"),
    # optimisation item 3
    ("The pilot brain proved that sending *passages* instead of whole documents",
     f"The pilot brain {LBL} proved that sending *passages* instead of whole "
     "documents"),
    # never-do list
    ("The standing instruction in the readiness brief is a **config freeze**",
     f"The standing instruction in the readiness brief {LBL} is a "
     "**config freeze**"),
    # demo fallback row
    ("This fallback is a standing recommendation in the readiness brief and "
     "**must be rehearsed once before the session**",
     "This fallback is a standing recommendation in the readiness brief "
     f"{LBL} and **must be rehearsed once before the session**"),
]

missing = [a for a, b in R if a not in s]
if missing:
    print("MISSING %d:" % len(missing))
    for m in missing:
        print("---", m[:100])
    raise SystemExit(1)

for a, b in R:
    s = s.replace(a, b, 1)
io.open(DST, "w", encoding="utf-8").write(s)
print("labelled %d pilot citations -> %s" % (len(R), os.path.basename(DST)))
