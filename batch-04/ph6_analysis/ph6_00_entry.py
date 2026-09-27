"""Phase 6 entry check (Python, not grep)."""
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = True
def chk(n, c, d=""):
    global ok; ok &= bool(c); print(f"  [{'OK ' if c else 'BAD'}] {n} {d}")
chk("branch", git("rev-parse", "--abbrev-ref", "HEAD") == "deliverable/2026-09", git("rev-parse", "--abbrev-ref", "HEAD"))
chk("HEAD", git("rev-parse", "HEAD").startswith("406e4e5"), git("rev-parse", "--short", "HEAD"))
js = [p for p in ROOT.glob("corpus/*/*/*.json") if p.parts[-3] in ("columns", "books", "speeches", "biography")]
mds = [p for p in ROOT.glob("corpus/*/*/*.md") if p.parts[-3] in ("columns", "books", "speeches", "biography")]
chk("corpus .json / .md", len(js) == 1290 and len(mds) == 1290, f"{len(js)} / {len(mds)}")
cr = sum(1 for p in js + mds if b"\r" in p.read_bytes())
chk("corpus files containing a CR byte", cr == 0, cr)
tp = sum(1 for p in js if "topic_paths" in json.loads(p.read_text(encoding="utf-8")))
chk("topic_paths present", tp == 1290, f"{tp} of 1290")
snap = json.loads((ROOT / "corpus_snapshot.json").read_text(encoding="utf-8"))
chk("corpus_snapshot entries", len(snap["docs"]) == 1295, len(snap["docs"]))
r = subprocess.run([sys.executable, str(ROOT / "scripts/verify_pin.py")], capture_output=True, text=True); chk("verify_pin", r.returncode == 0, r.stdout.strip()[:70])
chk("chunk_index.json sha8", sha(ROOT / "corpus/index/chunk_index.json")[:8] == "e672757b", sha(ROOT / "corpus/index/chunk_index.json")[:8])
tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))
chk("topic_map", len(tm["topics"]) == 30 and tm["taxonomy_version"] == 2 and tm["corpus_stats"]["n_docs"] == 1290 and list(tm["intents"]) == ["robot_identity_meta"])
chk("centroids shape", np.load(ROOT / "data/index/topic_centroids.npy").shape == (30, 768))
mu = np.load(ROOT / "data/index/corpus_mean.npy"); chk("corpus_mean", mu.shape == (768,) and sha(ROOT / "data/index/corpus_mean.npy")[:8] == "596a9fb0", sha(ROOT / "data/index/corpus_mean.npy")[:8])
print("\nENTRY STATE:", "ALL CHECKS PASSED" if ok else "FAILED"); sys.exit(0 if ok else 1)
