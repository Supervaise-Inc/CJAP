"""
CE-10 Step 1 — write the corpus mean vector, ONCE.

    mean of all 13,549 chunk vectors in data/index/corpus_dense.npy  ->  data/index/corpus_mean.npy

The mean is accumulated in float64 and stored float32 (768 values). It is an index artifact: the centroid build
(scripts/build_centroids_fullcorpus.py), the tagger (scripts/merge_tag_topics.py) and the runtime
(app/retrieval.py) all LOAD this file through app/centering.py — nobody recomputes a mean locally.

Idempotent and refuses to overwrite: if the file exists it must equal the recomputed mean bit for bit;
otherwise this exits non-zero. Prints the sha256 that build_centroids_fullcorpus.py records in the centroid meta.

Usage:  python scripts/build_corpus_mean.py
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402


def main() -> int:
    meta = json.loads(config.CORPUS_DENSE_META_PATH.read_text(encoding="utf-8"))
    mat = np.load(config.CORPUS_DENSE_PATH)
    assert mat.shape == (meta["n_chunks"], config.EMBED_DIM), (mat.shape, meta["n_chunks"])
    assert meta["model_id"] == config.EMBED_MODEL_ID, meta["model_id"]
    mu = mat.astype(np.float64).mean(axis=0).astype(np.float32)
    out = config.CORPUS_MEAN_PATH
    if out.exists():
        old = np.load(out)
        if old.shape == mu.shape and np.array_equal(old, mu):
            print(f"[corpus_mean] {out.name} already present and identical — nothing written")
        else:
            print(f"[corpus_mean] REFUSING to overwrite {out}: it differs from the mean of the current "
                  f"corpus_dense.npy. Archive it (move to data/index/_archive/) if you really rebuilt the index.",
                  file=sys.stderr)
            return 1
    else:
        np.save(out, mu)
        print(f"[corpus_mean] wrote {out}")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"[corpus_mean] shape={mu.shape} dtype={mu.dtype} |mu|={float(np.linalg.norm(mu)):.6f} "
          f"n_chunks={meta['n_chunks']} corpus_dense_build_date={meta['build_date']}")
    print(f"[corpus_mean] sha256={sha}")
    print(f"[corpus_mean] chunk_index_sha256={meta.get('chunk_index_sha256')}  built {datetime.date.today().isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
