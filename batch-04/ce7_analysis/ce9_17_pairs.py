"""CE-9 step 17: fast separability iteration on DEPLOYED centroids. Reads a matchers JSON, optionally applies overrides given on the command line, and prints per-dimension caught / P@3 and every pair of
dimensions whose centred centroid cosine is >= 0.55 (with the overlap of their caught documents). Read-only. Centred scale only.
Usage: ce9_17_pairs.py <matchers_json> [--set "<key>: term | term"  or  "<key>=term | term" (use = for keys containing a colon)]... [--del <key>]... [--pairs a,b a,b]   (keys are cluster numbers or 'x:name')"""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from ce9_09_deploy import *          # loads Corpus/Index/centred vectors; the analysis itself is under __main__ there

args = sys.argv[1:]; M = json.load(open(args[0])); i = 1; want_pairs = []
while i < len(args):
    if args[i] == "--set": k, v = args[i + 1].split("=", 1) if "=" in args[i + 1].split("|")[0] else args[i + 1].split(":", 1); M[k.strip()] = {"keywords": [t.strip() for t in v.split("|") if t.strip()], "entities": []}; i += 2
    elif args[i] == "--del": M.pop(args[i + 1], None); i += 2
    elif args[i] == "--pairs": want_pairs = [tuple(p.split(",")) for p in args[i + 1:]]; break
    else: i += 1
keys = sorted(M, key=lambda c: (not c.isdigit(), int(c) if c.isdigit() else 0)); K = len(keys); col = {k: j for j, k in enumerate(keys)}
H = np.zeros((N, K), dtype=bool)
for j, k in enumerate(keys): H[:, j] = ix.engine_hits(list(M[k]["keywords"]) + list(M[k].get("entities", [])))
prec, rank = neighbourhood_precision(H)
BC, DM, CEN = affinity(H, loo=False); G = CEN @ CEN.T; np.fill_diagonal(G, -2)
print(f"K={K}  median P@3 {np.nanmedian([p[3] for p in prec]):.2f}  (median caught {int(np.median(H.sum(0)))})")
for j, k in enumerate(keys): print(f"  {k:>16s} caught={int(H[:, j].sum()):3d} P@3={prec[j][3]:.2f} maxcos={G[j].max():.2f} with {keys[int(G[j].argmax())]}")
print("pairs >= 0.55 (centred cosine of deployed centroids | caught overlap | Jaccard):")
seen = set()
for a in range(K):
    for b in range(a + 1, K):
        if G[a, b] >= 0.55 or (keys[a], keys[b]) in want_pairs:
            ov = int((H[:, a] & H[:, b]).sum()); jc = ov / max(1, int((H[:, a] | H[:, b]).sum()))
            print(f"   {keys[a]:>16s} - {keys[b]:<16s} {G[a, b]:.3f} | {ov:3d} | {jc:.2f}")
json.dump(M, open(CACHE / "ce9_pairs_last_matchers.json", "w"), indent=1)
