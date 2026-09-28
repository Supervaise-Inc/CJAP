"""Fish word timings (2026-09-16): a sentence spoken by the Fish clone must
reach the captions with per-word timings, like an ElevenLabs one.

Fish's timestamp stream returns segments with punctuation stripped; the
captions show the ORIGINAL tokens. voice.fish.words_from_segments reconciles
the two, and falls back to the bare segments rather than guessing.
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voice import fish  # noqa: E402

SEGS = [["Good", 0.16, 0.32], ["afternoon", 0.32, 1.12], ["I", 1.12, 1.36],
        ["am", 1.36, 1.52], ["Artemio", 1.52, 2.08], ["Panganiban", 2.08, 3.04]]


def test_tokens_keep_their_punctuation():
    w = fish.words_from_segments("Good afternoon. I am Artemio Panganiban.", SEGS)
    assert [x[0] for x in w] == ["Good", "afternoon.", "I", "am", "Artemio", "Panganiban."]
    assert w[1][1:] == [0.32, 1.12]


def test_token_spanning_segments_takes_their_union():
    segs = [["the", 0.0, 0.2], ["Court", 0.2, 0.6], ["s", 0.6, 0.7], ["ruling", 0.7, 1.2]]
    w = fish.words_from_segments("the Court's ruling", segs)
    assert w[1] == ["Court's", 0.2, 0.7]
    assert len(w) == 3


def test_pure_punctuation_rides_on_the_previous_word():
    segs = [["law", 0.0, 0.4], ["and", 0.5, 0.7]]
    w = fish.words_from_segments("law — and", segs)
    assert w == [["law —", 0.0, 0.4], ["and", 0.5, 0.7]]


def test_leading_punctuation_joins_the_first_word():
    w = fish.words_from_segments("— and", [["and", 0.1, 0.3]])
    assert w == [["— and", 0.1, 0.3]]


def test_unreconcilable_tail_is_spread_over_the_remaining_audio():
    # "2006" spoken as three words: the timed prefix keeps its timings, the
    # rest is spread from where the untimed speech starts to the clip's end
    segs = [["in", 0.0, 0.2], ["two", 0.2, 0.4], ["thousand", 0.4, 0.8], ["six", 0.8, 1.0]]
    w = fish.words_from_segments("in 2006 he retired", segs, dur=2.0)
    assert [x[0] for x in w] == ["in", "2006", "he", "retired"]
    assert w[0] == ["in", 0.0, 0.2]
    assert w[1][1] == 0.2 and w[-1][2] == 2.0
    assert all(a[1] <= b[1] for a, b in zip(w, w[1:]))   # never out of order


def test_words_the_stream_never_timed_still_appear_after_the_timed_ones():
    segs = [["Good", 0.1, 0.3], ["day", 0.3, 0.6]]
    w = fish.words_from_segments("Good day. (1789)", segs, dur=3.0)
    assert [x[0] for x in w] == ["Good", "day.", "(1789)"]
    assert w[2][1] >= 0.6 and w[2][2] == 3.0


class _Resp:
    status_code = 200

    def __init__(self, lines):
        self._lines = lines

    def iter_lines(self, decode_unicode=True):
        return iter(self._lines)

    def close(self):
        pass


def _event(pcm_i16, seq, off, segs):
    return "data: " + json.dumps({
        "audio_base64": base64.b64encode(pcm_i16.tobytes()).decode(),
        "chunk_seq": seq, "chunk_audio_offset_sec": off,
        "alignment": {"segments": [{"text": t, "start": a, "end": b} for t, a, b in segs]}
        if segs is not None else None})


def test_stream_concatenates_audio_and_offsets_later_chunks():
    a = np.full(2400, 1000, dtype="<i2")
    lines = ["event: message", _event(a, 0, 0.0, None),
             _event(a, 0, 0.0, [["Good", 0.0, 0.1]]),          # superseded
             _event(a, 0, 0.0, [["Good", 0.0, 0.1], ["day", 0.1, 0.2]]),
             _event(a, 1, 0.3, [["Sir", 0.0, 0.2]])]
    pcm, segs = fish._read_stream(_Resp(lines))
    assert pcm.size == 4 * 2400 and pcm.dtype == np.float32
    assert segs == [["Good", 0.0, 0.1], ["day", 0.1, 0.2], ["Sir", 0.3, 0.5]]


def test_synthesize_fills_words_out(monkeypatch):
    monkeypatch.setenv("FISH_API_KEY", "k")
    monkeypatch.setenv("FISH_MODEL_ID", "m")
    a = np.full(4800, 3000, dtype="<i2")
    seen = {}

    def fake_post(url, body, stream=False):
        seen["url"], seen["format"] = url, body["format"]
        return _Resp([_event(a, 0, 0.0, [["Hello", 0.0, 0.1], ["there", 0.1, 0.2]])])

    monkeypatch.setattr(fish, "_post", fake_post)
    monkeypatch.setattr(fish.audio, "process", lambda pcm, sr: pcm)
    words = []
    pcm = fish.synthesize("Hello there.", words_out=words)
    assert seen == {"url": fish.STREAM_URL, "format": "pcm"}
    assert words == [["Hello", 0.0, 0.1], ["there.", 0.1, 0.2]]
    assert pcm.size == 4800


def test_rejected_timestamp_endpoint_falls_back_to_plain(monkeypatch):
    monkeypatch.setenv("FISH_API_KEY", "k")
    monkeypatch.setenv("FISH_MODEL_ID", "m")
    calls = []

    def fake_post(url, body, stream=False):
        calls.append(url)
        if url == fish.STREAM_URL:
            e = fish.FishError("error", "http 404")
            e.status = 404
            raise e
        return type("R", (), {"content": b"wav"})()

    monkeypatch.setattr(fish, "_post", fake_post)
    monkeypatch.setattr(fish, "_decode", lambda raw: (np.zeros(10, np.float32), 24000))
    monkeypatch.setattr(fish.audio, "process", lambda pcm, sr: pcm)
    words = []
    fish.synthesize("Hi.", words_out=words)
    assert calls == [fish.STREAM_URL, fish.API_URL] and words == []


def test_quota_on_timestamp_endpoint_is_not_retried_plain(monkeypatch):
    monkeypatch.setenv("FISH_API_KEY", "k")
    monkeypatch.setenv("FISH_MODEL_ID", "m")
    calls = []

    def fake_post(url, body, stream=False):
        calls.append(url)
        raise fish.FishError("quota", "http 402")

    monkeypatch.setattr(fish, "_post", fake_post)
    try:
        fish.synthesize("Hi.", words_out=[])
    except fish.FishError as e:
        assert e.reason == "quota"
    assert calls == [fish.STREAM_URL]
