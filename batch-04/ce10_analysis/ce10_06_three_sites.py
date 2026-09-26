"""CE-10 Step 1 proof (positive side): each of the three cosine sites demonstrably uses data/index/corpus_mean.npy, and the raw dense arm is untouched.
Also measures what centring does to retrieval itself (LAMBDA * topic_affinity now has teeth) by replaying the frozen 40 queries with the
BEFORE configuration emulated in-process (v1 raw centroids, mean = 0 so centring is a no-op, OUT_OF_SCOPE 0.15) against the AFTER (v2 centred).
Read-only on the repo (monkeypatches module globals in-process only)."""
import csv, json, sys
from pathlib import Path
import numpy as np
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
import config, centering, embeddings
embeddings.get_model()
import retrieval
CACHE = ROOT / "batch-04/ce10_analysis/cache"
ok = True
def chk(name, cond, detail=""):
    global ok; ok &= bool(cond); print(f"  [{'OK ' if cond else 'BAD'}] {name} {detail}")

cen, meta = retrieval._load_centroids()
mu_file = np.load(config.CORPUS_MEAN_PATH).astype(np.float32)
print("== the mean the runtime holds is the file's, and the file is the one the centroid meta names ==")
chk("runtime mean == corpus_mean.npy", np.array_equal(retrieval._corpus_mean(), mu_file))
chk("meta sha256 == sha256(corpus_mean.npy)", meta["corpus_mean"]["sha256"] == centering.sha256_file(config.CORPUS_MEAN_PATH), meta["corpus_mean"]["sha256"][:16] + "…")
chk("meta scale / taxonomy_version", meta["scale"] == "centred" and meta["taxonomy_version"] == 2)

print("== SITE 1 — centroid build: recompute independently from the map's members + the FILE's mean ==")
cm = json.loads(config.CORPUS_DENSE_META_PATH.read_text(encoding="utf-8")); mat = np.load(config.CORPUS_DENSE_PATH).astype(np.float32)
rows_of = {}
for i, c in enumerate(cm["chunk_ids"]): rows_of.setdefault(c.split("::")[0], []).append(i)
tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))["topics"]
diff, rawdiff = 0.0, []
for j, tid in enumerate(meta["topic_ids"]):
    rows = [r for d in sorted(tm[tid]["doc_ids"]) for r in rows_of[d]]
    v = mat[rows].astype(np.float64).mean(0)
    indep = (v - mu_file) / np.linalg.norm(v - mu_file)
    raw = v / np.linalg.norm(v)
    diff = max(diff, float(np.abs(indep - cen[j]).max())); rawdiff.append(float(raw @ cen[j]))
chk("stored centroids == unit(mean(members) - corpus_mean) for all 30", diff < 1e-5, f"max |Δ| {diff:.2e}")
chk("...and they are NOT the raw-mean centroids", max(rawdiff) < 0.9, f"cosine(raw-built, stored) max {max(rawdiff):.3f}, median {np.median(rawdiff):.3f}")

print("== SITE 2 — index time: _load_pilot() topic_affinity sims ==")
pmat, cids, dids, sims = retrieval._load_pilot()
indep = centering.center(pmat, mu_file) @ cen.T
chk("chunk_cen_sims == unit(mat - mu) @ cen.T", np.allclose(sims, indep, atol=1e-5), f"max |Δ| {np.abs(sims - indep).max():.2e}")
rawsims = pmat @ cen.T
chk("...and are NOT the raw mat @ cen.T", not np.allclose(sims, rawsims, atol=1e-2), f"mean |Δ| vs raw {np.abs(sims - rawsims).mean():.3f}, max {np.abs(sims - rawsims).max():.3f}; a chunk's nearest topic differs in {100 * float((sims.argmax(1) != rawsims.argmax(1)).mean()):.1f}% of chunks")
chk("dense matrix handed to the dense arm is still RAW", np.allclose(pmat, mat, atol=1e-6))

print("== SITE 3 — query time: route() ==")
z = np.load(CACHE / "qvecs.npz"); V = z["vecs"]; texts = z["texts"]
qv = V[0]
ri = retrieval.route(str(texts[0]), qv=qv)
indep = cen @ centering.center(qv, mu_file)
chk("route cos == cen @ unit(qv - mu)", np.allclose(ri["cos"], indep, atol=1e-6), f"top {ri['top_topic']} {ri['top_cosine']}")
chk("...and is NOT cen @ qv (raw)", not np.allclose(ri["cos"], cen @ qv, atol=1e-2), f"mean |Δ| vs raw {np.abs(ri['cos'] - cen @ qv).mean():.3f}; raw top cos would read {float((cen @ qv).max()):.3f} vs centred {ri['top_cosine']}")
chk("route returns the RAW qv for the dense arm", np.array_equal(ri["qv"], qv))

print("== retrieval drift on the frozen 40 (BEFORE emulated: v1 raw centroids, mean=0, OUT_OF_SCOPE 0.15) ==")
G = list(csv.DictReader(open(ROOT / "eval/results/gold_reference_set.csv", encoding="utf-8-sig")))
allow = set(dids)
arch = ROOT / "data/index/_archive"
v1c = np.load(arch / "_v1_pre-CE10_2026-09-27_topic_centroids.npy").astype(np.float32); v1m = json.loads((arch / "_v1_pre-CE10_2026-09-27_topic_centroids_meta.json").read_text(encoding="utf-8"))
def run_all(mode):
    out = {}
    saved = (retrieval._CENTROIDS, retrieval._MU, retrieval._PILOT, config.OUT_OF_SCOPE_THRESHOLD)
    try:
        if mode == "before":
            retrieval._CENTROIDS = (v1c, v1m); retrieval._MU = np.zeros_like(mu_file); retrieval._PILOT = (pmat, cids, dids, pmat @ v1c.T); config.OUT_OF_SCOPE_THRESHOLD = 0.15
        for r in G:
            qi = int(np.where((z["sets"] == "gold40") & (z["ids"] == r["qid"]))[0][0])
            ri = retrieval.route(r["query"], qv=V[qi])
            rr = retrieval.retrieve(r["query"], allow, route_info=ri)
            su = retrieval._score_universe(r["query"], allow, route_info=ri)
            ranked = sorted(su["universe"], key=lambda c: -su["score"][c]); rdocs = []
            for c in ranked:
                d = c.split("::")[0]
                if d not in rdocs: rdocs.append(d)
                if len(rdocs) >= 10: break
            out[r["qid"]] = {"sel": [c for c, _, _ in rr["selected"]], "top": ri["top_topic"], "in_scope": ri["in_scope"], "relmax": float(ri["relevance"].max()), "rdocs": rdocs}
    finally:
        retrieval._CENTROIDS, retrieval._MU, retrieval._PILOT, config.OUT_OF_SCOPE_THRESHOLD = saved
    return out
B, A = run_all("before"), run_all("after")
jac = [len(set(B[q]["sel"]) & set(A[q]["sel"])) / max(1, len(set(B[q]["sel"]) | set(A[q]["sel"]))) for q in B]
same_top_doc = sum(1 for q in B if B[q]["sel"][0].split("::")[0] == A[q]["sel"][0].split("::")[0])
same_set = sum(1 for q in B if set(B[q]["sel"]) == set(A[q]["sel"]))
print(f"  selected-chunk sets identical before/after: {same_set}/40 | top-1 chunk's document unchanged: {same_top_doc}/40 | mean Jaccard of the selected sets {np.mean(jac):.3f} (min {np.min(jac):.3f})")
print(f"  topic prior peak (max relevance) before {np.median([B[q]['relmax'] for q in B]):.3f} -> after {np.median([A[q]['relmax'] for q in B]):.3f} (uniform over 34 = 0.029, over 30 = 0.033)")
print(f"  in_scope before {sum(B[q]['in_scope'] for q in B)}/40 -> after {sum(A[q]['in_scope'] for q in A)}/40")
SENT = {"OOS", "META", "GAP", "RETIRED", "NONE"}
def gold(r): return [x.strip() for x in r["gold_source_docs"].split(";") if x.strip() and x.strip() not in SENT]
ins = [r for r in G if r["scope_gold"] == "in" and gold(r)]
rec = {}
for side, R in (("before", B), ("after", A)):
    rec[side] = {k: sum(any(d in gold(r) for d in R[r["qid"]]["rdocs"][:k]) for r in ins) / len(ins) for k in (1, 3, 5, 10)}
print(f"  gold-doc hit@k over {len(ins)} in-scope queries (v4 gold, FULL 1,290-doc universe both sides — relative, not the ratified 95-doc baseline):")
for k in (1, 3, 5, 10): print(f"     hit@{k:<2d} before {100 * rec['before'][k]:5.1f}%  after {100 * rec['after'][k]:5.1f}%  Δ {100 * (rec['after'][k] - rec['before'][k]):+5.1f} pts")
json.dump({"hit_at_k": rec, "jaccard": jac, "same_set": same_set, "same_top_doc": same_top_doc,
           "before": {q: {k: v for k, v in B[q].items() if k != 'sel'} for q in B}, "after": {q: {k: v for k, v in A[q].items() if k != 'sel'} for q in A}}, open(CACHE / "retrieval_drift.json", "w"), indent=1)
print("\nALL CHECKS PASSED" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
