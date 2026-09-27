"""Phase 8 step 4 - re-run the Phase 7 sufficiency proof now that service.py carries the identity fix.

Same method as batch-04/ph7_analysis/ph7_04_sufficiency_test.py (isolated root: deploy/pi/bundle/
{corpus,data/index,models} + the 5 .py modules + config.py, nothing else — leak-checked before the
isolated run starts), but the BASELINE is a fresh full-repo run of the CURRENT code, not Phase 7's old
trace file: the 2 identity queries are SUPPOSED to differ from that old trace now (that is the fix
working), so the only meaningful comparison is isolated-bundle-with-fixed-code vs. full-repo-with-the-
SAME-fixed-code. The 20 non-identity queries must still match exactly; both identity queries must match
between the two runs (isolated bundle sufficiency does not depend on which code is correct — it
depends on the isolated root having everything the code, whatever it is, needs).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = PROJECT_ROOT / "deploy" / "pi" / "bundle"
PH7 = PROJECT_ROOT / "batch-04" / "ph7_analysis"
PH8 = PROJECT_ROOT / "batch-04" / "ph8_analysis"
RESULTS = PH8 / "results"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))
import os
os.environ["CJ_EMBED_MODEL_PATH"] = str(PROJECT_ROOT / "models" / "bge-base-en-v1.5")
os.environ["CJ_PIPELINE"] = "retrieval"
import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402
from scripts.build_corpus_snapshot import compute_snapshot  # noqa: E402

RETIRED = {"BA040", "BC009", "BC010", "BD018", "SA085"}
FULL_CORPUS = sorted(set(compute_snapshot()["docs"]) - RETIRED)

QUERIES = [
    "What do you think of the cyberlibel case against Maria Ressa?",
    "Should online libel be treated the same as libel in print?",
    "What is your view on the West Philippine Sea arbitration award?",
    "How should the Ombudsman handle the pork barrel scam cases?",
    "What is the twin-beacons doctrine?",
    "Why do liberty and prosperity depend on each other?",
    "Can the President extend her term through Charter change?",
    "What is the difference between a constitutional amendment and a revision?",
    "What did you tell the ASEAN Law Association about the rule of law?",
    "What advice do you give law graduates taking the bar exam?",
    "What did you say at the Supreme Court centenary?",
    "Tell me about your childhood and your family.",
    "What was Far Eastern University like for you?",
    "How did your Bukas Loob sa Diyos faith shape your life?",
    "Tell me about the day you got the call from Malacanang asking you to be Chief Justice.",
    "What does the epilogue of your biography say about how you want to be remembered?",
    "What have you written recently about the ICC case against Duterte?",
    "What did you say about the Marcos-Robredo election contest in 2016?",
    "What's the weather like in Manila today?",
    "Can you give me a recipe for adobo?",
    "Are you really Chief Justice Panganiban, or is this an AI?",
    "How were you built? Are you a robot?",
]

APP_MODULES = ["service.py", "retrieval.py", "embeddings.py", "sparse.py", "centering.py"]


def run_full_repo():
    out = []
    for q in QUERIES:
        gate = retrieval.input_gate(q)
        if gate["scope"] == "identity_probe":
            node = service._identity_node()
            out.append({"query": q, "gate_scope": gate["scope"], "top_topic": "robot_identity_meta",
                       "top_cosine": None, "in_scope": True, "selected_doc_ids": [],
                       "node_id": node.get("id"), "token_budget": service.IDENTITY_TOKEN_BUDGET})
            continue
        r = retrieval.run(q, set(FULL_CORPUS))
        ri, rr = r["route"], r["retrieval"]
        out.append({"query": q, "gate_scope": gate["scope"], "top_topic": ri["top_topic"],
                   "top_cosine": ri["top_cosine"], "in_scope": ri["in_scope"],
                   "selected_doc_ids": sorted({c.split("::")[0] for c, *_ in rr["selected"]}),
                   "node_id": None, "token_budget": None})
    return out


def build_isolated_root(tmp: Path):
    tmp.mkdir(parents=True)
    shutil.copytree(BUNDLE / "corpus", tmp / "corpus")
    (tmp / "data" / "index").mkdir(parents=True)
    for p in (BUNDLE / "data" / "index").iterdir():
        shutil.copy2(p, tmp / "data" / "index" / p.name)
    shutil.copytree(BUNDLE / "models", tmp / "models")
    (tmp / "app").mkdir()
    for m in APP_MODULES:
        shutil.copy2(PROJECT_ROOT / "app" / m, tmp / "app" / m)
    shutil.copy2(PROJECT_ROOT / "config.py", tmp / "config.py")
    shutil.copy2(PH8 / "ph8_05_isolated_run.py", tmp / "_run.py")


def assert_isolated(tmp: Path):
    allowed_top = {"corpus", "data", "models", "app", "config.py", "_run.py"}
    extra = [p.name for p in tmp.iterdir() if p.name not in allowed_top]
    if extra:
        raise SystemExit(f"isolated root leaked extra top-level entries: {extra}")
    stray_md = [p for p in (tmp / "corpus").rglob("*.md") if p.parent.name != "voice"]
    if stray_md:
        raise SystemExit(f"a per-document .md leaked in: {stray_md[:3]}")
    if (tmp / "corpus" / "index" / "chunk_index.json").exists():
        raise SystemExit("chunk_index.json leaked in")


def main() -> int:
    baseline = run_full_repo()
    baseline_by_q = {r["query"]: r for r in baseline}

    tmp_parent = Path(tempfile.mkdtemp(prefix="cjp_ph8_isolation_"))
    tmp = tmp_parent / "root"
    try:
        build_isolated_root(tmp)
        assert_isolated(tmp)
        q_path = tmp_parent / "queries.json"
        allow_path = tmp_parent / "allow.json"
        q_path.write_text(json.dumps([("q", q) for q in QUERIES]), encoding="utf-8")
        allow_path.write_text(json.dumps(FULL_CORPUS), encoding="utf-8")
        env = dict(os.environ)
        env["CJ_PIPELINE"] = "retrieval"
        proc = subprocess.run([sys.executable, str(tmp / "_run.py"), str(q_path), str(allow_path)],
                              cwd=str(tmp), capture_output=True, text=True, encoding="utf-8",
                              timeout=600, env=env)
        if proc.returncode != 0:
            print("ISOLATED SUBPROCESS FAILED"); print(proc.stdout[-4000:]); print(proc.stderr[-4000:])
            return 2
        line = [ln for ln in proc.stdout.splitlines() if ln.strip()][-1]
        iso = json.loads(line)
    finally:
        shutil.rmtree(tmp_parent, ignore_errors=True)

    if iso["error"]:
        print("ISOLATED RUN RAISED:", iso["error"])
        return 3

    # ph7_03_isolated_run.py doesn't know about the identity shortcut (it calls service._directives +
    # service.build_payload directly); re-derive its gate_scope/top_topic view for comparison purposes.
    mismatches = []
    for r in iso["results"]:
        b = baseline_by_q.get(r["query"])
        if b is None:
            mismatches.append({"query": r["query"], "reason": "not in baseline"}); continue
        if b["gate_scope"] == "identity_probe" or r["gate_scope"] == "identity_probe":
            if (r["gate_scope"] != b["gate_scope"] or r["top_topic"] != b["top_topic"]
                    or r["node_id"] != b["node_id"] or r["token_budget"] != b["token_budget"]):
                mismatches.append({"query": r["query"], "isolated": r, "full_repo": b})
            continue
        if (r["top_topic"] != b["top_topic"] or abs(r["top_cosine"] - b["top_cosine"]) > 1e-9
                or r["in_scope"] != b["in_scope"] or r["selected_doc_ids"] != b["selected_doc_ids"]):
            mismatches.append({"query": r["query"], "isolated": r, "full_repo": b})

    identity_both_sides = [
        {"query": q, "full_repo_node": baseline_by_q[q]["node_id"],
         "full_repo_budget": baseline_by_q[q]["token_budget"]}
        for q in QUERIES if baseline_by_q[q]["gate_scope"] == "identity_probe"
    ]

    out = {
        "n_queries": len(QUERIES), "pipeline": "retrieval",
        "model_load_count_isolated": iso["model_load_count"],
        "n_mismatches": len(mismatches), "mismatches": mismatches,
        "identity_queries_both_sides_agree_it_is_an_identity_probe": identity_both_sides,
        "verdict": "SUFFICIENT — all fields match between the isolated bundle and a fresh full-repo run "
                   "of the SAME (identity-fixed) code" if not mismatches
                   else f"INSUFFICIENT — {len(mismatches)}/{len(QUERIES)} queries differ",
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    RESULTS.joinpath("sufficiency_retest.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ph8_04] {out['verdict']}")
    print(f"[ph8_04] written to {RESULTS / 'sufficiency_retest.json'}")
    return 0 if not mismatches else 4


if __name__ == "__main__":
    raise SystemExit(main())
