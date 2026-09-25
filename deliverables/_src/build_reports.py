import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2docx import convert

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT  = os.path.join(ROOT, "deliverables")

COMMIT = "pi/deployment-snapshots @ 2545882 (2026-08-31)"

convert(
    md_path=os.path.join(ROOT, "deliverables", "_src", "DELIVERABLE-1-labeled.md"),
    out_path=os.path.join(OUT, "CJAP_Client_Turnover.docx"),
    title="CJAP Client Turnover\n& Status Report",
    subtitle="Chief Justice Artemio V. Panganiban Conversation Robot",
    meta_rows=[
        ["Prepared for", "Foundation for Liberty and Prosperity (FLP) — executive sponsor"],
        ["Prepared by", "Supervaise Inc."],
        ["Source of truth", "github.com/Supervaise-Inc/CJAP"],
        ["Branch / commit", COMMIT],
        ["Document date", "20 September 2026"],
    ],
    classification="CLIENT DELIVERABLE — contains [TO CONFIRM] items; see Open Items Register",
    footer_text="CJAP Client Turnover & Status Report — Supervaise Inc.",
)

convert(
    md_path=os.path.join(OUT, "_src", "DELIVERABLE-2-tightened.md"),
    out_path=os.path.join(OUT, "CJAP_Internal_Playbook.docx"),
    title="CJAP Internal\nMaster Playbook",
    subtitle="Rebuilding this system for a different subject and corpus",
    meta_rows=[
        ["Audience", "Supervaise engineering — internal only"],
        ["Prepared by", "Supervaise Inc."],
        ["Source of truth", "github.com/Supervaise-Inc/CJAP"],
        ["Branch / commit", COMMIT],
        ["Document date", "20 September 2026"],
    ],
    classification="INTERNAL — NOT FOR CLIENT DISTRIBUTION",
    footer_text="CJAP Internal Master Playbook — Supervaise Inc. (internal)",
)
print("reports built")
