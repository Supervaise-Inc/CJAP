"""
Phase 7 step 1 - instrument a cold run and record every file the runtime opens. Not a hand-written list.

Target: the "new-arch" deterministic retrieval pipeline (app/retrieval.py + app/service.py; config.py
calls it "[NEW-ARCH] ... runs TODAY"). It is the ONLY pipeline in this repo that can run end to end
without an ANTHROPIC_API_KEY up to the point the composer needs one: embed_query -> route() -> retrieve()
-> build_payload() -> _composer_system(), which is exactly "embed a query -> route() -> retrieve() ->
assemble the payload -> the composer call up to the point it needs the API" from the phase brief, and
matches retrieval.py's own public function names (route, retrieve) literally.

app/service.py is UNTRACKED in git (present on disk, dated 2026-07-18, never committed - see the ph7
report). The currently deployed systemd unit runs a DIFFERENT, OLDER pipeline (main_voice_robot.py ->
answer_pipeline.py, the Haiku-router architecture) that touches NONE of data/index/ or models/ at all
(verified separately by grep across app/*.py) and needs an API key for every turn including identity
classification. Both findings are flagged prominently in the phase report; this script traces the one
pipeline that is actually traceable offline and that config.py says is current.

Method: monkeypatch builtins.open, io.open, Path.open/read_text/read_bytes, np.load and pickle.load to
record (path, size, api) for every read whose resolved path is under the repo root, before importing any
pipeline module. Traces are deduped by path (first-touch order preserved) since resident singletons load
each backing file once regardless of query count - repeats would just be noise.

Limitation, stated once: safetensors' Rust extension memory-maps model.safetensors directly and does not
go through Python's io layer, so this trace cannot observe that one read at the byte level. Step 2a's
directory-reduction test (ph7_02) is the empirical check for the model directory instead of this trace.
"""
from __future__ import annotations

import builtins
import io
import json
import pickle
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The bundle must be self-contained (no HF cache, no internet on the Pi): point the encoder at the
# repo-local flat copy for this trace, so what gets recorded matches what a fresh Pi clone will resolve.
import os
os.environ["CJ_EMBED_MODEL_PATH"] = str(PROJECT_ROOT / "models" / "bge-base-en-v1.5")

# ---------------------------------------------------------------------------------------------------
# tracer — installed BEFORE any pipeline module import so module-load-time reads are caught too
# ---------------------------------------------------------------------------------------------------
TRACE: list[dict] = []
_SEEN: set[str] = set()


# Only these top-level directories can hold candidate bundle files; everything else opened during the
# run (the venv's own library/interpreter files, __pycache__, this harness's own source, app/*.py) is
# Python-import machinery noise, not a runtime DATA dependency, and is excluded at the source rather
# than filtered after the fact.
_CANDIDATE_ROOTS = ("corpus", "data", "models")


def _record(path, api: str):
    try:
        p = Path(path).resolve()
        if not p.is_file():
            return
        rel = p.relative_to(PROJECT_ROOT) if PROJECT_ROOT in p.parents else None
        if rel is None or rel.parts[0] not in _CANDIDATE_ROOTS or p.suffix == ".py":
            return
        key = str(p)
        if key in _SEEN:
            return
        _SEEN.add(key)
        TRACE.append({"path": rel.as_posix(),
                      "bytes": p.stat().st_size, "first_api": api,
                      "t_ms": round((time.perf_counter() - _T0) * 1000, 1)})
    except (OSError, ValueError):
        pass


_T0 = time.perf_counter()

_orig_builtins_open = builtins.open


def _traced_open(file, mode="r", *a, **kw):
    f = _orig_builtins_open(file, mode, *a, **kw)
    if isinstance(file, (str, bytes, os.PathLike)) and ("r" in mode or mode == ""):
        _record(file, "open")
    return f


_orig_io_open = io.open


def _traced_io_open(file, mode="r", *a, **kw):
    f = _orig_io_open(file, mode, *a, **kw)
    if isinstance(file, (str, bytes, os.PathLike)) and ("r" in mode or mode == ""):
        _record(file, "io.open")
    return f


_orig_path_open = Path.open


def _traced_path_open(self, mode="r", *a, **kw):
    if "r" in mode or mode == "":
        _record(self, "Path.open")
    return _orig_path_open(self, mode, *a, **kw)


_orig_read_text = Path.read_text


def _traced_read_text(self, *a, **kw):
    _record(self, "Path.read_text")
    return _orig_read_text(self, *a, **kw)


_orig_read_bytes = Path.read_bytes


def _traced_read_bytes(self, *a, **kw):
    _record(self, "Path.read_bytes")
    return _orig_read_bytes(self, *a, **kw)


def install_tracer():
    builtins.open = _traced_open
    io.open = _traced_io_open
    Path.open = _traced_path_open
    Path.read_text = _traced_read_text
    Path.read_bytes = _traced_read_bytes


def patch_np_and_pickle():
    # deferred: np/pickle aren't imported yet at module top, and we want the FIRST import of numpy
    # (inside embeddings.py etc.) to already see the traced open/read (harmless either order, but this
    # keeps torch/numpy's own import-time file reads out of the corpus/index trace).
    import numpy as np
    global _orig_np_load
    _orig_np_load = np.load

    def _traced_np_load(file, *a, **kw):
        if isinstance(file, (str, bytes, os.PathLike, Path)):
            _record(file, "np.load")
        return _orig_np_load(file, *a, **kw)
    np.load = _traced_np_load

    global _orig_pickle_load
    _orig_pickle_load = pickle.load

    def _traced_pickle_load(f, *a, **kw):
        name = getattr(f, "name", None)
        if name:
            _record(name, "pickle.load")
        return _orig_pickle_load(f, *a, **kw)
    pickle.load = _traced_pickle_load


# ---------------------------------------------------------------------------------------------------
# test-harness setup done BEFORE the tracer installs, so building our OWN allowlist (reading the pinned
# xlsx via compute_snapshot) is never mistaken for something the pipeline itself reads. The pipeline
# never touches data/csv/*.xlsx — only this harness does, to know which doc ids are live.
# ---------------------------------------------------------------------------------------------------
from scripts.build_corpus_snapshot import compute_snapshot  # noqa: E402

RETIRED = {"BA040", "BC009", "BC010", "BD018", "SA085"}
snap = compute_snapshot()
FULL_CORPUS = set(snap["docs"]) - RETIRED
assert len(FULL_CORPUS) == 1290, len(FULL_CORPUS)

install_tracer()
patch_np_and_pickle()

# ---------------------------------------------------------------------------------------------------
# now import the pipeline (module-level reads, if any, are traced)
# ---------------------------------------------------------------------------------------------------
sys.path.insert(0, str(PROJECT_ROOT / "app"))
import config  # noqa: E402
import retrieval  # noqa: E402
import service  # noqa: E402

QUERIES = [
    # columns (current-events commentary, his newspaper voice)
    ("column", "What do you think of the cyberlibel case against Maria Ressa?"),
    ("column", "Should online libel be treated the same as libel in print?"),
    ("column", "What is your view on the West Philippine Sea arbitration award?"),
    ("column", "How should the Ombudsman handle the pork barrel scam cases?"),
    # books (chapters of his own books, esp. Liberty and Prosperity)
    ("book", "What is the twin-beacons doctrine?"),
    ("book", "Why do liberty and prosperity depend on each other?"),
    ("book", "Can the President extend her term through Charter change?"),
    ("book", "What is the difference between a constitutional amendment and a revision?"),
    # speeches
    ("speech", "What did you tell the ASEAN Law Association about the rule of law?"),
    ("speech", "What advice do you give law graduates taking the bar exam?"),
    ("speech", "What did you say at the Supreme Court centenary?"),
    # biography (chapters about his own life, written by others)
    ("biography", "Tell me about your childhood and your family."),
    ("biography", "What was Far Eastern University like for you?"),
    ("biography", "How did your Bukas Loob sa Diyos faith shape your life?"),
    ("biography", "Tell me about the day you got the call from Malacanang asking you to be Chief Justice."),
    ("biography", "What does the epilogue of your biography say about how you want to be remembered?"),
    # date question
    ("date", "What have you written recently about the ICC case against Duterte?"),
    ("date", "What did you say about the Marcos-Robredo election contest in 2016?"),
    # out of scope
    ("out_of_scope", "What's the weather like in Manila today?"),
    ("out_of_scope", "Can you give me a recipe for adobo?"),
    # identity intent
    ("identity", "Are you really Chief Justice Panganiban, or is this an AI?"),
    ("identity", "How were you built? Are you a robot?"),
]
assert len(QUERIES) >= 15

results = []
for kind, q in QUERIES:
    gate = retrieval.input_gate(q)
    r = retrieval.run(q, FULL_CORPUS)
    ri, rr = r["route"], r["retrieval"]
    directives = service._directives(q, ri)
    payload = service.build_payload(q, rr["selected"], directives)
    system = service._composer_system()          # reads voice_card.md; assembled, not sent
    selected_docs = sorted({c.split("::")[0] for c, *_ in rr["selected"]})
    results.append({
        "kind": kind, "query": q, "gate_scope": gate["scope"],
        "top_topic": ri["top_topic"], "top_cosine": ri["top_cosine"], "in_scope": ri["in_scope"],
        "n_selected_chunks": len(rr["selected"]), "selected_doc_ids": selected_docs,
        "selected_doc_formats": sorted({d[0] for d in selected_docs}),
        "payload_chars": len(payload), "system_chars": len(system),
    })

# format coverage sanity (columns=C, books=B, speeches=S, biography=G)
formats_hit = set()
for r in results:
    formats_hit |= set(r["selected_doc_formats"])

out_dir = PROJECT_ROOT / "batch-04" / "ph7_analysis" / "results"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "runtime_trace.json").write_text(
    json.dumps({
        "n_queries": len(QUERIES), "formats_covered": sorted(formats_hit),
        "embed_model_path_used": os.environ["CJ_EMBED_MODEL_PATH"],
        "model_load_count": __import__("embeddings").model_load_count(),
        "results": results,
        "trace": TRACE,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"[ph7_01] {len(QUERIES)} queries run; formats covered: {sorted(formats_hit)}")
print(f"[ph7_01] model_load_count = {__import__('embeddings').model_load_count()} (must be 1)")
print(f"[ph7_01] {len(TRACE)} distinct repo-relative files opened; written to "
      f"{out_dir / 'runtime_trace.json'}")
for t in TRACE:
    print(f"   {t['bytes']:>12,}  {t['path']}   ({t['first_api']}, first touched at query-time "
          f"t={t['t_ms']}ms)")
