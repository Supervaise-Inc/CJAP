"""CE-10 Step 2 (part 2): re-derive OUT_OF_SCOPE_THRESHOLD on the CENTRED scale from the query distribution. Read-only.

Declared BEFORE looking at the centred numbers (so the rule cannot be fitted to them):
  What the gate does. retrieval.route(): in_scope = max centred cos(query, centroid) >= T; when False the topic prior is DROPPED
  (uniform relevance) and retrieval falls through to global. It biases, never gates; the composer owns real out-of-scope declines
  (config.py W3.7 note). So the gate must (1) leave real in-domain queries alone and (2) ideally fire on clearly out-of-domain input.
  Rule. T = the median of the top-1 centred cosine of the NOISE controls (nonsense strings: 'a query no closer to any topic than a
  typical nonsense string is out of scope' — the same null-median logic that gave TOPIC_ASSIGN_MIN_COSINE = 0.31), PROVIDED at least
  97.5% of the REAL in-domain queries (gold40 in + ce11 in, n=49) stay in_scope at that T. If the constraint fails, T = the largest value
  that keeps 97.5% of them (permissive by design). Both candidates and the alternatives are reported; nothing else is fitted.
Sets: gold40, ce11 (real queries); ood (40 authored out-of-domain probes) and noise (20 nonsense strings) are CONTROLS; titles (300 random
document titles) are in-domain pseudo-queries used as a second look at the in-domain tail only (they contain the document's own words).
Writes cache/oos_after.json. Uses cached raw query vectors (qvecs.npz); centring by app/centering (sha256-verified)."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
import config, centering
CACHE = ROOT / "batch-04/ce10_analysis/cache"
z = np.load(CACHE / "qvecs.npz"); sets, ids, scope, texts, V = z["sets"], z["ids"], z["scope"], z["texts"], z["vecs"]
meta = json.loads(Path(config.CENTROIDS_META_PATH).read_text(encoding="utf-8")); mu = centering.mean_for_meta(meta)
cen = np.load(config.CENTROIDS_PATH).astype(np.float32); tids = meta["topic_ids"]
Q = centering.center(V, mu); cos = Q @ cen.T; top = cos.max(1); arg = cos.argmax(1)
def sel(s, sc): return np.where((sets == s) & (scope == sc))[0]
real_in = np.concatenate([sel("gold40", "in"), sel("ce11", "in")]); real_out = np.concatenate([sel("gold40", "out"), sel("ce11", "out")]); meta_q = sel("gold40", "meta")
ood, noise, titles = sel("ood", "out"), sel("noise", "noise"), sel("titles", "in")
pct = lambda a, p: float(np.percentile(top[a], p))
print(f"centred top-1 cosine (query -> nearest of {len(tids)} centroids); n_real_in={len(real_in)}")
for name, a in [("real in-domain (gold40 in + ce11 in)", real_in), ("real out (X35 weather, X36 restaurant, CE-11 oos)", real_out), ("gold40 meta (identity)", meta_q), ("ood controls (40)", ood), ("noise controls (20)", noise), ("titles pseudo-queries (300)", titles)]:
    print(f"  {name:52s} n={len(a):3d} min {top[a].min():.3f} p5 {pct(a, 5):.3f} p25 {pct(a, 25):.3f} median {pct(a, 50):.3f} p75 {pct(a, 75):.3f} max {top[a].max():.3f}")
T_noise_median = float(np.median(top[noise])); T_in_p25 = float(np.percentile(top[real_in], 2.5))
keep = lambda T: float((top[real_in] >= T).mean())
print(f"\ncandidate A (noise-null median)      = {T_noise_median:.3f}  keeps {100 * keep(T_noise_median):.1f}% of real in-domain")
print(f"candidate B (real in-domain p2.5)    = {T_in_p25:.3f}  keeps {100 * keep(T_in_p25):.1f}%")
T = T_noise_median if keep(T_noise_median) >= 0.975 else float(np.sort(top[real_in])[int(np.floor(0.025 * len(real_in)))])
T = round(float(np.floor(T * 100) / 100), 2)      # round DOWN to 2 dp (permissive side)
print(f"RULE -> OUT_OF_SCOPE_THRESHOLD = {T:.2f} (centred)")
def rates(T):
    return {n: {"n": len(a), "in_scope": int((top[a] >= T).sum()), "rate": float((top[a] >= T).mean())} for n, a in
            [("real_in", real_in), ("real_out", real_out), ("meta_identity", meta_q), ("ood", ood), ("noise", noise), ("titles", titles)]}
after = rates(T); before = json.load(open(CACHE / "oos_before.json"))
print("\nin_scope rate at the derived T (centred) vs BEFORE (raw 0.15, v1):")
bmap = {"real_in": ["gold40/in", "ce11/in"], "real_out": ["gold40/out", "ce11/out"], "meta_identity": ["gold40/meta"], "ood": ["ood/out"], "noise": ["noise/noise"], "titles": ["titles/in"]}
for n, v in after.items():
    b_in = sum(before["sets"][k]["in_scope_at_0.15"] for k in bmap[n]); b_n = sum(before["sets"][k]["n"] for k in bmap[n])
    print(f"  {n:14s} before {b_in:3d}/{b_n:<3d} ({100 * b_in / b_n:5.1f}% in)   after {v['in_scope']:3d}/{v['n']:<3d} ({100 * v['rate']:5.1f}% in)")
# sensitivity + control: the same rule on shuffled labels (noise <-> in-domain swapped) must NOT reproduce the separation
sens = {f"{t:.2f}": {"real_in_kept": keep(t), "ood_rejected": float((top[ood] < t).mean()), "noise_rejected": float((top[noise] < t).mean())} for t in np.arange(0.10, 0.61, 0.05)}
print("\nsensitivity (T: real-in kept | ood rejected | noise rejected):")
for t, v in sens.items(): print(f"  {t}: {100 * v['real_in_kept']:5.1f}% | {100 * v['ood_rejected']:5.1f}% | {100 * v['noise_rejected']:5.1f}%")
rng = np.random.default_rng(1); pool = np.concatenate([real_in, noise]); ctrl = []
for _ in range(2000):
    p = rng.permutation(pool); a, b = p[:len(noise)], p[len(noise):]
    ctrl.append(float((top[b] >= np.median(top[a])).mean()))
print(f"control (labels shuffled between in-domain and noise, 2000x): share of the 'in-domain' group kept at the 'noise' median = {np.mean(ctrl):.3f} ± {np.std(ctrl):.3f}  (real: {100 * keep(T_noise_median):.1f}%)")
worst = real_in[np.argsort(top[real_in])[:5]]
print("lowest real in-domain queries:", [(str(ids[i]), round(float(top[i]), 3), str(texts[i])[:48], tids[arg[i]]) for i in worst])
json.dump({"threshold_after": T, "scale_after": "centred cosine, v2 centroids (n=%d)" % len(tids), "candidates": {"noise_median": T_noise_median, "real_in_p2.5": T_in_p25},
           "rates_after": after, "sensitivity": sens, "control_shuffled_kept_mean": float(np.mean(ctrl)), "control_shuffled_kept_sd": float(np.std(ctrl)),
           "top_cos": {n: [float(top[i]) for i in a] for n, a in [("real_in", real_in), ("ood", ood), ("noise", noise)]}},
          open(CACHE / "oos_after.json", "w"), indent=1)
