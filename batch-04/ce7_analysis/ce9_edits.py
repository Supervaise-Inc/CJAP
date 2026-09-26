# CE-9 explicit hand edits to the greedy readable matchers (read by ce9_13_finalize.py). Every edit is visible here.
# DROP: terms the greedy pass chose because they are precise on the cluster's documents, but which are incidental co-occurrences, not the subject
#       (checked in context: 'noon' = the hour of an oath; 'fisherman' = a parable; 'levy' = coconut levy funds; 'unexpired' = an unexpired card; 'camera' = a courtroom camera; ...).
DROP = {
    1: ["munich", "donna may lina"],
    2: ["sbn"],                                        # abbreviation of 'Sandiganbayan' (kept as the spelled-out word via TRY_ADD)
    5: ["political patronage", "marcos burial at libingan ng mga bayani"],
    7: ["noon", "rebellion"],                     # 'rebellion' is also a criminal-law word (union P@3 0.57 with it, 0.62 without)
    9: ["katarungan", "people v. genosa"],
    12: ["camera"],
    13: ["fisherman"],
    15: ["tan yan", "kee", "business law", "emerson gregorio", "joel emerson"],
    18: ["unexpired"],
    23: ["sins"],
    26: ["data collection"],
    27: ["levy"],
    32: ["corporate ethics"],
}
# TRY_ADD: defining vocabulary taken from each cluster's own top TF-IDF terms / lifted keywords / entities (cache/ce9_candidate_side.json, ce9_11_terms.py output),
#          tried IN THIS ORDER; a term is admitted only if the union keeps caught <= 1.9x the cluster AND >= 65% of caught docs in the dimension's top-3 neighbourhood AND it adds >= 2 cluster docs.
TRY_ADD = {
    1: ["far eastern university", "eulogy", "pope", "archbishop", "jovito r. salonga", "church", "faith"],
    2: ["sandiganbayan", "plunder", "probable cause", "napoles", "prosecution", "accused", "conviction", "acquittal", "arrest", "icc", "rome statute"],
    3: ["west philippine sea", "south china sea", "arbitral award", "eez", "nine-dash line", "scarborough", "permanent court of arbitration", "icj", "sovereignty", "china"],
    4: ["contracts", "employment", "investors", "mining", "regalian doctrine", "national labor relations commission", "security of tenure", "unjust enrichment", "labor"],
    5: ["judicial independence", "anti-terrorism act", "separation of powers", "decision-writing style"],
    6: ["revised penal code", "death penalty", "libel", "cyberlibel", "maria ressa", "warrantless", "rape", "arraignment", "evidence"],
    7: ["martial law", "edsa", "estrada", "arroyo", "marawi", "people power", "revolutionary government"],
    8: ["comelec", "pcos", "smartmatic", "election", "automated", "canvassing", "disenfranchisement"],
    9: ["centenary", "retirement", "toast", "testimonial", "tribute", "honor"],
    10: ["judicial reform", "backlog", "apjr", "trial courts", "salary standardization law", "justice on wheels", "davide watch", "judges"],
    11: ["party-list", "charter change", "dynasties", "constitutional convention", "banat v. comelec", "congress"],
    12: ["dna", "cloning", "internet", "artificial intelligence", "digital", "smartphone", "technology", "stem cell"],
    13: ["economy", "taxes", "wages", "vat", "economic growth", "asean integration", "inflation"],
    14: ["impeachment", "articles of impeachment", "house of representatives", "high crimes", "sara duterte", "corona"],
    15: ["flp", "foundation for liberty and prosperity", "scholars", "dissertation", "scholarship", "tan yan kee foundation", "museum for liberty and prosperity", "prosperity fund"],
    16: ["budget", "dap", "pdaf", "dollar deposits", "deposits", "malampaya fund", "senate blue ribbon committee", "corona"],
    17: ["trump", "donald trump", "scotus", "biden", "electoral college", "us supreme court", "kagan"],
    18: ["ombudsman", "comelec", "commission on audit", "civil service commission", "ad interim", "independent commission", "coa"],
    19: ["liberty and prosperity", "rule of law", "poverty", "twin beacons", "social justice"],
    20: ["robredo", "leni robredo", "ppcrv", "bongbong marcos", "presidential electoral tribunal", "canvass", "election protest", "pacquiao"],
    21: ["bangsamoro", "milf", "peace process", "bangsamoro basic law", "moro islamic liberation front"],
    22: ["sereno", "carpio", "chief justice", "duterte appointees", "senior justices", "jbc nominees", "retirement"],
    23: ["gospel", "jesus", "christ", "prayer", "holy spirit", "apostles", "lord", "faith"],
    24: ["philanthropy", "tycoon", "philanthropist", "csr", "jollibee", "metrobank", "george ty", "foundation"],
    25: ["asean law association", "governing council", "asean", "ala"],
    26: ["data privacy", "privacy", "saln", "ethical standards", "cpra", "right to privacy", "public officials"],
    27: ["ill-gotten wealth", "pcgg", "sequestration", "forfeiture", "marcoses", "estate of marcos v. republic"],
    28: ["poe", "grace poe", "natural-born", "citizenship", "foundlings", "residency", "domicile"],
    29: ["psychological incapacity", "annulment", "divorce", "nullity", "marriage"],
    30: ["bar exam", "bar exams", "topnotchers", "legal education", "legal education board", "bar examinations"],
    32: ["corporate governance", "independent directors", "governance", "shareholders", "integrity", "european chamber of commerce"],
    33: ["judicial and bar council", "jbc", "jbc chair", "nominees", "ex-officio", "vacancy", "shortlist"],
}
ADD = {7: ["coup", "marawi", "maute group", "lagman vs medialdea", "constitutional authoritarianism", "revolutionary government"]}      # readable topical terms (coup attempts, the Marawi siege and the martial-law case, revolutionary government); chosen from probe variants, evaluated below like every other term
EXTRA = {"x:death_penalty": ["death penalty", "echegaray", "leo echegaray"]}
