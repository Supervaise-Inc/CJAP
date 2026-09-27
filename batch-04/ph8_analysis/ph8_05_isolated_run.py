"""Runs INSIDE an isolated root (see ph8_04_sufficiency_retest.py, which builds the root and launches
this as a fresh subprocess with cwd=<isolated root>). Unlike ph7_analysis/ph7_03_isolated_run.py, this
calls retrieval.input_gate() and BRANCHES on it (service._identity_node() for an identity probe,
retrieval.run() otherwise) — the shape service.answer() itself now has post-Phase-8, stopping short of
the actual composer network call the same way ph7_03 did, so this can run with no ANTHROPIC_API_KEY.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # the isolated root (cwd), NOT the real repo
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "app"))
os.environ["CJ_EMBED_MODEL_PATH"] = str(HERE / "models" / "bge-base-en-v1.5")
os.environ["CJ_PIPELINE"] = "retrieval"

import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402
import embeddings  # noqa: E402

assert Path(config.REPO_ROOT).resolve() == HERE, (config.REPO_ROOT, HERE)

QUERIES = [q for _, q in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))]
FULL_CORPUS = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))

results = []
error = None
try:
    for q in QUERIES:
        gate = retrieval.input_gate(q)
        if gate["scope"] == "identity_probe":
            node = service._identity_node()
            results.append({"query": q, "gate_scope": gate["scope"], "top_topic": "robot_identity_meta",
                           "top_cosine": None, "in_scope": True, "selected_doc_ids": [],
                           "node_id": node.get("id"), "token_budget": service.IDENTITY_TOKEN_BUDGET})
            continue
        r = retrieval.run(q, FULL_CORPUS)
        ri, rr = r["route"], r["retrieval"]
        results.append({"query": q, "gate_scope": gate["scope"], "top_topic": ri["top_topic"],
                       "top_cosine": ri["top_cosine"], "in_scope": ri["in_scope"],
                       "selected_doc_ids": sorted({c.split("::")[0] for c, *_ in rr["selected"]}),
                       "node_id": None, "token_budget": None})
except Exception as e:
    import traceback
    error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

print(json.dumps({
    "repo_root_resolved_to_isolated": True,
    "model_load_count": embeddings.model_load_count(),
    "error": error,
    "results": results,
}, ensure_ascii=False))
