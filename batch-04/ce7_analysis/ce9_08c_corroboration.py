"""CE-9 step 8c: independent corroboration. Where do Phase 3's 23 viable candidates (orphan clusters P0/P2, curated-keyword pools) land in the recommended partition?
For each candidate: how its documents distribute over the dimensions. For each dimension: which Phase 3 candidates corroborate it (candidate docs inside it / dimension docs).
Read-only. Writes cache/ce9_corroboration.json."""
import json, sys, warnings, ast, re
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

C = Corpus(); lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist()))
doc_i = C.doc_index
S = json.load(open(CACHE / "separation.json")); O = json.load(open(CACHE / "orphan_clusters.json"))["detail"]
kwd = json.load(open(CACHE / "vocab_candidates.json"))["keywords_all_ge5"]
def docs_of(cid):
    m = re.match(r"orphan (P\d) k=(\d+) · c(\d+)", cid)
    if m:
        pop, k, lbl = m.group(1), int(m.group(2)), int(m.group(3))
        for key, v in O.items():
            if key.startswith(pop) and v["k"] == k:
                for c in v["clusters"]:
                    if c["label"] == lbl: return [d for d in (c["docs"] if isinstance(c["docs"], list) else ast.literal_eval(c["docs"]))]
        raise KeyError(cid)
    m = re.match(r"kw · (.+)", cid)
    return [C.doc_ids[i] if isinstance(i, int) else i for i in kwd[m.group(1)]]
res = {}; by_dim = defaultdict(list)
for cid in S["viable"]:
    ds = docs_of(cid); idx = [doc_i[d] for d in ds if d in doc_i]; cnt = Counter(lab[idx].tolist()); n = len(idx)
    top = [(int(c), k, k / n, k / int((lab == c).sum())) for c, k in cnt.most_common(3)]
    res[cid] = {"n": n, "landing": [dict(dim=c, docs=k, share_of_candidate=a, share_of_dim=b) for c, k, a, b in top]}
    for c, k, a, b in top:
        if a >= 0.25 or b >= 0.25: by_dim[c].append((cid, k, a, b))
    print(f"{cid:34s} n={n:3d} -> " + "; ".join(f"d{c}: {k} docs ({100*a:.0f}% of candidate, {100*b:.0f}% of dim)" for c, k, a, b in top))
json.dump({"candidates": res, "by_dimension": {str(c): [dict(candidate=x[0], docs=x[1], share_of_candidate=x[2], share_of_dim=x[3]) for x in v] for c, v in by_dim.items()}}, open(CACHE / "ce9_corroboration.json", "w"), indent=1)
print("\nby dimension (candidate docs inside >= 25% of the candidate or >= 25% of the dimension):")
for c in ids: print(f"  d{c:2d}: " + ("; ".join(f"{x[0]} [{x[1]} docs; {100*x[2]:.0f}%/{100*x[3]:.0f}%]" for x in by_dim.get(c, [])) or "-"))
