"""Phase 8 entry check. Python, not grep, per the phase guard.

Run once at the very start of the phase (before step 0's commit); re-run at the end, this file
unchanged, to confirm ee2a39c is still an ancestor of HEAD and nothing regressed the pin/taxonomy/bundle.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout.strip()


branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
head = sh("git", "rev-parse", "--short", "HEAD")
print(f"branch={branch} head={head}")
assert branch == "deliverable/2026-09", branch

merge_base = sh("git", "merge-base", "--is-ancestor", "ee2a39c", "HEAD")
rc = subprocess.run(["git", "merge-base", "--is-ancestor", "ee2a39c", "HEAD"], cwd=ROOT).returncode
print("ee2a39c is an ancestor of HEAD:", rc == 0)
assert rc == 0

# app/service.py: untracked at ee2a39c (the phase's own precondition), tracked at HEAD once step 0 lands
untracked_at_entry = subprocess.run(
    ["git", "cat-file", "-e", "ee2a39c:app/service.py"], cwd=ROOT).returncode != 0
print("app/service.py untracked at ee2a39c:", untracked_at_entry)
assert untracked_at_entry

from scripts import verify_pin  # noqa: E402
rc = verify_pin.main()
print("verify_pin rc =", rc)
assert rc == 0

tm = json.loads((ROOT / "corpus" / "voice" / "topic_map.json").read_text(encoding="utf-8"))
print("n_topics =", len(tm["topics"]), "taxonomy_version =", tm["taxonomy_version"])
assert len(tm["topics"]) == 30 and tm["taxonomy_version"] == 2

n_bundle = sum(1 for p in (ROOT / "deploy" / "pi" / "bundle").rglob("*") if p.is_file())
print("deploy/pi/bundle files =", n_bundle)
assert n_bundle == 1315, n_bundle

print("[ph8_00] entry check PASS")
