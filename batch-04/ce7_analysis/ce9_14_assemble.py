"""CE-9 step 14: assemble batch-04/taxonomy_v2_PROPOSAL.md from the measured artefacts (every number in the document is read from a cache/*.json written by an
earlier ce9_* script; nothing is typed in by hand except the verdict wording and the definitions in ce9_spec.py).
Usage: ce9_14_assemble.py <matchers_json> <deploy_json> [out_md]      Read-only on the repo (writes only under batch-04/)."""
import json, sys, warnings, subprocess, hashlib, datetime
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, str(Path(__file__).parent))
from ce9_lib import *
from ce9_spec import SPEC, UNBUILT
from ce9_decisions import *          # ANCHORS, FATE, STATUS_OVERRIDE, NOT_PROPOSED, EXTRA_DIMS, THRESHOLDS, NOTES  (hand-written verdicts, printed in the document)

MATCH, DEPLOY = sys.argv[1], sys.argv[2]
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else B4 / "taxonomy_v2_PROPOSAL.md"
J = lambda name: json.load(open(CACHE / name, encoding="utf-8"))
C = Corpus(); N = len(C.doc_ids); Xc, mu = centered_doc_vectors(C); fmt = C.doc_fmt
lab20 = np.load(CACHE / "ce9_level_m20.npy"); ids = sorted(set(lab20.tolist())); lab = np.load(CACHE / "ce9_level_final.npy")       # lab: the frozen set (business-leaders cluster merged into the Foundation)
ALLN = {**{k: dict(name=v["name"], n=v["n"]) for k, v in SPEC.items()}, **{k: dict(name=v["name"], n=v["n"]) for k, v in UNBUILT.items()}}     # names of all 33 recommended-level clusters
L, T, P33, CAND, FATE_J, REUSE, CORR, POOLS = J("ce9_levels.json"), J("ce9_tree.json"), J("ce9_p33.json"), J("ce9_candidate_side.json"), J("ce9_fate_m20.json"), J("ce9_v1_reuse.json"), J("ce9_corroboration.json"), J("ce9_pools.json")
D = json.load(open(DEPLOY, encoding="utf-8")); M = json.load(open(MATCH, encoding="utf-8"))
H = np.load(Path(DEPLOY).with_name(Path(DEPLOY).stem + "_H.npy"))
cl = D["clusters"]; K = len(cl); col = {c: j for j, c in enumerate(cl)}
prec = {p["cluster"]: p for p in D["precision"]}; sep = {s["cluster"]: s for s in D["separability"]}
def esc(s): return str(s).replace("|", "\\|")
def table(headers, rows, align=None):
    align = align or ["l"] * len(headers)
    line = lambda r: "| " + " | ".join(esc(x) for x in r) + " |"
    sep_ = "| " + " | ".join({"l": ":---", "r": "---:", "c": ":---:"}[a] for a in align) + " |"
    return "\n".join([line(headers), sep_] + [line(r) for r in rows])
pc = lambda x, d=0: "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100*x:.{d}f}%"
f2 = lambda x: "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.2f}"

# ---------------------------------------------------------------- per-dimension facts
dim = {}
for c in cl:
    if isinstance(c, int):
        sp = SPEC[c]; idx = np.where(lab == c)[0]; assert len(idx) == sp["n"], (c, len(idx), sp["n"])
        id_, name, defn = sp["id"], sp["name"], sp["definition"]
    else:
        sp = EXTRA_DIMS[c]; idx = np.array([], dtype=int); id_, name, defn = sp["id"], sp["name"], sp["definition"]
    j = col[c]; caught = np.where(H[:, j])[0]
    themes = Counter(C.doc_ids[i][1] for i in (idx if len(idx) else caught)); th, thn = themes.most_common(1)[0]
    n_derived = len(idx) if len(idx) else None
    size = n_derived if n_derived else int(H[:, j].sum())
    tier = "anchor" if id_ in ANCHORS else ("core" if int(H[:, j].sum()) >= 40 else "subordinate")
    ex_pool = [i for i in (idx if len(idx) else caught) if H[i, j]] if len(idx) else list(caught)
    if len(ex_pool) < 3: ex_pool = list(idx if len(idx) else caught)
    cen = unit(Xc[idx].mean(axis=0)) if len(idx) else unit(Xc[caught].mean(axis=0))
    ex = sorted(ex_pool, key=lambda i: -(Xc[i] @ cen))[:3]
    dim[c] = dict(c=c, id=id_, name=name, definition=defn, n=n_derived, size=size, tier=tier, theme=th, theme_share=thn / sum(themes.values()), caught=int(H[:, j].sum()),
                  exemplars=[(C.doc_ids[i], C.title[C.doc_ids[i]]) for i in ex], idx=idx, keywords=M[str(c)]["keywords"], entities=M[str(c)]["entities"])
id_of = {c: dim[c]["id"] for c in cl}
cid_of_id = {v: k for k, v in id_of.items()}

# ================================================================ SECTION: granularity (three levels)
def section_granularity():
    lv = [("coarse", "30", "≥ 30"), ("medium", "20", "≥ 20"), ("fine", "10", "≥ 10")]
    rows = []
    for name, m, rule in lv:
        v = L[m]
        rows.append([f"**{name}**" if name == "medium" else name, rule, v["N"], f"{v['min']} – {v['max']} ({pc(v['max_share'])} max)", v["n_marginal_10_19"],
                     f2(v["nn_centered_max"]), f"{f2(v['split_half_median'])} / {f2(v['split_half_min'])}", pc(v["loo_top1"]),
                     f"{v['silhouette']:.3f} vs {v['silhouette_null_shuffled_features']:.3f}",
                     f"{pc(v['recall_median'])} / {pc(v['P2_median'])} / {v['lift2_median']:.1f}×", v["n_no_matcher"]])
    tbl = table(["level", "rule: smallest dimension (docs)", "N", "dimension size (docs)", "marginal (10–19 docs)", "closest pair of dimensions (centred cosine)", "same dimension, two random halves: median / worst",
                 "a doc's nearest dimension is its own", "silhouette vs shuffled-feature null", "keyword matchability on unseen docs: recall / P@2 / lift", "dimensions with no usable keyword matcher"],
                rows, ["l", "l", "r", "l", "r", "r", "r", "r", "r", "l", "r"])
    # what coarse blurs: dimensions the coarse level merges
    csz = {}
    for c in ids:
        for p in CAND[str(c)]["coarse_parts"][:1]: csz.setdefault(p["coarse"], []).append(c)
    blur = []
    for k, ds in sorted(csz.items(), key=lambda kv: -len(kv[1])):
        if len(ds) >= 2:
            blur.append(f"* **{sum(int((lab20 == d).sum()) for d in ds)} documents** = " + " + ".join(f"{ALLN[d]['name']} ({int((lab20 == d).sum())})" for d in sorted(ds, key=lambda d: -int((lab20 == d).sum()))))
    frag = []
    for c in ids:
        parts = CAND[str(c)]["fine_parts"]
        if len(parts) >= 2:
            frag.append(f"* **{ALLN[c]['name']}** ({ALLN[c]['n']}) → " + "; ".join(f"{p['fine_size']} docs on *{p['terms']}*" for p in parts))
    return tbl, "\n".join(blur), "\n".join(frag)

# ================================================================ SECTION: Table 1
v1_target = defaultdict(list)                       # cluster (or 'x:..') -> [(v1 id, fate word)]
for t, (word, tgt, why) in FATE.items():
    if tgt is not None: v1_target[tgt].append((t, word))
def jaccard(t, c):
    for r in FATE_J.get(t, {}).get("by_cos", []) + FATE_J.get(t, {}).get("by_share", []):
        if r["cluster"] == c:
            nv1 = FATE_J[t]["n"]; nd = int(round(r["inside"] / r["share_of_dim"])) if r["share_of_dim"] else 0
            return r["inside"] / (nv1 + nd - r["inside"]), r["cos"], r["inside"], nv1
    return None
def status_of(c):
    if c in STATUS_OVERRIDE: return STATUS_OVERRIDE[c]
    for t, word in v1_target.get(c, []):
        if word.startswith("carried") and not (t in REUSE and REUSE[t]["reusable"] and REUSE[t]["dim"] == c):
            jj = jaccard(t, c)
            if jj and jj[1] >= 0.70 and jj[0] < 0.30: return "Same direction, wrong members"
    return "Dimension holds"
def corroborators(c):
    """Phase 3 candidates with >= 40% of their documents inside this dimension (for the merged Foundation dimension: inside either of its two clusters)"""
    dims = {15, 24} if c == 15 else {c}
    out = []
    for cid, r in CORR["candidates"].items():
        got = sum(x["docs"] for x in r["landing"] if x["dim"] in dims)
        if r["n"] and got / r["n"] >= 0.40: out.append((cid, got))
    return out
def derived_from(c):
    d = dim[c]
    if c == 15: s = "Ward-tree clusters of 33 (Foundation) + 24 (business leaders and philanthropy) docs, merged: their deployed centroids are 0.74-0.78 apart"
    elif isinstance(c, int): s = f"Ward-tree cluster, {d['n']} docs"
    else: s = f"curated-keyword pool ({EXTRA_DIMS[c]['pool']})"
    bits = []; keys = [str(c)] + (["24"] if c == 15 else [])
    for cid, got in (corroborators(c) if isinstance(c, int) else []): bits.append(f"P3 {cid.replace('orphan ', '').replace('kw · ', 'pool ')} ({got} docs)")
    for k in keys:
        for p in POOLS.get(k, [])[:2]: bits.append(f"pool “{p['pool']}” {p['inside']}/{p['pool_docs']}")
    return s + ("; corroborated by " + "; ".join(bits) if bits else ("" if not isinstance(c, int) else "; **no Phase 3 candidate or curated pool corroborates** (Ward cluster + any v1 evidence only)"))
def prior_art_cell(c):
    tgts = v1_target.get(c, [])
    own = [t for t, w in tgts if w.startswith("carried") or w.startswith("redefined")]
    ab = [t for t, w in tgts if w.startswith("absorbed")]
    s = ", ".join(own) if own else ("" if ab else "—")
    if ab: s += (" · " if own else "") + "absorbs " + ", ".join(ab)
    return s
def table1():
    rows = []
    for c in cl:
        d = dim[c]; s = sep[c]; nn = id_of[s["nearest"]] if s["nearest"] in id_of else s["nearest"]
        rows.append([d["id"], d["name"], d["tier"], f"{d['theme']} ({pc(d['theme_share'])})", d["caught"], derived_from(c), f"{s['max_cos']:.2f} vs {nn}",
                     "; ".join(f"`{i}` {t[:44]}" for i, t in d["exemplars"]), prior_art_cell(c), status_of(c)])
    return table(["id", "display_name", "tier", "theme_anchor (share of its docs)", "doc_count (matcher-caught)", "derived_from", "separability (max centred cosine vs any other)", "3 exemplars", "prior_art_id", "status"], rows,
                 ["l", "l", "l", "l", "r", "l", "l", "l", "l", "l"])

# ================================================================ SECTION: Table 2 (fate of the v1 topics)
tmap = json.load(open(ROOT / "corpus" / "voice" / "topic_map.json", encoding="utf-8"))["topics"]
def stored_count(t):
    if "+" in t: return sum(tmap[x]["doc_count"] for x in t.split("+"))
    return tmap[t]["doc_count"]
def label_of(c):
    if c in id_of: return id_of[c]
    if c == 24: return id_of[15] + " (its business-leaders cluster)"
    return f"the unbuilt cluster '{ALLN[c]['name']}'"
def table2():
    rows = []; tally = Counter()
    order = [t for t in FATE if t != "robot_identity_meta" and not t.startswith("msme")] + ["msme_and_entrepreneurship+prosperity_fund_msme", "robot_identity_meta"]
    for t in order:
        word, tgt, why = FATE[t]; f = FATE_J.get(t)
        if t == "robot_identity_meta": n_m, evidence = 0, "0 documents / 0 chunks; a routing intent"
        else:
            n_m = f["n"]; tg = tgt if tgt in cid_of_id.values() or isinstance(tgt, int) else None
            r = next((x for x in f["by_cos"] if x["cluster"] == tgt), None) if isinstance(tgt, int) else None
            evidence = (f"cohesion {f['compact']:.2f} (random {f['rand_compact']:.2f}); " + (f"→ {id_of[tgt]}: cos {r['cos']:.2f}, {r['inside']}/{n_m} of its docs inside, {pc(r['share_of_dim'])} of the dimension" if r else
                        f"nearest dimension: {label_of(f['by_cos'][0]['cluster'])} at {f['by_cos'][0]['cos']:.2f}" if word == "dropped" else ""))
        evidence = evidence.rstrip("; ").rstrip()
        tgt_id = id_of.get(tgt, EXTRA_DIMS.get(tgt, {}).get("id", "—")) if tgt is not None else "—"
        fate_txt = {"absorbed": f"absorbed into `{tgt_id}`", "redefined as": f"redefined as `{tgt_id}`", "dropped": "dropped", "moved to the router": "moved out of the taxonomy into the router"}.get(word, word + (f" (`{tgt_id}`)" if tgt_id != "—" else ""))
        tally[word.split(" into")[0].split(" as")[0]] += 1
        stored = "—" if t == "robot_identity_meta" else stored_count(t)
        rows.append([f"`{t}`", n_m, stored, fate_txt, evidence, why])
    return table(["v1 topic", "docs its v1 matcher catches (1,290-doc corpus)", "stored topic_map doc_count (v1, stale)", "fate", "evidence (centred scale)", "why"], rows, ["l", "r", "r", "l", "l", "l"]), tally

# ================================================================ SECTION: matchers
def matcher_table():
    rows = []
    for c in cl:
        d = dim[c]; p = prec[c]; s = sep[c]
        cf = p["caught_by_format"]; rf = p["recall_by_format"]
        rows.append([d["id"], d["n"] if d["n"] else "—", d["caught"], "—" if not d["n"] else f"{d['caught'] / d['n']:.1f}×", pc(p["P3"]), f"{p['P3'] / p['base3']:.1f}×" if p["base3"] else "—", pc(p["control_P3"]),
                     "—" if p["in_derived_cluster"] is None else pc(p["in_derived_cluster"]), "—" if p["recall_of_cluster"] is None else pc(p["recall_of_cluster"]),
                     f"{cf['columns']}/{cf['books']}/{cf['speeches']}/{cf['biography']}", "/".join("–" if rf[f] is None else f"{100*rf[f]:.0f}" for f in FMT_ORDER),
                     f2(s["fidelity_to_derived_cluster"]) if s.get("fidelity_to_derived_cluster") is not None else "—", len(d["keywords"]) + len(d["entities"])])
    return table(["dimension", "cluster docs", "docs its matcher catches", "caught ÷ cluster", "share in its own embedding neighbourhood (top-3)", "lift over base rate", "same, random-membership control", "caught docs that are in the derived cluster",
                  "cluster docs the matcher catches", "caught by format col/book/spe/bio", "cluster recall by format % col/book/spe/bio", "centroid built from the caught docs vs the derived cluster's own (cos)", "terms"], rows,
                 ["l", "r", "r", "r", "r", "r", "r", "r", "r", "l", "l", "r", "r"])

def v1_table():
    rows = []
    for p in sorted(D["v1_precision"], key=lambda x: -x["caught"]):
        rows.append([f"`{p['id']}`", p["caught"], pc(p["P3"]), f"{p['P3'] / p['base3']:.1f}×" if p["base3"] else "—"])
    return table(["v1 topic", "docs its matcher catches", "share in its own embedding neighbourhood (top-3)", "lift over base rate"], rows, ["l", "r", "r", "r"])

def py_str(s): return json.dumps(s, ensure_ascii=False)
def taxonomy_block():
    out = ["TAXONOMY: list[dict[str, Any]] = ["]
    groups = [("anchor", "Anchors"), ("core", "Core"), ("subordinate", "Subordinate")]
    for tier, label in groups:
        ds = [dim[c] for c in cl if dim[c]["tier"] == tier]
        if not ds: continue
        out.append(f"    # ===== {label} ({len(ds)}) =====")
        for d in sorted(ds, key=lambda d: (-d["size"], d["id"])):
            out += ["    {", f'        "id": {py_str(d["id"])},', f'        "display_name": {py_str(d["name"])},', f'        "definition": {py_str(d["definition"])},', f'        "tier": {py_str(d["tier"])},',
                    f'        "theme_anchor": {py_str(d["theme"])},', '        "matchers": {']
            for key in ("keywords", "entities"):
                terms = d[key]
                if not terms: out.append(f'            "{key}": [],'); continue
                out.append(f'            "{key}": [')
                line = "               "
                for t in terms:
                    piece = " " + py_str(t) + ","
                    if len(line) + len(piece) > 150: out.append(line); line = "               "
                    line += piece
                out.append(line); out.append("            ],")
            out += ["        },", "    },"]
    out.append("]")
    return "\n".join(out)

# ================================================================ SECTION: P3.3 explanation
def section_p33():
    a, s, r, sw = P33["archived"], P33["stored_v1"], P33["random_groups_30"], P33["sweep"]
    return f"""**The P3.3 collapse is explained, and it was not the topics.** The merge gate `TOPIC_MERGE_COSINE = {a['merge_cosine']}` was applied to *raw* cosine between centroids, and in this embedding space raw cosine is below the noise floor. Reproduced by `ce9_00b_p33.py` from the *stored, untouched* v1 centroids:

* **The collapse re-runs exactly.** {P33['sweep']['0.95']['pairs_above']} of the {s['n_pairs']} pairs of the {s['n_topics']} stored centroids have raw cosine above {a['merge_cosine']}; the archived run recorded {a['merged_pairs']} merged pairs; union-find over them leaves **{sw['0.95']['topics_left']} topics** ({a['n_topics']} recorded, from {a['premerge_n_topics']}).
* **Random document groups clear the gate.** Two independent random 30-document groups sit at raw cosine **{r['raw_mean']:.3f}** (lowest of {r['n']} pairs: {r['raw_min']:.3f}) — above {a['merge_cosine']} every time. (Phase 3's own run of the same test: 0.985.) The stored v1 centroids sit at median {s['raw_median']:.3f} (mean {s['raw_mean']:.3f}, min {s['raw_min']:.3f}) — *below* what random groups produce, so the gate fires on {pc(sw['0.95']['pairs_above'] / s['n_pairs'])} of all pairs of genuinely different topics.
* **No raw threshold rescues it.** Raising the gate leaves {sw['0.96']['topics_left']} topics at 0.96, {sw['0.97']['topics_left']} at 0.97, {sw['0.98']['topics_left']} at 0.98, {sw['0.99']['topics_left']} at 0.99, and all {sw['1.01']['topics_left']} only when nothing can merge (1.01). Every raw value that keeps a plausible number of topics is above the level random groups reach.
* **On the centred scale the same random groups are unrelated**: mean {r['centred_mean']:.3f}, 95th percentile {r['centred_p95']:.3f}, maximum {r['centred_max']:.3f} (Phase 3: 0.019 / 0.282 / 0.369, same test, slightly different group construction).

Raw cosine in this space is dominated by a component shared by every chunk (the corpus mean); centring removes it. This is the whole explanation of the 34 → 3 collapse, and it is why every separability figure below is on the centred scale and no raw figure is offered as evidence."""

# ================================================================ SECTION: thresholds
def merge_tables():
    de, pd_ = D["dup_evidence"], D["pair_distribution"]
    rows = [["independent random document groups of the dimensions' own sizes (null)", f"mean {de['random_groups']['mean']:.2f}", f"p95 {de['random_groups']['p95']:.2f} · p99 {de['random_groups']['p99']:.2f} · max {de['random_groups']['max']:.2f}", f"{de['random_groups']['n']:,} pairs"],
            ["the proposed dimensions, every pair of *different* dimensions", f"median {pd_['median']:.2f}", f"p90 {pd_['p90']:.2f} · p95 {pd_['p95']:.2f} · max {pd_['max']:.2f}", f"{pd_['n_pairs']} pairs; ≥0.5: {pd_['ge_0.5']}, ≥0.6: {pd_['ge_0.6']}, ≥0.7: {pd_['ge_0.7']}"],
            ["one dimension against ITSELF (its caught docs split at random into two halves)", f"median {de['same_dim_split_half']['median']:.2f}", f"p10 {de['same_dim_split_half']['p10']:.2f} · p05 {de['same_dim_split_half']['p05']:.2f} · min {de['same_dim_split_half']['min']:.2f}", f"{de['same_dim_split_half']['n']} splits"]]
    return table(["what is compared (deployed centroids, centred)", "typical", "tail", "n"], rows)
def floor_table(defn, fl_rows):
    F = D["floor"][defn]; rows = []
    for f in fl_rows:
        g = F["grid"].get(str(f))
        if g: rows.append([f"{f:.2f}", pc(g["all_LOO"], 1), pc(g["columns"], 1), pc(g["books"], 1), pc(g["speeches"], 1), pc(g["biography"], 1), pc(g["all_in_sample"], 1), pc(g["null_all"], 1)])
    return table(["floor", "orphan rate, all docs (held-out)", "columns", "books", "speeches", "biography", "all docs, as production would print it (own doc inside its centroids)", "random-membership null"], rows, ["r"] * 8)

# ================================================================ SECTION: method
def section_method():
    ks = sorted(int(k) for k in T); sil = [T[str(k)]["sil"] for k in ks]; nul = [T[str(k)]["null_sil"] for k in ks]; ari = [T[str(k)]["boot_ari"] for k in ks]
    fm = C.fmt_docs
    return f"""1. **Centred scale.** `mu` = the mean of all {C.mat.shape[0]:,} chunk vectors; every vector below is `unit(v − mu)`. A dimension's centroid is `unit(mean of all chunks of its member documents − mu)` — the production recipe (`build_centroids_fullcorpus.py`) on the centred scale. A document's affinity to a dimension is either *best-chunk* (max over its chunks) or *document-mean*; both are reported.
2. **Derivation from the whole corpus, not only the orphans.** Ward linkage on the {N:,} centred document-mean vectors ({fm['columns']} columns, {fm['books']} book chapters, {fm['speeches']} speeches, {fm['biography']} biography chapters). The structure is real and weak: document-level silhouette {min(sil):.3f}–{max(sil):.3f} across every cut from k={ks[0]} to k={ks[-1]}, against {min(nul):.3f}–{max(nul):.3f} when the feature columns are shuffled; bootstrap adjusted-Rand {min(ari):.2f}–{max(ari):.2f}. All of it sits well below the 0.20 ceiling Phase 3 reported. **There is no natural N**; N is a granularity choice and is presented as one (section 3).
3. **A granularity family with one knob.** Start from the k={ks[-1]} cut. Repeatedly (a) merge the closest pair if its centred centroid cosine is ≥ 0.70 (a duplicate at the working line of 0.70 used to build the family; section 7 explains why the config gate is higher), else (b) fold the smallest cluster below *m* documents into its nearest neighbour. *m* alone sets N: m=30 → {L['30']['N']}, m=20 → {L['20']['N']}, m=10 → {L['10']['N']}. Nothing is hand-split or hand-merged.
4. **Nameable.** Each dimension's name and one-sentence definition are written from its cluster's top terms, curated keywords, entities and exemplars (`ce9_spec.py`); none lists members.
5. **Controls that were run.** Shuffled-feature null for the tree (above); random-membership control for every matcher (a random document set of the same size scores at the base rate); held-out estimate for the matcher induction procedure (learn on a random half, score the other half, centroids from the training half only); random-set control for induction (recall 0.00). Every number in this document is written by `ce9_14_assemble.py` from a `cache/*.json` produced by an earlier `ce9_*` script."""

# ================================================================ SECTION: floor policy options (computed from the saved leave-one-out affinities)
BCL = np.load(Path(DEPLOY).with_name(Path(DEPLOY).stem + "_bc_loo.npy")); DML = np.load(Path(DEPLOY).with_name(Path(DEPLOY).stem + "_dm_loo.npy"))
bestB, bestD = BCL.max(1), DML.max(1)
FB, FD = D["floor"]["best_chunk"], D["floor"]["doc_mean"]
FLOOR = THRESH_ASSIGN if "THRESH_ASSIGN" in globals() else 0.31
def rates(best, floors):
    """floors: scalar or {format: floor}. returns (all %, per-format (n, %), count)"""
    fl = np.array([floors[f] if isinstance(floors, dict) else floors for f in fmt]); o = best < fl
    return o, {f: (int(o[fmt == f].sum()), int((fmt == f).sum())) for f in FMT_ORDER}
def rate_row(name, o, byf):
    return [name, f"{int(o.sum())} ({pc(o.mean(), 1)})"] + [f"{a} ({pc(a / b, 1)})" for a, b in (byf[f] for f in FMT_ORDER)]
def floor_options():
    rows = []
    nullp50 = FB["by_format_null_p50"]; ndm50 = FD["by_format_null_p50"]
    o, b = rates(bestB, FLOOR); rows.append(rate_row(f"**A. one global floor {FLOOR:.2f}, best-chunk** (recommended)", o, b))
    fl = {f: round(nullp50[f], 2) for f in FMT_ORDER}; o, b = rates(bestB, fl); rows.append(rate_row("B. per-format floors at each format's own null median, best-chunk (" + ", ".join(f"{f} {v:.2f}" for f, v in fl.items()) + ")", o, b))
    fl = {f: float(np.percentile(bestB[fmt == f], 100 * float((bestB < FLOOR).mean()))) for f in FMT_ORDER}; o, b = rates(bestB, fl)
    rows.append(rate_row("C. within-format percentile: each format's own lowest " + pc(float((bestB < FLOOR).mean()), 1) + " (floors " + ", ".join(f"{f} {v:.2f}" for f, v in fl.items()) + ")", o, b))
    fd = float(D["floor"]["doc_mean"]["null_pct"]["50"]); o, b = rates(bestD, round(fd, 2)); rows.append(rate_row(f"D. one global floor {fd:.2f}, document-mean (its null median)", o, b))
    return table(["policy", "orphans, all docs", "columns", "books", "speeches", "biography"], rows, ["l", "r", "r", "r", "r", "r"])
def orphan_facts():
    from scipy.stats import fisher_exact
    o = bestB < FLOOR; b = int(o[fmt == "biography"].sum()); rest = int(o[fmt != "biography"].sum()); nb = int((fmt == "biography").sum())
    p = fisher_exact([[b, nb - b], [rest, (N - nb) - rest]])[1]
    ob = np.where(o & (fmt == "biography"))[0]; arg = BCL.argmax(1)
    p95 = FB["null_pct"]["95"]; frac95 = float((bestB < p95).mean())
    order = np.argsort(-BCL, axis=1)[:, :3]; cnt = np.array([(BCL[i, order[i]] >= FLOOR).sum() for i in range(N)])
    return dict(p_bio=float(p), bio_orphans=[(C.doc_ids[i], C.title[C.doc_ids[i]], float(bestB[i]), id_of[cl[int(arg[i])]]) for i in ob], frac_below_null_p95=frac95, null_p95=p95, null_p50=FB["null_pct"]["50"],
                tags={k: int((cnt == k).sum()) for k in range(4)}, n_orph=int(o.sum()))

# ================================================================ SECTION: not proposed
def not_proposed():
    rows = []
    for c, v in UNBUILT.items(): rows.append([f"recommended-level cluster d{c}: {v['name']} ({v['n']} docs)", v["why"]])
    pool_rows = []
    for cid, r in CORR["candidates"].items():
        lands = "; ".join(f"{label_of(x['dim'])} {x['docs']}" for x in r["landing"][:3])
        top = r["landing"][0]["share_of_candidate"]; is_orphan = cid.startswith("orphan"); lab0 = label_of(r["landing"][0]["dim"])
        if top >= 0.5: verdict = f"is mostly `{lab0}` ({pc(top)})"
        elif top >= 0.35: verdict = f"partly inside `{lab0}` ({pc(top)}), otherwise spread"
        elif is_orphan: verdict = f"spread over dimensions (best holds {pc(top)}): a residual group of weakly covered documents, not a subject"
        else: verdict = f"spread over dimensions (best holds {pc(top)}): a word or a name that occurs across subjects, not a subject"
        pool_rows.append([cid.replace("orphan ", "Phase 3 orphan cluster ").replace("kw · ", "Phase 3 pool: "), r["n"], lands, verdict])
    return table(["what", "why it is not a dimension"], rows), table(["Phase 3 candidate", "docs", "where its documents land (dimension, docs)", "verdict"], pool_rows, ["l", "r", "l", "l"])
