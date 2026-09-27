"""
Runs INSIDE an isolated root (see ph7_04_sufficiency_test.py, which builds the root and launches this as
a fresh subprocess with cwd=<isolated root>). Not meant to be run from the real repo - it imports
whatever `config`/`retrieval`/`service` resolve to on sys.path[0], which the isolated root's own copies
of those five .py files will be, if the isolation actually worked. Prints one JSON object to stdout.
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

import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402
import embeddings  # noqa: E402

assert Path(config.REPO_ROOT).resolve() == HERE, (config.REPO_ROOT, HERE)   # prove no fallback to the real repo

QUERIES = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))         # [[kind, query], ...]
FULL_CORPUS = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))

results = []
error = None
try:
    for kind, q in QUERIES:
        gate = retrieval.input_gate(q)
        r = retrieval.run(q, FULL_CORPUS)
        ri, rr = r["route"], r["retrieval"]
        directives = service._directives(q, ri)
        payload = service.build_payload(q, rr["selected"], directives)
        system = service._composer_system()
        selected = [c for c, *_ in rr["selected"]]
        results.append({
            "kind": kind, "query": q, "gate_scope": gate["scope"],
            "top_topic": ri["top_topic"], "top_cosine": ri["top_cosine"], "in_scope": ri["in_scope"],
            "selected_chunk_ids": selected,
            "selected_doc_ids": sorted({c.split("::")[0] for c in selected}),
            "payload_sha256": __import__("hashlib").sha256(payload.encode("utf-8")).hexdigest(),
            "payload_chars": len(payload), "system_chars": len(system),
        })
except Exception as e:
    import traceback
    error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

print(json.dumps({
    "repo_root_resolved_to_isolated": True,
    "model_load_count": embeddings.model_load_count(),
    "error": error,
    "results": results,
}, ensure_ascii=False))
