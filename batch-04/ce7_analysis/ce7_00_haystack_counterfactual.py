"""CE-7 counterfactual for step 4b: is the matchers' low zero-score count caused by the enrichment prose in the haystack?
Re-scores every document with the v1 matchers after removing prose fields from the haystack. Writes cache/haystack_cf.json
(read by ce7_01_coverage.py). Read-only on the repo."""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ce7_common import *

C = Corpus(); P = prior_art(); m = P["module"]; tax = P["taxonomy"]
VARIANTS = [("full haystack (as the matchers actually run)", []),
            ("minus one_paragraph_summary", ["one_paragraph_summary"]),
            ("minus primary_topics + sub_topics", ["primary_topics", "sub_topics"]),
            ("minus all three prose fields", ["one_paragraph_summary", "primary_topics", "sub_topics"])]
out = []
for label, strip in VARIANTS:
    z, w1 = Counter(), Counter()
    for d in C.doc_ids:
        doc = dict(C.docs[d])
        for f in strip:
            doc[f] = [] if isinstance(doc.get(f), list) else ""
        hs = m._doc_haystack(doc); best = max(m.score_topic(t, hs) for t in tax.values())
        if best == 0: z[fmt_of(d)] += 1
        if best <= 1: w1[fmt_of(d)] += 1
    out.append({"variant": label, "zero": sum(z.values()), "zero_by_format": dict(z), "le1": sum(w1.values())})
    print(label, out[-1], flush=True)
json.dump(out, open(CACHE / "haystack_cf.json", "w"), indent=1)
