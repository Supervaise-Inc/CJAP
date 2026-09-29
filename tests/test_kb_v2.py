"""Knowledge base v2 (2026-09-29): the imported corpus is reachable by the
Haiku-router path — book ids resolve, the identity intent survives the v2
topic map, the router fallback exists, and a routed topic's documents are
picked by the question rather than alphabetically."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import answer_pipeline as ap  # noqa: E402


@pytest.fixture(scope="module")
def art():
    return ap.CorpusArtifacts()


def test_every_topic_doc_resolves(art):
    ids = {d for t in art.topics.values() for d in t.get("doc_ids", [])}
    assert len(ids) > 1000
    assert [d for d in ids if art.load_raw_doc(d) is None] == []


def test_book_chapters_resolve(art):
    assert art.load_raw_doc("BA001")["type"] == "book"
    assert art.load_doc_body("BA001")


def test_meta_and_fallback_are_valid(art):
    assert ap.META_TOPIC in art.valid_topic_ids
    assert ap.FALLBACK_TOPIC in art.valid_topic_ids
    assert art.topics[ap.FALLBACK_TOPIC]["doc_ids"]


def test_question_steers_ties(art):
    r = {"primary_topic": "life_story_family_school_and_church", "secondary_topics": []}
    blind = ap._select_source_doc_ids(r, art, 3)
    salonga = ap._select_source_doc_ids(r, art, 3, question="Who were your mentors, like Salonga?")
    sampaloc = ap._select_source_doc_ids(r, art, 3, question="What was your childhood in Sampaloc like?")
    assert salonga != blind and sampaloc != blind and salonga != sampaloc
    assert any("salonga" in art.doc_index[d][0] for d in salonga)


def test_question_beats_secondary_overlap(art):
    """A doc naming the case outranks docs that only sit in two routed topics."""
    r = {"primary_topic": "party_list_charter_change_and_dynasties",
         "secondary_topics": ["presidential_power_martial_law_people_power",
                              "how_the_supreme_court_decides"]}
    q = "What did you think of the Lambino people's initiative to change the Charter?"
    picked = ap._select_source_doc_ids(r, art, 3, question=q)
    assert any("lambino" in art.doc_index[d][0] for d in picked)
