"""Runs INSIDE (a) the fresh clone of release/kb-v2-2026-09-27 or (b) the real repo, pointed at
Bundle Folder/cjap-bundle/ as the self-contained runtime root - the same self-consistent layout Phase 9
proved sufficient on its own (app/ + config.py + corpus/ + data/index/ + models/ all at consistent
relative depths). The bare repo root cannot run this pipeline standalone: data/index/'s runtime files
(pilot_dense.npy, pilot_sparse.pkl, sparse_phrase_dict.json, date_index.json) are git-ignored and were
never committed there - only inside the two bundle copies. That is by design (Phase 7-9's whole point),
not a defect this script works around; it is why the test targets cjap-bundle/, exactly what an operator
would actually copy to a Pi.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()          # the clone root OR the real repo root
CJAP = ROOT / "Bundle Folder" / "cjap-bundle"
sys.path.insert(0, str(CJAP))
sys.path.insert(0, str(CJAP / "app"))
os.environ["CJ_EMBED_MODEL_PATH"] = str(CJAP / "models" / "bge-base-en-v1.5")
os.environ["CJ_PIPELINE"] = "retrieval"

import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402
import embeddings  # noqa: E402

assert Path(config.REPO_ROOT).resolve() == CJAP, (config.REPO_ROOT, CJAP)

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
assert len(QUERIES) == 22

# The full-corpus allowlist, derived from cjap-bundle's OWN corpus (not the repo's data/csv, which is
# not part of the bundle) - just the doc ids actually present.
FULL_CORPUS = {p.stem for p in (CJAP / "corpus").rglob("*.json")
              if "voice" not in p.parts and "index" not in p.parts}
assert len(FULL_CORPUS) == 1290, len(FULL_CORPUS)

results = []
error = None
try:
    for q in QUERIES:
        gate = retrieval.input_gate(q)
        if gate["scope"] == "identity_probe":
            node = service._identity_node()
            results.append({"query": q, "gate_scope": gate["scope"], "top_topic": "robot_identity_meta",
                           "node_id": node.get("id"), "token_budget": service.IDENTITY_TOKEN_BUDGET,
                           "selected_doc_ids": []})
            continue
        r = retrieval.run(q, FULL_CORPUS)
        ri, rr = r["route"], r["retrieval"]
        directives = service._directives(q, ri)
        payload = service.build_payload(q, rr["selected"], directives)
        results.append({"query": q, "gate_scope": gate["scope"], "top_topic": ri["top_topic"],
                       "top_cosine": ri["top_cosine"], "in_scope": ri["in_scope"],
                       "selected_doc_ids": sorted({c.split("::")[0] for c, *_ in rr["selected"]}),
                       "payload_sha256": __import__("hashlib").sha256(payload.encode("utf-8")).hexdigest()})
except Exception as e:
    import traceback
    error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

print(json.dumps({
    "root_tested": str(ROOT), "cjap_bundle_resolved": str(CJAP),
    "model_load_count": embeddings.model_load_count(),
    "n_full_corpus": len(FULL_CORPUS),
    "error": error,
    "results": results,
}, ensure_ascii=False))
