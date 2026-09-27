"""Phase 10 entry check. Python, not grep, per the phase guard."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout.strip()


branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
print(f"branch={branch}")
assert branch == "deliverable/2026-09", branch

from scripts import verify_pin  # noqa: E402
rc = verify_pin.main()
assert rc == 0

n_bf = sum(1 for p in (ROOT / "Bundle Folder").rglob("*") if p.is_file())
n_cjap = sum(1 for p in (ROOT / "Bundle Folder" / "cjap-bundle").rglob("*") if p.is_file())
print(f"Bundle Folder/: {n_bf} files; cjap-bundle/: {n_cjap} files")
assert n_bf == 1332 and n_cjap == 1321

tag_sha = sh("git", "rev-parse", "pi-snapshot-pre-kbv2-2026-09-27")
branch_sha = sh("git", "rev-parse", "pi/deployment-snapshots")
print(f"pi-snapshot-pre-kbv2-2026-09-27={tag_sha} pi/deployment-snapshots={branch_sha}")
assert tag_sha == branch_sha, "the safety tag must still point at the untouched branch"

print("[ph10_00] entry check PASS")
