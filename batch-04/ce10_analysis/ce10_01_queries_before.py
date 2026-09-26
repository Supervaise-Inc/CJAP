"""CE-10 Step 2 (part 1): embed the query sets ONCE and record the BEFORE state of OUT_OF_SCOPE_THRESHOLD.
Read-only on the repo. Uses the still-in-place v1 centroids (raw scale) exactly as the old route() did: cos = cen @ qv, in_scope = max(cos) >= 0.15.

Query sets
  gold40  : eval/results/gold_reference_set.csv — the frozen 40 (34 in-scope + 2 gap-in + 2 out + 2 meta)      [real queries]
  ce11    : eval/results/ce11_queries_2026-09-26.json — the 14 batch-03 gold additions (13 in-domain + 1 oos)   [real queries]
  ood     : 40 clearly out-of-domain probes written for this calibration (weather, food, sport, code, ...)      [CONTROL, authored]
  noise   : 20 nonsense strings (random tokens, numbers, keyboard mash)                                         [CONTROL, null]
  titles  : 300 randomly drawn document titles (seeded) used as in-domain pseudo-queries                       [in-domain by construction]
Writes cache/qvecs.npz (labels, sets, texts, RAW query vectors) and cache/oos_before.json."""
import csv, json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
import config, embeddings   # noqa: E402
embeddings.get_model()      # model first (exit-139 family on this env)
CACHE = ROOT / "batch-04" / "ce10_analysis" / "cache"; CACHE.mkdir(parents=True, exist_ok=True)

OOD = ["What's the weather like in Manila today?", "Can you recommend a good restaurant near me?", "Who won the NBA finals last year?",
       "How do I bake sourdough bread at home?", "Write me a Python function that reverses a string.", "What is the square root of 1764?",
       "Which smartphone should I buy under 20,000 pesos?", "What is the current price of Bitcoin?", "Tell me a joke about cats.",
       "How do I fix a leaking kitchen faucet?", "What are the symptoms of the flu?", "Recommend a good movie to watch tonight.",
       "How many calories are in a banana?", "Translate 'good morning' into Japanese.", "What time does the mall open on Sundays?",
       "Who is the best basketball player of all time?", "How do I change a flat tyre?", "What's a good workout routine for beginners?",
       "Explain how photosynthesis works.", "What is the capital of Australia?", "How do I reset my wifi router?",
       "Suggest a name for my new puppy.", "What's the best way to learn guitar?", "How far is the moon from the earth?",
       "Which airline has the cheapest flights to Cebu?", "What is the plot of Harry Potter?", "How do I remove a red wine stain?",
       "Give me a recipe for adobo.", "What's the exchange rate of the dollar to the peso?", "How do vaccines work?",
       "What is the tallest mountain in the world?", "Can you help me write a wedding toast?", "What should I plant in a small balcony garden?",
       "Who sang Bohemian Rhapsody?", "How do I install Windows on a new laptop?", "What is the best diet to lose weight fast?",
       "How long does it take to boil an egg?", "What is the meaning of the word serendipity?", "How do I start a podcast?",
       "Which is better, iPhone or Android?"]
NOISE = ["asdf qwer zxcv", "lorem ipsum dolor sit amet consectetur", "blue 47 seventeen tomato window", "zzzz qqqq xxxx", "12345 67890 13579",
         "hmm ok well so", "the of and to in", "banana orbit velvet quartz", "!!! ??? ...", "xylophone marmalade gigabyte",
         "kjhg lkjh mnbv", "purple monkey dishwasher", "aaa bbb ccc ddd eee", "seven eight nine ten", "random words go here",
         "qwertyuiop", "tuesday cheese lamp", "foo bar baz qux", "nnnn mmmm", "one two three four five six"]
gold = list(csv.DictReader(open(ROOT / "eval/results/gold_reference_set.csv", encoding="utf-8-sig")))
ce11 = json.load(open(ROOT / "eval/results/ce11_queries_2026-09-26.json", encoding="utf-8"))["queries"]
rng = np.random.default_rng(20260927)
titles = []
for p in sorted(ROOT.glob("corpus/*/*/*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(d, dict) and d.get("id", " ")[0] in "CBSG" and d.get("format") and d.get("title"): titles.append((d["id"], d["title"]))
titles = [titles[i] for i in rng.choice(len(titles), 300, replace=False)]
items = []   # (set, id, scope, text)
for r in gold: items.append(("gold40", r["qid"], {"in": "in", "out": "out", "meta": "meta", "in(gap)": "in", "in(gap-v4)": "in"}[r["scope_gold"]], r["query"]))
for q in ce11: items.append(("ce11", q["id"], "out" if q["type"] == "oos" else "in", q["query"]))
for i, t in enumerate(OOD): items.append(("ood", f"O{i+1:02d}", "out", t))
for i, t in enumerate(NOISE): items.append(("noise", f"N{i+1:02d}", "noise", t))
for did, t in titles: items.append(("titles", did, "in", t))
qv = np.stack([embeddings.embed_query(t) for _, _, _, t in items]).astype(np.float32)
np.savez(CACHE / "qvecs.npz", sets=np.array([i[0] for i in items]), ids=np.array([i[1] for i in items]), scope=np.array([i[2] for i in items]),
         texts=np.array([i[3] for i in items]), vecs=qv)
# ---- BEFORE: the old route() on the v1 raw centroids
cen = np.load(ROOT / "data/index/topic_centroids.npy").astype(np.float32); meta = json.loads((ROOT / "data/index/topic_centroids_meta.json").read_text(encoding="utf-8"))
cos = qv @ cen.T; top = cos.max(1); T0 = config.OUT_OF_SCOPE_THRESHOLD
out = {"threshold_before": T0, "scale_before": "raw cosine, v1 centroids (n=%d)" % cen.shape[0], "sets": {}}
for s in ("gold40", "ce11", "ood", "noise", "titles"):
    for sc in sorted({i[2] for i in items if i[0] == s}):
        idx = [k for k, i in enumerate(items) if i[0] == s and i[2] == sc]
        out["sets"][f"{s}/{sc}"] = {"n": len(idx), "top_cos_min": float(top[idx].min()), "top_cos_median": float(np.median(top[idx])), "top_cos_max": float(top[idx].max()),
                                     "in_scope_at_0.15": int((top[idx] >= T0).sum()), "in_scope_rate": float((top[idx] >= T0).mean())}
json.dump(out, open(CACHE / "oos_before.json", "w"), indent=1)
for k, v in out["sets"].items(): print(f"{k:14s} n={v['n']:3d} raw top-cos min {v['top_cos_min']:.3f} median {v['top_cos_median']:.3f} max {v['top_cos_max']:.3f} | in_scope at {T0}: {v['in_scope_at_0.15']}/{v['n']}")
print("embedded", len(items), "queries ->", CACHE / "qvecs.npz")
