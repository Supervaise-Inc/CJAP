"""CE-9 step 8: where does each of the v1 topics land in the recommended partition? (evidence for Table 2). Read-only. Centred scale only.
For each v1 topic (members = docs its v1 matcher catches, from cache/prior_members.json): centred-centroid cosine to every recommended dimension,
how many of its members sit in each dimension, and the reverse share. Also the v1 topic's own compactness on the centred scale
(mean centred cosine of its members to its centroid vs the same for a random doc set of the same size)."""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

C = Corpus(); Xc, mu = centered_doc_vectors(C); N = len(C.doc_ids)
M = int(sys.argv[1]) if len(sys.argv) > 1 else 20
lab = np.load(CACHE / f"ce9_level_m{M}.npy"); ids = sorted(set(lab.tolist()))
members = json.load(open(CACHE / "prior_members.json"))
P = prior_art()
cen = {c: unit(Xc[lab == c].mean(axis=0)) for c in ids}
rng = np.random.default_rng(20260926)
out = {}
print(f"{'v1 topic':34s} {'n':>4s} {'compact':>7s} {'rand':>5s}  best dimensions (centred cos | v1 members inside | share of dimension that is v1)")
for t in sorted(members):
    ms = members.get(t, [])
    if not ms: print(t, "no members"); continue
    idx = np.array([C.doc_index[d] for d in ms])
    cv = unit(Xc[idx].mean(axis=0))
    comp = float((Xc[idx] @ cv).mean())
    ri = rng.choice(N, size=len(idx), replace=False); rc = unit(Xc[ri].mean(axis=0)); rcomp = float((Xc[ri] @ rc).mean())
    rows = []
    for c in ids:
        inside = int((lab[idx] == c).sum()); nc = int((lab == c).sum())
        rows.append((float(cv @ cen[c]), c, inside, inside / len(idx), inside / nc))
    rows.sort(reverse=True)
    byshare = sorted(rows, key=lambda r: -r[3])[:3]
    out[t] = {"n": len(idx), "compact": comp, "rand_compact": rcomp,
              "by_cos": [dict(cluster=r[1], cos=r[0], inside=r[2], share_of_v1=r[3], share_of_dim=r[4]) for r in rows[:4]],
              "by_share": [dict(cluster=r[1], cos=r[0], inside=r[2], share_of_v1=r[3], share_of_dim=r[4]) for r in byshare]}
    print(f"{t:34s} {len(idx):4d} {comp:7.2f} {rcomp:5.2f}  " + "; ".join(f"d{r[1]} {r[0]:.2f}|{r[2]}/{len(idx)}|{100*r[4]:.0f}%" for r in rows[:3]) +
          "   [by share: " + "; ".join(f"d{r[1]} {r[2]}/{len(idx)}" for r in byshare) + "]")
json.dump(out, open(CACHE / f"ce9_fate_m{M}.json", "w"), indent=1, default=float)
