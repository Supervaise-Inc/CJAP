"""CE-9 step 13: freeze the matcher lists. Starts from the greedy readable matchers (cache/ce9_readable_m20.json), applies the explicit, printed edits below
(every edit is listed here so a reviewer can see exactly what was changed by hand and why), re-evaluates with the REAL v1 engine, splits terms into the
taxonomy's two buckets (`entities` = a term that is a name in some document's entity list; `keywords` = everything else), and writes cache/ce9_matchers_final.json.
Read-only on the repo."""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

# --- explicit hand edits: {cluster: [terms]} -------------------------------------------------------------------------------------------------------------
DROP = {}     # terms removed from the greedy result (with the reason as a comment)
ADD = {}      # terms added by hand, unconditionally
TRY_ADD = {}  # defining vocabulary tried in order; admitted only while the union stays acceptable (see ce9_edits.py)
EXTRA = {}    # extra candidate dimensions evaluated alongside the 33 (key "x:<name>")
exec(open(Path(__file__).parent / "ce9_edits.py", encoding="utf-8").read()) if (Path(__file__).parent / "ce9_edits.py").exists() else None

C = Corpus(); ix = Index(C); N = ix.N; Xc, mu = centered_doc_vectors(C); fmt = C.doc_fmt
lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist()))
S, rank = rank_matrix(Xc, lab, ids, np.ones(N, dtype=bool))
R = json.load(open(CACHE / "ce9_readable_m20.json"))
out = {}
print(f"{'cl':>3s} {'n':>4s} {'terms':>5s} {'caught':>6s} {'ratio':>5s} {'recall':>6s} {'in-dim':>6s} {'P@3':>5s} ok  recall by format col/book/spe/bio")
for j, c in enumerate(ids):
    terms = [t for t in R[str(c)]["terms"] if t not in DROP.get(c, [])] + [t for t in ADD.get(c, []) if t not in R[str(c)]["terms"]]
    seeds0 = lab == c; n0 = int(seeds0.sum())
    cur = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool)
    for t in TRY_ADD.get(c, []):
        if t in terms: continue
        h = ix.engine_hits([t]); u = cur | h
        if int((h & seeds0 & ~cur).sum()) < 2 or int(u.sum()) > 1.9 * n0 or float((rank[u, j] <= 3).mean()) < 0.65: continue
        terms.append(t); cur = u
    terms = prune_subsumed(terms)
    ent = [t for t in terms if t in ix.entity_terms]; kw = [t for t in terms if t not in ix.entity_terms]
    hit = ix.engine_hits(terms) if terms else np.zeros(N, dtype=bool); seeds = lab == c; n = int(seeds.sum()); ca = int(hit.sum())
    p3 = float((rank[hit, j] <= 3).mean()) if ca else float("nan")
    byf = {f: (float((hit & seeds & (fmt == f)).sum() / (seeds & (fmt == f)).sum()) if (seeds & (fmt == f)).sum() else None) for f in FMT_ORDER}
    ok = bool(ca and ca <= 2 * n and p3 >= 0.60)
    out[str(c)] = {"keywords": kw, "entities": ent}
    print(f"{c:3d} {n:4d} {len(terms):5d} {ca:6d} {ca/n:5.2f} {(hit & seeds).sum()/n:6.2f} {(hit & seeds).sum()/max(1,ca):6.2f} {p3:5.2f} {'Y' if ok else 'n'}   " + "/".join("-" if v is None else f"{v:.2f}" for v in byf.values()) + "\n      " + ", ".join(terms))
for k, v in EXTRA.items():
    out[k] = {"keywords": [t for t in v if t not in ix.entity_terms], "entities": [t for t in v if t in ix.entity_terms]}
    print(k, int(ix.engine_hits(v).sum()), "docs", v)
json.dump(out, open(CACHE / "ce9_matchers_final.json", "w"), indent=1)
