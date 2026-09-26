"""
Build a curated topic map for the CJ Panganiban corpus.

Reads every generated .json under corpus/{columns,books,speeches,biography}/ (1,290 documents)
and writes:
  - corpus/voice/topic_map.json   — taxonomy + per-topic stats
  - reports/topic_map_report.json — coverage / unmatched-docs report

The taxonomy (v2, CE-10) is a curated list of 30 topics with matcher rules
(case-insensitive substring matches against title, primary_topics,
sub_topics, keywords, and entity names). Each topic carries a default
register and wit calibration from PROJECT.md §9.

Each document is scored against every topic; the top scorers become the
doc's primary topic_paths, the next tier become secondary. The same
matcher data is used by `apply_topic_paths.py` to backfill the per-doc
.json files.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = PROJECT_ROOT / "corpus"
VOICE_DIR = CORPUS_ROOT / "voice"
REPORTS_DIR = PROJECT_ROOT / "reports"
sys.path.insert(0, str(PROJECT_ROOT))
import config  # noqa: E402  (CORPUS_MEAN_PATH)

THEME_LABELS = {
    "A": "Liberty and Rule of Law",
    "B": "Prosperity and Economic Philosophy",
    "C": "Biographical and Personal",
    "D": "FLP Mission and Foundation",
    "E": "Signature Current Events Commentary",
}

# Default register by theme — per PROJECT.md §9.
THEME_REGISTER = {
    "A": ("ceremonial_doctrinal", "sparing, diplomatic"),
    "B": ("case_analytical_with_openers", "professional warmth"),
    "C": ("testimonial", "gentle, self-deprecating"),
    "D": ("ceremonial_with_humor", "freely, head-table style"),
    "E": ("reflective_pedagogical", "thoughtful, warm"),
}


# -- Taxonomy ----------------------------------------------------------------
#
# Each topic is a dict with:
#   id              : snake_case slug
#   display_name    : human readable
#   definition      : 1-2 sentence semantic anchor
#   tier            : anchor | core | subordinate | meta
#   theme_anchor    : "A".."E" or "META"
#   default_register: from THEME_REGISTER or topic-specific override
#   wit_calibration : same
#   matchers        : { keywords: list[str], entities: list[str] }
#     matched against title + primary_topics + sub_topics + keywords +
#     entity names + register_markers (all lowercased substring tests)
#
# Topic scoring: each unique matcher term that appears in the doc adds 1 to
# the score; documents are assigned primary topic_paths for their top 2
# scorers and secondary for the next 3.

TAXONOMY: list[dict[str, Any]] = [
    # ===== Anchors (2) =====
    {
        "id": "foundation_for_liberty_and_prosperity",
        "display_name": "The Foundation for Liberty and Prosperity and Its Benefactors",
        "definition": "The Foundation's work and people: scholarships and dissertation fellows, its museum and Prosperity Fund, and the business leaders and donors who fund it.",
        "tier": "anchor",
        "theme_anchor": "D",
        "matchers": {
            "keywords": [
                "rvr", "csr", "philanthropy", "philanthropist", "busog lusog", "dissertation writing", "corporate social responsibility",
            ],
            "entities": [
                "jollibee", "george ty", "flp scholars society", "tan yan kee foundation", "museum for liberty and prosperity",
            ],
        },
    },
    {
        "id": "twin_beacons_doctrine",
        "display_name": "Liberty and Prosperity: the Twin Beacons",
        "definition": "The Chief Justice's core philosophy that liberty and prosperity depend on each other, and that both rest on the rule of law and social justice.",
        "tier": "anchor",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "social order", "twin beacons", "liberty prosperity",
            ],
            "entities": [],
        },
    },
    # ===== Core (13) =====
    {
        "id": "life_story_family_school_and_church",
        "display_name": "Life Story: Family, School and Church",
        "definition": "The Chief Justice's own life: his family, his schooling and mentors, his church and community life, and the eulogies and tributes he gives to people who shaped him.",
        "tier": "core",
        "theme_anchor": "C",
        "matchers": {
            "keywords": [
                "eulogy", "sampaloc", "jovito r. salonga",
            ],
            "entities": [
                "sylvia lina", "yale law school", "mapa high school", "far eastern university", "feu institute of law", "rotary club of manila",
            ],
        },
    },
    {
        "id": "criminal_trials_and_prosecutions",
        "display_name": "Criminal Trials, Prosecutions and the ICC",
        "definition": "How major criminal cases actually proceed in the Philippines: bail, probable cause, the Sandiganbayan and the plunder and pork-barrel trials, and the International Criminal Court's case against Duterte.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "bail", "plunder", "napoles", "probable cause", "moral turpitude", "warrant of arrest",
            ],
            "entities": [
                "mark jimenez", "fatou bensouda", "icc pre-trial chamber",
            ],
        },
    },
    {
        "id": "international_law_disputes",
        "display_name": "International Law: the West Philippine Sea and Arbitration",
        "definition": "The Philippines' sea dispute with China: the 2016 arbitral award, UNCLOS, the exclusive economic zone and the nine-dash line, and what international arbitration can and cannot enforce.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "icj", "west philippine sea",
            ],
            "entities": [
                "unclos", "un charter", "mutual defense treaty",
            ],
        },
    },
    {
        "id": "property_contracts_and_economic_rights",
        "display_name": "Property, Contracts and Labor Rights",
        "definition": "Supreme Court decisions on ownership, contracts, natural resources, investment and labor, read for what they mean for livelihoods and business.",
        "tier": "core",
        "theme_anchor": "B",
        "matchers": {
            "keywords": [
                "investors", "monopolies", "res judicata", "voting shares", "agan v. piatco",
            ],
            "entities": [
                "labor code", "department of environment and natural resources",
            ],
        },
    },
    {
        "id": "presidential_power_martial_law_people_power",
        "display_name": "Presidential Power, Martial Law and People Power",
        "definition": "The limits of presidential power in a crisis: martial law and rebellion, EDSA and the presidencies of Estrada and Arroyo.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "coup", "marawi", "romulo neri", "constitutional authoritarianism", "lagman vs medialdea",
            ],
            "entities": [
                "maute group", "edsa shrine",
            ],
        },
    },
    {
        "id": "elections_and_automated_voting",
        "display_name": "Elections and Automated Voting",
        "definition": "How Philippine elections are run and litigated: the Commission on Elections, precinct-count optical scanners and the disputes over automation.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ballots", "comelec's",
            ],
            "entities": [],
        },
    },
    {
        "id": "judicial_reform",
        "display_name": "Judicial Reform and Court Delay",
        "definition": "Reforming the courts: the Action Program for Judicial Reform, case backlogs, judges' pay and how to speed up justice.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "zero backlog", "judicial compensation",
            ],
            "entities": [
                "action program for judicial reform",
            ],
        },
    },
    {
        "id": "party_list_charter_change_and_dynasties",
        "display_name": "Party-List, Charter Change and Political Dynasties",
        "definition": "How Congress is chosen and the Constitution is amended: the party-list system, Charter change and political dynasties.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "con-ass", "dynasty", "charter change", "party-list seats",
            ],
            "entities": [
                "party-list law",
            ],
        },
    },
    {
        "id": "science_technology_and_the_law",
        "display_name": "Science, Technology and the Law",
        "definition": "How courts and lawyers should deal with new science: DNA and genetics, cloning, the internet and artificial intelligence.",
        "tier": "core",
        "theme_anchor": "E",
        "matchers": {
            "keywords": [
                "bio-age", "genetic", "smartphone", "artificial intelligence",
            ],
            "entities": [],
        },
    },
    {
        "id": "impeachment_accountability",
        "display_name": "Impeachment",
        "definition": "The impeachment process from the House to the Senate: its rules and limits, and the Corona and Sara Duterte cases.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "senate trial", "articles of impeachment", "francisco v. house of representatives",
            ],
            "entities": [
                "nixon", "sara duterte",
            ],
        },
    },
    {
        "id": "public_funds_budget_and_bank_evidence",
        "display_name": "Public Funds, the Budget and Bank Evidence",
        "definition": "How public money is spent and traced: the budget, the DAP and PDAF rulings, and bank deposits used as evidence of corruption.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "amla", "malampaya fund",
            ],
            "entities": [
                "psbank", "general appropriations act", "senate blue ribbon committee",
            ],
        },
    },
    {
        "id": "us_supreme_court_and_american_politics",
        "display_name": "The US Supreme Court and American Politics",
        "definition": "Commentary on the American presidency and the US Supreme Court, from Trump to Biden and the electoral college, and what they teach the Philippines.",
        "tier": "core",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "kagan", "donald",
            ],
            "entities": [],
        },
    },
    {
        "id": "faith_journey",
        "display_name": "Faith: Scripture, Prayer and the Gospel",
        "definition": "Reflections on scripture and prayer, on Jesus and the Gospel and on the Bukas Loob sa Diyos community, drawn mainly from the faith-themed books.",
        "tier": "core",
        "theme_anchor": "C",
        "matchers": {
            "keywords": [
                "gospel", "apostles",
            ],
            "entities": [
                "luke",
            ],
        },
    },
    # ===== Subordinate (15) =====
    {
        "id": "how_the_supreme_court_decides",
        "display_name": "How the Supreme Court Decides",
        "definition": "How the Court reasons and writes its decisions, and why the judiciary's independence from the other branches matters.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ata", "judicial activism", "decision-writing style",
            ],
            "entities": [],
        },
    },
    {
        "id": "libel_and_cybercrime",
        "display_name": "Libel and Cybercrime",
        "definition": "Criminal libel and cybercrime cases: the Maria Ressa cyberlibel prosecution, libel of public figures online, and the Cybercrime Prevention Act.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "libel", "cyberlibel", "cybercrime",
            ],
            "entities": [
                "maria ressa",
            ],
        },
    },
    {
        "id": "judiciary_milestones_and_tributes",
        "display_name": "The Judiciary's Milestones and Tributes",
        "definition": "Celebrations of the judiciary and of the people in it: the Supreme Court centenary, retirements, book launches, honors and tributes to fellow justices.",
        "tier": "subordinate",
        "theme_anchor": "C",
        "matchers": {
            "keywords": [
                "toast", "toobin",
            ],
            "entities": [
                "centenary executive committee",
            ],
        },
    },
    {
        "id": "economy_taxes_and_prosperity",
        "display_name": "The Economy, Taxes and Wages",
        "definition": "Economic policy seen through a lawyer's eyes: growth, jobs, taxes and wages, and what makes nations prosper.",
        "tier": "subordinate",
        "theme_anchor": "B",
        "matchers": {
            "keywords": [
                "minimum wage", "inclusive growth",
            ],
            "entities": [
                "asean integration",
            ],
        },
    },
    {
        "id": "death_penalty_and_echegaray",
        "display_name": "The Death Penalty and the Echegaray Reflection",
        "definition": "The Chief Justice's writing on capital punishment: the Echegaray case, the 2006 abolition of the death penalty and the conscience-versus-institution distinction.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "echegaray",
            ],
            "entities": [
                "death penalty",
            ],
        },
    },
    {
        "id": "independent_commissions_and_appointments",
        "display_name": "Independent Commissions and Appointments",
        "definition": "The constitutional commissions and the Ombudsman: how their officials are appointed, how long they serve and how independent they really are.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ad interim", "independent commission",
            ],
            "entities": [
                "ombudsman law",
            ],
        },
    },
    {
        "id": "bangsamoro_peace_process",
        "display_name": "The Bangsamoro Peace Process",
        "definition": "The peace agreements with the MILF, the Bangsamoro Basic Law and the question of whether they fit the Constitution.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "peace process", "armed conflict",
            ],
            "entities": [
                "moa-ad",
            ],
        },
    },
    {
        "id": "marcos_robredo_election_contest",
        "display_name": "The Marcos-Robredo Election Contest",
        "definition": "The vice-presidential protest of 2016 and the 2022 campaign that followed: canvassing, protests and what the results meant.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "ppcrv's", "robredo",
            ],
            "entities": [],
        },
    },
    {
        "id": "supreme_court_vacancies_and_chief_justiceship",
        "display_name": "Supreme Court Vacancies and the Chief Justiceship",
        "definition": "Who sits on the Court and who leads it: retirements, appointments by President Duterte and the succession to the chief justiceship.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "jbc nominees", "senior justices", "duterte appointees", "cj teresita j. leonardo-de castro",
            ],
            "entities": [
                "cj renato corona",
            ],
        },
    },
    {
        "id": "asean_law_association",
        "display_name": "The ASEAN Law Association",
        "definition": "The regional association of lawyers and judges the Chief Justice helped lead, and the rule of law in Southeast Asia.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [],
            "entities": [
                "ala philippines",
            ],
        },
    },
    {
        "id": "ill_gotten_wealth_and_the_pcgg",
        "display_name": "Ill-Gotten Wealth and the PCGG",
        "definition": "The recovery of wealth amassed under Marcos: sequestration, forfeiture and the Sandiganbayan's rulings.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "luisita", "marcoses", "sequestration", "estate of marcos v. republic",
            ],
            "entities": [],
        },
    },
    {
        "id": "bar_exam_and_legal_education",
        "display_name": "The Bar Exam and Legal Education",
        "definition": "How lawyers are trained and admitted: the bar examinations, legal education and the profession's duties.",
        "tier": "subordinate",
        "theme_anchor": "D",
        "matchers": {
            "keywords": [
                "passers",
            ],
            "entities": [
                "legal education board",
            ],
        },
    },
    {
        "id": "citizenship_and_residency_grace_poe",
        "display_name": "Citizenship and Residency: the Grace Poe Case",
        "definition": "Who counts as a natural-born citizen (foundlings, dual citizens and residency), argued through the Grace Poe case.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "poe's", "naturalized",
            ],
            "entities": [],
        },
    },
    {
        "id": "marriage_annulment_and_the_family_code",
        "display_name": "Marriage, Annulment and the Family Code",
        "definition": "How the law treats marriage: psychological incapacity, nullity, divorce and the Family Code.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [],
            "entities": [
                "family code",
            ],
        },
    },
    {
        "id": "jbc_discernment_and_appointment",
        "display_name": "The Judicial and Bar Council",
        "definition": "How judges are nominated: the Council's role, its rules and the shortlist for each vacancy.",
        "tier": "subordinate",
        "theme_anchor": "A",
        "matchers": {
            "keywords": [
                "jbc's", "ex-officio", "jbc chair",
            ],
            "entities": [],
        },
    },
]


# -- META intents (CE-10 Step 4) ----------------------------------------------
#
# robot_identity_meta is an INTENT, not a corpus topic: it holds 0 documents and 0 chunks, is routed by the
# input gate / router (retrieval.input_gate, answer_pipeline.force_meta_routing), and must never get a centroid.
# It is kept OUT of TAXONOMY and emitted under topic_map['intents'] so the legacy pipeline's topic_data node —
# the persona instruction the composer reads for identity probes — is unchanged.

META_INTENTS: list[dict[str, Any]] = [
    {
        "id": "robot_identity_meta",
        "display_name": "Robot Identity (META)",
        "definition": "Questions about whether this is the real CJP, an AI, a robot, or how it works. Answered fully in persona as Chief Justice Panganiban himself — gracious, lightly amused, never describing himself as an AI, robot, machine, or rendering (the voice card's Identity rule).",
        "tier": "meta",
        "theme_anchor": "META",
        "default_register_override": ("gracious_in_persona", "gentle, self-deprecating"),
        "matchers": {
            "keywords": [
                "are you ai",
                "are you a robot",
                "are you real",
                "is this really cjp",
                "how do you work",
                "are you panganiban",
                "robot rendering",
                "ai conversation robot",
            ],
            "entities": [],
        },
    },
]


# -- Matching engine ---------------------------------------------------------

def _doc_haystack(doc: dict[str, Any]) -> str:
    """Build a single lowercased searchable string from doc fields."""
    parts: list[str] = [doc.get("title", ""), doc.get("one_paragraph_summary", "")]
    for k in ("primary_topics", "sub_topics", "keywords", "register_markers"):
        for item in doc.get(k, []) or []:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("phrase", "")))
                parts.append(str(item.get("summary", "")))
    ent = doc.get("entities", {}) or {}
    for k in ("people", "institutions", "cases", "laws_treaties", "events"):
        for item in ent.get(k, []) or []:
            if isinstance(item, str):
                parts.append(item)
    return " || ".join(p for p in parts if p).lower()


_KW_CACHE: dict[str, re.Pattern[str]] = {}


def _kw_pattern(term: str) -> re.Pattern[str]:
    """Compile a word-boundary regex for a matcher term (cached)."""
    if term not in _KW_CACHE:
        _KW_CACHE[term] = re.compile(r"\b" + re.escape(term.lower()) + r"\b")
    return _KW_CACHE[term]


def score_topic(topic: dict[str, Any], haystack: str) -> int:
    score = 0
    for kw in topic["matchers"]["keywords"]:
        if _kw_pattern(kw).search(haystack):
            score += 1
    for ent in topic["matchers"].get("entities", []):
        if _kw_pattern(ent).search(haystack):
            score += 1
    return score


# -- Aggregation -------------------------------------------------------------

def load_docs() -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    for p in sorted(CORPUS_ROOT.glob("columns/**/*.json")):
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    for p in sorted(CORPUS_ROOT.glob("speeches/**/*.json")):
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    for p in sorted(CORPUS_ROOT.glob("biography/**/*.json")):
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    # CE-10 Step 0a: books/** was never globbed, so layer 2 never saw a book chapter (299 of 1,290 docs).
    for p in sorted(CORPUS_ROOT.glob("books/**/*.json")):
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    return out


def _doc_year(d: dict[str, Any]) -> int | None:
    """Year of a document: its `year` key if present, else the year in `date` (the corpus JSONs carry `date` only;
    v1 indexed d["year"] directly). Jan-1 placeholder dates still give the right YEAR; date precision is untouched."""
    y = d.get("year")
    if y:
        return int(y)
    m = re.match(r"(\d{4})", str(d.get("date") or ""))
    return int(m.group(1)) if m else None


def _corpus_mean_sha256() -> str:
    """The map records the scale its centroids live on. The mean file must already exist (build_corpus_mean.py); no fallback."""
    p = Path(config.CORPUS_MEAN_PATH)
    if not p.exists():
        raise FileNotFoundError(f"{p} missing: run scripts/build_corpus_mean.py before rebuilding the topic map")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_topic_map(docs: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    # Score every doc against every topic.
    doc_scores: dict[str, dict[str, int]] = {}
    for _, doc in docs:
        hs = _doc_haystack(doc)
        doc_scores[doc["id"]] = {t["id"]: score_topic(t, hs) for t in TAXONOMY}

    topics_out: dict[str, dict[str, Any]] = {}

    for topic in TAXONOMY:
        matched = [
            doc for _, doc in docs if doc_scores[doc["id"]][topic["id"]] > 0
        ]
        doc_ids = [d["id"] for d in matched]
        years = sorted({y for y in (_doc_year(d) for d in matched) if y})
        dates = sorted({d["date"] for d in matched if d.get("date")})
        date_range = [dates[0], dates[-1]] if dates else []

        type_dist: Counter[str] = Counter(d["type"] for d in matched)
        theme_dist: Counter[str] = Counter(d["theme"] for d in matched)

        # Aggregate signature phrases across matched docs, with frequency.
        phrase_counter: Counter[str] = Counter()
        phrase_docs: dict[str, set[str]] = {}
        for d in matched:
            for sp in d.get("signature_phrases", []) or []:
                if isinstance(sp, dict):
                    phrase = (sp.get("phrase") or "").strip()
                else:
                    phrase = str(sp).strip()
                if not phrase or len(phrase) > 200:
                    continue
                phrase_counter[phrase] += 1
                phrase_docs.setdefault(phrase, set()).add(d["id"])

        top_phrases = [
            {
                "phrase": phrase,
                "count": count,
                "doc_ids": sorted(phrase_docs[phrase]),
            }
            for phrase, count in phrase_counter.most_common(8)
        ]

        # Aggregate entities.
        people: Counter[str] = Counter()
        institutions: Counter[str] = Counter()
        cases: Counter[str] = Counter()
        for d in matched:
            ent = d.get("entities", {}) or {}
            for p in ent.get("people", []) or []:
                if isinstance(p, str):
                    people[p.split("(")[0].strip()] += 1
            for i in ent.get("institutions", []) or []:
                if isinstance(i, str):
                    institutions[i.split("(")[0].strip()] += 1
            for c in ent.get("cases", []) or []:
                if isinstance(c, str):
                    cases[c.split("(")[0].strip()] += 1

        # Register defaults.
        default_register = topic.get("default_register_override") or THEME_REGISTER.get(
            topic["theme_anchor"], ("doctrinal-formal", "sparing")
        )

        topics_out[topic["id"]] = {
            "id": topic["id"],
            "display_name": topic["display_name"],
            "definition": topic["definition"],
            "tier": topic["tier"],
            "theme_anchor": topic["theme_anchor"],
            "default_register": default_register[0],
            "wit_calibration": default_register[1],
            "doc_count": len(doc_ids),
            "doc_ids": sorted(doc_ids),
            "date_range": date_range,
            "year_range": [years[0], years[-1]] if years else [],
            "type_distribution": dict(type_dist),
            "theme_distribution": dict(theme_dist),
            "top_signature_phrases": top_phrases,
            "top_people": [k for k, _ in people.most_common(6)],
            "top_institutions": [k for k, _ in institutions.most_common(6)],
            "top_cases": [k for k, _ in cases.most_common(4)],
            "matchers": topic["matchers"],
        }

    intents_out: dict[str, dict[str, Any]] = {}
    for it in META_INTENTS:
        reg = it.get("default_register_override") or THEME_REGISTER.get(it["theme_anchor"], ("doctrinal-formal", "sparing"))
        intents_out[it["id"]] = {
            "id": it["id"], "kind": "intent", "display_name": it["display_name"], "definition": it["definition"],
            "tier": it["tier"], "theme_anchor": it["theme_anchor"], "default_register": reg[0], "wit_calibration": reg[1],
            "doc_count": 0, "doc_ids": [], "date_range": [], "year_range": [], "type_distribution": {}, "theme_distribution": {},
            "top_people": [], "top_institutions": [], "top_cases": [], "matchers": it["matchers"],
        }

    return {
        "schema_version": "2.0",
        "taxonomy_version": 2,
        "scale": "centred",
        "corpus_mean": {"path": "data/index/corpus_mean.npy", "sha256": _corpus_mean_sha256()},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_stats": {
            "n_docs": len(docs),
            "n_topics": len(TAXONOMY),
            "doc_type_distribution": dict(
                Counter(d["type"] for _, d in docs)
            ),
            "theme_distribution": dict(
                Counter(d["theme"] for _, d in docs)
            ),
            "year_distribution": dict(
                sorted(Counter(_doc_year(d) for _, d in docs).items(), key=lambda kv: (kv[0] is None, kv[0] or 0))
            ),
        },
        "themes": {
            letter: {
                "letter": letter,
                "label": THEME_LABELS[letter],
                "default_register": THEME_REGISTER[letter][0],
                "wit_calibration": THEME_REGISTER[letter][1],
            }
            for letter in "ABCDE"
        },
        "topics": topics_out,
        "intents": intents_out,
    }, doc_scores


# -- Per-doc topic_paths derivation -----------------------------------------

def derive_topic_paths(
    doc_id: str, doc_scores: dict[str, dict[str, int]],
    primary_n: int = 2, secondary_n: int = 3,
) -> dict[str, list[str]]:
    """Pick top topics for one doc — primary (≥2 keyword hits), secondary (≥1).

    Returns {primary: [...], secondary: [...]}.
    """
    scores = doc_scores.get(doc_id, {})
    # Sort topics by score desc, then by tier (anchor > core > subordinate > meta).
    tier_rank = {"anchor": 0, "core": 1, "subordinate": 2, "meta": 9}
    by_tier = {t["id"]: tier_rank.get(t["tier"], 5) for t in TAXONOMY}
    ranked = sorted(
        ((tid, sc) for tid, sc in scores.items() if sc > 0),
        key=lambda kv: (-kv[1], by_tier[kv[0]]),
    )
    primary: list[str] = []
    secondary: list[str] = []
    for tid, sc in ranked:
        if sc >= 2 and len(primary) < primary_n:
            primary.append(tid)
        elif len(secondary) < secondary_n:
            secondary.append(tid)
        if len(primary) >= primary_n and len(secondary) >= secondary_n:
            break
    # If no topic crossed the ≥2 threshold, promote the strongest scorer
    # to primary so every doc has at least one route.
    if not primary and ranked:
        primary = [ranked[0][0]]
        secondary = [tid for tid, _ in ranked[1 : 1 + secondary_n]]
    return {"primary": primary, "secondary": secondary}


# -- Write outputs -----------------------------------------------------------

def write_topic_map(tm: dict[str, Any]) -> Path:
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VOICE_DIR / "topic_map.json"
    out_path.write_text(
        json.dumps(tm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return out_path


def matcher_health_check(
    tm: dict[str, Any],
    doc_scores: dict[str, dict[str, int]],
    docs: list[tuple[Path, dict[str, Any]]],
    over_broad_frac: float = 0.25,
    near_dup_jaccard: float = 0.50,
    dominant_term_frac: float = 0.80,
) -> list[dict[str, Any]]:
    """
    Per PLAN-0007 §4 — flag taxonomy issues that should trigger curator
    review. Returns a list of warning dicts; also prints them.

    Categories:
      - zero-coverage  : non-meta topic with 0 docs
      - over-broad     : topic claims > over_broad_frac of corpus
      - near-duplicate : topic pair with Jaccard overlap > near_dup_jaccard
      - dominant-term  : within a topic, ≥ dominant_term_frac of its docs
                         match on a single matcher term
    """
    warnings_out: list[dict[str, Any]] = []
    topics = tm["topics"]
    n_docs = len(docs)
    over_broad_cutoff = max(1, int(over_broad_frac * n_docs))

    # 1. Zero-coverage and over-broad
    for tid, t in topics.items():
        if t["tier"] == "meta":
            continue
        if t["doc_count"] == 0:
            warnings_out.append(
                {"kind": "zero-coverage", "topic": tid,
                 "msg": f"{tid} has 0 docs; consider loosening matchers or "
                        f"retiring (PLAN-0007 §3b/§3d)"}
            )
        elif t["doc_count"] > over_broad_cutoff:
            warnings_out.append(
                {"kind": "over-broad", "topic": tid, "doc_count": t["doc_count"],
                 "msg": f"{tid} claims {t['doc_count']} of {n_docs} docs "
                        f"({t['doc_count']/n_docs:.0%}); consider tightening "
                        f"matchers (PLAN-0007 §3c)"}
            )

    # 2. Near-duplicate topic pairs
    topic_ids = list(topics.keys())
    for i, a in enumerate(topic_ids):
        a_set = set(topics[a]["doc_ids"])
        if not a_set:
            continue
        for b in topic_ids[i + 1 :]:
            b_set = set(topics[b]["doc_ids"])
            if not b_set:
                continue
            intersection = a_set & b_set
            union = a_set | b_set
            if not union:
                continue
            jaccard = len(intersection) / len(union)
            if jaccard > near_dup_jaccard:
                warnings_out.append(
                    {"kind": "near-duplicate", "topics": [a, b],
                     "jaccard": round(jaccard, 3),
                     "msg": f"{a} and {b} overlap (Jaccard={jaccard:.2f}); "
                            f"consider merge or matcher-disjoint refactor "
                            f"(PLAN-0007 §3e)"}
                )

    # 3. Dominant-term per topic
    docs_by_id = {doc["id"]: doc for _, doc in docs}
    for tid, t in topics.items():
        members = t["doc_ids"]
        if len(members) < 3:
            continue  # Too small for the dominance ratio to mean much.
        all_terms = list(t["matchers"]["keywords"]) + list(
            t["matchers"].get("entities", [])
        )
        for term in all_terms:
            pat = _kw_pattern(term)
            hits = sum(
                1 for mid in members
                if mid in docs_by_id and pat.search(_doc_haystack(docs_by_id[mid]))
            )
            frac = hits / len(members)
            if frac >= dominant_term_frac:
                warnings_out.append(
                    {"kind": "dominant-term", "topic": tid, "term": term,
                     "fraction": round(frac, 3),
                     "msg": f"{tid}: '{term}' fires on {hits}/{len(members)} "
                            f"({frac:.0%}) of its docs; topic depends on one "
                            f"term — consider adding diversifying matchers"}
                )

    return warnings_out


def write_coverage_report(
    docs: list[tuple[Path, dict[str, Any]]],
    doc_scores: dict[str, dict[str, int]],
    health_warnings: list[dict[str, Any]] | None = None,
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "topic_map_report.json"
    rows = []
    unmatched: list[str] = []
    for _, doc in docs:
        scores = doc_scores[doc["id"]]
        topic_paths = derive_topic_paths(doc["id"], doc_scores)
        nonzero = sum(1 for v in scores.values() if v > 0)
        if not topic_paths["primary"]:
            unmatched.append(doc["id"])
        rows.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "theme": doc["theme"],
                "topics_hit": nonzero,
                "primary": topic_paths["primary"],
                "secondary": topic_paths["secondary"],
                "top_scores": dict(
                    sorted(scores.items(), key=lambda kv: -kv[1])[:5]
                ),
            }
        )
    out_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "n_docs": len(docs),
                "unmatched_docs": unmatched,
                "health_warnings": health_warnings or [],
                "per_doc": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return out_path


def main() -> int:
    docs = load_docs()
    print(f"[load] {len(docs)} corpus documents")
    tm, doc_scores = build_topic_map(docs)
    health_warnings = matcher_health_check(tm, doc_scores, docs)
    tm_path = write_topic_map(tm)
    rep_path = write_coverage_report(docs, doc_scores, health_warnings)
    n_topics = len(tm["topics"])
    avg_docs = sum(t["doc_count"] for t in tm["topics"].values()) / n_topics
    unmatched = [
        d["id"] for _, d in docs
        if not derive_topic_paths(d["id"], doc_scores)["primary"]
    ]
    print(f"[write] {tm_path}")
    print(f"[write] {rep_path}")
    print(f"[stats] {n_topics} topics; avg {avg_docs:.1f} docs per topic")
    print(f"[stats] unmatched docs (no topic_path): {len(unmatched)}")
    for d in unmatched:
        print(f"        - {d}")
    # Matcher health summary
    if health_warnings:
        by_kind: dict[str, int] = {}
        for w in health_warnings:
            by_kind[w["kind"]] = by_kind.get(w["kind"], 0) + 1
        kind_summary = ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items()))
        print(f"[health] {len(health_warnings)} taxonomy warning(s): {kind_summary}")
        for w in health_warnings:
            print(f"  [{w['kind']:>14}] {w['msg']}")
    else:
        print("[health] no taxonomy warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
