"""Deterministic premise gate — refuse the question the corpus cannot answer.

The 2026-09-12 adversarial audit measured the output gates blocking 0 of 277
sentences while 37 invented particulars reached speech. Reading the three worst
cases explains why no output gate could have caught them:

  Q "Who is the current Solicitor General and what did you tell them?"
    -> "SolGen Lelen Berberabe ... the mission I entrusted to her"

That pairing is REAL. It is in corpus/speeches/D_flp_mission_foundation/SD002
(dated 2025-08-29), word for word. Nothing about the sentence is ungrounded —
the falsehood is that the question asked who holds the office NOW, and the
corpus can only say who held it then. An output gate checking the sentence
against its grounding context must pass it, correctly, every time. Same shape
for "What did you say to Chief Justice Gesmundo last week?": the premise is
unanswerable, so every answer to it is invention, however well grounded the
pieces are.

So this gate runs on the QUESTION, before the router and composer, and hands
an unanswerable premise to the curated decline pool instead. Zero tokens, zero
latency, and it removes the failure rather than trying to catch it downstream.
It is the "narrower robot" the audit recommended over a better gate.

Four refusable premises:
  current_office  who holds an office now / is X still the Y
  recency         a time deixis ("last week", "recently") on a factual ask
  pending         a matter still before a court, or how it will be decided
  post_corpus     a year after the corpus horizon, or an outright prediction
  outcome         an election or vote result the corpus does not record

Deliberately conservative: a recency word alone never refuses ("my advice to
young lawyers today" must still be answered). It refuses when the question
demands a fact the corpus cannot hold. CJ_PREMISE_GATE=0 disables; =log scores
and logs without refusing. Every function fails OPEN — a bug here must never
silence a turn.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Offices whose holder changes. Asking who holds one NOW is unanswerable from a
# fixed corpus no matter how much of the corpus is about that office.
_OFFICE = (r"(?:chief justice|associate justice|justice|solicitor ?general|solgen|"
           r"ombudsman|president|vice[- ]president|senator|senate president|speaker|"
           r"congressman|congresswoman|representative|secretary(?: of justice)?|"
           r"justice secretary|executive secretary|chairman|chairperson|chair|"
           r"commissioner|governor|mayor|ambassador|court administrator|"
           r"dean|prosecutor|attorney ?general)")

# A question is about the present holder of an office.
_CURRENT_OFFICE = [
    # "who is the current/sitting/present/incumbent <anything>"
    re.compile(r"\bwho(?:'s| is| are)\s+(?:the\s+)?(?:current|present|sitting|incumbent|new)\b"),
    # "who is the <office>?" with nothing qualifying it — asks about now
    re.compile(r"\bwho(?:'s| is)\s+(?:the\s+|our\s+)?" + _OFFICE +
               r"\s*(?:now|today|currently|at present|these days)?\s*[?.!]*$"),
    # "is X still the <office>", "are you still the <office>"
    re.compile(r"\b(?:is|are)\s+\w+(?:\s+\w+){0,3}\s+still\s+(?:the\s+)?" + _OFFICE),
    # "who (now) heads/leads/chairs/runs ..."
    re.compile(r"\bwho\s+(?:now\s+)?(?:heads|leads|chairs|runs|sits as)\b"),
    # "who is the <office> now/today"
    re.compile(r"\b" + _OFFICE + r"\s+(?:now|today|currently|at the moment)\b"),
]

# Time deixis, in two tiers. STRONG words are about a recent event and almost
# never rhetorical; WEAK ones are routinely used in a general question ("my
# advice to young lawyers today") and only refuse when the question also asks
# for a specific event or statement.
_RECENCY_STRONG = re.compile(
    r"\b(?:last (?:week|month|night|year)|yesterday|this (?:morning|afternoon|evening)|"
    r"just now|recently|lately|as we speak|so far this year|the latest|latest news|"
    r"most recent(?:ly)?|of late|any news|an update)\b")
_RECENCY_WEAK = re.compile(
    r"\b(?:today|nowadays|these days|right now|currently|at the moment|at present|"
    r"this (?:week|month|year)|newest|the new)\b")

# The specific asks a time word turns unanswerable: an event, a statement, an
# outcome. Deliberately NOT "what is/are" — that is most legitimate questions.
_FACTUAL_ASK = re.compile(
    r"\b(?:what (?:did|do|does|has|have)|who (?:did|won|said|met)|"
    r"when did|where did|how did|did (?:you|he|she|they|the)|"
    r"has (?:he|she|they|the)|what happened|what'?s happening|what is happening|"
    r"what'?s going on|what(?:'?s| is) the (?:status|news|result|latest)|"
    r"tell me what|any news|an update)\b")
_BODY = re.compile(
    r"\b(?:supreme court|the court|congress|senate|house|comelec|sandiganbayan|"
    r"ombudsman|palace|administration|government|commission)\b")

# An outcome the corpus does not record. Narrow on purpose: "who won" alone
# would swallow "who won that case", which the corpus may well answer.
_OUTCOME = [
    re.compile(r"\bwho (?:won|lost)\b.{0,40}\b(?:election|elections|race|poll|polls|"
               r"presidency|senate seat|vice[- ]presidency)\b"),
    re.compile(r"\bwhat (?:was|were) the (?:result|results|outcome) of the\b.{0,30}"
               r"\b(?:election|elections|race|poll|vote)\b"),
    re.compile(r"\bhow did \w+(?:\s+\w+){0,2} vote\b"),
]

# A matter still open before a court, or how one will come out.
_PENDING = [
    re.compile(r"\b(?:pending|sub ?judice|still (?:before|in|pending in) (?:the )?court|"
               r"currently before|now before the (?:court|supreme court)|ongoing (?:case|trial|litigation))\b"),
    re.compile(r"\bhow (?:will|would|should) (?:the )?(?:court|supreme court|justices|they)\b"),
    re.compile(r"\b(?:will|would) (?:the )?(?:court|supreme court|justices)\s+(?:rule|decide|uphold|strike|grant|deny)\b"),
    re.compile(r"\b(?:expected|about|set|due) to (?:rule|decide|be decided|come out)\b"),
    re.compile(r"\bwhat (?:will|is going to) happen to\b"),
    re.compile(r"\bthe case against\b"),
]

# Predictions and anything dated after the corpus ends.
_FUTURE = [
    re.compile(r"\bwho (?:will|is going to) (?:win|be elected|become|succeed)\b"),
    re.compile(r"\bnext (?:year|election|president|chief justice|administration)\b"),
    re.compile(r"\b(?:do you )?(?:predict|forecast)\b"),
    re.compile(r"\bwhat (?:will|is going to) (?:happen|be)\b.*\b(?:next|future|20\d\d)\b"),
]
_YEAR = re.compile(r"\b(20\d\d)\b")

_CATEGORY_NOTE = {
    "current_office": "asks who holds an office now — the corpus can only say who held it when it was written",
    "recency": "asks about something recent — outside the corpus, which has a fixed end date",
    "pending": "asks about a matter still open, or how it will be decided",
    "post_corpus": "asks about a year, or a prediction, after the corpus ends",
    "outcome": "asks for an election or vote result the corpus does not record",
}

# Which curated decline pool answers each category (data/entities/canned_answers.json).
_POOL = {
    "current_office": "premise_current_office",
    "recency": "premise_recency",
    "pending": "premise_pending",
    "post_corpus": "premise_post_corpus",
    "outcome": "premise_outcome",
}

_HORIZON = {"year": None}


def corpus_horizon() -> int:
    """Newest year any corpus document carries. Anything after it is outside
    the record by definition. Computed once; CJ_CORPUS_HORIZON_YEAR overrides."""
    if _HORIZON["year"] is not None:
        return _HORIZON["year"]
    env = os.environ.get("CJ_CORPUS_HORIZON_YEAR", "").strip()
    if env.isdigit():
        _HORIZON["year"] = int(env)
        return _HORIZON["year"]
    newest = 0
    try:
        for js in REPO_ROOT.glob("corpus/*/*/*.json"):
            try:
                y = json.loads(js.read_text(encoding="utf-8")).get("year")
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(y, int) and y > newest:
                newest = y
    except OSError:
        pass
    _HORIZON["year"] = newest or 2026
    return _HORIZON["year"]


def mode() -> str:
    """'block' (default), 'log' (score only), or 'off'."""
    v = os.environ.get("CJ_PREMISE_GATE", "1").strip().lower()
    if v in {"0", "off", "false", "no"}:
        return "off"
    if v in {"log", "warn"}:
        return "log"
    return "block"


def check(question: str) -> dict:
    """Classify the question's premise.

    Returns {refuse, category, pool, reason, matched}. refuse is False whenever
    the gate is off or nothing matched; the caller answers normally."""
    out = {"refuse": False, "category": None, "pool": None, "reason": "", "matched": []}
    try:
        if mode() == "off" or not question:
            return out
        q = " ".join(str(question).lower().split())

        def _hit(cat, what):
            out["category"] = out["category"] or cat
            out["matched"].append(what)

        for rx in _CURRENT_OFFICE:
            if rx.search(q):
                _hit("current_office", rx.pattern[:48])
                break
        if not out["category"]:
            for rx in _PENDING:
                if rx.search(q):
                    _hit("pending", rx.pattern[:48])
                    break
        if not out["category"]:
            for rx in _FUTURE:
                if rx.search(q):
                    _hit("post_corpus", rx.pattern[:48])
                    break
        if not out["category"]:
            horizon = corpus_horizon()
            for y in _YEAR.findall(q):
                if int(y) > horizon:
                    _hit("post_corpus", f"year {y} > corpus horizon {horizon}")
                    break
        if not out["category"]:
            for rx in _OUTCOME:
                if rx.search(q):
                    _hit("outcome", rx.pattern[:48])
                    break
        if not out["category"]:
            # A time word never refuses on its own. A STRONG one refuses when
            # the question also names an institution or an office or asks for a
            # specific fact; a WEAK one only on a specific factual ask.
            strong = _RECENCY_STRONG.search(q)
            weak = _RECENCY_WEAK.search(q)
            asks = _FACTUAL_ASK.search(q)
            if strong and (asks or _BODY.search(q) or re.search(_OFFICE, q)):
                _hit("recency", f"'{strong.group(0)}' + factual ask")
            elif weak and asks:
                _hit("recency", f"'{weak.group(0)}' + '{asks.group(0)}'")

        if out["category"]:
            out["reason"] = _CATEGORY_NOTE[out["category"]]
            out["pool"] = _POOL[out["category"]]
            out["refuse"] = mode() == "block"
    except Exception:
        return {"refuse": False, "category": None, "pool": None,
                "reason": "", "matched": []}
    return out
