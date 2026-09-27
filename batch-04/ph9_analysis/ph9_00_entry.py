"""Phase 9 entry check. Python, not grep, per the phase guard."""
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
assert head == "fcfe6f7", head

from scripts import verify_pin  # noqa: E402
rc = verify_pin.main()
print("verify_pin rc =", rc)
assert rc == 0

tracked = sh("git", "ls-files", "app/service.py")
print("app/service.py tracked:", bool(tracked))
assert tracked

import config as _config_check  # noqa: E402
print("config.CJ_PIPELINE default:", _config_check.CJ_PIPELINE)
assert _config_check.CJ_PIPELINE == "legacy"

n_bundle = sum(1 for p in (ROOT / "deploy" / "pi" / "bundle").rglob("*") if p.is_file())
size_bundle = sum(p.stat().st_size for p in (ROOT / "deploy" / "pi" / "bundle").rglob("*") if p.is_file())
print(f"deploy/pi/bundle/: {n_bundle} files, {size_bundle:,} bytes ({size_bundle / 1024 / 1024:.1f} MB)")
assert n_bundle == 1315

print("[ph9_00] entry check PASS")
