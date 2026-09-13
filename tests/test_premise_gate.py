"""Premise gate — refuse the question the corpus cannot answer (offline, $0).

The 2026-09-12 adversarial audit measured the output gates blocking 0 of 277
sentences. Reading its worst case explains why: "SolGen Lelen Berberabe" is in
the corpus word for word (a 2025 speech), so a gate checking the sentence
against its grounding context must pass it — the falsehood is that the question
asked who holds the office NOW. This gate runs on the question instead.

Two failure directions, and the second one matters as much as the first: a gate
that refuses a legitimate question has made the exhibit useless. The question
set in docs/test-specs/TS-007-premise-gate-questions.json carries both.

Pytest-compatible; also runnable standalone:  python tests/test_premise_gate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

import answer_canned  # noqa: E402
import premise_gate as pg  # noqa: E402

QUESTIONS = json.loads(
    (ROOT / "docs" / "test-specs" / "TS-007-premise-gate-questions.json")
    .read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _gate_on(monkeypatch):
    monkeypatch.setenv("CJ_PREMISE_GATE", "1")


# ---------------------------------------------------------------------------
# the two directions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entry", QUESTIONS["refuse"],
                         ids=[e["q"][:48] for e in QUESTIONS["refuse"]])
def test_unanswerable_premise_is_refused(entry):
    got = pg.check(entry["q"])
    assert got["refuse"], f"reached the composer: {entry['q']!r}"
    assert got["category"] == entry["category"], (
        f"{entry['q']!r} classed {got['category']}, expected {entry['category']}")
    assert got["pool"], "a refusal with no decline pool would fall through"


@pytest.mark.parametrize("entry", QUESTIONS["answer"],
                         ids=[e["q"][:48] for e in QUESTIONS["answer"]])
def test_answerable_question_is_untouched(entry):
    got = pg.check(entry["q"])
    assert not got["refuse"], (
        f"gate refused a question he can answer: {entry['q']!r} "
        f"({got['category']}, {got['matched']})")


# ---------------------------------------------------------------------------
# the decline pools exist and are in voice
# ---------------------------------------------------------------------------

def test_every_category_has_a_decline_pool(monkeypatch):
    monkeypatch.setenv("CJ_CANNED_ENABLED", "1")
    for entry in QUESTIONS["refuse"]:
        pool = pg.check(entry["q"])["pool"]
        text = answer_canned.get(pool)
        assert text, f"no curated decline for {pool}"
        assert len(text.split()) >= 25, f"{pool} decline is too curt to be in voice"


def test_decline_pools_rotate(monkeypatch):
    """A visitor asking two unanswerable questions must not hear one script."""
    monkeypatch.setenv("CJ_CANNED_ENABLED", "1")
    for pool in {pg.check(e["q"])["pool"] for e in QUESTIONS["refuse"]}:
        seen = {answer_canned.get(pool) for _ in range(40)}
        assert len(seen) >= 2, f"{pool} has only one variant"


# ---------------------------------------------------------------------------
# switches and fail-open
# ---------------------------------------------------------------------------

def test_gate_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("CJ_PREMISE_GATE", "0")
    got = pg.check("Who is the current Solicitor General?")
    assert not got["refuse"] and got["category"] is None


def test_log_mode_scores_without_refusing(monkeypatch):
    monkeypatch.setenv("CJ_PREMISE_GATE", "log")
    got = pg.check("Who is the current Solicitor General?")
    assert got["category"] == "current_office"
    assert not got["refuse"], "log mode must not silence the turn"


@pytest.mark.parametrize("junk", ["", None, 12345, "?" * 4000, "\n\n"])
def test_never_raises(junk):
    got = pg.check(junk)
    assert got["refuse"] in (True, False)


def test_horizon_comes_from_the_corpus(monkeypatch):
    monkeypatch.delenv("CJ_CORPUS_HORIZON_YEAR", raising=False)
    pg._HORIZON["year"] = None
    assert 2020 <= pg.corpus_horizon() <= 2030
    pg._HORIZON["year"] = None
    monkeypatch.setenv("CJ_CORPUS_HORIZON_YEAR", "2019")
    assert pg.corpus_horizon() == 2019
    pg._HORIZON["year"] = None


def test_year_past_the_horizon_refuses(monkeypatch):
    monkeypatch.setenv("CJ_CORPUS_HORIZON_YEAR", "2026")
    pg._HORIZON["year"] = None
    assert pg.check("What did the Court decide in 2029?")["category"] == "post_corpus"
    assert pg.check("What did the Court decide in 2019?")["category"] is None
    pg._HORIZON["year"] = None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
