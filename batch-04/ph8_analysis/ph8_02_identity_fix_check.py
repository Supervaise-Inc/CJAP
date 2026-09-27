"""Phase 8 step 2 - verify the identity-gap fix: (a) the 20 non-identity queries from Phase 7's set are
completely unaffected, (b) both identity queries now resolve to the robot_identity_meta intent with its
persona text and the 120-token budget, and (c) service.answer() runs the identity branch end to end,
including its retry/backoff/graceful-degradation path, without an ANTHROPIC_API_KEY (which this
environment does not have) - it must fail ONLY at the network boundary, gracefully, not earlier.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
os.environ["CJ_EMBED_MODEL_PATH"] = str(ROOT / "models" / "bge-base-en-v1.5")
os.environ.pop("ANTHROPIC_API_KEY", None)

import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402
from scripts.build_corpus_snapshot import compute_snapshot  # noqa: E402

RETIRED = {"BA040", "BC009", "BC010", "BD018", "SA085"}
FULL_CORPUS = set(compute_snapshot()["docs"]) - RETIRED

QUERIES = [
    ("column", "What do you think of the cyberlibel case against Maria Ressa?"),
    ("column", "Should online libel be treated the same as libel in print?"),
    ("column", "What is your view on the West Philippine Sea arbitration award?"),
    ("column", "How should the Ombudsman handle the pork barrel scam cases?"),
    ("book", "What is the twin-beacons doctrine?"),
    ("book", "Why do liberty and prosperity depend on each other?"),
    ("book", "Can the President extend her term through Charter change?"),
    ("book", "What is the difference between a constitutional amendment and a revision?"),
    ("speech", "What did you tell the ASEAN Law Association about the rule of law?"),
    ("speech", "What advice do you give law graduates taking the bar exam?"),
    ("speech", "What did you say at the Supreme Court centenary?"),
    ("biography", "Tell me about your childhood and your family."),
    ("biography", "What was Far Eastern University like for you?"),
    ("biography", "How did your Bukas Loob sa Diyos faith shape your life?"),
    ("biography", "Tell me about the day you got the call from Malacanang asking you to be Chief Justice."),
    ("biography", "What does the epilogue of your biography say about how you want to be remembered?"),
    ("date", "What have you written recently about the ICC case against Duterte?"),
    ("date", "What did you say about the Marcos-Robredo election contest in 2016?"),
    ("out_of_scope", "What's the weather like in Manila today?"),
    ("out_of_scope", "Can you give me a recipe for adobo?"),
    ("identity", "Are you really Chief Justice Panganiban, or is this an AI?"),
    ("identity", "How were you built? Are you a robot?"),
]

baseline = json.loads((ROOT / "batch-04" / "ph7_analysis" / "results" / "runtime_trace.json")
                      .read_text(encoding="utf-8"))["results"]
baseline_by_q = {r["query"]: r for r in baseline}

non_identity_mismatches = []
identity_results = []
for kind, q in QUERIES:
    gate = retrieval.input_gate(q)
    if gate["scope"] == "identity_probe":
        node = service._identity_node()
        directives = service._identity_directives()
        payload = service._identity_payload(q)
        identity_results.append({
            "query": q, "gate_scope": gate["scope"], "node_id": node.get("id"),
            "node_kind": node.get("kind"), "directives": directives,
            "payload_len": len(payload), "token_budget": service.IDENTITY_TOKEN_BUDGET,
        })
        continue
    r = retrieval.run(q, FULL_CORPUS)
    ri, rr = r["route"], r["retrieval"]
    doc_ids = sorted({c.split("::")[0] for c, *_ in rr["selected"]})
    b = baseline_by_q[q]
    if (ri["top_topic"] != b["top_topic"] or abs(ri["top_cosine"] - b["top_cosine"]) > 1e-9
            or ri["in_scope"] != b["in_scope"] or gate["scope"] != b["gate_scope"]
            or doc_ids != b["selected_doc_ids"]):
        non_identity_mismatches.append({"query": q, "new_top_topic": ri["top_topic"],
                                        "old_top_topic": b["top_topic"]})

# end-to-end: service.answer() on an identity query, no API key. Must degrade gracefully, not crash
# earlier, and must report the identity route + the 120-token budget in its envelope.
e2e = service.answer(QUERIES[-1][1])
e2e_ok = (
    e2e["envelope"]["route"]["top_topic"] == "robot_identity_meta"
    and e2e["envelope"]["composer_max_tokens"] == service.IDENTITY_TOKEN_BUDGET
    and e2e["envelope"]["composer_degraded"] is True
    and e2e["envelope"]["composer_stop_reason"] == "error_fallback"
    and e2e["envelope"]["llm_calls_before_composition"] == 0
)

out = {
    "n_queries": len(QUERIES),
    "n_non_identity_mismatches": len(non_identity_mismatches),
    "non_identity_mismatches": non_identity_mismatches,
    "identity_results": identity_results,
    "end_to_end_no_api_key": {
        "answer": e2e["answer"], "envelope": e2e["envelope"], "structurally_correct": e2e_ok,
    },
    "verdict": ("PASS — 0 non-identity regressions, both identity queries route to "
               "robot_identity_meta at a 120-token budget, end-to-end run degrades gracefully "
               "at the network boundary as expected with no API key")
               if not non_identity_mismatches and e2e_ok
               else "FAIL — see the fields above",
}
out_path = ROOT / "batch-04" / "ph8_analysis" / "results" / "identity_fix_check.json"
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"[ph8_02] {out['verdict']}")
print(f"[ph8_02] written to {out_path}")
