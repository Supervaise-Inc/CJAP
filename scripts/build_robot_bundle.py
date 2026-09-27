"""
Phase 7 step 3 - build deploy/pi/bundle/, the data the Reachy Mini needs on the Pi.

deploy/pi/bundle/ is a BUILD OUTPUT, never hand-edited. It carries only DATA - no application code
(app/, config.py and requirements-pi.txt reach the Pi through the existing deploy/pi/install.sh git-clone
path; see batch-04/BATCH-04_REPORT.md for why that split does not fully match how install.sh works today).

The file list is not hand-written. It is the union of two traces batch-04/ph7_analysis/ captured:

  - a DYNAMIC cold-run trace of app/retrieval.py + app/service.py (the "new-arch" deterministic
    pipeline; config.py calls it "[NEW-ARCH] ... runs TODAY") across 22 queries covering all four
    corpus formats, a date question, an out-of-scope question and the identity intent - the only
    pipeline in this repo that runs offline, without an ANTHROPIC_API_KEY, up through payload assembly
    (batch-04/ph7_analysis/ph7_01_trace_runtime.py, results/runtime_trace.json);
  - a STATIC read of app/answer_pipeline.py, the pipeline main_voice_robot.py's systemd unit actually
    runs today (the Haiku-router architecture), which cannot be cold-traced here (every turn needs the
    API, including its identity-probe classification) but is read directly for its file dependencies.

Where the two disagree, this script includes the file: the deployed pipeline's needs are not optional
just because the offline trace could not exercise them. batch-04/BATCH-04_REPORT.md carries the full
table and reasoning. Two files neither pipeline reads under any traced or read code path are dropped
with high confidence: corpus/**/<id>.md (a body neither pipeline's citation code ever opens - confirmed
by the 22-query trace AND by reading answer_pipeline.py's load_doc_body, which is defined but never
called) and corpus/index/chunk_index.json (only its sha256 - already embedded as a string field in
pilot_dense_meta.json and topic_centroids_meta.json - is ever compared; the file itself is never opened).

    python scripts/build_robot_bundle.py            # delete deploy/pi/bundle/ and rebuild it
    python scripts/build_robot_bundle.py --check     # rebuild into staging, diff against the committed
                                                       # bundle, exit 1 on any difference
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import verify_pin  # noqa: E402
from scripts.build_corpus_snapshot import SNAPSHOT_PATH, DATA_CSV  # noqa: E402

OUT_DIR = PROJECT_ROOT / "deploy" / "pi" / "bundle"
STAGE_DIR = PROJECT_ROOT / "deploy" / "pi" / "bundle.staging"
CORPUS = PROJECT_ROOT / "corpus"
DATA_INDEX = PROJECT_ROOT / "data" / "index"
MODEL_DIR_SRC = PROJECT_ROOT / "models" / "bge-base-en-v1.5"
REGISTER = DATA_CSV / "retired_doc_ids.csv"

FORMAT_DIRS = {"columns": "C", "books": "B", "speeches": "S", "biography": "G"}
BATCH_RE = re.compile(rb"batch[-_ ]?0?4", re.I)

# Root-level HF snapshot files only (step 2a): the nested a5beb1e.../ subdirectory is a byte-identical
# duplicate (verified: batch-04/ph7_analysis/logs/model_dir_dupe_check.txt, and an empirical
# SentenceTransformer load-and-encode comparison, batch-04/ph7_analysis/results/size_reductions.json,
# "2a_model_dir") of these same 9 files and is never opened when the loader is pointed at the ROOT dir.
MODEL_FILES = [
    "config.json", "config_sentence_transformers.json", "modules.json",
    "sentence_bert_config.json", "special_tokens_map.json", "tokenizer.json",
    "tokenizer_config.json", "vocab.txt", "1_Pooling/config.json",
    "model.safetensors",
]

# (repo-relative path, one-line note on what reads it, whether it's dark-by-default in the traced
# pipeline). float16 for pilot_dense.npy was measured and REJECTED (1/40 top-10 query rankings
# changed - batch-04/ph7_analysis/results/size_reductions.json, "2b") so it ships as float32, unchanged.
INDEX_FILES = [
    ("data/index/pilot_dense.npy",
     "app/embeddings.py load_dense_index() - the dense (meaning-similarity) arm. float32: float16 "
     "changed 1/40 query top-10 orderings in testing, so it was not shipped (see MANIFEST).", False),
    ("data/index/pilot_dense_meta.json",
     "app/embeddings.py load_dense_index() - chunk_ids/doc_ids row order for the matrix above.", False),
    ("data/index/pilot_sparse.pkl",
     "app/sparse.py load_index() - the BM25 keyword-search arm.", False),
    ("data/index/sparse_phrase_dict.json",
     "app/sparse.py load_phrase_dict() - the curated atomic-phrase tokenizer dictionary.", False),
    ("data/index/topic_centroids.npy",
     "app/retrieval.py _load_centroids() - the 30 taxonomy-dimension vectors the router compares a "
     "question against.", False),
    ("data/index/topic_centroids_meta.json",
     "app/retrieval.py _load_centroids() - topic ids in matrix row order, and the corpus_mean pairing "
     "hash (see below).", False),
    ("data/index/corpus_mean.npy",
     "app/centering.py load_corpus_mean() - subtracted from every vector before a centroid cosine; "
     "MUST travel with topic_centroids_meta.json (its sha256 is checked against the field the meta "
     "records, and the loader raises if they disagree).", False),
    ("data/index/date_index.json",
     "app/retrieval.py _load_date_table() - per-document date + precision, for the date filter/boost. "
     "Dark by default (config.DATE_INDEX_ENABLED=False in the traced 22-query run: not opened). "
     "Shipped anyway - 153 KB - so flipping that one env var on the Pi does not also require a bundle "
     "rebuild.", True),
    ("data/index/date_index_provenance.json",
     "Sidecar to date_index.json above; not read by the app itself, kept for the same reason.", True),
]

VOICE_FILES = [
    ("topic_map.json", "Read by BOTH pipelines: app/service.py _theme_of() (register/theme cues) and "
                        "app/answer_pipeline.py CorpusArtifacts (the taxonomy + the robot_identity_meta "
                        "intent node)."),
    ("voice_card.md", "Read by BOTH pipelines: the composer's system prompt (Sonnet call)."),
    ("router_prompt.md", "Read by the CURRENTLY DEPLOYED pipeline only (main_voice_robot.py -> "
                          "answer_pipeline.py's Haiku router system prompt). The traced offline pipeline "
                          "(app/service.py) does not read it - its router is the centroid math in "
                          "app/retrieval.py, not an LLM call. Shipped because the deployed robot needs it "
                          "today; see batch-04/BATCH-04_REPORT.md."),
]


class BuildError(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"[build_robot_bundle] REFUSING: {msg}")


def die(msg: str):
    raise BuildError(msg)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def load_register() -> list[dict]:
    import csv
    with REGISTER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 5:
        die(f"the retired register holds {len(rows)} rows, expected 5")
    return rows


class Stage:
    def __init__(self, root: Path):
        self.root = root
        self.entries: dict[str, tuple[int, str]] = {}
        self.notes: dict[str, str] = {}

    def emit(self, rel: str, data: bytes, note: str):
        if rel in self.entries:
            die(f"duplicate output path {rel}")
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        self.entries[rel] = (len(data), sha256_bytes(data))
        self.notes[rel] = note

    def copy(self, rel: str, src: Path, note: str):
        self.emit(rel, src.read_bytes(), note)


# ---------------------------------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------------------------------
def gate(register: list[dict]) -> dict:
    if verify_pin.main() != 0:
        die("verify_pin failed - the workbooks no longer match corpus_snapshot.json")
    pinned = load_json(SNAPSHOT_PATH)
    pin_ids = set(pinned["docs"])
    ret_ids = {r["doc_id"] for r in register}
    expected = pin_ids - ret_ids
    corpus_ids = {p.stem for p in CORPUS.rglob("*.json") if "voice" not in p.parts and "index" not in p.parts}
    if corpus_ids != expected:
        die(f"corpus/ holds {len(corpus_ids)} ids but pinned-minus-retired is {len(expected)}: "
            f"missing {sorted(expected - corpus_ids)[:5]}, extra {sorted(corpus_ids - expected)[:5]}")
    # the corpus_mean <-> topic_centroids_meta pairing the loader enforces at query time (app/centering.py)
    cen_meta = load_json(DATA_INDEX / "topic_centroids_meta.json")
    cm = cen_meta.get("corpus_mean") or {}
    if not cm.get("sha256") or sha256_file(DATA_INDEX / "corpus_mean.npy") != cm["sha256"]:
        die("corpus_mean.npy does not match the sha256 topic_centroids_meta.json records - "
            "they must travel together")
    dense_meta = load_json(DATA_INDEX / "pilot_dense_meta.json")
    if cm.get("chunk_index_sha256") != dense_meta.get("corpus_chunk_index_sha256"):
        die("pilot_dense_meta.json and topic_centroids_meta.json disagree on which chunk_index built "
            "them - they must travel together")
    for f in MODEL_FILES:
        if not (MODEL_DIR_SRC / f).exists():
            die(f"models/bge-base-en-v1.5/{f} is missing")
    return {"pin_sha256": sha256_file(SNAPSHOT_PATH), "expected_ids": expected}


# ---------------------------------------------------------------------------------------------------
# retired-id text scan (as knowledge-base/ does: one declared rewrite, everything else is a hard error)
# ---------------------------------------------------------------------------------------------------
class Rewriter:
    def __init__(self, register: list[dict]):
        ids = [r["doc_id"] for r in register]
        self.id_re = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, ids)) + r")(?![0-9])", re.I)
        self.successor = {r["doc_id"].upper(): r["superseded_by"].strip() for r in register if r["superseded_by"].strip()}
        self.hits: list[tuple[str, str]] = []

    def data(self, b: bytes, where: str) -> bytes:
        s = b.decode("utf-8")

        def rep(m):
            new = self.successor.get(m.group(1).upper())
            if not new:
                return m.group(0)
            self.hits.append((where, m.group(1)))
            return new
        return self.id_re.sub(rep, s).encode("utf-8")


# ---------------------------------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------------------------------
def build(stage_dir: Path) -> Stage:
    register = load_register()
    rewriter = Rewriter(register)
    g = gate(register)

    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    st = Stage(stage_dir)

    # corpus/index/chunks.jsonl — needed (chunk text for the composer payload); chunk_index.json is
    # deliberately NOT shipped (see module docstring: only its sha256, embedded as a string in the two
    # meta files above, is ever compared — the file itself is never opened by either pipeline).
    st.copy("corpus/index/chunks.jsonl", CORPUS / "index" / "chunks.jsonl",
            "app/service.py _chunk_text()/_doc_chunk_ids() - the chunk text the composer payload quotes.")

    # corpus/voice/
    for name, note in VOICE_FILES:
        st.copy(f"corpus/voice/{name}", CORPUS / "voice" / name, note)

    # corpus/<type>/<theme>/<id>.json — no .md pair (step 2c). Retired-id text scrubbed on copy (the one
    # declared case: SC090's register_markers names the retired SA085; rewritten to its successor SB085,
    # exactly as knowledge-base/ does).
    n_json = 0
    for folder, letter in FORMAT_DIRS.items():
        for theme_dir in sorted(p for p in (CORPUS / folder).iterdir() if p.is_dir()):
            for jp in sorted(theme_dir.glob("*.json")):
                doc_id = jp.stem
                if doc_id not in g["expected_ids"]:
                    die(f"{doc_id}: not in the expected (pinned-minus-retired) id set")
                b = rewriter.data(jp.read_bytes(), f"corpus/{folder}/{theme_dir.name}/{doc_id}.json")
                st.emit(f"corpus/{folder}/{theme_dir.name}/{doc_id}.json", b,
                        "app/answer_pipeline.py CorpusArtifacts.load_raw_doc() (deployed pipeline, "
                        "always) and app/service.py _doc_json() (traced pipeline, only when "
                        "config.COMPOSER_SIGNATURE_PALETTE=1 - dark by default).")
                n_json += 1
    declared = {("corpus/speeches/C_biographical_personal/SC090.json", "SA085")}
    if set(rewriter.hits) != declared:
        die(f"retired-id references found beyond the one declared case (SC090): {rewriter.hits}")
    if n_json != len(g["expected_ids"]):
        die(f"copied {n_json} corpus json cards, expected {len(g['expected_ids'])}")

    # data/index/
    for rel, note, dark in INDEX_FILES:
        src = PROJECT_ROOT / rel
        if not src.exists():
            die(f"{rel} is missing")
        st.copy(f"{rel}", src, note + (" [dark by default]" if dark else ""))

    # models/bge-base-en-v1.5/ — root-level files only (step 2a)
    for f in MODEL_FILES:
        st.copy(f"models/bge-base-en-v1.5/{f}", MODEL_DIR_SRC / f,
                "app/embeddings.py get_model() (SentenceTransformer) - the resident query/document "
                "encoder. Point CJ_EMBED_MODEL_PATH at this directory on the Pi.")

    # MANIFEST + checksums
    manifest = render_manifest(st, g)
    st.emit("MANIFEST.md", manifest.encode("utf-8"), "this file")
    checksums = "\n".join(f"{sha}  {rel}" for rel, (_, sha) in sorted(st.entries.items())) + "\n"
    st.emit("checksums.sha256", checksums.encode("utf-8"),
            "machine-readable list for `sha256sum -c checksums.sha256` on the Pi after transfer")

    final_scans(st, rewriter.id_re)
    return st


def render_manifest(st: Stage, g: dict) -> str:
    entries = st.entries
    total_bytes = sum(v[0] for v in entries.values())
    rows = "\n".join(f"| `{p}` | {entries[p][0]:,} | `{entries[p][1]}` | {st.notes[p]} |"
                     for p in sorted(entries))
    return f"""# MANIFEST - deploy/pi/bundle/

The data the Reachy Mini needs on the Pi. Built by `scripts/build_robot_bundle.py`, which refuses to run
unless the four pinned workbooks still match `corpus_snapshot.json` (SHA-256 `{g['pin_sha256']}`) and
corpus/ names exactly the same {len(g['expected_ids']):,} live documents (1,295 pinned rows minus the 5
retired ids in `data/csv/retired_doc_ids.csv`).

**This bundle is data only.** Application code (`app/`, `config.py`, `requirements-pi.txt`) reaches the
Pi through the existing `deploy/pi/install.sh` git-clone path, not this folder - see
`deploy/pi/TRANSFER.md` §7-8 and `docs/architecture/PIPELINES.md` for why that split does not fully
match how `install.sh` works today: `app/service.py` (the pipeline this bundle's file list was traced
against) is committed on `deliverable/2026-09` as of Phase 8, but neither it nor `app/retrieval.py`,
`app/embeddings.py`, `app/sparse.py` or `app/centering.py` exist yet on `pi/deployment-snapshots`, the
branch `install.sh` actually clones - so `install.sh` alone still does not deliver the code this data
serves.

Totals: **{len(entries) + 1:,} files** ({len(entries):,} listed below plus this manifest),
**{total_bytes:,} bytes**.

## How the file list was decided

Not hand-written. `batch-04/ph7_analysis/ph7_01_trace_runtime.py` instrumented a cold run of
`app/retrieval.py` + `app/service.py` (the only pipeline that runs offline, without an API key, through
payload assembly) across 22 queries and recorded every file it opened. `app/answer_pipeline.py` - the
pipeline `main_voice_robot.py`'s systemd unit actually runs today - was read directly instead, since
every one of its turns needs a live API call. Where the two disagree this bundle includes the file; full
reasoning is in `batch-04/BATCH-04_REPORT.md`.

Two files neither pipeline reads are deliberately absent: `corpus/**/<id>.md` (dead code in both - see
the per-file note below) and `corpus/index/chunk_index.json` (only its SHA-256, already embedded as a
string in `pilot_dense_meta.json` and `topic_centroids_meta.json`, is ever compared; the 308 KB file
itself is never opened).

`data/index/pilot_dense.npy` ships as float32. float16 was measured
(`batch-04/ph7_analysis/results/size_reductions.json`) and rejected: 1 of 40 test queries' top-10 chunk
ranking changed order, which the phase's own stop rule treats as disqualifying.

`models/bge-base-en-v1.5/` ships 9 files (~419 MB), not the ~838 MB the full local directory holds: that
directory holds the SAME HuggingFace snapshot twice, once at its root and once again, byte-identical,
nested under a commit-hash subdirectory. The nested copy is dropped; an empirical check (load a
`SentenceTransformer` from each and compare embeddings) found them bit-identical.

## Files

| Path | Bytes | SHA-256 | What reads it |
|---|---:|---|---|
{rows}
"""


def final_scans(st: Stage, id_re):
    root = st.root
    on_disk = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    if on_disk != sorted(st.entries):
        die("files on disk differ from files emitted")
    for p in root.rglob("*"):
        if p.is_dir() and not any(p.iterdir()):
            die(f"empty directory {p.relative_to(root)}")
        parts = p.relative_to(root).parts
        for part in parts:
            if part.startswith(".") or part == "__pycache__" or part.endswith((".tmp", ".pyc")) or part == "_archive":
                die(f"forbidden name {'/'.join(parts)}")
        if BATCH_RE.search(p.name.encode()) or id_re.search(p.name):
            die(f"forbidden token in the file name {'/'.join(parts)}")
    for rel in on_disk:
        if rel in ("MANIFEST.md", "checksums.sha256"):
            continue
        b = (root / rel).read_bytes()
        if BATCH_RE.search(b):
            die(f"{rel}: carries the internal batch tag")
        try:
            m = id_re.search(b.decode("utf-8"))
        except UnicodeDecodeError:
            continue   # binary (npy/pkl/safetensors) - the id regex is a text-only check
        if m:
            die(f"{rel}: a retired id ({m.group(0)}) reaches the bundle")


def swap(st: Stage):
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    st.root.rename(OUT_DIR)


def check(st: Stage) -> int:
    if not OUT_DIR.exists():
        print("[build_robot_bundle] --check: deploy/pi/bundle/ does not exist")
        return 1
    have = {p.relative_to(OUT_DIR).as_posix(): sha256_file(p) for p in OUT_DIR.rglob("*") if p.is_file()}
    want = {rel: h for rel, (_, h) in st.entries.items()}
    bad = sorted(set(have) ^ set(want)) + sorted(k for k in set(have) & set(want) if have[k] != want[k])
    if bad:
        print(f"[build_robot_bundle] --check: bundle has drifted ({len(bad)} files), e.g. {bad[:5]}")
        return 1
    print(f"[build_robot_bundle] --check: deploy/pi/bundle/ matches a fresh build ({len(want)} files)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        st = build(STAGE_DIR)
        if args.check:
            rc = check(st)
        else:
            swap(st)
            total = sum(v[0] for v in st.entries.values())
            print(f"[build_robot_bundle] wrote {OUT_DIR}: {len(st.entries)} files, {total:,} bytes")
            rc = 0
    except BaseException:
        if STAGE_DIR.exists():
            shutil.rmtree(STAGE_DIR, ignore_errors=True)
        raise
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR, ignore_errors=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
