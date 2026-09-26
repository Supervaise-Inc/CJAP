"""CE-10 entry check (Python, not grep). Branch/HEAD, protected-file hashes, corpus state, and the sign-off reconciliation against Table 1 of the proposal."""
import hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
def sha8(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]
def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = True
def chk(name, cond, detail=""):
    global ok; ok &= bool(cond); print(f"  [{'OK ' if cond else 'BAD'}] {name} {detail}")
print("== branch / HEAD ==")
chk("branch", git("rev-parse", "--abbrev-ref", "HEAD") == "deliverable/2026-09", git("rev-parse", "--abbrev-ref", "HEAD"))
chk("HEAD", git("rev-parse", "HEAD").startswith("cb4e7ac"), git("rev-parse", "--short", "HEAD"))
print("== protected files (expected untouched) ==")
for f, exp in [("scripts/build_topic_map.py", "0c6dabaf"), ("config.py", "b30ad346"), ("corpus/voice/topic_map.json", "da34048f"), ("data/index/topic_centroids.npy", "71a7c294")]:
    chk(f, sha8(ROOT / f) == exp, f"{sha8(ROOT / f)} (expect {exp})")
print("== corpus ==")
docs = [p for p in ROOT.glob("corpus/*/*/*.json")]
docs = [p for p in docs if isinstance(json.loads(p.read_text(encoding='utf-8')), dict) and 'id' in json.loads(p.read_text(encoding='utf-8')) and json.loads(p.read_text(encoding='utf-8')).get('format')]
chk("docs on disk", len(docs) == 1290, len(docs))
cm = json.loads((ROOT / "data/index/corpus_dense_meta.json").read_text(encoding="utf-8"))
chk("chunks", cm["n_chunks"] == 13549, cm["n_chunks"])
chk("chunk_index.json sha8", sha8(ROOT / "corpus/index/chunk_index.json") == "f89071b9", sha8(ROOT / "corpus/index/chunk_index.json"))
snap = json.loads((ROOT / "corpus_snapshot.json").read_text(encoding="utf-8"))
chk("corpus_snapshot.json still the old pin", snap["header"]["doc_id_count"] == 1109, snap["header"]["doc_id_count"])
print("== sign-off reconciliation ==")
phase = (ROOT / "batch-04/PHASE-5_CE-10_build_taxonomy_v2.md").read_text(encoding="utf-8")
block = re.search(r"APPROVED:(.*?)\| TOPIC_MERGE_COSINE=([0-9.]+) \| TOPIC_ASSIGN_MIN_COSINE=([0-9.]+)", phase, re.S)
ids = [x.strip() for x in block.group(1).replace("\n", " ").split(",") if x.strip()]
prop = (ROOT / "batch-04/taxonomy_v2_PROPOSAL.md").read_text(encoding="utf-8")
sec0 = re.search(r"APPROVED: (.*?) \| TOPIC_MERGE_COSINE=([0-9.]+) \| TOPIC_ASSIGN_MIN_COSINE=([0-9.]+)", prop, re.S)
prop_line_ids = [x.strip() for x in sec0.group(1).split(",")]
t1 = re.search(r"\| id \| display_name.*?\n\| :---.*?\n((?:\|.*\n)+)", prop).group(1)
t1_ids = [r.split("|")[1].strip() for r in t1.strip().split("\n")]
chk("count of approved ids == 30", len(ids) == 30, len(ids))
chk("no duplicate ids", len(set(ids)) == len(ids))
chk("Table 1 has 30 rows", len(t1_ids) == 30, len(t1_ids))
chk("approved ids == Table 1 ids (as sets)", set(ids) == set(t1_ids), f"only-in-signoff {sorted(set(ids) - set(t1_ids))} only-in-table {sorted(set(t1_ids) - set(ids))}")
chk("approved ids == section-0 line of the proposal (same order)", ids == prop_line_ids)
chk("TOPIC_MERGE_COSINE 0.75 matches section 7", block.group(2) == "0.75" and "TOPIC_MERGE_COSINE` → **0.75" in prop, block.group(2))
chk("TOPIC_ASSIGN_MIN_COSINE 0.31 matches section 7", block.group(3) == "0.31" and "TOPIC_ASSIGN_MIN_COSINE` → **0.31" in prop, block.group(3))
appendix = re.search(r"```python\n(TAXONOMY.*?)\n```", prop, re.S).group(1)
app_ids = re.findall(r'^        "id": "([a-z_]+)",', appendix, re.M)
chk("Appendix A TAXONOMY ids == approved ids (as sets)", set(app_ids) == set(ids) and len(app_ids) == 30, len(app_ids))
print("\nENTRY STATE:", "ALL CHECKS PASSED" if ok else "FAILED")
sys.exit(0 if ok else 1)
