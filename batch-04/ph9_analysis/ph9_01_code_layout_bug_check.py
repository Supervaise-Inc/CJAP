"""Phase 9 step 2 - empirically confirm the flat code/ layout the phase spec lists is broken, and that
the app/ + config.py-at-root split scripts/build_bundle_folder.py uses instead is not.

config.py computes REPO_ROOT = Path(__file__).resolve().parent (one hop: it normally sits AT the repo
root). app/service.py, retrieval.py, embeddings.py, sparse.py and centering.py each compute their own
_REPO_ROOT = Path(__file__).resolve().parent.parent (two hops: they normally sit one level under the
repo root, in app/). Put config.py at the SAME depth as those five (a flat code/ folder) and its
REPO_ROOT lands one level too deep - every path it defines from data/index/ or corpus/ points at a
directory that does not exist. config.py imports nothing project-local, so this is checked directly
against it (the definitive case), then cross-checked against the ACTUAL built Bundle Folder/cjap-bundle/
(where config.py sits at the payload root and the five modules sit in app/, agreeing with each other -
already confirmed live in this phase's own build+verify step, restated here as a committed record).
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def probe(config_py_at: str) -> dict:
    """config_py_at: 'flat' (same dir as a marker 2 hops from data/) or 'root' (1 hop from data/)."""
    with tempfile.TemporaryDirectory(prefix="cjp_layout_probe_") as tmp:
        tmp = Path(tmp)
        (tmp / "data" / "index").mkdir(parents=True)
        (tmp / "data" / "index" / "marker.txt").write_text("x", encoding="utf-8")
        if config_py_at == "flat":
            codedir = tmp / "code"
        else:
            codedir = tmp
        codedir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "config.py", codedir / "config.py")
        code = (f'import sys; sys.path.insert(0, r"{codedir}")\n'
                'import config\n'
                'print(config.REPO_ROOT)\n'
                'print((config.REPO_ROOT / "data" / "index" / "marker.txt").exists())\n')
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        lines = proc.stdout.strip().splitlines()
        return {
            "config_py_placement": config_py_at, "expected_repo_root": str(tmp),
            "actual_repo_root": lines[0] if lines else None,
            "finds_the_real_data_dir": lines[1] if len(lines) > 1 else None,
            "stderr": proc.stderr[-300:] if proc.returncode else None,
        }


flat = probe("flat")     # config.py alongside the app modules, as the phase's literal spec lists it
root = probe("root")     # config.py at the payload root, one level above app/ — what is actually shipped

# Cross-check against the REAL built folder: both computed roots must already agree there (this just
# restates, as a committed check, what build_bundle_folder.py's own build + this phase's manual
# verification already established for the genuine service.py/retrieval.py/config.py trio).
bundle = ROOT / "Bundle Folder" / "cjap-bundle"
real = None
if bundle.exists():
    code = (f'import sys; sys.path.insert(0, r"{bundle}"); sys.path.insert(0, r"{bundle / "app"}")\n'
            'import config, retrieval\n'
            'print(config.REPO_ROOT)\nprint(retrieval._REPO_ROOT)\n'
            'print(config.REPO_ROOT == retrieval._REPO_ROOT)\n'
            'print(config.CENTROIDS_META_PATH.exists())\n')
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    lines = proc.stdout.strip().splitlines()
    real = {
        "config_repo_root": lines[0] if len(lines) > 0 else None,
        "retrieval_repo_root": lines[1] if len(lines) > 1 else None,
        "roots_agree": lines[2] if len(lines) > 2 else None,
        "config_finds_real_centroids_meta": lines[3] if len(lines) > 3 else None,
    }

out = {
    "synthetic_probe": {"flat_code_folder_the_literal_phase_spec": flat,
                        "config_at_payload_root_what_is_shipped": root},
    "real_bundle_cross_check": real,
    "conclusion": (
        f"CONFIRMED broken: flat placement finds the real data dir = {flat['finds_the_real_data_dir']}. "
        f"CONFIRMED correct: root placement finds it = {root['finds_the_real_data_dir']}. "
        f"Real built Bundle Folder/cjap-bundle/: roots_agree={real['roots_agree'] if real else 'N/A - not built yet'}, "
        f"config finds its real centroids meta={real['config_finds_real_centroids_meta'] if real else 'N/A'}."
    ),
}
out_path = ROOT / "batch-04" / "ph9_analysis" / "results" / "code_layout_bug_check.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(out["conclusion"])
print(f"[ph9_01] written to {out_path}")
