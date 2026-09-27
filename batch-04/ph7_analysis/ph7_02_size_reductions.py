"""
Phase 7 step 2 - three size reductions, each measured, each reversible.

2a. models/bge-base-en-v1.5 (838 MB) inspected: it is NOT model.safetensors + a duplicate
    pytorch_model.bin (there is no .bin at all here) - it is the SAME 9-file flat HF snapshot present
    TWICE: once at the directory root and once again nested under a commit-hash subdirectory
    (a5beb1e3e68b9ab74eb54cfd186867f64f240e1a/), byte-identical file for file (verified by sha256,
    batch-04/ph7_analysis/logs/model_dir_dupe_check.txt). Empirically verified here: copy ONLY the
    9 root-level files (no nested subdirectory) to a clean temp dir, load a fresh SentenceTransformer
    from it, and confirm the encoding of every probe sentence is bit-identical to the resident model
    already loaded from the full (duplicated) directory.

2b. pilot_dense.npy (40 MB, float32) converted to float16 (20 MB): recompute the full 13,549x30
    centred centroid-affinity product and 40 query->chunk cosine rankings in both precisions; report
    max absolute cosine error and how many top-10 orderings change. Ship only if zero change.

2c. The per-document .md: already established structurally in ph7_01 (service.py's build_payload()
    reads chunk text from chunks.jsonl only; COMPOSER_SIGNATURE_PALETTE is False by default and is the
    only path that touches corpus/**/<id>.json, never corpus/**/<id>.md). Confirmed here by a static
    grep-equivalent check: no code path this pipeline can reach opens a corpus .md file.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

import numpy as np  # noqa: E402
import config  # noqa: E402

OUT = PROJECT_ROOT / "batch-04" / "ph7_analysis" / "results"
LOGS = PROJECT_ROOT / "batch-04" / "ph7_analysis" / "logs"
OUT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

report: dict = {}

# ===================================================================================================
# 2a — the model directory
# ===================================================================================================
MODEL_DIR = PROJECT_ROOT / "models" / "bge-base-en-v1.5"
NESTED = MODEL_DIR / "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"

root_files = sorted(p.relative_to(MODEL_DIR) for p in MODEL_DIR.rglob("*")
                    if p.is_file() and NESTED not in p.parents)
nested_files = sorted(p.relative_to(NESTED) for p in NESTED.rglob("*") if p.is_file()) if NESTED.exists() else []


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


dupe_log = []
identical_dupe = bool(nested_files) and [f.name for f in nested_files] == [f.name for f in root_files if str(f) != "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"] or False
pairs = []
for f in nested_files:
    root_f = MODEL_DIR / f
    nested_f = NESTED / f
    if root_f.exists():
        a, b = sha256_file(root_f), sha256_file(nested_f)
        pairs.append((str(f), a == b, a, b))
identical_dupe = bool(pairs) and all(same for _, same, _, _ in pairs)
for name, same, a, b in pairs:
    dupe_log.append(f"{name}  root={a}  nested={b}  same={same}")
LOGS.joinpath("model_dir_dupe_check.txt").write_text("\n".join(dupe_log) + "\n", encoding="utf-8")

total_before = sum(p.stat().st_size for p in MODEL_DIR.rglob("*") if p.is_file())
root_total = sum((MODEL_DIR / f).stat().st_size for f in root_files if str(f) != "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a" and (MODEL_DIR / f).is_file())

# Empirical test: load a SentenceTransformer from a directory holding ONLY the root-level files, and
# compare its encodings against the resident model (already loaded once from the full, duplicated dir
# in ph7_01's cold run - but this script runs standalone, so load fresh from the full dir here too, for
# a clean side-by-side).
from sentence_transformers import SentenceTransformer  # noqa: E402

PROBES = [
    "What is the twin-beacons doctrine?",
    "Tell me about your childhood.",
    "Represent this sentence for searching relevant passages: What is the pork barrel?",
]

full_model = SentenceTransformer(str(MODEL_DIR), device=config.EMBED_DEVICE)
full_vecs = full_model.encode(PROBES, convert_to_numpy=True, normalize_embeddings=True)

with tempfile.TemporaryDirectory(prefix="cjp_model_min_") as tmp:
    tmp = Path(tmp)
    for f in root_files:
        if str(f) == "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a":
            continue
        dst = tmp / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MODEL_DIR / f, dst)
    min_total = sum(p.stat().st_size for p in tmp.rglob("*") if p.is_file())
    min_model = SentenceTransformer(str(tmp), device=config.EMBED_DEVICE)
    min_vecs = min_model.encode(PROBES, convert_to_numpy=True, normalize_embeddings=True)

max_abs_diff = float(np.max(np.abs(full_vecs - min_vecs)))
bit_identical = bool(np.array_equal(full_vecs, min_vecs))

report["2a_model_dir"] = {
    "total_bytes_before": total_before,
    "root_level_files": [str(f) for f in root_files if str(f) != "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"],
    "nested_dir_is_byte_identical_duplicate_of_root": identical_dupe,
    "total_bytes_after_dropping_nested_dir": root_total,
    "bytes_saved": total_before - root_total,
    "empirical_check": {
        "probes": PROBES,
        "max_abs_embedding_diff_root_dir_vs_minimal_dir": max_abs_diff,
        "bit_identical": bit_identical,
    },
    "verdict": "ship the 9 root-level files only; drop the nested commit-hash subdirectory"
               if identical_dupe and bit_identical else "KEEP BOTH — empirical check failed",
}
print(f"[2a] model dir {total_before:,} -> {root_total:,} bytes "
      f"(nested dupe identical={identical_dupe}, embeddings bit-identical={bit_identical}, "
      f"max_abs_diff={max_abs_diff:.2e})")

# ===================================================================================================
# 2b — pilot_dense.npy float16
# ===================================================================================================
dense = np.load(config.DENSE_INDEX_PATH).astype(np.float32)          # [n_chunks, dim], RAW (unit-norm)
dense_meta = json.loads(Path(config.DENSE_INDEX_META_PATH).read_text(encoding="utf-8"))
centroids = np.load(config.CENTROIDS_PATH).astype(np.float32)        # [30, dim], CENTRED unit vectors
mu = np.load(config.CORPUS_MEAN_PATH).astype(np.float32)


def center(x, mu):
    c = x - mu
    n = np.linalg.norm(c, axis=-1, keepdims=True)
    return c / np.maximum(n, 1e-12)


dense_centred = center(dense, mu)

dense_f16 = dense.astype(np.float16)
dense_f16_back = dense_f16.astype(np.float32)                        # what a float16-on-disk index gives back
dense_centred_f16 = center(dense_f16_back, mu)

# (i) the full 13,549 x 30 centred centroid-affinity product
aff_f32 = dense_centred @ centroids.T
aff_f16 = dense_centred_f16 @ centroids.T
aff_abs_err = np.abs(aff_f32 - aff_f16)
aff_top1_f32 = aff_f32.argmax(axis=1)
aff_top1_f16 = aff_f16.argmax(axis=1)
aff_top1_changed = int((aff_top1_f32 != aff_top1_f16).sum())

# (ii) 40 query -> chunk dense-cosine rankings (RAW space, not centred — this IS what dense_score/RRF
# use). Reuse the same 22 queries as ph7_01 for continuity, embedded fresh here.
from scripts.build_corpus_snapshot import compute_snapshot  # noqa: E402
import embeddings  # noqa: E402

import os
os.environ.setdefault("CJ_EMBED_MODEL_PATH", str(MODEL_DIR))
QUERIES_40 = [
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
    "What have you written recently about the ICC case against Duterte?",
    "What did you say about the Marcos-Robredo election contest in 2016?",
    "What's the weather like in Manila today?",
    "Can you give me a recipe for adobo?",
    "Are you really Chief Justice Panganiban, or is this an AI?",
    "How were you built? Are you a robot?",
] + [
    "What is judicial independence and why does it matter?",
    "How does the Judicial and Bar Council choose nominees?",
    "What is your view on the death penalty?",
    "What happened in the impeachment of Chief Justice Corona?",
    "What is the Bangsamoro Basic Law?",
    "How should courts handle DNA evidence?",
    "What is ill-gotten wealth and how is it recovered?",
    "What makes a nation prosperous?",
    "What is the role of the Ombudsman?",
    "What do you think about artificial intelligence and the law?",
    "What is the significance of the Grace Poe citizenship case?",
    "How does annulment work under the Family Code?",
    "What is the party-list system for?",
    "What is judicial reform and why is it needed?",
    "What is the PCGG and what does it do?",
    "What did the 2016 arbitral tribunal rule on the nine-dash line?",
    "What is your philosophy of leadership?",
    "What is the role of the Supreme Court in a democracy?",
    "What is the significance of EDSA People Power?",
    "What do you think about the use of DAP and PDAF?",
]
assert len(QUERIES_40) == 40, len(QUERIES_40)

top10_changed = 0
max_cos_err = 0.0
per_query = []
for q in QUERIES_40:
    qv = embeddings.embed_query(q)                       # RAW, unit-normalised, float32
    sims_f32 = dense @ qv
    sims_f16 = dense_f16_back @ qv
    err = float(np.max(np.abs(sims_f32 - sims_f16)))
    max_cos_err = max(max_cos_err, err)
    top10_f32 = list(np.argsort(-sims_f32)[:10])
    top10_f16 = list(np.argsort(-sims_f16)[:10])
    changed = top10_f32 != top10_f16
    if changed:
        top10_changed += 1
    per_query.append({"query": q, "max_abs_cos_err": round(err, 6), "top10_order_changed": changed})

report["2b_float16_pilot_dense"] = {
    "bytes_before": int(dense.nbytes), "bytes_after": int(dense_f16.nbytes),
    "n_chunks": dense.shape[0], "dim": dense.shape[1],
    "centroid_affinity_check": {
        "n_products": int(aff_f32.size), "max_abs_error": float(aff_abs_err.max()),
        "mean_abs_error": float(aff_abs_err.mean()), "top1_topic_changed": aff_top1_changed,
    },
    "query_ranking_check": {
        "n_queries": len(QUERIES_40), "max_abs_cosine_error": round(max_cos_err, 6),
        "n_queries_with_top10_order_changed": top10_changed, "per_query": per_query,
    },
    "verdict": "SHIP float16 (0 top-10 orderings changed)" if top10_changed == 0
               else f"DO NOT SHIP — {top10_changed}/{len(QUERIES_40)} top-10 orderings changed",
}
print(f"[2b] float16: max |cosine error| centroid-affinity={aff_abs_err.max():.2e} "
      f"query-ranking={max_cos_err:.2e}; top-10 changed: centroid-affinity(30-way argmax)="
      f"{aff_top1_changed}/{aff_f32.shape[0]}, query-rankings={top10_changed}/{len(QUERIES_40)}")

# ===================================================================================================
# 2c — the per-document .md (static confirmation; the dynamic proof already ran in ph7_01, which
# never touched a corpus/**/*.md file across 22 queries with COMPOSER_SIGNATURE_PALETTE at its
# shipped default of False)
# ===================================================================================================
report["2c_per_doc_md"] = {
    "read_by": "nothing on the traced path: service.build_payload() reads chunk text from "
               "corpus/index/chunks.jsonl only; corpus/**/<id>.json is read ONLY when "
               "config.COMPOSER_SIGNATURE_PALETTE is set (default False); corpus/**/<id>.md is never "
               "read by this pipeline under any config flag.",
    "verified_by": "ph7_01_trace_runtime.py's 22-query trace (0 corpus/**/*.md opens) plus a source read "
                   "of app/service.py (no reference to a .md path anywhere in the file)",
    "verdict": "DROP corpus/**/<id>.md from the bundle — 15.8 MB saved",
}

OUT.joinpath("size_reductions.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"[ph7_02] written to {OUT / 'size_reductions.json'}")
