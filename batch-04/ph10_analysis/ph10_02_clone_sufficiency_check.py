"""Phase 10 step 4 - the proof that makes the release real: clone the PUSHED tag fresh, exactly as
install.sh would, and from that clone alone confirm the five modules, 1,290 documents, verify_pin at
1,295, and the 22-query sufficiency proof with CJ_PIPELINE=retrieval.

    python batch-04/ph10_analysis/ph10_02_clone_sufficiency_check.py [existing_clone_dir]

With no argument, clones release/kb-v2-2026-09-27 fresh into a temp directory (~500 MB download,
including the LFS-tracked encoder). Pass an existing clone's path to reuse one instead of re-cloning -
this run reused the clone already made and verified in this phase's own session
(C:\\Users\\ASUS\\AppData\\Local\\Temp\\claude\\ph10t2), rather than downloading ~500 MB a second time
for the same tag; the clone step itself was already exercised once via a plain `git clone -b
release/kb-v2-2026-09-27 --depth 1 <origin> <tmp>` and is not the part this script re-verifies.

The bare repo root is NOT what this script points the pipeline at: data/index/'s runtime files
(pilot_dense.npy, pilot_sparse.pkl, sparse_phrase_dict.json, date_index.json) are git-ignored and were
never committed at the repo root in ANY commit - only inside the two bundle copies
(deploy/pi/bundle/, Bundle Folder/cjap-bundle/). That is by design (Phase 7-9's point), not something to
route around: the test targets Bundle Folder/cjap-bundle/, the exact self-contained unit an operator
would copy to a Pi (see batch-04/ph9_analysis's own sufficiency proof for the same reasoning applied
against the pre-push working tree).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "release/kb-v2-2026-09-27"
REMOTE = "https://github.com/Supervaise-Inc/CJAP.git"
RUN_HELPER = Path(__file__).resolve().parent / "ph10_01_clone_run_helper.py"


def clone_fresh(dest: Path):
    subprocess.run(["git", "-c", "core.longpaths=true", "clone", "-b", TAG, "--depth", "1", REMOTE,
                    str(dest)], check=True)


def main() -> int:
    reused = len(sys.argv) > 1
    clone_dir = Path(sys.argv[1]).resolve() if reused else Path(tempfile.mkdtemp(prefix="cjp_release_clone_"))
    if not reused:
        clone_fresh(clone_dir)

    checks = {"reused_existing_clone": reused, "clone_dir": str(clone_dir)}

    # HEAD / detached-at-tag
    head = subprocess.run(["git", "-C", str(clone_dir), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    checks["clone_head"] = head

    # the five modules + config.py
    modules = ["app/service.py", "app/retrieval.py", "app/embeddings.py", "app/sparse.py",
              "app/centering.py", "config.py"]
    checks["modules_present"] = {m: (clone_dir / m).is_file() for m in modules}

    # 1,290 documents
    doc_jsons = [p for p in (clone_dir / "corpus").rglob("*.json")
                if "voice" not in p.parts and "index" not in p.parts]
    checks["corpus_doc_count"] = len(doc_jsons)

    # verify_pin
    py = sys.executable
    vp = subprocess.run([py, str(clone_dir / "scripts" / "verify_pin.py")],
                        cwd=str(clone_dir), capture_output=True, text=True)
    checks["verify_pin_returncode"] = vp.returncode
    checks["verify_pin_stdout"] = vp.stdout.strip()

    # encoder integrity (byte-exact, not converted/quantised)
    enc = clone_dir / "deploy" / "pi" / "bundle" / "models" / "bge-base-en-v1.5" / "model.safetensors"
    checks["encoder_bytes"] = enc.stat().st_size if enc.exists() else None
    sha = subprocess.run(["python", "-c",
                          f"import hashlib; print(hashlib.sha256(open(r'{enc}','rb').read()).hexdigest())"],
                         capture_output=True, text=True).stdout.strip()
    checks["encoder_sha256"] = sha
    checks["encoder_sha256_expected"] = "c7c1988aae201f80cf91a5dbbd5866409503b89dcaba877ca6dba7dd0a5167d7"

    # 22-query sufficiency proof: clone's Bundle Folder/cjap-bundle/ vs. THIS repo's own copy
    clone_out = clone_dir / "_ph10_out.json"
    proc = subprocess.run([py, str(RUN_HELPER), str(clone_dir)],
                          capture_output=True, text=True, timeout=600)
    checks["clone_run_returncode"] = proc.returncode
    clone_result = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else None

    base_proc = subprocess.run([py, str(RUN_HELPER), str(ROOT)],
                               capture_output=True, text=True, timeout=600)
    base_result = json.loads(base_proc.stdout.strip().splitlines()[-1]) if base_proc.returncode == 0 else None

    mismatches = []
    if clone_result and base_result and not clone_result["error"] and not base_result["error"]:
        cb = {r["query"]: r for r in clone_result["results"]}
        bb = {r["query"]: r for r in base_result["results"]}
        for q, r in cb.items():
            b = bb.get(q)
            if b is None:
                mismatches.append({"query": q, "reason": "missing from baseline"}); continue
            if r.get("gate_scope") == "identity_probe" or b.get("gate_scope") == "identity_probe":
                if (r.get("gate_scope") != b.get("gate_scope") or r.get("node_id") != b.get("node_id")
                        or r.get("token_budget") != b.get("token_budget")):
                    mismatches.append({"query": q, "clone": r, "baseline": b})
                continue
            if (r["top_topic"] != b["top_topic"] or abs(r["top_cosine"] - b["top_cosine"]) > 1e-9
                    or r["in_scope"] != b["in_scope"] or r["selected_doc_ids"] != b["selected_doc_ids"]
                    or r["payload_sha256"] != b["payload_sha256"]):
                mismatches.append({"query": q, "clone": r, "baseline": b})

    checks["sufficiency"] = {
        "n_queries": len(clone_result["results"]) if clone_result else 0,
        "clone_error": clone_result["error"] if clone_result else "clone run itself failed",
        "baseline_error": base_result["error"] if base_result else "baseline run itself failed",
        "n_mismatches": len(mismatches), "mismatches": mismatches,
        "verdict": "SUFFICIENT" if clone_result and base_result and not mismatches
                   and not clone_result["error"] and not base_result["error"] else "INSUFFICIENT",
    }

    all_ok = (
        all(checks["modules_present"].values())
        and checks["corpus_doc_count"] == 1290
        and checks["verify_pin_returncode"] == 0
        and checks["encoder_sha256"] == checks["encoder_sha256_expected"]
        and checks["sufficiency"]["verdict"] == "SUFFICIENT"
    )
    checks["overall_verdict"] = "RELEASE VERIFIED — a clone that has been tested" if all_ok else "FAILED"

    if not reused:
        shutil.rmtree(clone_dir, ignore_errors=True)

    out_path = ROOT / "batch-04" / "ph10_analysis" / "results" / "clone_sufficiency_check.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ph10_02] {checks['overall_verdict']}")
    print(f"[ph10_02] written to {out_path}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
