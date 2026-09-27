"""Phase 6 Step 5: measure the centroid router on concept questions, one per dimension at least. The question set is written HERE, before anything is run
(two per dimension = 60), drawn from the dimension definitions in batch-04/taxonomy_v2_PROPOSAL.md in ordinary user phrasing. Nothing is tuned to the result.
Measured: retrieval.route() — the deterministic centroid router (query centred on corpus_mean, cosine to 30 centred centroids). top-1 = the intended dimension is
the highest-scoring one; top-3 = it is among the three routed_topics (MAX_TOPIC_TAGS). NOT measured: the live robot's Haiku router (no ANTHROPIC_API_KEY here).
Controls: chance (1/30, 3/30) and 5,000 label shuffles (the intended dimension permuted across questions). Writes results/routing_check.json."""
import json, sys, collections
from pathlib import Path
import numpy as np
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "app"))
import config, embeddings
embeddings.get_model()
import retrieval

Q = {
 "life_story_family_school_and_church": ["What was your family life like growing up, and what did your parents teach you?", "Tell me about your years at Far Eastern University and the people who mentored you."],
 "criminal_trials_and_prosecutions": ["How does a criminal case actually move from arrest to bail to trial in the Philippines?", "What happened in the plunder trials at the Sandiganbayan?"],
 "international_law_disputes": ["What did the 2016 arbitral award say about the West Philippine Sea?", "What is the nine-dash line and why does UNCLOS matter?"],
 "property_contracts_and_economic_rights": ["How do Supreme Court decisions protect the property and contract rights of investors?", "What are the rights of workers under the labor code when they are dismissed?"],
 "how_the_supreme_court_decides": ["How does the Supreme Court reason and write its decisions?", "Why is the independence of the judiciary from the other branches important?"],
 "libel_and_cybercrime": ["What is criminal libel and how does the cybercrime law apply to online posts?", "What do you think of the cyberlibel case against Maria Ressa?"],
 "presidential_power_martial_law_people_power": ["What are the limits of presidential power when martial law is declared?", "Was the removal of a president at EDSA constitutional?"],
 "elections_and_automated_voting": ["How does the Commission on Elections run automated elections?", "What are the problems with precinct count optical scanners?"],
 "judiciary_milestones_and_tributes": ["What did the Supreme Court's centenary celebration mean?", "What did you say when you retired from the Court and were honored?"],
 "judicial_reform": ["How can we reduce court delay and case backlogs?", "What is the Action Program for Judicial Reform?"],
 "party_list_charter_change_and_dynasties": ["How does the party-list system work and should it be reformed?", "Should we amend the Constitution through Charter change, and what about political dynasties?"],
 "science_technology_and_the_law": ["How should courts handle DNA evidence and genetic technology?", "What is the impact of artificial intelligence and the internet on the law?"],
 "economy_taxes_and_prosperity": ["What makes a nation prosper economically?", "How do taxes and minimum wages affect jobs and growth?"],
 "impeachment_accountability": ["How does impeachment work, from the House to the Senate?", "What was the impeachment trial of Chief Justice Corona about?"],
 "foundation_for_liberty_and_prosperity": ["What does the Foundation for Liberty and Prosperity do?", "How do the Foundation's scholarships and dissertation contest work, and who supports it?"],
 "public_funds_budget_and_bank_evidence": ["What did the Supreme Court rule about the DAP and the pork barrel?", "Can bank deposits be used as evidence of corruption?"],
 "us_supreme_court_and_american_politics": ["What can the Philippines learn from the United States Supreme Court?", "What do you make of Donald Trump and the American electoral college?"],
 "independent_commissions_and_appointments": ["How independent are the constitutional commissions like the Ombudsman and the Commission on Audit?", "How are commissioners appointed and how long do they serve?"],
 "twin_beacons_doctrine": ["What is the twin-beacons doctrine of liberty and prosperity?", "Why do liberty and prosperity depend on each other?"],
 "marcos_robredo_election_contest": ["What was the vice-presidential election protest between Marcos and Robredo?", "What happened in the 2022 campaign and the canvassing of votes?"],
 "bangsamoro_peace_process": ["What is the Bangsamoro Basic Law and the peace agreement with the MILF?", "Is the Bangsamoro peace deal constitutional?"],
 "supreme_court_vacancies_and_chief_justiceship": ["Who will succeed the retiring justices and lead the Supreme Court?", "What do you think about the appointment of new justices by the president?"],
 "faith_journey": ["What role do prayer and scripture play in your life?", "Tell me about Jesus and the Gospel and what they mean to you."],
 "asean_law_association": ["What is the ASEAN Law Association and what does it do?", "How can lawyers and judges in Southeast Asia promote the rule of law?"],
 "ill_gotten_wealth_and_the_pcgg": ["What is the PCGG and how are Marcos ill-gotten assets recovered?", "What did the courts decide about sequestration and forfeiture of Marcos wealth?"],
 "citizenship_and_residency_grace_poe": ["Is a foundling a natural-born Filipino citizen?", "What did the Court decide in the Grace Poe residency case?"],
 "marriage_annulment_and_the_family_code": ["What is psychological incapacity in marriage annulment cases?", "Should the Philippines allow divorce under the Family Code?"],
 "bar_exam_and_legal_education": ["How should the bar examinations and law schools prepare lawyers?", "What advice do you have for bar topnotchers and new lawyers?"],
 "jbc_discernment_and_appointment": ["How does the Judicial and Bar Council select nominees for the judiciary?", "What are the JBC's rules for drawing up the shortlist for a vacancy?"],
 "death_penalty_and_echegaray": ["What do you think about the death penalty?", "What was the Echegaray case and what was your reflection on it?"],
}
# Supplementary SHORT-FORM set (one per dimension, written before running, same rule): the way a visitor actually types - no descriptive
# vocabulary to lean on. Phase 5's anecdote ("What is the twin-beacons doctrine?" -> international_law_disputes) was of this kind.
SHORT = {
 "life_story_family_school_and_church": "Tell me about your childhood.", "criminal_trials_and_prosecutions": "How does bail work?",
 "international_law_disputes": "What is the arbitral award?", "property_contracts_and_economic_rights": "What are contract rights?",
 "how_the_supreme_court_decides": "How does the Court decide cases?", "libel_and_cybercrime": "What is cyberlibel?",
 "presidential_power_martial_law_people_power": "What is martial law?", "elections_and_automated_voting": "What is wrong with automated elections?",
 "judiciary_milestones_and_tributes": "Tell me about the centenary.", "judicial_reform": "Why are court cases delayed?",
 "party_list_charter_change_and_dynasties": "What is the party-list system?", "science_technology_and_the_law": "What about artificial intelligence?",
 "economy_taxes_and_prosperity": "How do taxes affect the economy?", "impeachment_accountability": "What is impeachment?",
 "foundation_for_liberty_and_prosperity": "What is the Foundation?", "public_funds_budget_and_bank_evidence": "What is the pork barrel?",
 "us_supreme_court_and_american_politics": "Tell me about Donald Trump.", "independent_commissions_and_appointments": "What is the Ombudsman?",
 "twin_beacons_doctrine": "What is the twin-beacons doctrine?", "marcos_robredo_election_contest": "Tell me about Leni Robredo's protest.",
 "bangsamoro_peace_process": "What is the Bangsamoro?", "supreme_court_vacancies_and_chief_justiceship": "Who will be the next Chief Justice?",
 "faith_journey": "Tell me about your faith.", "asean_law_association": "What is the ASEAN Law Association?", "ill_gotten_wealth_and_the_pcgg": "What is ill-gotten wealth?",
 "citizenship_and_residency_grace_poe": "Who is a natural-born citizen?", "marriage_annulment_and_the_family_code": "What is annulment?",
 "bar_exam_and_legal_education": "Tell me about the bar exam.", "jbc_discernment_and_appointment": "What is the JBC?", "death_penalty_and_echegaray": "Tell me about the death penalty."}
tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))["topics"]
assert set(Q) == set(tm) and set(SHORT) == set(tm) and all(len(v) == 2 for v in Q.values()), "one set of questions per dimension"
allow = None
rows = []
for tid, qs in Q.items():
    for k, q in enumerate(qs, 1):
        qv = embeddings.embed_query(q); ri = retrieval.route(q, qv=qv)
        top3 = [t for t, _ in ri["routed_topics"]]; full = np.argsort(-ri["cos"]); rank = 1 + int(np.where(np.array(retrieval._load_centroids()[1]["topic_ids"])[full] == tid)[0][0])
        rows.append({"dimension": tid, "q": k, "question": q, "top1": top3[0], "top3": top3, "top1_cos": ri["top_cosine"], "rank_of_intended": rank, "in_scope": ri["in_scope"], "hit1": top3[0] == tid, "hit3": tid in top3})
n = len(rows); a1 = sum(r["hit1"] for r in rows) / n; a3 = sum(r["hit3"] for r in rows) / n
per = {t: {"n": 2, "top1": sum(r["hit1"] for r in rows if r["dimension"] == t), "top3": sum(r["hit3"] for r in rows if r["dimension"] == t)} for t in Q}
never1 = [t for t, v in per.items() if v["top1"] == 0]; never3 = [t for t, v in per.items() if v["top3"] == 0]
wins = collections.Counter(r["top1"] for r in rows)                       # which dimension wins, regardless of intent
wrong = collections.Counter((r["dimension"], r["top1"]) for r in rows if not r["hit1"])
rng = np.random.default_rng(20260927); dims = list(Q); ctl1, ctl3 = [], []
lab = np.array([r["dimension"] for r in rows]); t1 = np.array([r["top1"] for r in rows]); t3 = [set(r["top3"]) for r in rows]
for _ in range(5000):
    p = rng.permutation(lab); ctl1.append(np.mean(p == t1)); ctl3.append(np.mean([p[i] in t3[i] for i in range(n)]))
print(f"ROUTING (retrieval.route, centroid router) on {n} concept questions, 2 per dimension x {len(Q)} dimensions")
print(f"  top-1 accuracy {100 * a1:.1f}%  ({sum(r['hit1'] for r in rows)}/{n})    top-3 accuracy {100 * a3:.1f}%  ({sum(r['hit3'] for r in rows)}/{n})")
print(f"  controls: chance top-1 {100 / 30:.1f}% / top-3 {300 / 30:.1f}%;  label-shuffle control top-1 {100 * np.mean(ctl1):.1f}% ± {100 * np.std(ctl1):.1f}, top-3 {100 * np.mean(ctl3):.1f}% ± {100 * np.std(ctl3):.1f} (max of 5,000 shuffles: {100 * max(ctl1):.1f}% / {100 * max(ctl3):.1f}%)")
print(f"  in_scope on all {n} in-domain questions: {sum(r['in_scope'] for r in rows)}/{n}")
print(f"  dimensions that NEVER win their own question ({len(never1)}): {never1}")
print(f"  dimensions never even in the top 3 ({len(never3)}): {never3}")
print("  per dimension (top-1 / top-3 of 2):")
for t, v in per.items(): print(f"    {t:48s} {v['top1']}/2  {v['top3']}/2   won {wins.get(t, 0)} questions in total")
print("  most common wrong winners:", [(f"{a} -> {b}", c) for (a, b), c in wrong.most_common(8)])
print("  dimensions that win questions that are not theirs ('attractors'):", [(t, sum(c for (a, b), c in wrong.items() if b == t)) for t, _ in wins.most_common(6)])
srows = []
for tid, q in SHORT.items():
    qv = embeddings.embed_query(q); ri = retrieval.route(q, qv=qv); top3 = [t for t, _ in ri["routed_topics"]]
    srows.append({"dimension": tid, "question": q, "top1": top3[0], "top3": top3, "top1_cos": ri["top_cosine"], "in_scope": ri["in_scope"], "hit1": top3[0] == tid, "hit3": tid in top3})
sa1 = sum(r["hit1"] for r in srows) / 30; sa3 = sum(r["hit3"] for r in srows) / 30
print(f"SHORT-FORM supplementary set (one per dimension, {len(srows)} questions): top-1 {100 * sa1:.1f}% ({sum(r['hit1'] for r in srows)}/30)   top-3 {100 * sa3:.1f}% ({sum(r['hit3'] for r in srows)}/30)   in_scope {sum(r['in_scope'] for r in srows)}/30")
print("  never win (short form):", [r["dimension"] for r in srows if not r["hit1"]])
for r in srows:
    if not r["hit1"]: print(f"    miss: {r['question']!r:52s} intended {r['dimension']:44s} -> {r['top1']} (top3 {r['top3']})")
json.dump({"n_questions": n, "top1_accuracy": a1, "top3_accuracy": a3, "chance": {"top1": 1 / 30, "top3": 3 / 30}, "shuffle_control": {"top1_mean": float(np.mean(ctl1)), "top3_mean": float(np.mean(ctl3)), "top1_max": float(max(ctl1)), "top3_max": float(max(ctl3))},
           "never_win_top1": never1, "never_in_top3": never3, "per_dimension": per, "wins_total": dict(wins), "wrong_winners": {f"{a}->{b}": c for (a, b), c in wrong.items()}, "rows": rows,
           "short_form": {"n": 30, "top1_accuracy": sa1, "top3_accuracy": sa3, "rows": srows, "never_win_top1": [r["dimension"] for r in srows if not r["hit1"]]},
           "router_measured": "retrieval.route() centroid router; NOT the live robot's Haiku router (no ANTHROPIC_API_KEY in this environment)"},
          open(ROOT / "batch-04/ph6_analysis/results/routing_check.json", "w"), indent=1)
