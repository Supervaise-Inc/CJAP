"""Phase 9 step 4 - prove Bundle Folder/cjap-bundle/ is sufficient, alone, in BOTH CJ_PIPELINE modes.

RETRIEVAL mode: full self-containment. cjap-bundle/ ships its own app/{service,retrieval,embeddings,
sparse,centering}.py + config.py + corpus + data/index + models - literally everything
retrieval.run()/service.answer() need. Proof: run the same 22 queries as a subprocess with cwd=cjap-
bundle/ and NOTHING from the real repo on sys.path, and diff every field against a fresh full-repo run
of the identical code.

LEGACY mode: cjap-bundle/ deliberately does NOT ship app/answer_pipeline.py, speech_streaming.py or the
rest of the legacy pipeline's code - legacy is unchanged by this batch and already reaches the Pi
through the existing install.sh; that code is not part of what Phase 7-9 built. So "legacy still works
from the bundle" cannot mean "run the whole legacy pipeline using only files in the bundle" (there is no
entry point in it at all) - it means the bundle's DATA (corpus/, topic_map.json, voice_card.md,
router_prompt.md) remains fully compatible with the UNCHANGED, real repo's app/answer_pipeline.py: that
CorpusArtifacts loads from cjap-bundle/corpus/ without error, that build_context() resolves citations
from cjap-bundle/corpus/**/<id>.json for a spread of routings drawn from the 22-query concept set, and
that the identity intent (force_meta_routing -> robot_identity_meta) is still reachable and carries its
persona/definition text. This is the correctness check that actually matters for "legacy still works":
whether swapping in this bundle's data breaks the pipeline that does not change.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = PROJECT_ROOT / "Bundle Folder"
CJAP = BUNDLE / "cjap-bundle"
PH9 = PROJECT_ROOT / "batch-04" / "ph9_analysis"
RESULTS = PH9 / "results"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))
import os
os.environ["CJ_EMBED_MODEL_PATH"] = str(PROJECT_ROOT / "models" / "bge-base-en-v1.5")
import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402
from scripts.build_corpus_snapshot import compute_snapshot  # noqa: E402

RETIRED = {"BA040", "BC009", "BC010", "BD018", "SA085"}
FULL_CORPUS = sorted(set(compute_snapshot()["docs"]) - RETIRED)

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


# =====================================================================================================
# leak check — cjap-bundle/ must contain ONLY its own material
# =====================================================================================================
def leak_check() -> dict:
    allowed_top = {"MANIFEST.md", "checksums.sha256", "config.py", "app", "corpus", "data", "models"}
    extra = [p.name for p in CJAP.iterdir() if p.name not in allowed_top]
    stray_md = [p for p in (CJAP / "corpus").rglob("*.md") if p.parent.name != "voice"]
    chunk_index_leak = (CJAP / "corpus" / "index" / "chunk_index.json").exists()
    got_app = sorted(p.name for p in (CJAP / "app").iterdir())
    want_app = sorted(["service.py", "retrieval.py", "embeddings.py", "sparse.py", "centering.py"])
    ok = not extra and not stray_md and not chunk_index_leak and got_app == want_app
    return {"ok": ok, "extra_top_level": extra, "stray_md": [str(p) for p in stray_md],
           "chunk_index_leaked": chunk_index_leak, "app_contents": got_app}


# =====================================================================================================
# retrieval mode
# =====================================================================================================
def run_retrieval_baseline():
    out = []
    for _, q in QUERIES:
        gate = retrieval.input_gate(q)
        if gate["scope"] == "identity_probe":
            node = service._identity_node()
            out.append({"query": q, "gate_scope": gate["scope"], "top_topic": "robot_identity_meta",
                       "top_cosine": None, "in_scope": True, "selected_doc_ids": [],
                       "node_id": node.get("id"), "token_budget": service.IDENTITY_TOKEN_BUDGET})
            continue
        r = retrieval.run(q, set(FULL_CORPUS))
        ri, rr = r["route"], r["retrieval"]
        directives = service._directives(q, ri)
        payload = service.build_payload(q, rr["selected"], directives)
        out.append({"query": q, "gate_scope": gate["scope"], "top_topic": ri["top_topic"],
                   "top_cosine": ri["top_cosine"], "in_scope": ri["in_scope"],
                   "selected_doc_ids": sorted({c.split("::")[0] for c, *_ in rr["selected"]}),
                   "node_id": None, "token_budget": None,
                   "payload_sha256": __import__("hashlib").sha256(payload.encode("utf-8")).hexdigest()})
    return out


def run_retrieval_from_bundle():
    q_path = PH9 / "_tmp_queries.json"
    allow_path = PH9 / "_tmp_allow.json"
    q_path.write_text(json.dumps(QUERIES), encoding="utf-8")
    allow_path.write_text(json.dumps(FULL_CORPUS), encoding="utf-8")
    script = PH9 / "ph9_02_isolated_run.py"
    import shutil
    shutil.copy2(script, CJAP / "_run.py")   # must live INSIDE cjap-bundle/ so __file__.parent == CJAP
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"   # verifying the bundle must not leave __pycache__ inside it
    try:
        proc = subprocess.run([sys.executable, "-B", str(CJAP / "_run.py"), str(q_path), str(allow_path)],
                              cwd=str(CJAP), capture_output=True, text=True, encoding="utf-8", timeout=600,
                              env=env)
    finally:
        (CJAP / "_run.py").unlink(missing_ok=True)
        q_path.unlink(missing_ok=True)
        allow_path.unlink(missing_ok=True)
        for pc in CJAP.rglob("__pycache__"):
            shutil.rmtree(pc, ignore_errors=True)
    if proc.returncode != 0:
        return None, f"subprocess failed rc={proc.returncode}\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}"
    line = [ln for ln in proc.stdout.splitlines() if ln.strip()][-1]
    return json.loads(line), None


def compare_retrieval(baseline, iso) -> list:
    baseline_by_q = {r["query"]: r for r in baseline}
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
                or r["in_scope"] != b["in_scope"] or r["selected_doc_ids"] != b["selected_doc_ids"]
                or r["payload_sha256"] != b["payload_sha256"]):
            mismatches.append({"query": r["query"], "isolated": r, "full_repo": b})
    return mismatches


# =====================================================================================================
# legacy mode — the real (unbundled) answer_pipeline.py, pointed at the bundle's data
# =====================================================================================================
def legacy_check() -> dict:
    import answer_pipeline as ap

    bundle_config = ap.Config(
        corpus_root=CJAP / "corpus",
        voice_dir=CJAP / "corpus" / "voice",
        topic_map_path=CJAP / "corpus" / "voice" / "topic_map.json",
        voice_card_path=CJAP / "corpus" / "voice" / "voice_card.md",
        router_prompt_path=CJAP / "corpus" / "voice" / "router_prompt.md",
    )
    artifacts = ap.CorpusArtifacts(config=bundle_config)

    rows = []
    ok = True
    for kind, q in QUERIES:
        if kind == "identity":
            routing = ap.force_meta_routing("test")
        else:
            ri = retrieval.route(q)   # deterministic centroid pick, just to get a plausible topic id
            primary = ri["top_topic"] if ri["top_topic"] in artifacts.valid_topic_ids else \
                next(iter(artifacts.topics))
            routing = {"primary_topic": primary, "secondary_topics": [], "confidence": "high"}
        try:
            ctx = ap.build_context(routing, artifacts)
            has_docs = "<source_documents>" in ctx and ctx.strip() != ""
        except Exception as e:
            has_docs = False
            ok = False
            rows.append({"query": q, "kind": kind, "topic": routing["primary_topic"],
                        "error": f"{type(e).__name__}: {e}"})
            continue
        rows.append({"query": q, "kind": kind, "topic": routing["primary_topic"],
                    "context_assembled": has_docs, "context_chars": len(ctx)})
        if not has_docs and kind != "out_of_scope":
            ok = False

    identity_node_present = "robot_identity_meta" in artifacts.valid_topic_ids
    identity_definition = artifacts.topics.get("robot_identity_meta", {}).get("definition", "")
    ok = ok and identity_node_present and bool(identity_definition)
    return {"ok": ok, "n_queries": len(QUERIES), "identity_node_present": identity_node_present,
           "identity_definition_len": len(identity_definition), "rows": rows}


def main() -> int:
    import shutil
    for pc in CJAP.rglob("__pycache__"):   # defensive: a prior manual check may have left one behind
        shutil.rmtree(pc, ignore_errors=True)
    leak = leak_check()
    print(f"[ph9_03] leak check: {'OK' if leak['ok'] else 'FAILED'}")
    if not leak["ok"]:
        print(leak)
        return 2

    baseline = run_retrieval_baseline()
    iso, err = run_retrieval_from_bundle()
    if err:
        print("[ph9_03] RETRIEVAL isolated run failed:", err)
        return 3
    mismatches = compare_retrieval(baseline, iso)

    legacy = legacy_check()

    out = {
        "leak_check": leak,
        "retrieval_mode": {
            "n_queries": len(QUERIES), "model_load_count_isolated": iso["model_load_count"],
            "n_mismatches": len(mismatches), "mismatches": mismatches,
            "verdict": "SUFFICIENT" if not mismatches else "INSUFFICIENT",
        },
        "legacy_mode": {
            "what_this_checks": ("cjap-bundle/ ships no legacy pipeline code (unchanged, already on "
                                 "the Pi via install.sh) - this proves the bundle's DATA does not break "
                                 "the real, unbundled app/answer_pipeline.py: CorpusArtifacts loads, "
                                 "build_context() resolves citations for every query topic, and the "
                                 "identity intent's persona text is present."),
            **legacy,
            "verdict": "SUFFICIENT (data compatible with the unchanged legacy pipeline)" if legacy["ok"]
                       else "INSUFFICIENT",
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    RESULTS.joinpath("sufficiency_both_modes.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ph9_03] retrieval: {out['retrieval_mode']['verdict']} "
          f"({out['retrieval_mode']['n_mismatches']}/{len(QUERIES)} mismatches)")
    print(f"[ph9_03] legacy: {out['legacy_mode']['verdict']}")
    print(f"[ph9_03] written to {RESULTS / 'sufficiency_both_modes.json'}")
    return 0 if (not mismatches and legacy["ok"]) else 4


if __name__ == "__main__":
    raise SystemExit(main())
