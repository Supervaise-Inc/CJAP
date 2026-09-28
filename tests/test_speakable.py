"""No asterisk is ever voiced (2026-09-28: the composer's *emphasis* was read aloud)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import speech_engines as se  # noqa: E402


def test_inline_emphasis_keeps_the_words():
    assert se.speakable("That is *exactly* the point.") == "That is exactly the point."
    assert se.speakable("The **rule of law** matters.") == "The rule of law matters."


def test_whole_sentence_stage_direction_is_dropped():
    assert se.speakable("*chuckles warmly*") == ""
    assert se.speakable("*A moment of quiet before answering.*") == ""
    assert se.speakable("**pauses**.") == ""


def test_plain_text_untouched():
    s = "Justice delayed is justice denied."
    assert se.speakable(s) == s
    assert se.speakable("") == ""


def test_tts_backstop_strips_asterisks(monkeypatch):
    seen = []
    monkeypatch.setattr(se, "engine_order", lambda: ["elevenlabs"])
    monkeypatch.setattr(se, "_synth_with",
                        lambda eng, text, *a, **k: seen.append(text) or "/dev/null")
    import voice_guard
    monkeypatch.setattr(voice_guard, "spoke", lambda *a, **k: None)
    se.tts_cloned_wav("I say *au contraire* to that.", where="test")
    assert seen == ["I say au contraire to that."]
