"""
CE-10 — corpus-mean centring: the ONE place that loads and applies the mean vector.

Why it exists
-------------
Raw cosine in this embedding space is below the noise floor: two independent random
30-document groups already score 0.984 (batch-04/taxonomy_v2_PROPOSAL.md section 1), which is
what collapsed the v1 taxonomy 34 -> 3 at TOPIC_MERGE_COSINE = 0.95. Removing the corpus mean
(the component every chunk shares) fixes that. It only works if EVERY cosine that touches a topic
centroid is taken against vectors centred on the SAME mean:

    site          code                                        what is centred
    ------------  ------------------------------------------  ---------------------------------
    build time    scripts/build_centroids_fullcorpus.py       unit(mean(member chunks) - mu)
    build time    scripts/merge_tag_topics.py                 unit(chunk - mu)  (tagging + independence)
    index time    app/retrieval.py _load_pilot()              unit(mat - mu) @ cen.T  (topic_affinity)
    query time    app/retrieval.py route()                    unit(qv - mu) @ cen.T

Centre the centroids and leave the query raw and every cosine is meaningless while nothing crashes
— a silent failure on the retrieval path. So the loaders below RAISE, loudly, if the mean file is
missing, if its sha256 disagrees with the one recorded in the centroid meta, or if the meta does not
declare the centred scale. There is deliberately no fallback to raw.

Normalisation happens AFTER centring: centred(x) = (x - mu) / ||x - mu||.
The dense retrieval arm (`mat @ qv`, RRF) stays on RAW vectors — only centroid cosines are centred.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

import config


class CorpusMeanError(RuntimeError):
    """The corpus mean is missing, unverifiable, or inconsistent with the centroids. Never caught internally."""


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_corpus_mean(expected_sha256: str | None, path=None) -> np.ndarray:
    """Load data/index/corpus_mean.npy (float32 [EMBED_DIM]) and verify it against `expected_sha256`."""
    p = Path(path or config.CORPUS_MEAN_PATH)
    if not p.exists():
        raise CorpusMeanError(
            f"corpus mean vector missing: {p}. Refusing to fall back to raw cosine — every centroid cosine "
            "in this system is defined on centred vectors. Run scripts/build_corpus_mean.py.")
    if not expected_sha256:
        raise CorpusMeanError("no expected sha256 for the corpus mean (the centroid meta does not record one) — "
                              "rebuild the centroids with scripts/build_centroids_fullcorpus.py.")
    actual = sha256_file(p)
    if actual != expected_sha256:
        raise CorpusMeanError(f"corpus mean sha256 mismatch: {p.name} is {actual}, the centroid meta records "
                              f"{expected_sha256}. The centroids and the mean were not built together.")
    mu = np.load(p).astype(np.float32)
    if mu.shape != (config.EMBED_DIM,) or not np.isfinite(mu).all():
        raise CorpusMeanError(f"corpus mean has bad shape/values: {mu.shape}")
    return mu


def mean_for_meta(meta: dict) -> np.ndarray:
    """The mean vector a centroid meta was built against. Raises unless the meta declares the centred scale."""
    cm = (meta or {}).get("corpus_mean") or {}
    if (meta or {}).get("scale") != "centred" or not cm.get("sha256"):
        raise CorpusMeanError("centroid meta does not declare scale='centred' with corpus_mean.sha256 — these are "
                              "raw-scale (v1) centroids; a centred query against them would be meaningless.")
    return load_corpus_mean(cm["sha256"])


def center(x: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """unit(x - mu) along the last axis (float32). Works on a single vector or a [n, dim] matrix."""
    c = np.asarray(x, dtype=np.float32) - mu
    n = np.linalg.norm(c, axis=-1, keepdims=True)
    return c / np.maximum(n, 1e-12)
