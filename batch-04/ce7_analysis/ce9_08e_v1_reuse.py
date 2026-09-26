"""CE-9 step 8e: could each v1 matcher be REUSED unchanged as the matcher of its successor dimension? Same acceptance test as the new matchers:
caught <= 2x the dimension's documents AND >= 60% of the caught documents have the dimension among their 3 nearest (leave-one-out).
For every v1 topic and every dimension (not only the best): reports the pair with the highest 'P@3 of caught docs' among dimensions with centred cosine >= 0.5. Read-only.
Writes cache/ce9_v1_reuse.json."""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

C = Corpus(); N = len(C.doc_ids); Xc, mu = centered_doc_vectors(C)
lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist()))
S, rank = rank_matrix(Xc, lab, ids, np.ones(N, dtype=bool))
members = json.load(open(CACHE / "prior_members.json"))
cen = {c: unit(Xc[lab == c].mean(axis=0)) for c in ids}
out = {}
print(f"{'v1 topic':46s} {'n':>4s} -> {'dim':>4s} {'cos':>5s} {'dim n':>5s} {'ratio':>5s} {'P@3':>5s} {'inside':>6s} reusable?")
for t in sorted(members):
    ms = members[t]
    if not ms: continue
    idx = np.array([C.doc_index[d] for d in ms]); cv = unit(Xc[idx].mean(axis=0))
    best = None
    for j, c in enumerate(ids):
        cs = float(cv @ cen[c])
        if cs < 0.5: continue
        n = int((lab == c).sum()); p3 = float((rank[idx, j] <= 3).mean()); ins = int((lab[idx] == c).sum())
        row = dict(dim=int(c), cos=cs, dim_n=n, caught=len(idx), ratio=len(idx) / n, P3=p3, inside=ins, reusable=bool(len(idx) <= 2 * n and p3 >= 0.60))
        if best is None or cs > best["cos"]: best = row
    if best is None: print(f"{t:46s} {len(idx):4d} -> (no dimension with centred cosine >= 0.5)"); continue
    out[t] = best
    print(f"{t:46s} {len(idx):4d} -> d{best['dim']:<3d} {best['cos']:5.2f} {best['dim_n']:5d} {best['ratio']:5.2f} {best['P3']:5.2f} {best['inside']:6d} {'YES' if best['reusable'] else 'no'}")
json.dump(out, open(CACHE / "ce9_v1_reuse.json", "w"), indent=1)
