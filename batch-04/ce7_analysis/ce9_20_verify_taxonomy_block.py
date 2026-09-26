"""CE-9 step 20: prove the Appendix A block is paste-ready. Extracts the ```python block from taxonomy_v2_PROPOSAL.md, splices it over lines 70-645 of a COPY of scripts/build_topic_map.py
(in the scratchpad / cache, never in scripts/), imports the copy, and checks: 30 entries, required keys, unique ids, tiers/theme anchors valid, matcher terms compile through the real _kw_pattern,
and that the copy's own score_topic reproduces the document counts reported in Table 1. Read-only on the repo."""
import ast, importlib.util, json, re, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import ROOT, B4, CACHE
src = (ROOT / "scripts" / "build_topic_map.py").read_text(encoding="utf-8").split("\n")
assert src[69].startswith("TAXONOMY: list[dict[str, Any]] = ["), src[69]
assert src[644].strip() == "]", repr(src[644])
print("v1 file: line 70 opens TAXONOMY, line 645 closes it (", len(src), "lines total; the brief's 69-649 also spans a blank line and the '# -- Matching engine' banner )")
md = (B4 / "taxonomy_v2_PROPOSAL.md").read_text(encoding="utf-8")
block = re.search(r"```python\n(TAXONOMY.*?)\n```", md, re.S).group(1)
ast.parse(block)
new = src[:68] + block.split("\n") + src[649:]
tmp = CACHE / "build_topic_map_v2_candidate.py"; tmp.write_text("\n".join(new), encoding="utf-8")
spec = importlib.util.spec_from_file_location("btm_v2", tmp); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
T = m.TAXONOMY; print("entries:", len(T))
ids = [t["id"] for t in T]; assert len(set(ids)) == len(ids)
for t in T:
    assert set(t) == {"id", "display_name", "definition", "tier", "theme_anchor", "matchers"}, t["id"]
    assert t["tier"] in ("anchor", "core", "subordinate") and t["theme_anchor"] in "ABCDE"
    assert set(t["matchers"]) == {"keywords", "entities"} and (t["matchers"]["keywords"] or t["matchers"]["entities"])
    for term in t["matchers"]["keywords"] + t["matchers"]["entities"]: m._kw_pattern(term)
print("schema OK; tiers:", {k: sum(1 for t in T if t["tier"] == k) for k in ("anchor", "core", "subordinate")})
docs = {}
for p in sorted(ROOT.glob("corpus/*/*/*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(d, dict) and "id" in d and d["id"][0] in "CBSG" and d.get("format"): docs[d["id"]] = d
assert len(docs) == 1290
hs = {k: m._doc_haystack(d) for k, d in docs.items()}
got = {t["id"]: sum(1 for k in docs if m.score_topic(t, hs[k]) > 0) for t in T}
rows = re.findall(r"^\| ([a-z_]+) \| [^|]+\| (?:anchor|core|subordinate) \| [^|]+\| (\d+) \|", md, re.M)
tab = {a: int(b) for a, b in rows}
bad = {k: (got[k], tab.get(k)) for k in got if tab.get(k) != got[k]}
print("Table 1 doc_count vs the pasted block's own score_topic on the 1,290 docs:", "ALL", len(got), "MATCH" if not bad else f"MISMATCH {bad}")
print("docs matched by >= 1 dimension:", len({k for k in docs if any(m.score_topic(t, hs[k]) > 0 for t in T)}))
tmp.unlink()
