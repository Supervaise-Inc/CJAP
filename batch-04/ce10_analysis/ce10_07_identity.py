"""CE-10 Step 4 proof: robot_identity_meta left the taxonomy (no topic, no centroid) but the identity intent still routes.
Local proofs only - the composer LLM call needs ANTHROPIC_API_KEY, which is not present in this environment (no app/.env, no .env, no env var)."""
import json, os, sys
from pathlib import Path
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
os.environ["CJ_DYNAMIC_TOKENS_ENABLED"] = "1"
import numpy as np, config
ok = True
def chk(name, cond, detail=""):
    global ok; ok &= bool(cond); print(f"  [{'OK ' if cond else 'BAD'}] {name} {detail}")
tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))
meta = json.loads(Path(config.CENTROIDS_META_PATH).read_text(encoding="utf-8"))
print("== the intent is out of the taxonomy and out of the centroid set ==")
chk("not in topic_map['topics']", "robot_identity_meta" not in tm["topics"], f"({len(tm['topics'])} topics)")
chk("not in the centroid set", "robot_identity_meta" not in meta["topic_ids"], f"({meta['n_topics']} centroids)")
chk("present under topic_map['intents']", "robot_identity_meta" in tm["intents"])
import answer_pipeline as ap, retrieval
art = ap.CorpusArtifacts()
print("== legacy pipeline (answer_pipeline; the live robot's path) ==")
chk("artifacts.topics resolves the intent", "robot_identity_meta" in art.topics and art.topics["robot_identity_meta"]["tier"] == "meta")
chk("valid_topic_ids accepts it (router validation)", "robot_identity_meta" in art.valid_topic_ids)
routing = ap.force_meta_routing("identity probe")
chk("force_meta_routing primary_topic", routing["primary_topic"] == "robot_identity_meta", routing["primary_topic"])
chk("source docs for it: none, no error", ap._select_source_doc_ids(routing, art) == [])
ctx = ap.build_context(routing, art)
chk("composer context carries the persona instruction (topic_data node)", "in persona as Chief Justice Panganiban himself" in ctx and "never describing himself as an AI" in ctx)
b = ap._topic_max_tokens(routing, art)
chk("token budget for the intent (120 x scale)", b == ap._scale_budget(120), f"-> max_tokens {b}")
chk("v2 topics have a budget entry (no silent default)", all(t in ap.TOKEN_BUDGET_BY_DIM for t in tm["topics"]), f"{sum(t in ap.TOKEN_BUDGET_BY_DIM for t in tm['topics'])}/30")
chk("no v1-only id left in the budget table", set(ap.TOKEN_BUDGET_BY_DIM) == set(tm["topics"]) | {"robot_identity_meta"})
chk("voice card still states the Identity rule", "robot_identity_meta" in art.voice_card or "Identity" in art.voice_card)
print("== new arch (retrieval) ==")
for q in ("Are you an AI?", "Are you really Chief Justice Panganiban?", "Who made you?", "How do you work?"):
    g = retrieval.input_gate(q); chk(f"input_gate({q!r})", g["scope"] == "identity_probe", g["scope"])
r = retrieval.run("Are you an AI?", set(json.loads(Path(config.DENSE_INDEX_META_PATH).read_text(encoding="utf-8"))["doc_ids"]))
chk("retrieval.run on an identity probe completes; gate flags it, route is a v2 topic", r["gate"]["scope"] == "identity_probe" and r["route"]["top_topic"] in tm["topics"], f"gate={r['gate']['scope']} top_topic={r['route']['top_topic']} cos={r['route']['top_cosine']}")
print("== NOT run: the composer LLM call (no ANTHROPIC_API_KEY here). The persona text the composer receives is asserted above. ==")
print("\nALL CHECKS PASSED" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
