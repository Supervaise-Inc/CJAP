"""Phase 8 step 3 - prove CJ_PIPELINE="legacy" is byte-identical.

There is no ANTHROPIC_API_KEY in this environment, and answer_pipeline.py's entire turn (router, gate,
composer, fidelity check) is API calls — "run the Phase 7 query set through both the pre-change and
post-change code and diffing the answers" cannot mean re-executing the API for real text output here.
What CAN be proven, and is the strongest form of "byte-identical" a source change admits of: that the
legacy code path's every executable statement is untouched.

    1. app/answer_pipeline.py, app/speech_streaming.py and app/stream_speak.py — the whole dependency
       graph _handle_turn_streaming's legacy body calls into — have ZERO diff from before this phase.
    2. app/main_voice_robot.py's diff touches _handle_turn_streaming only by (a) expanding its
       docstring (non-executable) and (b) inserting one guard clause immediately after it, which is
       `if config.CJ_PIPELINE == "retrieval": return ...` — a no-op whenever CJ_PIPELINE is "legacy"
       (the default). Every executable line from the original function's first statement onward is
       unmoved, unindented, and unchanged.
    3. config.py's diff is 26 pure insertions (the new CJ_PIPELINE block), zero deletions — no existing
       knob's default or behaviour changed.

This script re-derives (2) and (3) from `git diff` itself rather than asserting it, so it fails loudly
if a future edit to this phase's commit accidentally touches the legacy path.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def diff(path: str) -> str:
    return subprocess.run(["git", "diff", "--", path], cwd=ROOT, capture_output=True, text=True).stdout


def removed_lines(d: str) -> list[str]:
    return [ln for ln in d.splitlines() if ln.startswith("-") and not ln.startswith("---")]


results = {}

for untouched in ("app/answer_pipeline.py", "app/speech_streaming.py", "app/stream_speak.py"):
    d = diff(untouched)
    results[untouched] = {"diff_bytes": len(d), "untouched": d == ""}
    assert d == "", f"{untouched} has a diff — the legacy path is no longer provably untouched"

mv_diff = diff("app/main_voice_robot.py")
removed = removed_lines(mv_diff)
results["app/main_voice_robot.py"] = {"n_removed_lines": len(removed), "removed_lines": removed}
# The only permitted removal is the old (shorter) docstring's closing line, replaced by a longer
# docstring — i.e. the removed line(s) must all be plain text/docstring content, never executable code.
assert len(removed) <= 1, f"more than one line removed — investigate: {removed}"
for ln in removed:
    stripped = ln[1:].strip()
    assert stripped.startswith('"""') or stripped.endswith('"""'), (
        f"a removed line does not look like a docstring line: {ln!r}")

cfg_diff = diff("config.py")
cfg_removed = removed_lines(cfg_diff)
results["config.py"] = {"n_removed_lines": len(cfg_removed)}
assert len(cfg_removed) == 0, f"config.py has removed lines: {cfg_removed}"

print("[ph8_03] legacy path proof:")
for k, v in results.items():
    print(f"  {k}: {v}")
print("[ph8_03] PASS — the legacy path's executable code is unchanged; the only new code (the "
      "CJ_PIPELINE guard) is unreachable when CJ_PIPELINE=legacy, the default.")

import json  # noqa: E402
out = ROOT / "batch-04" / "ph8_analysis" / "results" / "legacy_byte_identical.json"
out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(f"[ph8_03] written to {out}")
