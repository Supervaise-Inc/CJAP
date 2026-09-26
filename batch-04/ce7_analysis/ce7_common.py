"""CE-7 shared loaders. READ-ONLY on the repo: reads corpus/, data/index/, corpus/voice/topic_map.json,
scripts/build_topic_map.py (imported for its matchers). Writes only under batch-04/ (cache + reports).

Definitions mirror the project's own:
  * matcher      : build_topic_map._doc_haystack + score_topic (word-boundary hits); membership = score > 0
  * centroid     : scripts/build_centroids_fullcorpus.py — unit-normalised mean of ALL chunk vectors of the member docs
  * doc affinity : scripts/merge_tag_topics.py — best-chunk cosine (max over a doc's chunks)
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
IDX = ROOT / "data" / "index"
B4 = ROOT / "batch-04"
CACHE = B4 / "ce7_analysis" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
import config  # noqa: E402  (knobs are READ from config, never hardcoded)

FORMATS = {"C": "columns", "B": "books", "S": "speeches", "G": "biography"}
FMT_ORDER = ["columns", "books", "speeches", "biography"]
FLOOR = config.TOPIC_ASSIGN_MIN_COSINE      # 0.68
MERGE = config.TOPIC_MERGE_COSINE           # 0.95


def fmt_of(doc_id: str) -> str:
    return FORMATS[doc_id[0]]


def work_of_title(title: str) -> str:
    t = title.split(" -- ")[0].strip()
    return re.sub(r"\s*\(Vol\.\s*\d+\)\s*$", "", t)


def norm_value(s: str) -> str:
    return re.sub(r"\s+", " ", s.casefold().strip())


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, 1, n)


class Corpus:
    """Everything the analyses need, loaded once."""

    def __init__(self):
        cmeta = json.loads((IDX / "corpus_dense_meta.json").read_text(encoding="utf-8"))
        assert cmeta["model_id"] == config.EMBED_MODEL_ID and cmeta["dim"] == 768 and cmeta["n_chunks"] == 13549
        self.mat = np.load(IDX / "corpus_dense.npy").astype(np.float32)
        self.chunk_ids = cmeta["chunk_ids"]
        assert self.mat.shape == (13549, 768)
        chunks = {}
        for line in (ROOT / "corpus/index/chunks.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                chunks[r["chunk_id"]] = r
        self.chunk_text = [chunks[c]["text"] for c in self.chunk_ids]
        self.chunk_doc = [c.split("::")[0] for c in self.chunk_ids]
        self.docs = {}
        for p in sorted(ROOT.glob("corpus/*/*/*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict) and "id" in d and d["id"][0] in FORMATS and d.get("format"):
                self.docs[d["id"]] = d
        assert len(self.docs) == 1290, len(self.docs)
        self.doc_ids = sorted(self.docs)
        self.doc_index = {d: i for i, d in enumerate(self.doc_ids)}
        self.rows_of = defaultdict(list)
        for i, d in enumerate(self.chunk_doc):
            self.rows_of[d].append(i)
        self.n_chunks = np.array([len(self.rows_of[d]) for d in self.doc_ids])
        self.doc_fmt = np.array([fmt_of(d) for d in self.doc_ids])
        self.doc_vec = unit(np.stack([self.mat[self.rows_of[d]].mean(axis=0) for d in self.doc_ids]))   # mean of chunks
        self.title = {d: self.docs[d]["title"] for d in self.doc_ids}
        self.work = {d: work_of_title(self.title[d]) for d in self.doc_ids if d[0] == "B"}
        self.fmt_docs = Counter(self.doc_fmt.tolist())
        chunk_fmt = Counter(fmt_of(d) for d in self.chunk_doc)
        self.fmt_chunks = chunk_fmt
        self.gmean = unit(self.mat.mean(axis=0))

    def doc_text(self, d: str) -> str:
        return "\n".join(self.chunk_text[i] for i in self.rows_of[d])


_prior = None


def prior_art():
    """The v1 taxonomy + its matchers, imported (not modified). Returns dict."""
    global _prior
    if _prior is not None:
        return _prior
    spec = importlib.util.spec_from_file_location("build_topic_map_v1", ROOT / "scripts" / "build_topic_map.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    cmeta = json.loads((IDX / "topic_centroids_meta.json").read_text(encoding="utf-8"))
    tmap = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))
    tax = {t["id"]: t for t in m.TAXONOMY}
    _prior = {"module": m, "taxonomy": tax, "order": [t["id"] for t in m.TAXONOMY],
              "centroid_ids": cmeta["topic_ids"], "v1_doc_count": {k: v["doc_count"] for k, v in tmap["topics"].items()},
              "v1_centroids": np.load(IDX / "topic_centroids.npy").astype(np.float32), "v1_meta": cmeta}
    return _prior


def score_all_docs(C: Corpus):
    """score[doc][topic_id] with the v1 matchers, over the 35 taxonomy topics. Cached."""
    p = prior_art(); m = p["module"]
    out = {}
    for d in C.doc_ids:
        hs = m._doc_haystack(C.docs[d])
        out[d] = {tid: m.score_topic(t, hs) for tid, t in p["taxonomy"].items()}
    return out


def centroid_from_docs(C: Corpus, docs, weight="chunk"):
    """weight='chunk': production recipe (mean of ALL member chunks); weight='doc': every doc counts equally."""
    docs = list(docs)
    if not docs:
        return None, 0
    if weight == "chunk":
        rows = [r for d in docs for r in C.rows_of[d]]
        return unit(C.mat[rows].mean(axis=0)), len(rows)
    v = np.stack([C.mat[C.rows_of[d]].mean(axis=0) for d in docs]).mean(axis=0)
    return unit(v), sum(len(C.rows_of[d]) for d in docs)


def pct(n, tot):
    return f"{100.0 * n / tot:.1f}%" if tot else "-"
