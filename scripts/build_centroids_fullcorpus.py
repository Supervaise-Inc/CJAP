"""
CE-10 Step 3.4 — topic centroids, built FROM SCRATCH on the CENTRED scale (taxonomy v2).

    centroid(topic) = unit( mean of ALL chunks of the topic's member docs  -  corpus_mean )

Members are the `doc_ids` in corpus/voice/topic_map.json (the documents each topic's matcher catches); every
member document contributes all of its chunks (chunk-weighted — the production recipe since OPS-2 Phase B, now on
the centred scale). Nothing is grown incrementally from a previous centroid file, there is no zero-member
fallback (v2 has none: every dimension has >= 11 member documents; the script asserts it), and the corpus mean is
LOADED from data/index/corpus_mean.npy through app/centering.py — never recomputed here. Normalisation happens
after centring.

The centroid meta records the mean's sha256, n_chunks and the corpus_dense build date alongside
taxonomy_version: 2 and scale: "centred"; app/retrieval.py re-verifies the sha256 at every load.

The script REFUSES to overwrite existing centroid files: archive them first (move into data/index/_archive/ with a
dated prefix — see batch-04 CE-10 Step 3.1). Run scripts/build_corpus_mean.py first.

Usage:  python scripts/build_centroids_fullcorpus.py
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
import config  # noqa: E402
import centering  # noqa: E402
import numpy as np  # noqa: E402

IDX = ROOT / "data" / "index"


def main() -> int:
    cmeta = json.loads(config.CORPUS_DENSE_META_PATH.read_text(encoding="utf-8"))
    assert cmeta["model_id"] == config.EMBED_MODEL_ID and cmeta["dim"] == config.EMBED_DIM, \
        f"corpus_dense is {cmeta['model_id']}/{cmeta['dim']}"
    mat = np.load(config.CORPUS_DENSE_PATH).astype(np.float32)
    chunk_ids = cmeta["chunk_ids"]
    assert mat.shape == (len(chunk_ids), config.EMBED_DIM)

    # the corpus mean comes from its FILE; prove it is the mean of THIS matrix (the file is written once)
    mean_sha = centering.sha256_file(config.CORPUS_MEAN_PATH)     # FileNotFoundError => run build_corpus_mean.py
    mu = centering.load_corpus_mean(mean_sha)
    assert np.array_equal(mat.astype(np.float64).mean(axis=0).astype(np.float32), mu), \
        "corpus_mean.npy is not the mean of the current corpus_dense.npy"

    for p in (config.CENTROIDS_PATH, config.CENTROIDS_META_PATH):
        if p.exists():
            print(f"[centroids] REFUSING to overwrite {p}: archive it first (move into data/index/_archive/).", file=sys.stderr)
            return 1

    tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))
    assert tm.get("taxonomy_version") == 2, "topic_map.json is not taxonomy_version 2"
    tmap = tm["topics"]
    topic_ids = list(tmap.keys())                                   # taxonomy order
    members = {tid: set(tmap[tid]["doc_ids"]) for tid in topic_ids}

    rows_of_doc: dict[str, list[int]] = {}
    for i, cid in enumerate(chunk_ids):
        rows_of_doc.setdefault(cid.split("::")[0], []).append(i)

    cen = np.zeros((len(topic_ids), config.EMBED_DIM), dtype=np.float32)
    topics_meta = []
    for i, tid in enumerate(topic_ids):
        rows = [r for d in sorted(members[tid]) for r in rows_of_doc.get(d, [])]
        assert len(members[tid]) >= 10 and rows, f"{tid}: {len(members[tid])} member docs — v2 has no thin/empty topics"
        cen[i] = centering.center(mat[rows].astype(np.float64).mean(axis=0), mu)     # normalise AFTER centring
        topics_meta.append({"topic_id": tid, "n_member_docs": len(members[tid]), "n_member_chunks": len(rows)})

    S = cen @ cen.T; iu = np.triu_indices(len(cen), 1); pv = S[iu]
    np.save(config.CENTROIDS_PATH, cen)
    meta = {
        "model_id": config.EMBED_MODEL_ID, "dim": config.EMBED_DIM, "backend": config.EMBED_BACKEND,
        "n_topics": len(topic_ids), "taxonomy_version": 2, "scale": "centred",
        "corpus_mean": {"path": "data/index/corpus_mean.npy", "sha256": mean_sha, "n_chunks": len(chunk_ids),
                        "corpus_dense_build_date": cmeta["build_date"], "chunk_index_sha256": cmeta.get("chunk_index_sha256"),
                        "normalisation": "after centring: centred(x) = (x - mu) / ||x - mu||"},
        "centroid_recipe": ("unit(mean of ALL chunks of the member docs - corpus_mean); chunk-weighted; built from scratch "
                            "(no incremental growth, no zero-member fallback); members = topic_map.json doc_ids"),
        "n_corpus_chunks": len(chunk_ids), "build_date": datetime.date.today().isoformat(),
        "corpus_dense_build_date": cmeta["build_date"],
        "separation_centred_pair_cosine": {"n_pairs": int(len(pv)), "median": round(float(np.median(pv)), 4),
                                           "p95": round(float(np.percentile(pv, 95)), 4), "max": round(float(pv.max()), 4)},
        "topic_ids": topic_ids, "topics": topics_meta,
    }
    config.CENTROIDS_META_PATH.write_text(
        json.dumps(meta, ensure_ascii=config.JSON_ENSURE_ASCII, indent=2) + "\n",
        encoding=config.OUTPUT_ENCODING, newline="\n")
    print(f"[centroids] wrote {config.CENTROIDS_PATH.name} {cen.shape} (centred, built from scratch)")
    print(f"[centroids] corpus_mean sha256={mean_sha} n_chunks={len(chunk_ids)} corpus_dense_build_date={cmeta['build_date']}")
    print(f"[centroids] centred pair cosine: median {np.median(pv):.3f}  p95 {np.percentile(pv, 95):.3f}  max {pv.max():.3f}")
    print(f"[centroids] member docs per topic: min {min(t['n_member_docs'] for t in topics_meta)}  max {max(t['n_member_docs'] for t in topics_meta)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
