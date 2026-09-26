"""CE-9 step 19: FREEZE the recommended dimension set and its matchers.
Starts from ce9_13_finalize's output (greedy readable matchers - drops + admitted defining vocabulary, cache/ce9_matchers_final.json) and applies the separability-driven edits below,
each with the measurement that forced it (all measured with ce9_17_pairs.py on DEPLOYED centroids, centred scale):
  * d1  life story      : its first matcher used church/pope/priest vocabulary and pulled its centroid to 0.85 of the faith dimension (d23). Life-story-only terms bring it to 0.69.
  * d6  criminal law    : its first matcher (searches, arraignment, moral certainty...) put it at 0.77 of criminal trials (d2). Restricted to libel / cybercrime it is 0.43 of the nearest dimension.
  * x:death_penalty     : carried as its own dimension (the brief's verdict). Separable (0.43 of the nearest dimension) ONLY while d6's matcher does not carry its terms: with them in d6 the two are 0.96 apart.
  * d24 business leaders: 0.74 - 0.78 of the Foundation (d15) whatever its matcher: the same people (donors) -> merged into d15.
  * d7  presidential power: 'rebellion' lowered its neighbourhood precision below the acceptance bar; the seven-term set below is 0.67.
  * d26, d31, d32       : no readable term set catches >= 10 documents at acceptable precision (best: 6, 0, 4 documents) -> not proposed (matcher unfinished).
Writes cache/ce9_matchers_v2.json, cache/ce9_level_final.npy (the partition with d24 relabelled into d15), cache/ce9_freeze_report.json. Read-only on the repo."""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *

OVERRIDE = {
    "1": ["sampaloc", "yale law school", "far eastern university", "rotary club of manila", "eulogy", "mapa high school", "feu institute of law", "jovito r. salonga", "sylvia lina"],
    "6": ["libel", "cyberlibel", "cybercrime", "maria ressa"],
    "x:death_penalty": ["death penalty", "echegaray"],
    "7": ["coup", "marawi", "romulo neri", "maute group", "lagman vs medialdea", "constitutional authoritarianism", "edsa shrine"],
    "15": ["tan yan kee foundation", "dissertation writing", "flp scholars society", "museum for liberty and prosperity", "rvr", "george ty", "jollibee", "busog lusog", "philanthropist", "corporate social responsibility", "csr", "philanthropy"],
}
REMOVE = ["24", "26", "31", "32"]
C = Corpus(); ix = Index(C); N = ix.N; fmt = C.doc_fmt
lab = np.load(CACHE / "ce9_level_m20.npy"); labF = lab.copy(); labF[lab == 24] = 15; np.save(CACHE / "ce9_level_final.npy", labF)
M = json.load(open(CACHE / "ce9_matchers_final.json"))
for k, terms in OVERRIDE.items(): M[k] = {"keywords": terms, "entities": []}
for k in REMOVE: M.pop(k, None)
out = {}
ORDER = lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0)
for k in sorted(M, key=ORDER):
    terms = prune_subsumed(list(M[k]["keywords"]) + list(M[k].get("entities", [])))
    out[k] = {"keywords": [t for t in terms if t not in ix.entity_terms], "entities": [t for t in terms if t in ix.entity_terms]}
json.dump(out, open(CACHE / "ce9_matchers_v2.json", "w"), indent=1)
rep = {}
print(f"{len(out)} dimensions; cluster sizes from ce9_level_final.npy")
for k in sorted(out, key=ORDER):
    c = int(k) if k.isdigit() else None; seeds = (labF == c) if c is not None else np.zeros(N, dtype=bool); n = int(seeds.sum()); terms = out[k]["keywords"] + out[k]["entities"]; hit = ix.engine_hits(terms); ca = int(hit.sum())
    rep[k] = dict(n=n, caught=ca, ratio=(ca / n if n else None), in_dim=float((hit & seeds).sum() / max(1, ca)), recall=(float((hit & seeds).sum() / n) if n else None))
    print(f"  d{k:>2s} n={n:3d} caught={ca:3d} ({(ca/n if n else 0):.2f}x) in-cluster {(hit & seeds).sum()/max(1,ca):.2f} recall {((hit & seeds).sum()/n if n else 0):.2f}  {', '.join(terms)}")
json.dump(rep, open(CACHE / "ce9_freeze_report.json", "w"), indent=1)
