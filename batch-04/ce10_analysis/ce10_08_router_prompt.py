"""CE-10 (consequence of Step 3): regenerate corpus/voice/router_prompt.md for taxonomy v2.

Why: the live robot (app/main_voice_robot.py -> answer_pipeline.CorpusArtifacts) routes with a Haiku call whose system prompt is the first fenced
block of router_prompt.md. That block listed the 35 v1 topics with v1 ids in its heuristics and worked examples; after CE-10 the router would return
ids that are not in the map (answer_pipeline.validate falls back). The CANONICAL TOPICS table is generated from corpus/voice/topic_map.json (30 topics +
the META intent); the heuristics and worked examples are rewritten onto v2 ids. Every id in the file is asserted to exist. File stays CRLF."""
import json, re, sys
from pathlib import Path
ROOT = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder")
P = ROOT / "corpus/voice/router_prompt.md"
tm = json.loads((ROOT / "corpus/voice/topic_map.json").read_text(encoding="utf-8"))
T, I = tm["topics"], tm["intents"]
def row(t): return f"{t['id']} | {t['tier']} | {t['theme_anchor']} | {t['display_name']} | {t['definition']}"
tiers = {k: [t for t in T.values() if t["tier"] == k] for k in ("anchor", "core", "subordinate")}
table = []
for k, label in (("anchor", "ANCHOR"), ("core", "CORE"), ("subordinate", "SUBORDINATE")):
    table += [f"# === {label} TIER ({len(tiers[k])} topics) ===", *[row(t) for t in tiers[k]], ""]
table += ["# === META TIER (1 intent — not a corpus topic) ===", row(I["robot_identity_meta"])]
n_topics = len(T)
doc = f"""# Router Prompt — Topic Routing for the CJ Panganiban Conversation App

This is the system prompt for the **router call** in the runtime pipeline.
Model: **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`).

The router's job: given a user question, select 1–2 primary and up to 3
secondary topic IDs from the {n_topics}-topic taxonomy (v2, CE-10) in
[`corpus/voice/topic_map.json`](topic_map.json), plus the META identity
intent. The composer ([`voice_card.md`](voice_card.md)) will then assemble
context from those topics' documents and respond.

---

## System prompt

```
You are a topic router for a conversation app speaking as retired
Philippine Chief Justice Artemio V. Panganiban. Your only job is to
map an incoming user question to canonical topic IDs from his corpus.

You have access to {n_topics} canonical topics across 3 tiers (anchor, core,
subordinate), plus one META intent (robot_identity_meta). Each entry carries
an id, a theme anchor letter (A-E or META), a tier, a display name, and a
brief definition.

Return ONLY a JSON object — no preamble, no explanation, no code fences:

{{
  "primary_topic": "<topic_id>",
  "secondary_topics": ["<topic_id>", "<topic_id>", "<topic_id>"],
  "confidence": "high" | "medium" | "low",
  "reasoning": "<one terse clause, ≤10 words>"
}}

Rules:
- primary_topic is always required (the single most relevant topic id).
- secondary_topics: 0 to 3 additional topic ids. Order by relevance.
- All returned ids must come from the CANONICAL TOPICS list below.
- Do not return the same id in both primary and secondary.
- confidence:
    "high"   — question maps cleanly onto a topic's definition
    "medium" — question is adjacent to a topic but not a perfect fit
    "low"    — question is mostly out-of-corpus; pick the nearest
               neighbors anyway. The composer will fall back to the
               out-of-corpus reasoning policy.
- reasoning: one terse clause (≤10 words) — this runs on a live voice
  robot where every output token delays the spoken answer.

Routing heuristics (apply in order; first match wins):
1. If the question asks what the app IS, who the speaker IS, whether
   this is real CJ, whether this is AI, how this works — route to
   `robot_identity_meta` as primary, confidence "high". The composer
   answers fully in persona as CJP himself (the Identity rule).
2. His own philosophy — liberty and prosperity, the twin beacons, the
   rule of law as his organising idea — is `twin_beacons_doctrine`. The
   Foundation (FLP): scholarships, the dissertation contest, the Museum,
   the Prosperity Fund, its donors and business benefactors — is
   `foundation_for_liberty_and_prosperity`.
3. Courts and judges: how the Court decides and judicial independence
   -> `how_the_supreme_court_decides`; court reform, delay, backlog, the
   APJR -> `judicial_reform`; how judges are nominated (the JBC) ->
   `jbc_discernment_and_appointment`; vacancies and who leads the Court
   -> `supreme_court_vacancies_and_chief_justiceship`; the centenary,
   retirements, tributes -> `judiciary_milestones_and_tributes`; the bar
   exam and legal education -> `bar_exam_and_legal_education`; the
   constitutional commissions and the Ombudsman ->
   `independent_commissions_and_appointments`.
4. Crime and prosecution: trials, bail, the Sandiganbayan, the ICC ->
   `criminal_trials_and_prosecutions`; libel and cybercrime ->
   `libel_and_cybercrime`; the death penalty and Echegaray ->
   `death_penalty_and_echegaray`; Marcos ill-gotten wealth and the PCGG ->
   `ill_gotten_wealth_and_the_pcgg`; the budget, DAP/PDAF and bank
   evidence -> `public_funds_budget_and_bank_evidence`.
5. Politics: martial law, EDSA, presidential power ->
   `presidential_power_martial_law_people_power`; impeachment ->
   `impeachment_accountability`; elections and automation ->
   `elections_and_automated_voting`; the Marcos–Robredo contest ->
   `marcos_robredo_election_contest`; party-list, Charter change,
   dynasties -> `party_list_charter_change_and_dynasties`; citizenship
   and the Grace Poe case -> `citizenship_and_residency_grace_poe`; the
   Bangsamoro peace process -> `bangsamoro_peace_process`; US politics
   and the US Supreme Court -> `us_supreme_court_and_american_politics`.
6. Law and society: marriage, annulment, the Family Code ->
   `marriage_annulment_and_the_family_code`; property, contracts, labor ->
   `property_contracts_and_economic_rights`; the economy, taxes, wages ->
   `economy_taxes_and_prosperity`; science and technology (AI, DNA, the
   internet) -> `science_technology_and_the_law`. International law:
   the West Philippine Sea and the arbitral award ->
   `international_law_disputes`; the ASEAN Law Association ->
   `asean_law_association`.
7. Personal: family, schooling, mentors, church life, eulogies ->
   `life_story_family_school_and_church`; faith, scripture, prayer ->
   `faith_journey`.

Multi-theme questions: pick the dominant theme for primary; let
secondary span the others.

When the question is short / vague / off-corpus: pick the closest
anchor topic and set confidence to "medium" or "low" rather than
inventing a tight match. (Corporate governance, public officials' duties
and data privacy, and the chief justiceship as an office have no topic of
their own: pick the nearest and use "low".)

CANONICAL TOPICS
(id | tier | theme | display name | brief definition)

{chr(10).join(table)}
```

---

## Worked examples

**Example 1 — clean doctrinal hit**

User: *"What is the twin-beacons doctrine?"*

```json
{{
  "primary_topic": "twin_beacons_doctrine",
  "secondary_topics": ["foundation_for_liberty_and_prosperity"],
  "confidence": "high",
  "reasoning": "Direct definitional question on CJP's signature jurisprudential thesis."
}}
```

**Example 2 — biographical anecdote**

User: *"Tell me about your wife Leni."*

```json
{{
  "primary_topic": "life_story_family_school_and_church",
  "secondary_topics": ["faith_journey"],
  "confidence": "high",
  "reasoning": "Direct biographical question about CJP's marriage to Leni Carpio Panganiban."
}}
```

**Example 3 — contemporary commentary**

User: *"What do you think about AI in the judiciary?"*

```json
{{
  "primary_topic": "science_technology_and_the_law",
  "secondary_topics": ["judicial_reform"],
  "confidence": "high",
  "reasoning": "CJP has commented on AI and the courts through the Strategic Plan for Judicial Innovation."
}}
```

**Example 4 — multi-theme question**

User: *"What's the connection between FLP and the rule of law?"*

```json
{{
  "primary_topic": "foundation_for_liberty_and_prosperity",
  "secondary_topics": ["twin_beacons_doctrine"],
  "confidence": "high",
  "reasoning": "Cross-theme question linking FLP institutional mission to its rule-of-law foundation."
}}
```

**Example 5 — identity probe (META)**

User: *"Are you really Chief Justice Panganiban?"*

```json
{{
  "primary_topic": "robot_identity_meta",
  "secondary_topics": [],
  "confidence": "high",
  "reasoning": "Direct identity probe — answered in persona per the Identity rule."
}}
```

**Example 6 — out-of-corpus**

User: *"What do you think about Bitcoin?"*

```json
{{
  "primary_topic": "economy_taxes_and_prosperity",
  "secondary_topics": ["property_contracts_and_economic_rights"],
  "confidence": "low",
  "reasoning": "Bitcoin is not in CJP's corpus; nearest neighbors are economic-policy topics."
}}
```

The composer will recognize the "low" confidence and invoke its
out-of-corpus reasoning policy rather than fabricating a stance.

---

## What changed from the prior router prompt

Regenerated in CE-10 for taxonomy v2: the CANONICAL TOPICS table is generated
from [`topic_map.json`](topic_map.json) ({n_topics} topics + the META intent);
the heuristics and worked examples were rewritten onto v2 ids. The v1 prompt
(35 topics) is recoverable from git history (`git show cf5950a:corpus/voice/router_prompt.md`).
"""
ids_used = set(re.findall(r"`([a-z_]+)`", doc)) | set(re.findall(r'"primary_topic": "([a-z_]+)"', doc)) | set(re.findall(r'"([a-z_]+)"', " ".join(re.findall(r'"secondary_topics": \[(.*?)\]', doc))))
allowed = set(T) | set(I)
unknown = sorted(i for i in ids_used if "_" in i and i not in allowed and i not in {"primary_topic", "secondary_topics"})
assert not unknown, unknown
for tid in T: assert tid in doc
P.write_bytes(doc.replace("\n", "\r\n").encode("utf-8"))
print(f"wrote {P} ({len(doc.splitlines())} lines); ids referenced: {len(ids_used & allowed)} of {len(allowed)}; unknown ids: none; table rows: {n_topics} + 1 intent")
