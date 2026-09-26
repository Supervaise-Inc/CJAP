"""CE-9 hand-written verdicts (the ONLY judgement that is not read from a measurement). Everything here is printed in the proposal next to the numbers that support it.
Fate vocabulary (the Phase 4 prompt's): carried | carried, matcher rewritten | absorbed into <id> | redefined as <id> | dropped  (+ one row: moved to the router)."""

ANCHORS = {"twin_beacons_doctrine", "foundation_for_liberty_and_prosperity"}     # tier 'anchor' is a POLICY label (the Chief Justice's organising philosophy and the Foundation), not a size rule

# v1 topic -> (fate word, target cluster number or None, why)   [numbers for the 'evidence' column are computed from cache/ce9_fate_m20.json + ce9_v1_reuse.json]
FATE = {
    "rule_of_law": ("absorbed", 19, "A concept mentioned across the corpus, not a place in it: 211 matcher documents, member cohesion barely above random. Its centroid sits at 0.72 from the twin-beacons dimension, whose matcher already carries 'rule of law'."),
    "twin_beacons_doctrine": ("carried, matcher rewritten", 19, "Same direction, wrong members: the v1 matcher fires on 213 documents, 24 of which are the 27-document dimension."),
    "foundation_for_liberty_and_prosperity": ("carried, matcher rewritten", 15, "The Foundation dimension holds (centred cosine 0.91); the v1 matcher over-fires 4x."),
    "with_due_respect_persona": ("dropped", None, "The column's stance is a property of the voice, not a subject: 197 matcher documents, nearest dimension only 0.54. It belongs in the voice card (already there), not the taxonomy."),
    "constitutional_doctrine": ("dropped", None, "A catch-all: 611 documents (47% of the corpus) at cohesion barely above random. Its specific subjects live on as impeachment, presidential power, charter change, the commissions and how the Court decides."),
    "due_process": ("dropped", None, "Cross-cutting doctrine with no cluster of its own (nearest dimension 0.66, 12 of 145 documents inside it); its content is criminal procedure and criminal law."),
    "judicial_reform": ("carried, matcher rewritten", 10, "Dimension holds (0.84). The Davide pool (23 book chapters) lands here: 9 of them inside this dimension, more than in any other."),
    "supreme_court_history": ("dropped", None, "Diffuse: 406 matcher documents (31% of the corpus), nearest dimension 0.63. The Puno pool that Phase 3 read as 'same direction' does not form a dimension of its own (21 book chapters spread over 11 dimensions, 7 of them in property and contracts). The institution's subjects are carried by the tributes/milestones, vacancies, chief-justiceship and how-the-Court-decides dimensions."),
    "impeachment_accountability": ("carried, matcher rewritten", 14, "Dimension holds (0.84); the v1 matcher fires on 171 documents for a 35-document subject."),
    "international_law_disputes": ("carried, matcher rewritten", 3, "Dimension holds (0.95). The v1 matcher would pass the acceptance test as it stands (1.2x, P@3 0.68, recall 72%); the new one is better on all three (1.3x, P@3 0.72 on the same partition-neighbourhood definition, recall 83%) - and it is the closest v1 came to a finished matcher."),
    "icc_and_duterte": ("absorbed", 2, "Its coherent core is an 18-document ICC cluster (13 of them v1 matcher hits) that the recommended level folds into criminal trials - it is one of the fine level's fragments; the other 143 of its 156 matcher documents are diffuse (cohesion 0.26 vs 0.09 random)."),
    "judicial_activism_and_political_question": ("dropped", None, "No cluster (nearest dimension 0.57): 78 documents on a doctrine mentioned across several subjects; 'judicial activism' catches 9 documents in total."),
    "asean_law_association": ("carried, matcher rewritten", 25, "Dimension holds (0.86). The v1 matcher passes the acceptance test as it stands (1.6x, P@3 0.62) but only 26% of what it catches is in the dimension; the new one is stricter (11 documents, 82% inside) at similar recall (38% vs 42%)."),
    "death_penalty_and_echegaray": ("carried, matcher rewritten", "x:death_penalty", "The brief's verdict holds, at a price. Real and narrow (Phase 3: cohesion 0.34 vs null p95 0.23; 30 documents, 17 of them book chapters). It passes all four tests as a dimension of its own - but only while criminal law's matcher does not carry its terms: with them in the same dimension the two are 0.96 apart; with libel/cybercrime alone it is 0.43 from the nearest dimension. Neighbourhood precision is 0.57, just under the 0.60 bar used for the others."),
    "bar_exam_and_legal_education": ("carried, matcher rewritten", 30, "Same direction, wrong members: the v1 centroid is closer to the life-story dimension (0.73) than to the bar-exam one (0.69) because 43 of its 132 matcher documents are life-story documents."),
    "economic_governance_and_business_law": ("absorbed", 19, "Centred cosine 0.86 with the twin-beacons dimension (duplicate at any sensible threshold); 'deferential interpretation' and the business-policy vocabulary are already in that dimension's matcher."),
    "eez_resource_sovereignty": ("absorbed", 3, "29 matcher documents at cohesion 0.42; 9 sit in the sea-dispute dimension (0.67) and 9 in property and contracts. Joint development in the South China Sea is a sub-theme of the dimension it joins."),
    "msme_and_entrepreneurship+prosperity_fund_msme": ("absorbed", 15, "v1 already merged these two into one centroid; that centroid is at 0.87 from the Foundation dimension."),
    "family_and_marriage": ("absorbed", 1, "Centred cosine 0.93 with the life-story dimension. (Marriage as LAW - annulment, the Family Code - is a different, new dimension.)"),
    "mentors_and_legal_lineage": ("absorbed", 1, "Centred cosine 0.78 with the life-story dimension; the recommended level has no stable split inside it."),
    "faith_journey": ("carried, matcher rewritten", 23, "Same direction, wrong members (the Phase 3 case): 0.80 to the scripture-and-prayer dimension, 22 of its 298 matcher documents inside it. The v1 matcher fires on any mention of God or faith; the members are the Gospel/prayer chapters."),
    "early_life_sampaloc": ("absorbed", 1, "Centred cosine 0.92 with the life-story dimension."),
    "jbc_discernment_and_appointment": ("redefined as", 33, "The v1 definition is the Chief Justice's own seven JBC rejections (a personal story); the v1 matcher keys on 'jbc' and so catches the Council's institutional documents (0.83). It is redefined to what its members are; the personal story ('Seven Rejections') sits in the scripture-and-prayer dimension."),
    "eulogies_and_passing": ("absorbed", 1, "Centred cosine 0.86 with the life-story dimension."),
    "friendships_and_civic_circles": ("absorbed", 1, "Centred cosine 0.86 with the life-story dimension (0.80 with business leaders and philanthropy, where its 8 funder documents sit)."),
    "honors_received": ("dropped", None, "Not established: 24 matcher documents, of which only 10 (42%) mention an honour at all (Phase 3); they scatter (5 life story, 4 tributes, 3 how-the-Court-decides). Honours are an incident inside tributes and life story, not a subject."),
    "flp_scholarship_programs": ("absorbed", 15, "Centred cosine 0.89 with the Foundation dimension."),
    "museum_for_liberty_and_prosperity": ("absorbed", 15, "Centred cosine 0.90 with the Foundation dimension; 20 matcher documents."),
    "flp_donors_and_partners": ("absorbed", 15, "Centred cosine 0.89 with the Foundation dimension (0.79 with business leaders and philanthropy)."),
    "lawyer_ethics_initiative": ("dropped", None, "No cluster: no dimension within centred cosine 0.5; 47 matcher documents at cohesion 0.23 vs 0.17 random."),
    "ai_and_technology": ("redefined as", 12, "Centred cosine 0.65; the coherent subject is broader than AI - DNA and the bio-age, the internet and data, then AI."),
    "global_geopolitics": ("redefined as", 17, "Centred cosine 0.77; 26 of its 83 matcher documents are 90% of the Trump/US-Supreme-Court dimension. The ICJ half is an arbitration fragment of the sea-dispute dimension."),
    "philippine_political_landscape": ("redefined as", 7, "Centred cosine 0.73 with the presidential-power dimension (GMA, martial law, EDSA); its Marcos-administration part is the Marcos-Robredo dimension."),
    "robot_identity_meta": ("moved to the router", None, "0 documents, 0 chunks: an intent, not a subject. Already an LLM-router intent (router_prompt.md) and a regex input gate (app/retrieval.py input_gate)."),
}

# extra candidate dimensions evaluated beside the 33 (key -> metadata); the matcher terms live in ce9_edits.py
EXTRA_DIMS = {
    "x:death_penalty": dict(id="death_penalty_and_echegaray", name="The Death Penalty and the Echegaray Reflection",
                            pool="“leo echegaray” 5/5 and “people v. echegaray” 5/5 pool documents inside one cluster; Phase 3 coherence 0.34 vs null p95 0.23; a 13-document fragment at the fine level",
                            definition="The Chief Justice's writing on capital punishment: the Echegaray case, the 2006 abolition of the death penalty and the conscience-versus-institution distinction."),
}

STATUS_OVERRIDE = {
    "x:death_penalty": "Dimension holds - marginal (P@3 0.57 < 0.60 bar; separable only while criminal law's matcher omits its terms)",
    6: "Dimension holds - marginal (P@3 0.61; matcher covers the libel/cybercrime part of its cluster, centroid 0.61 of the cluster's)",
}        # cluster -> status string; default is computed
NOT_PROPOSED = []           # filled by the assembler from measurements + the list in ce9_notes below
NOTES = {}
THRESHOLDS = {}

THRESH_MERGE = 0.75      # TOPIC_MERGE_COSINE proposed (centred)
THRESH_ASSIGN = 0.31     # TOPIC_ASSIGN_MIN_COSINE proposed (centred, best-chunk, global)
