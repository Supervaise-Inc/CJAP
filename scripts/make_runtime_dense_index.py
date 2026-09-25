"""
P3.2b — restore the RUNTIME dense index from the full-corpus matrix.

Why this script exists
----------------------
`app/embeddings.load_dense_index()` reads config.DENSE_INDEX_PATH
(data/index/pilot_dense.npy) and config.DENSE_INDEX_META_PATH — NOT
corpus_dense.npy. `app/retrieval._load_pilot()` then reads meta["chunk_ids"]
AND meta["doc_ids"].

`scripts/build_corpus_dense.py` only writes pilot_dense.npy when a prior
pilot index existed (the `if new_pilot is not None:` branch). With the stale
17-July pilot index archived — which is what we want, because batch-03 changed
18 of its 95 documents — `new_pilot` stays None and NO pilot index is written.
Its closing line still prints "pilot sliced+overwritten"; that line is wrong in
this case. The runtime index is therefore OFFLINE after P3.2 until this script
runs.

Pointing CJ_DENSE_INDEX_PATH at corpus_dense.npy does NOT work: the corpus meta
written by build_corpus_dense.py has no "doc_ids" key, so retrieval raises
KeyError. This script writes a runtime index with the schema retrieval expects.

What it does
------------
Copies the full-corpus matrix to DENSE_INDEX_PATH and writes a meta carrying
chunk_ids + doc_ids resolved from corpus/index/chunks.jsonl. No re-embedding:
the runtime index and the corpus matrix stay bit-identical — one encoder, one
dimensionality, one regime. The runtime universe becomes the full corpus
(1,104 docs / 9,804 chunks) rather than the frozen 95-doc pilot subset; that is
a deliberate consequence, recorded in the meta as allowlist_version.

Safety
------
Verifies before it writes anything. Backs up any existing pilot index. Writes
both outputs only at the end; on any error it removes whatever it wrote.

Usage:  python scripts/make_runtime_dense_index.py [--force]
"""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing runtime index (a backup is taken either way)")
    args = ap.parse_args()

    cmat_path = Path(config.CORPUS_DENSE_PATH)
    cmeta_path = Path(config.CORPUS_DENSE_META_PATH)
    out_mat = Path(config.DENSE_INDEX_PATH)
    out_meta = Path(config.DENSE_INDEX_META_PATH)
    chunks_jsonl = _REPO_ROOT / "corpus" / "index" / "chunks.jsonl"

    for p in (cmat_path, cmeta_path, chunks_jsonl):
        if not p.exists():
            print(f"[runtime-index] MISSING {p} — run P3.2 first. STOP.", file=sys.stderr)
            return 2

    cmeta = json.loads(cmeta_path.read_text(encoding="utf-8"))
    matrix = np.load(cmat_path).astype(np.float32)
    chunk_ids = list(cmeta["chunk_ids"])

    # ---- verify the corpus matrix before trusting it -------------------------
    if matrix.shape[0] != len(chunk_ids):
        print(f"[runtime-index] rows {matrix.shape[0]} != chunk_ids {len(chunk_ids)}. STOP.",
              file=sys.stderr)
        return 2
    if matrix.shape[1] != config.EMBED_DIM:
        print(f"[runtime-index] dim {matrix.shape[1]} != EMBED_DIM {config.EMBED_DIM}. STOP.",
              file=sys.stderr)
        return 2
    if cmeta.get("model_id") != config.EMBED_MODEL_ID:
        print(f"[runtime-index] model_id {cmeta.get('model_id')!r} != config "
              f"{config.EMBED_MODEL_ID!r}. STOP.", file=sys.stderr)
        return 2
    norms = np.linalg.norm(matrix, axis=1)
    dev = float(np.max(np.abs(norms - 1.0)))
    if dev > 1e-5:
        print(f"[runtime-index] rows are not unit-norm (max |‖v‖−1| = {dev:.3e}). STOP.",
              file=sys.stderr)
        return 2

    # ---- resolve doc_ids from the chunk store -------------------------------
    doc_of: dict[str, str] = {}
    with open(chunks_jsonl, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            doc_of[rec["chunk_id"]] = rec["doc_id"]

    missing = [c for c in chunk_ids if c not in doc_of]
    if missing:
        print(f"[runtime-index] {len(missing)} chunk_ids absent from chunks.jsonl "
              f"(e.g. {missing[:5]}) — the matrix and the chunk store disagree. STOP.",
              file=sys.stderr)
        return 2
    extra = len(doc_of) - len(chunk_ids)
    if extra:
        print(f"[runtime-index] chunks.jsonl has {extra} chunk(s) the matrix does not — "
              "re-run P3.2 against the current chunk set. STOP.", file=sys.stderr)
        return 2

    doc_ids = [doc_of[c] for c in chunk_ids]
    n_docs = len(set(doc_ids))

    # ---- retired IDs must not be present ------------------------------------
    retired_csv = _REPO_ROOT / "data" / "csv" / "retired_doc_ids.csv"
    if retired_csv.exists():
        import csv as _csv
        with open(retired_csv, encoding="utf-8-sig", newline="") as fh:
            retired = {r["doc_id"].strip() for r in _csv.DictReader(fh) if r.get("doc_id")}
        leaked = sorted(retired & set(doc_ids))
        if leaked:
            print(f"[runtime-index] retired doc_ids present in the index: {leaked}. STOP.",
                  file=sys.stderr)
            return 2

    # ---- back up, then write ------------------------------------------------
    if out_mat.exists() and not args.force:
        print(f"[runtime-index] {out_mat.name} already exists. Re-run with --force "
              "if you mean to replace it (a backup is taken). STOP.", file=sys.stderr)
        return 3

    stamp = datetime.date.today().isoformat()
    backed_up = []
    for p in (out_mat, out_meta):
        if p.exists():
            bak = p.with_name(f"_archived_{stamp}_{p.name}")
            shutil.copy2(p, bak)
            backed_up.append(str(bak))

    written = []
    try:
        out_mat.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_mat, matrix)
        written.append(out_mat)
        meta = {
            "model_id": cmeta["model_id"],
            "dim": cmeta["dim"],
            "normalize": cmeta.get("normalize", config.EMBED_NORMALIZE),
            "allowlist_version": "full-corpus (no allowlist; supersedes pilot_subset_frozen_v4)",
            "n_docs": n_docs,
            "n_chunks": len(chunk_ids),
            "build_date": stamp,
            "chunk_ids": chunk_ids,
            "doc_ids": doc_ids,
            "unresolved_docs": [],
            "backend": cmeta.get("backend", config.EMBED_BACKEND),
            "derived_from": (f"copy of {cmat_path.name} built {cmeta.get('build_date')} "
                             "(P3.2b — one regime, no re-embedding)"),
            "corpus_chunk_index_sha256": cmeta.get("chunk_index_sha256"),
        }
        out_meta.write_text(
            json.dumps(meta, ensure_ascii=config.JSON_ENSURE_ASCII, indent=2) + "\n",
            encoding=config.OUTPUT_ENCODING)
        written.append(out_meta)
    except Exception as e:                                    # noqa: BLE001
        for p in written:
            try:
                p.unlink()
            except OSError:
                pass
        print(f"[runtime-index] FAILED, wrote nothing: {e}", file=sys.stderr)
        return 1

    print(f"[runtime-index] wrote {out_mat.name} {matrix.shape} and {out_meta.name}")
    print(f"[runtime-index]   {n_docs} documents / {len(chunk_ids)} chunks, "
          f"model {meta['model_id']} @{meta['dim']}d, backend {meta['backend']}")
    print(f"[runtime-index]   max |‖v‖−1| = {dev:.3e}")
    for b in backed_up:
        print(f"[runtime-index]   backed up -> {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
