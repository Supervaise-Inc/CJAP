"""P0 answer gate — deterministic keyword recheck of composed answers ($0, no LLM).

Verifies the composed answer against hand-curated expected-data rules BEFORE
the robot speaks (pre-TTS). Was written to complement the LLM fidelity checker,
which no longer runs (see below): this gate is
zero-cost and deterministic, so it catches the concrete slips a sampled judge
can miss — a wrong year, a missing case name, AI self-description — and can
never hallucinate a verdict itself.

Rules file: config.ANSWER_GATE_RULES_PATH (data/entities/answer_gate_rules.json),
mtime hot-reloaded like entity_overrides.json — edits land without a restart.

Pattern convention (everywhere in the rules file):
  * plain string      -> case-insensitive substring match
  * "re:<pattern>"    -> regex, re.IGNORECASE

Rule semantics: a rule APPLIES to a turn when any `trigger.question_any`
pattern matches the question, OR a routed topic id is in `trigger.topics_any`.
An applied rule TRIPS when some `expect_groups` group has no alternate present
in the answer (kind=missing_expected), or a `forbid` pattern matches the
answer (kind=forbidden). `global_forbid` patterns are checked against every
answer regardless of triggers.

Fail-open: an unreadable/invalid rules file disables the gate for that call
(ok=True with a note). This module never raises into the caller.

Do NOT read the older phrasing of this line — "the composer and fidelity
checker remain the primary safety surface" — as describing the running system.
The LLM fidelity checker (answer_pipeline.generate_response_with_fidelity) is
NOT on the streaming path that supervaise.service actually runs, and
CJ_SKIP_FIDELITY=1 in app/.env disables it besides. Corrected 2026-09-14: when
this gate fails open, nothing downstream catches what it let through.
"""

from __future__ import annotations

import os

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ---------------------------------------------------------------------------
# Pattern compilation ("re:" prefix = regex, else casefolded substring)
# ---------------------------------------------------------------------------
def _compile(pat: str):
    if pat.startswith("re:"):
        return re.compile(pat[3:], re.IGNORECASE)
    return pat.casefold()


def _matches(compiled, text_folded: str, text_raw: str) -> bool:
    if isinstance(compiled, str):
        return compiled in text_folded
    return compiled.search(text_raw) is not None


class GateRules:
    """Compiled form of the rules file. Bad individual patterns are dropped
    (logged into self.pattern_errors) rather than failing the whole file."""

    def __init__(self, doc: dict):
        self.pattern_errors: list[str] = []

        def _plist(pats) -> list:
            out = []
            for p in pats or []:
                try:
                    out.append((p, _compile(str(p))))
                except re.error as e:
                    self.pattern_errors.append(f"{p!r}: {e}")
            return out

        self.global_forbid = [
            {"id": str(gf.get("id", "global")), "patterns": _plist(gf.get("patterns"))}
            for gf in doc.get("global_forbid", [])
        ]
        self.rules = []
        for r in doc.get("rules", []):
            trig = r.get("trigger", {}) or {}
            self.rules.append({
                "id": str(r.get("id", "?")),
                "question_any": _plist(trig.get("question_any")),
                "topics_any": set(trig.get("topics_any") or []),
                "expect_groups": [_plist(g) for g in r.get("expect_groups", [])],
                "forbid": _plist(r.get("forbid")),
            })


# ---------------------------------------------------------------------------
# Loading (resident; mtime hot-reload; fail-open)
# ---------------------------------------------------------------------------
_STATE: dict = {"rules": None, "mtime": None, "error": None}


def load(force: bool = False) -> GateRules | None:
    """Resident rules, reloaded when the file's mtime changes.
    Returns None when the file is missing/invalid (fail-open)."""
    path = config.ANSWER_GATE_RULES_PATH
    try:
        mt = path.stat().st_mtime_ns
    except OSError as e:
        _STATE.update(rules=None, mtime=None, error=f"rules file unreadable: {e}")
        return None
    if force or _STATE["rules"] is None or mt != _STATE["mtime"]:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            _STATE.update(rules=GateRules(doc), mtime=mt, error=None)
        except (json.JSONDecodeError, OSError, TypeError, AttributeError) as e:
            _STATE.update(rules=None, mtime=mt, error=f"{type(e).__name__}: {e}")
            return None
    return _STATE["rules"]


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------
def check_answer(question: str, answer: str,
                 topic_ids: list | None = None,
                 audit: bool = True,
                 forbid_only: bool = False) -> dict:
    """Deterministic recheck of a composed answer. Pure string matching,
    never raises. Returns:
      {ok, applied: [rule ids], tripped: [{rule, kind, detail}],
       note, elapsed_ms}
    kind is "missing_expected" (an expect_groups group had no alternate in
    the answer; detail lists the alternates) or "forbidden" (a forbid /
    global_forbid pattern matched; detail is the pattern).

    forbid_only=True skips the expect_groups checks — for screening a
    SINGLE SENTENCE mid-stream, where expected facts may legitimately
    live in a later sentence but a forbidden phrase is wrong anywhere."""
    t0 = time.perf_counter()
    result = {"ok": True, "applied": [], "tripped": [], "note": "", "elapsed_ms": 0.0}
    try:
        rules = load()
        if rules is None:
            result["note"] = f"gate fail-open: {_STATE['error']}"
            return result

        q_raw, a_raw = str(question), str(answer)
        q_fold, a_fold = q_raw.casefold(), a_raw.casefold()
        topics = set(topic_ids or [])

        for gf in rules.global_forbid:
            for raw, comp in gf["patterns"]:
                if _matches(comp, a_fold, a_raw):
                    result["tripped"].append(
                        {"rule": gf["id"], "kind": "forbidden", "detail": raw})

        for r in rules.rules:
            applies = any(_matches(c, q_fold, q_raw) for _, c in r["question_any"]) \
                or bool(topics & r["topics_any"])
            if not applies:
                continue
            result["applied"].append(r["id"])
            for group in ([] if forbid_only else r["expect_groups"]):
                if group and not any(_matches(c, a_fold, a_raw) for _, c in group):
                    result["tripped"].append(
                        {"rule": r["id"], "kind": "missing_expected",
                         "detail": " / ".join(raw for raw, _ in group)})
            for raw, comp in r["forbid"]:
                if _matches(comp, a_fold, a_raw):
                    result["tripped"].append(
                        {"rule": r["id"], "kind": "forbidden", "detail": raw})

        result["ok"] = not result["tripped"]
    except Exception as e:  # absolute backstop — never raise into the pipeline
        result.update(ok=True, note=f"gate fail-open: {type(e).__name__}: {e}")
    result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    if audit and result["tripped"]:
        _audit(question, answer, result, topic_ids)
    return result


# ---- fact gate (2026-08-29, user: "reduce all hallucinations in any form") ----
_YEAR_RX = re.compile(r"\b(1[89]\d\d|20\d\d)\b")
_TITLE_RX = re.compile(r"[*_\u201c\"]([A-Z][^*_\u201d\"]{6,80}?)[*_\u201d\"]")
_CORE = {"years": None, "text": ""}


def _core():
    """Persona-core text: voice card, topic map, router prompt, canned answers,
    gate rules. Years/titles found here are always allowed."""
    if _CORE["years"] is None:
        root = Path(__file__).resolve().parent.parent
        buf = []
        for pat in ("corpus/voice/*.md", "corpus/voice/*.json",
                    "data/entities/canned_answers.json", "data/entities/answer_gate_rules.json"):
            for f in root.glob(pat):
                try:
                    buf.append(f.read_text(errors="ignore"))
                except OSError:
                    pass
        _CORE["text"] = "\n".join(buf).casefold()
        _CORE["years"] = set(_YEAR_RX.findall(_CORE["text"]))
        _CORE["dates"] = _date_triples(_CORE["text"])
    return _CORE


_MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"])}
_MONTHS.update({m[:3]: i for m, i in list(_MONTHS.items())})
_MON_RX = "|".join(sorted(_MONTHS, key=len, reverse=True))
# "December 7, 2006" / "Dec. 7 2006" / "7 December 2006" / "2006-12-07"
_DATE_MDY = re.compile(r"\b(" + _MON_RX + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+((?:19|20)\d\d)\b", re.I)
_DATE_DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + _MON_RX + r")\.?,?\s+((?:19|20)\d\d)\b", re.I)
_DATE_ISO = re.compile(r"\b((?:19|20)\d\d)-(\d{2})-(\d{2})\b")


def _date_triples(text: str) -> set:
    """Every (year, month, day) a text states, in any of the three formats the
    corpus uses. Comparing triples rather than strings means the composer
    writing 'December 7, 1936' is still supported by a sidecar's '1936-12-07'."""
    out = set()
    for m in _DATE_MDY.finditer(text or ""):
        out.add((int(m.group(3)), _MONTHS[m.group(1).lower().rstrip(".")], int(m.group(2))))
    for m in _DATE_DMY.finditer(text or ""):
        out.add((int(m.group(3)), _MONTHS[m.group(2).lower().rstrip(".")], int(m.group(1))))
    for m in _DATE_ISO.finditer(text or ""):
        out.add((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return out


def fact_check(sentence: str, context_text: str = "", question: str = "") -> dict:
    """Deterministic pre-TTS fact gate. A sentence that states a YEAR or a full
    DATE that
    appears neither in the composer's grounding context, the question, nor
    the persona-core corpus is blocked — the composer had no source for it
    (the fidelity audit used to catch these only after they were spoken).
    Quoted / italic TITLES not found in context or core are logged, not
    blocked (CJ_FACT_GATE_TITLES=block to block). CJ_FACT_GATE=0 disables.
    Full dates are checked as (year, month, day) triples, so a date whose year
    is in the corpus but whose day never was is still blocked
    (CJ_FACT_GATE_DATES=log to log instead).
    Returns {ok, bad_years, bad_dates, unverified_titles}."""
    out = {"ok": True, "bad_years": [], "bad_dates": [], "unverified_titles": []}
    if os.environ.get("CJ_FACT_GATE", "1").strip().lower() in {"0", "off", "false"}:
        return out
    try:
        core = _core()
        ctx = (context_text or "").casefold()
        years = set(_YEAR_RX.findall(sentence))
        if years:
            allowed = set(_YEAR_RX.findall(ctx)) | core["years"] | set(_YEAR_RX.findall(question or ""))
            out["bad_years"] = sorted(years - allowed)
        # A full date is a stricter claim than its year: "December 7, 2006"
        # passes the year gate (2006 is everywhere in the corpus) while
        # conflating his birthday with his retirement — the audit's second
        # outright false claim. Check the whole triple, not the year alone.
        said = _date_triples(sentence)
        if said:
            known = (_date_triples(ctx) | _date_triples(question or "")
                     | _core()["dates"])
            out["bad_dates"] = sorted(f"{y:04d}-{m:02d}-{d:02d}"
                                      for (y, m, d) in said - known)
        for t in _TITLE_RX.findall(sentence):
            tf = t.casefold().strip()
            if len(tf.split()) >= 2 and tf not in ctx and tf not in core["text"]:
                out["unverified_titles"].append(t)
        block_titles = os.environ.get("CJ_FACT_GATE_TITLES", "log").strip().lower() == "block"
        block_dates = os.environ.get("CJ_FACT_GATE_DATES", "block").strip().lower() == "block"
        out["ok"] = (not out["bad_years"]
                     and not (block_dates and out["bad_dates"])
                     and not (block_titles and out["unverified_titles"]))
    except Exception:
        out["ok"] = True   # never break a turn
    return out


def correction_hint(result: dict) -> str:
    """Composer-facing recompose hint built from a tripped gate result.
    Appended to the user message (never the system prompt) so the cached
    prefix stays valid — same pattern as the fidelity_correction hint."""
    lines = []
    for t in result["tripped"]:
        if t["kind"] == "missing_expected":
            lines.append(f"- The answer MUST state this fact (any of): {t['detail']}")
        else:
            lines.append(f"- The answer must NOT contain: {t['detail']}")
    return ("<answer_correction>\n"
            "A prior draft failed a factual recheck against the documented "
            "record. Recompose, staying fully in voice, and fix the following:\n"
            + "\n".join(lines) + "\n</answer_correction>")


# ---------------------------------------------------------------------------
# Audit trail (JSONL, append-only; empty path disables)
# ---------------------------------------------------------------------------
def _audit(question: str, answer: str, result: dict, topic_ids) -> None:
    path = config.ANSWER_GATE_LOG_PATH
    if not str(path):
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "question": question, "answer": answer,
               "topic_ids": list(topic_ids or []),
               "applied": result["applied"], "tripped": result["tripped"]}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Curated / pre-rendered lines (2026-09-13)
# ---------------------------------------------------------------------------
# The duet and intro lines are authored, rendered to .wav offline, and played
# with no network — so they bypass every live gate. The 09-12 audit put the
# nine duet lines through the gates by hand and all nine passed, but noted the
# gap is procedural: nothing stops a tenth line with a date or a case name in
# it going straight to the speaker unchecked. The render scripts now call this,
# so an authored line is held to the same bar as a composed one, once, offline,
# where a failure costs nothing.
_CORPUS_TEXT: list = [None]


def corpus_text() -> str:
    """All corpus prose and sidecars as one string — the grounding an authored
    line is checked against (it has no routed context of its own)."""
    if _CORPUS_TEXT[0] is None:
        root = Path(__file__).resolve().parent.parent
        buf = []
        for pat in ("corpus/**/*.md", "corpus/**/*.json",
                    "data/entities/canned_answers.json"):
            for f in sorted(root.glob(pat)):
                try:
                    buf.append(f.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
        _CORPUS_TEXT[0] = "\n".join(buf)
    return _CORPUS_TEXT[0]


def check_curated(text: str, topic_ids=()) -> dict:
    """Gate an authored line the way a composed sentence is gated: forbidden
    patterns, then years and full dates against the whole corpus.

    Returns {ok, tripped: [{rule, kind, detail}]}."""
    tripped = []
    res = check_answer("", text, topic_ids=topic_ids, forbid_only=True, audit=False)
    tripped += res["tripped"]
    fc = fact_check(text, corpus_text(), "")
    for y in fc["bad_years"]:
        tripped.append({"rule": "fact-gate", "kind": "year", "detail": y})
    for d in fc["bad_dates"]:
        tripped.append({"rule": "fact-gate", "kind": "date", "detail": d})
    for t in fc["unverified_titles"]:
        tripped.append({"rule": "fact-gate", "kind": "unverified_title", "detail": t})
    return {"ok": not tripped, "tripped": tripped}
