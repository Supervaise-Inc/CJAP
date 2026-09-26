"""CE-10 Step 3.2/3.3 (code side): replace TAXONOMY in scripts/build_topic_map.py with the approved list IN FULL, and make the
map builder carry taxonomy_version 2, the centred-scale record and the META intent. The file is CRLF in git (`* -text`); this script
edits in LF space and writes CRLF back, so the diff is only the intended lines.

Edits (each asserted to match exactly once):
  1. TAXONOMY: lines 70-645 replaced by the Appendix A block of batch-04/taxonomy_v2_PROPOSAL.md (a replacement, not a patch).
     The boundary lines are read back off disk BEFORE and AFTER.
  2. META_INTENTS (robot_identity_meta) after TAXONOMY: an INTENT, not a corpus topic — emitted under topic_map["intents"], never scored,
     never given a centroid (Step 4).
  3. build_topic_map(): year derived from `date` when the doc has no `year` key (none of the 1,290 docs has one; v1 read d["year"]
     directly and would raise KeyError); taxonomy_version 2; scale 'centred' + the corpus mean's sha256 (file must exist); intents block.
  4. newline="\\n" on the two write_text calls (topic_map.json, topic_map_report.json).
  5. docstring: 1,290 documents across four formats, 30 topics.
"""
import ast, json, re, sys
from pathlib import Path
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
P = ROOT / "scripts" / "build_topic_map.py"

raw = P.read_bytes().decode("utf-8")
assert raw.count("\r\n") == raw.count("\n"), "expected a pure-CRLF file"
lines = raw.replace("\r\n", "\n").split("\n")
def show(tag, ls):
    print(f"[{tag}] line 69={ls[68]!r:60.60} | line 70={ls[69]!r:52.52} | line 645={ls[644]!r:20.20} | line 646={ls[645]!r} | line 648={ls[647]!r:.50}")
show("before", lines)
assert lines[69].startswith("TAXONOMY: list[dict[str, Any]] = [") and lines[644] == "]" and lines[68] == "" and lines[645] == ""

prop = (ROOT / "batch-04/taxonomy_v2_PROPOSAL.md").read_text(encoding="utf-8")
block = re.search(r"```python\n(TAXONOMY.*?)\n```", prop, re.S).group(1).split("\n")
assert block[0].startswith("TAXONOMY: list[dict[str, Any]] = [") and block[-1] == "]"
v1 = json.loads((ROOT / "corpus/voice/topic_map_v1_2026-05-25.json").read_text(encoding="utf-8"))["topics"]["robot_identity_meta"]
intent = ["", "", "# -- META intents (CE-10 Step 4) ----------------------------------------------",
          "#", "# robot_identity_meta is an INTENT, not a corpus topic: it holds 0 documents and 0 chunks, is routed by the",
          "# input gate / router (retrieval.input_gate, answer_pipeline.force_meta_routing), and must never get a centroid.",
          "# It is kept OUT of TAXONOMY and emitted under topic_map['intents'] so the legacy pipeline's topic_data node —",
          "# the persona instruction the composer reads for identity probes — is unchanged.", "",
          "META_INTENTS: list[dict[str, Any]] = [", "    {"]
for k in ("id", "display_name", "definition", "tier", "theme_anchor"): intent.append(f"        {json.dumps(k)}: {json.dumps(v1[k], ensure_ascii=False)},")
intent += [f'        "default_register_override": ("{v1["default_register"]}", "{v1["wit_calibration"]}"),', '        "matchers": {', '            "keywords": ['] + \
          [f"                {json.dumps(t)}," for t in v1["matchers"]["keywords"]] + ['            ],', '            "entities": [],', '        },', "    },", "]"]
new = lines[:69] + block + intent + lines[645:]
txt = "\n".join(new)

def sub(a, b):
    global txt
    assert txt.count(a) == 1, (txt.count(a), a[:70]); txt = txt.replace(a, b)
sub('Reads the 79 generated .json files under corpus/{columns,speeches,biography}/', 'Reads every generated .json under corpus/{columns,books,speeches,biography}/ (1,290 documents)')
sub('The taxonomy is a hand-curated dict of ~35 topics with matcher rules', 'The taxonomy (v2, CE-10) is a curated list of 30 topics with matcher rules')
sub('import json\nimport re\nfrom collections import Counter', 'import hashlib\nimport json\nimport re\nimport sys\nfrom collections import Counter')
sub('REPORTS_DIR = PROJECT_ROOT / "reports"\n', 'REPORTS_DIR = PROJECT_ROOT / "reports"\nsys.path.insert(0, str(PROJECT_ROOT))\nimport config  # noqa: E402  (CORPUS_MEAN_PATH)\n')
sub('        years = sorted({d["year"] for d in matched if d.get("year")})', '        years = sorted({y for y in (_doc_year(d) for d in matched) if y})')
sub('                sorted(Counter(d["year"] for _, d in docs).items())', '                sorted(Counter(_doc_year(d) for _, d in docs).items(), key=lambda kv: (kv[0] is None, kv[0] or 0))')
sub('def build_topic_map(docs: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:\n',
    'def _doc_year(d: dict[str, Any]) -> int | None:\n'
    '    """Year of a document: its `year` key if present, else the year in `date` (the corpus JSONs carry `date` only;\n'
    '    v1 indexed d["year"] directly). Jan-1 placeholder dates still give the right YEAR; date precision is untouched."""\n'
    '    y = d.get("year")\n'
    '    if y:\n'
    '        return int(y)\n'
    '    m = re.match(r"(\\d{4})", str(d.get("date") or ""))\n'
    '    return int(m.group(1)) if m else None\n\n\n'
    'def _corpus_mean_sha256() -> str:\n'
    '    """The map records the scale its centroids live on. The mean file must already exist (build_corpus_mean.py); no fallback."""\n'
    '    p = Path(config.CORPUS_MEAN_PATH)\n'
    '    if not p.exists():\n'
    '        raise FileNotFoundError(f"{p} missing: run scripts/build_corpus_mean.py before rebuilding the topic map")\n'
    '    return hashlib.sha256(p.read_bytes()).hexdigest()\n\n\n'
    'def build_topic_map(docs: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:\n')
sub('    return {\n        "schema_version": "2.0",\n        "generated_at": datetime.now(timezone.utc).isoformat(),\n',
    '    intents_out: dict[str, dict[str, Any]] = {}\n'
    '    for it in META_INTENTS:\n'
    '        reg = it.get("default_register_override") or THEME_REGISTER.get(it["theme_anchor"], ("doctrinal-formal", "sparing"))\n'
    '        intents_out[it["id"]] = {\n'
    '            "id": it["id"], "kind": "intent", "display_name": it["display_name"], "definition": it["definition"],\n'
    '            "tier": it["tier"], "theme_anchor": it["theme_anchor"], "default_register": reg[0], "wit_calibration": reg[1],\n'
    '            "doc_count": 0, "doc_ids": [], "date_range": [], "year_range": [], "type_distribution": {}, "theme_distribution": {},\n'
    '            "top_people": [], "top_institutions": [], "top_cases": [], "matchers": it["matchers"],\n'
    '        }\n\n'
    '    return {\n        "schema_version": "2.0",\n        "taxonomy_version": 2,\n'
    '        "scale": "centred",\n        "corpus_mean": {"path": "data/index/corpus_mean.npy", "sha256": _corpus_mean_sha256()},\n'
    '        "generated_at": datetime.now(timezone.utc).isoformat(),\n')
sub('        "topics": topics_out,\n    }, doc_scores', '        "topics": topics_out,\n        "intents": intents_out,\n    }, doc_scores')
sub('        json.dumps(tm, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8"\n    )', '        json.dumps(tm, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8", newline="\\n"\n    )')
sub('        + "\\n",\n        encoding="utf-8",\n    )\n    return out_path', '        + "\\n",\n        encoding="utf-8",\n        newline="\\n",\n    )\n    return out_path')
ast.parse(txt)
P.write_bytes(txt.replace("\n", "\r\n").encode("utf-8"))
chk = P.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
i0 = next(i for i, l in enumerate(chk) if l.startswith("TAXONOMY:")); i1 = next(i for i in range(i0, len(chk)) if chk[i] == "]")
print(f"[after]  TAXONOMY opens at line {i0 + 1}: {chk[i0]!r:.60}; closes at line {i1 + 1}: {chk[i1]!r}; next non-blank: {[l for l in chk[i1 + 1:i1 + 8] if l][0][:70]!r}")
print("[after]  read back off disk:", "\n".join(chk[i0:i0 + 3]).replace("\n", " | ")[:200])
assert P.read_bytes().count(b"\r\n") == P.read_bytes().count(b"\n"), "file must stay pure CRLF"
print("pure CRLF preserved; ast.parse OK; TAXONOMY entries:", sum(1 for l in chk[i0:i1] if l.startswith('        "id": ')))
