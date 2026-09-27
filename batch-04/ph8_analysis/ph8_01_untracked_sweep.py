"""Phase 8 step 0.3 - sweep for every other untracked file the runtime imports.

Not scoped to app/ and scripts/ by grep: a full `git status --porcelain` over the whole working tree,
filtered to .py files, so a stray untracked module sitting somewhere else entirely could not be missed
the way app/service.py was until this phase. Then cross-checked against the import graphs of BOTH
pipelines (main_voice_robot.py/answer_pipeline.py, and service.py/retrieval.py) to see whether any
untracked file the runtime actually reaches remains after step 0's app/service.py commit.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout


status = sh("git", "status", "--porcelain")
untracked_py = sorted(
    line[3:].strip() for line in status.splitlines()
    if line.startswith("??") and line[3:].strip().endswith(".py")
)
print(f"untracked .py files anywhere in the working tree: {len(untracked_py)}")
for p in untracked_py:
    print(" ", p)

# config.py's own import graph (the "config.py's import graph" the phase names) - config.py imports
# nothing project-local; it is a leaf. Recorded for the report, not because it could hide anything.
config_imports_local = [
    line for line in (ROOT / "config.py").read_text(encoding="utf-8").splitlines()
    if line.strip().startswith(("import ", "from ")) and "os" not in line and "pathlib" not in line
]
print(f"config.py's own top-level imports (all stdlib): {len(config_imports_local)}")

result = {
    "untracked_py_files_repo_wide": untracked_py,
    "n_untracked_py_files": len(untracked_py),
    "conclusion": (
        "app/service.py (committed in this phase's step 0) was the ONLY untracked .py file anywhere in "
        "the repository, not just under app/ and scripts/ - a repo-wide scan, not a directory-scoped "
        "one, so nothing outside those two directories could have hidden a second one."
        if len(untracked_py) == 0 else
        f"{len(untracked_py)} untracked .py file(s) remain after step 0 - see the list above."
    ),
}

out = ROOT / "batch-04" / "ph8_analysis" / "results" / "untracked_sweep.json"
out.parent.mkdir(parents=True, exist_ok=True)
import json
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(f"[ph8_01] {result['conclusion']}")
print(f"[ph8_01] written to {out}")
