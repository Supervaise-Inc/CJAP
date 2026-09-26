"""CE-9 probe: evaluate hand-proposed terms for one or more dimensions with the real engine.
Usage: ce9_15_probe.py "<cluster>: term | term | term" "<cluster>: term | term" ...   (one argument per dimension)"""
import sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *
C = Corpus(); ix = Index(C); N = ix.N; Xc, mu = centered_doc_vectors(C); fmt = C.doc_fmt
lab = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab.tolist()))
S, rank = rank_matrix(Xc, lab, ids, np.ones(N, dtype=bool))
for arg in sys.argv[1:]:
    head, tail = arg.split(":", 1); c = int(head); j = ids.index(c); seeds = lab == c; n = int(seeds.sum())
    terms = [t.strip() for t in tail.split("|") if t.strip()]
    print(f"### d{c} n={n}")
    allh = np.zeros(N, dtype=bool)
    for t in terms:
        h = ix.engine_hits([t]); df = int(h.sum()); inn = int((h & seeds).sum()); allh |= h
        print(f"  {t:36s} df={df:3d} in={inn:3d} share={inn/max(1,df):.2f} P3={float((rank[h, j] <= 3).mean()) if df else float('nan'):.2f}")
    ca = int(allh.sum()); print(f"  UNION caught={ca} ratio={ca/n:.2f} recall={(allh & seeds).sum()/n:.2f} in-dim={(allh & seeds).sum()/max(1,ca):.2f} P3={float((rank[allh, j] <= 3).mean()) if ca else float('nan'):.2f}")
