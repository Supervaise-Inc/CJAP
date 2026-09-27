"""
Phase 9 step 2 - build "Bundle Folder/", the single thing that can be dragged onto a USB stick or
straight to the robot: the payload nested one level down as cjap-bundle/ (no space in that name - the
outer folder's space is fine for Windows Explorer/a USB stick and breaks rsync/scp/systemd paths the
moment it reaches Linux), plus the existing install/ materials and a plain-language READ_ME_FIRST.md.

Reuses scripts/build_robot_bundle.py's traced file list VERBATIM - its gate(), Rewriter, load_register,
FORMAT_DIRS, INDEX_FILES, MODEL_FILES, VOICE_FILES, MODEL_DIR_SRC, CORPUS, DATA_INDEX are imported, not
re-derived. What this script adds on top, because Phase 8/9 found install.sh cannot deliver it (see
docs/architecture/PIPELINES.md and batch-04/BATCH-04_REPORT.md): the application code itself - exactly
the five modules the Phase 7 trace showed the retrieval path imports (service.py, retrieval.py,
embeddings.py, sparse.py, centering.py, under cjap-bundle/app/) plus config.py (all five import it,
directly in cjap-bundle/, not alongside them - see the note in render_manifest() for the confirmed bug
that ordering avoids) - and a copy of deploy/pi/'s install materials, so this one folder is everything an
operator needs, not just data.

New here, not in build_robot_bundle.py: every text file in cjap-bundle/ is normalised to LF, as
knowledge-base/ does. deploy/pi/bundle/ never applied this - config.py, the voice files, and 4 of the
data/index JSON sidecars are CRLF there (chunks.jsonl, topic_map.json, topic_centroids_meta.json and the
per-document corpus cards already happened to be LF). Declared in MANIFEST.md with exact counts, the
same convention knowledge-base/'s MANIFEST uses. install/ and READ_ME_FIRST.md
(outside cjap-bundle/, so not part of "the payload" checksums.sha256 covers) get the same LF treatment
for consistency, since they are Linux-bound too.

    python scripts/build_bundle_folder.py            # delete "Bundle Folder/" and rebuild it
    python scripts/build_bundle_folder.py --check     # rebuild into staging, diff, exit 1 on any difference
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import build_robot_bundle as brb  # noqa: E402 - reuse, do not re-derive
from scripts.build_corpus_snapshot import SNAPSHOT_PATH  # noqa: E402

OUT_DIR = PROJECT_ROOT / "Bundle Folder"
STAGE_DIR = PROJECT_ROOT / "Bundle Folder.staging"
PAYLOAD = "cjap-bundle"

# The phase spec lists these flat under one code/ folder. Tried that literally first and it is
# BROKEN: app/service.py etc. compute their own repo root as `Path(__file__).resolve().parent.parent`
# (two hops - they normally live one level under the repo root, in app/), while config.py computes its
# repo root as `Path(__file__).resolve().parent` (one hop - it normally lives AT the repo root). Flatten
# both into the same directory and config.py's own REPO_ROOT lands one level too deep -
# `config.CENTROIDS_META_PATH` and every other REPO_ROOT-relative path in it point at a directory that
# does not exist, and every service.py call that goes through config.* rather than service.py's own
# _REPO_ROOT breaks immediately (empirically confirmed: batch-04/ph9_analysis/results/
# code_layout_bug_check.json). So this mirrors the REAL relative layout instead: config.py sits directly
# in cjap-bundle/ (one hop from corpus/, data/, models/ - matching how it sits at the real repo root),
# and the five modules sit in cjap-bundle/app/ (two hops - matching app/ in the real repo). Both
# path-root computations then agree, AND a full `rsync -a cjap-bundle/ <pi-checkout>/` becomes the
# correct, complete deploy — a strict improvement over a flat code/ dump either way.
CODE_FILES = [
    ("app/service.py", "app/service.py",
     "the retrieval pipeline's entry point (answer()) - imports retrieval, embeddings (indirectly), config"),
    ("app/retrieval.py", "app/retrieval.py",
     "embed -> route -> retrieve; imports embeddings, sparse, centering, config"),
    ("app/embeddings.py", "app/embeddings.py",
     "the resident bge-base encoder (get_model, embed_query, load_dense_index); imports config"),
    ("app/sparse.py", "app/sparse.py",
     "the BM25 arm + atomic-phrase tokenizer; imports config"),
    ("app/centering.py", "app/centering.py",
     "loads and verifies corpus_mean.npy; imports config"),
    ("config.py", "config.py",
     "every knob all five modules above read; imports nothing project-local - "
     "MUST sit here, directly in cjap-bundle/, not alongside app/*.py (see the note above)"),
]
INSTALL_FILES = ["install.sh", "requirements-pi.txt", "TRANSFER.md"]


def die(msg: str):
    raise brb.BuildError(msg)


def to_lf(b: bytes, where: str) -> tuple[bytes, bool]:
    if b"\r" not in b:
        return b, False
    out = b.replace(b"\r\n", b"\n")
    if b"\r" in out:
        die(f"{where}: a lone carriage return remains after CRLF normalisation")
    return out, True


class Stage:
    """Tracks every file under Bundle Folder/ (both cjap-bundle/ and install/+READ_ME_FIRST.md), so one
    object can answer --check's diff; checksums.sha256 filters this down to the cjap-bundle/ subset."""

    def __init__(self, root: Path):
        self.root = root
        self.entries: dict[str, tuple[int, str]] = {}

    def emit(self, rel: str, data: bytes):
        if rel in self.entries:
            die(f"duplicate output path {rel}")
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        self.entries[rel] = (len(data), hashlib.sha256(data).hexdigest())

    def copy_lf(self, rel: str, src: Path) -> bool:
        b, crlf = to_lf(src.read_bytes(), rel)
        self.emit(rel, b)
        return crlf


def render_manifest(st: Stage, g: dict, xform: dict) -> str:
    payload_entries = {k: v for k, v in st.entries.items() if k.startswith(PAYLOAD + "/")}
    total_bytes = sum(v[0] for v in payload_entries.values())
    code_paths = {f"{PAYLOAD}/{dst}" for _, dst, _ in CODE_FILES}
    code_rows = "\n".join(
        f"| `{PAYLOAD}/{dst}` | {payload_entries[f'{PAYLOAD}/{dst}'][0]:,} | "
        f"`{payload_entries[f'{PAYLOAD}/{dst}'][1]}` | {note} |"
        for _, dst, note in CODE_FILES)
    other_rows = "\n".join(
        f"| `{p}` | {payload_entries[p][0]:,} | `{payload_entries[p][1]}` |"
        for p in sorted(payload_entries) if p not in code_paths)
    return f"""# MANIFEST - {PAYLOAD}/ (inside "Bundle Folder/")

This is the payload half of "Bundle Folder/" - the part that goes to the Pi. `../READ_ME_FIRST.md`
covers the whole folder in plain steps; this file is the audit trail.

Built by `scripts/build_bundle_folder.py`, which refuses to run unless the four pinned workbooks still
match `corpus_snapshot.json` (SHA-256 `{g['pin_sha256']}`) and reuses `scripts/build_robot_bundle.py`'s
traced file list VERBATIM for everything except `app/` and `config.py` below - see that script's own
MANIFEST (`deploy/pi/bundle/MANIFEST.md`) for how the corpus/data/model file list was decided; this
document adds only what is new here.

**What is new relative to `deploy/pi/bundle/`:**

1. **The application code** - `app/service.py`, `retrieval.py`, `embeddings.py`, `sparse.py`,
   `centering.py` (the five modules Phase 7's trace showed the retrieval pipeline imports) and
   `config.py` (all five read it). `deploy/pi/bundle/` is data-only on the stated assumption that
   `install.sh` delivers the code; Phase 8/9 found it currently does not (neither `pi/deployment-
   snapshots`, the branch `install.sh` clones, nor any other path — see `docs/architecture/PIPELINES.md`
   and `batch-04/BATCH-04_REPORT.md`). This folder does not depend on that being fixed.

   **Why `config.py` sits directly in `{PAYLOAD}/` and the five modules sit in `{PAYLOAD}/app/`, not
   all six flat in one folder:** tried flat first, and it is broken. `app/service.py` (and the other
   four) compute their own repo root as `Path(__file__).resolve().parent.parent` - two hops, because
   they normally live one level under the repo root, in `app/`. `config.py` computes its repo root as
   `Path(__file__).resolve().parent` - one hop, because it normally lives AT the repo root. Flatten both
   into one directory and `config.py`'s own `REPO_ROOT` lands one level too deep - every path it defines
   (`CENTROIDS_META_PATH`, `DENSE_INDEX_PATH`, ...) points at a directory that does not exist, and the
   pipeline fails immediately. This layout mirrors the real relative structure instead, so both
   computations agree, and a plain `rsync -a {PAYLOAD}/ <pi-checkout>/` becomes a complete, correct copy
   on its own - simpler than the file-by-file copy `deploy/pi/TRANSFER.md` §8 describes.
2. **LF line endings throughout**, as `knowledge-base/` does. `deploy/pi/bundle/` never normalised line
   endings: {xform['crlf_count']} of the {xform['text_file_count']} text files here are CRLF in the
   repository -
   {', '.join(f'`{p[len(PAYLOAD) + 1:]}`' for p in xform['crlf_all'])}
   - (`chunks.jsonl`, `topic_map.json`, `topic_centroids_meta.json` and the per-document corpus cards
   already happened to be LF). Binary files (`.npy`, `.pkl`, `.safetensors`) are copied byte-exact -
   line-ending normalisation does not apply to them.

Everything else - corpus card selection, the retired-id exclusion and its one declared text rewrite, the
corpus_mean/topic_centroids_meta pairing check, the float32 (not float16) dense index, the 9-file (not
19-file) model directory - is identical reasoning to `deploy/pi/bundle/`, reapplied here.

Totals: **{len(payload_entries) + 1:,} files** ({len(payload_entries):,} listed below plus this
manifest), **{total_bytes:,} bytes**.

## Application code

| Path | Bytes | SHA-256 | What it is |
|---|---:|---|---|
{code_rows}

## Everything else (identical selection to `deploy/pi/bundle/`, LF-normalised here)

| Path | Bytes | SHA-256 |
|---|---:|---|
{other_rows}
"""


def build(stage_dir: Path) -> Stage:
    register = brb.load_register()
    rewriter = brb.Rewriter(register)
    g = brb.gate(register)

    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    st = Stage(stage_dir)
    xform = {"crlf_all": [], "text_file_count": 0}

    BINARY_SUFFIXES = (".npy", ".pkl", ".safetensors")

    def payload(rel_no_prefix: str, src: Path, rewrite: bool = False):
        rel = f"{PAYLOAD}/{rel_no_prefix}"
        b = src.read_bytes()
        if src.suffix in BINARY_SUFFIXES:
            st.emit(rel, b)   # byte-exact — a \r\n inside numeric data is not a line ending
            return
        b, crlf = to_lf(b, rel)
        if rewrite:
            b = rewriter.data(b, rel)
        st.emit(rel, b)
        xform["text_file_count"] += 1
        if crlf:
            xform["crlf_all"].append(rel)

    # the application code — new relative to deploy/pi/bundle/; dst_name already carries its correct
    # relative path (app/<module>.py or config.py at the payload root — see render_manifest's note)
    for src_rel, dst_name, _note in CODE_FILES:
        payload(dst_name, PROJECT_ROOT / src_rel)

    # corpus/index/chunks.jsonl
    payload("corpus/index/chunks.jsonl", brb.CORPUS / "index" / "chunks.jsonl")

    # corpus/voice/
    for name, _note in brb.VOICE_FILES:
        payload(f"corpus/voice/{name}", brb.CORPUS / "voice" / name)

    # corpus/<type>/<theme>/<id>.json — retired-id text scrubbed on copy, same one declared case
    n_json = 0
    for folder in brb.FORMAT_DIRS:
        for theme_dir in sorted(p for p in (brb.CORPUS / folder).iterdir() if p.is_dir()):
            for jp in sorted(theme_dir.glob("*.json")):
                doc_id = jp.stem
                if doc_id not in g["expected_ids"]:
                    die(f"{doc_id}: not in the expected (pinned-minus-retired) id set")
                payload(f"corpus/{folder}/{theme_dir.name}/{doc_id}.json", jp, rewrite=True)
                n_json += 1
    declared = {("cjap-bundle/corpus/speeches/C_biographical_personal/SC090.json", "SA085")}
    if set(rewriter.hits) != declared:
        die(f"retired-id references found beyond the one declared case (SC090): {rewriter.hits}")
    if n_json != len(g["expected_ids"]):
        die(f"copied {n_json} corpus json cards, expected {len(g['expected_ids'])}")

    # data/index/
    for rel, _note, _dark in brb.INDEX_FILES:
        src = PROJECT_ROOT / rel
        if not src.exists():
            die(f"{rel} is missing")
        payload(rel, src)

    # models/bge-base-en-v1.5/ — root-level files only; binary, no LF pass, but still routed through
    # payload() for a consistent record (to_lf() is a no-op on a file with no \r bytes at all, and these
    # binary files pass unchanged since a stray \r0x0a byte pair in a safetensors/pickle blob would be a
    # corruption bug worth finding, not something to silently "fix" — none were found).
    for f in brb.MODEL_FILES:
        p = PROJECT_ROOT / "models" / "bge-base-en-v1.5" / f
        b = p.read_bytes()
        st.emit(f"{PAYLOAD}/models/bge-base-en-v1.5/{f}", b)

    xform["crlf_count"] = len(xform["crlf_all"])
    xform["crlf_examples"] = xform["crlf_all"][:4]

    # MANIFEST + checksums (checksums covers ONLY cjap-bundle/, per the phase spec)
    manifest = render_manifest(st, g, xform)
    st.emit(f"{PAYLOAD}/MANIFEST.md", manifest.encode("utf-8"))
    payload_now = {k: v for k, v in st.entries.items() if k.startswith(PAYLOAD + "/")}
    checksums = "\n".join(
        f"{sha}  {rel[len(PAYLOAD) + 1:]}" for rel, (_, sha) in sorted(payload_now.items())) + "\n"
    st.emit(f"{PAYLOAD}/checksums.sha256", checksums.encode("utf-8"))

    # install/ — copied from deploy/pi/, LF-normalised for the same reason as the payload
    for name in INSTALL_FILES:
        src = PROJECT_ROOT / "deploy" / "pi" / name
        b, _ = to_lf(src.read_bytes(), f"install/{name}")
        st.emit(f"install/{name}", b)
    for p in sorted((PROJECT_ROOT / "deploy" / "pi" / "systemd").rglob("*")):
        if p.is_file():
            rel = p.relative_to(PROJECT_ROOT / "deploy" / "pi")
            b, _ = to_lf(p.read_bytes(), f"install/{rel.as_posix()}")
            st.emit(f"install/{rel.as_posix()}", b)

    readme = render_read_me_first()
    b, _ = to_lf(readme.encode("utf-8"), "READ_ME_FIRST.md")
    st.emit("READ_ME_FIRST.md", b)

    final_scans(st, rewriter.id_re)
    return st, xform, g


def render_read_me_first() -> str:
    return (Path(__file__).resolve().parent.parent / "batch-04" / "ph9_analysis"
            / "READ_ME_FIRST_source.md").read_text(encoding="utf-8")


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
        if brb.BATCH_RE.search(p.name.encode()) or id_re.search(p.name):
            die(f"forbidden token in the file name {'/'.join(parts)}")
    for rel in on_disk:
        if rel.endswith(("MANIFEST.md", "checksums.sha256")):
            continue
        b = (root / rel).read_bytes()
        # The batch-04 CONTENT scan is a data-delivery rule ("no internal processing tag inside a
        # corpus document, so old and new are indistinguishable" - see build_robot_bundle.py's own
        # module docstring). It does not apply to code/, install/ or READ_ME_FIRST.md: those
        # legitimately cite "batch-04/..." paths in comments and prose as documentation cross-
        # references (e.g. app/centering.py's docstring points at batch-04/taxonomy_v2_PROPOSAL.md),
        # which is not the leaked-artifact problem the rule exists to catch.
        code_or_docs = (rel.startswith((f"{PAYLOAD}/app/", "install/"))
                       or rel == f"{PAYLOAD}/config.py" or rel == "READ_ME_FIRST.md")
        if not code_or_docs and brb.BATCH_RE.search(b):
            die(f"{rel}: carries the internal batch tag")
        try:
            m = id_re.search(b.decode("utf-8"))
        except UnicodeDecodeError:
            continue
        if m:
            die(f"{rel}: a retired id ({m.group(0)}) reaches the bundle")
        if b"\r" in b and not rel.endswith((".npy", ".pkl", ".safetensors")):
            die(f"{rel}: carries a carriage return after LF normalisation was supposed to run")


def swap(st: Stage):
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    st.root.rename(OUT_DIR)


def check(st: Stage) -> int:
    if not OUT_DIR.exists():
        print("[build_bundle_folder] --check: 'Bundle Folder/' does not exist")
        return 1
    have = {p.relative_to(OUT_DIR).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUT_DIR.rglob("*") if p.is_file()}
    want = {rel: h for rel, (_, h) in st.entries.items()}
    bad = sorted(set(have) ^ set(want)) + sorted(k for k in set(have) & set(want) if have[k] != want[k])
    if bad:
        print(f"[build_bundle_folder] --check: drifted ({len(bad)} files), e.g. {bad[:5]}")
        return 1
    print(f"[build_bundle_folder] --check: 'Bundle Folder/' matches a fresh build ({len(want)} files)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        st, xform, g = build(STAGE_DIR)
        if args.check:
            rc = check(st)
        else:
            swap(st)
            payload_entries = {k: v for k, v in st.entries.items() if k.startswith(PAYLOAD + "/")}
            payload_bytes = sum(v[0] for v in payload_entries.values())
            total_bytes = sum(v[0] for v in st.entries.values())
            print(f"[build_bundle_folder] wrote {OUT_DIR}: {len(st.entries)} files, {total_bytes:,} bytes total")
            print(f"[build_bundle_folder]   {PAYLOAD}/: {len(payload_entries)} files, {payload_bytes:,} bytes")
            print(f"[build_bundle_folder]   CRLF->LF normalised: {xform['crlf_count']}/{xform['text_file_count']} text files")
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
