"""CE-9 step 8b: candidate-side view. For each recommended dimension (m=20 partition): nearest v1 topics (centred centroid cosine; overlap of the v1 matcher's docs
with the dimension), what the FINE partition (m=10) splits it into, what the COARSE partition (m=30) merges it with, and its Phase 3 corroboration
(overlap with Phase 3 orphan clusters and curated keyword pools). Read-only. Centred scale only."""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *
import scipy.sparse as sp

C = Corpus(); Xc, mu = centered_doc_vectors(C); N = len(C.doc_ids)
lab = np.load(CACHE / "ce9_level_m20.npy"); fine = np.load(CACHE / "ce9_level_m10.npy"); coarse = np.load(CACHE / "ce9_level_m30.npy")
ids = sorted(set(lab.tolist()))
X = sp.load_npz(CACHE / "tfidf_doc.npz").tocsr(); vocab = pickle.load(open(CACHE / "tfidf_vocab.pkl", "rb"))["vocab"]
members = json.load(open(CACHE / "prior_members.json"))
cen_v1 = {t: unit(Xc[[C.doc_index[d] for d in members[t]]].mean(axis=0)) for t in members if members[t]}
oc = json.load(open(CACHE / "orphan_clusters.json"))
kw = json.load(open(CACHE / "vocab_candidates.json"))
print("orphan_clusters keys:", list(oc.keys())[:8], "| vocab_candidates keys:", list(kw.keys()))
def topterms(idx, k=8):
    tm = np.asarray(X[idx].mean(axis=0)).ravel(); return ", ".join(vocab[j] for j in np.argsort(-tm)[:k])
out = {}
for c in ids:
    idx = np.where(lab == c)[0]; cen = unit(Xc[idx].mean(axis=0)); n = len(idx)
    v1 = sorted(((float(cen @ v), t, len(set(C.doc_ids[i] for i in idx) & set(members[t])), len(members[t])) for t, v in cen_v1.items()), reverse=True)[:4]
    fsub = Counter(fine[idx].tolist()); parts = []
    for f, k in fsub.most_common():
        if k < 5: continue
        fi = np.where(fine == f)[0]; parts.append(dict(fine=int(f), docs_here=int(k), fine_size=int(len(fi)), terms=topterms(fi, 6)))
    csub = Counter(coarse[idx].tolist()); cparts = [dict(coarse=int(f), docs_here=int(k), coarse_size=int((coarse == f).sum())) for f, k in csub.most_common(3)]
    fmt = Counter(fmt_of(C.doc_ids[i]) for i in idx); th = Counter(C.doc_ids[i][1] for i in idx)
    out[int(c)] = dict(n=n, formats=dict(fmt), themes=dict(th), v1=[dict(t=t, cos=s, overlap=o, v1_n=m) for s, t, o, m in v1], fine_parts=parts, coarse_parts=cparts, terms=topterms(idx, 10))
    print(f"\n### d{c} n={n} fmt {dict(fmt)} themes {dict(th.most_common(3))}\n  terms: {out[int(c)]['terms']}")
    print("  v1   :", "; ".join(f"{t} {s:.2f} ({o}/{m})" for s, t, o, m in v1[:3]))
    print("  fine :", " | ".join(f"f{p['fine']}[{p['docs_here']}/{p['fine_size']}] {p['terms']}" for p in parts[:6]))
    print("  coarse:", cparts)
json.dump(out, open(CACHE / "ce9_candidate_side.json", "w"), indent=1, default=float)
