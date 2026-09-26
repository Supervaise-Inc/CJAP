"""CE-9 step 8d: which curated-keyword pools name each recommended dimension? (the granularity rule's 'Derived' test accepts a Phase 3 cluster OR a curated-keyword pool).
A pool = a `keywords` value carried by >= 5 documents (Phase 3's own vocabulary, cache/vocab_candidates.json:keywords_all_ge5). It NAMES a dimension when >= 5 of its documents
are inside the dimension and >= 50% of the pool's documents are inside it. Read-only. Writes cache/ce9_pools.json."""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

C = Corpus(); N = len(C.doc_ids)
lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist()))
kwd = json.load(open(CACHE / "vocab_candidates.json"))["keywords_all_ge5"]
def as_idx(v): return [C.doc_index[d] if isinstance(d, str) else int(d) for d in v]
out = {}
for c in ids:
    n = int((lab == c).sum()); rows = []
    for k, v in kwd.items():
        idx = as_idx(v); inn = int((lab[idx] == c).sum())
        if inn >= 5 and inn / len(idx) >= 0.5: rows.append((inn, inn / len(idx), k, len(idx)))
    rows.sort(reverse=True)
    out[str(c)] = [dict(pool=k, pool_docs=m, inside=i, share=s) for i, s, k, m in rows[:6]]
    print(f"d{c:2d} n={n:3d}: " + ("; ".join(f"“{k}” {i}/{m}" for i, s, k, m in rows[:4]) or "— (no pool passes)"))
json.dump(out, open(CACHE / "ce9_pools.json", "w"), indent=1)
