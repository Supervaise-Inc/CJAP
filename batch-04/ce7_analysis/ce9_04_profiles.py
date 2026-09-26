"""CE-9 step 4: full profiles of the recommended-level clusters (for naming, definitions, tiers, theme anchors). Read-only.
Usage: ce9_04_profiles.py <m> [start end]"""
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
X = sp.load_npz(CACHE / "tfidf_doc.npz").tocsr(); vocab = pickle.load(open(CACHE / "tfidf_vocab.pkl", "rb"))["vocab"]
m = int(sys.argv[1]); lab = np.load(CACHE / f"ce9_level_m{m}.npy"); ids = sorted(set(lab.tolist()), key=lambda c: -(lab == c).sum())
lo, hi = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, len(ids))
kwd = json.load(open(CACHE / "vocab_candidates.json"))["keywords_all_ge5"]
kw_docs = {k: set(v) for k, v in kwd.items()}
members = json.load(open(CACHE / "prior_members.json"))
cen = {c: unit(Xc[lab == c].mean(axis=0)) for c in ids}
P = prior_art()
ent = defaultdict(Counter)
for c in ids:
    for i in np.where(lab == c)[0]:
        e = C.docs[C.doc_ids[i]].get("entities") or {}
        for k in ("people", "institutions", "cases", "laws_treaties", "events"):
            for it in e.get(k, []) or []:
                if isinstance(it, str): ent[c][re.sub(r"\s*\([^)]*\)", "", it).strip()] += 1
for c in ids[lo:hi]:
    idx = np.where(lab == c)[0]; ds = [C.doc_ids[i] for i in idx]; fc = Counter(fmt_of(d) for d in ds); th = Counter(d[1] for d in ds)
    tm = np.asarray(X[idx].mean(axis=0)).ravel(); terms = ", ".join(vocab[j] for j in np.argsort(-tm)[:14])
    lifted = sorted(((len(kw_docs[k] & set(idx.tolist())) / len(idx)) / (len(kw_docs[k]) / N), k, len(kw_docs[k] & set(idx.tolist()))) for k in kw_docs if len(kw_docs[k] & set(idx.tolist())) >= 3)
    lifted = sorted(lifted, reverse=True)[:8]
    cen_v1 = {t: unit(Xc[[C.doc_index[d] for d in members[t]]].mean(axis=0)) for t in members if members[t]}
    v1 = sorted(((float(cen[c] @ v), t, len(set(ds) & set(members[t])), len(members[t])) for t, v in cen_v1.items()), reverse=True)[:3]
    print(f"\n### cluster {c}  n={len(ds)}  formats col/book/spe/bio = {fc['columns']}/{fc['books']}/{fc['speeches']}/{fc['biography']}  themes {dict(th.most_common(4))}")
    print("  terms   :", terms)
    print("  keywords:", "; ".join(f"{k}({n},x{l:.0f})" for l, k, n in lifted))
    print("  entities:", "; ".join(f"{e}({n})" for e, n in ent[c].most_common(7)))
    ex = [ds[i] for i in np.argsort(-(Xc[idx] @ cen[c]))[:5]]
    print("  exemplars:", " | ".join(f"{d} {C.title[d][:46]}" for d in ex))
    print("  nearest v1:", "; ".join(f"{t} (cos {s:.2f}, {o}/{n} of its matcher docs here)" for s, t, o, n in v1))
    works = Counter(C.work[d] for d in ds if d[0] == "B")
    if works: print("  books:", "; ".join(f"{w} x{n}" for w, n in works.most_common(4)))
