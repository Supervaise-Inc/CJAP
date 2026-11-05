"""app/gst_audio.py: the opt-in GStreamer sentence player (2026-11-05).

No GStreamer is needed: a fake Gst module records what the player does. What is
asserted:
  * the pipeline text names appsrc, the 0.3 s back-pressure window, the caps and
    the ALSA route pcm, and CJ_GST_SINK replaces the sink;
  * one pipeline serves every sentence of an answer (no re-open per sentence),
    and a new sample rate re-opens it;
  * a sentence is pushed in 50 ms chunks and play() returns False when written;
  * a stop word cuts play() mid-sentence: True, pipeline torn down, AEC told;
  * dry-run plays nothing; the dual route is refused so the caller falls to aplay;
  * close() sends end-of-stream and stops the pipeline; abort() skips the drain;
  * available() is False with no Gst and when an element is missing.
"""
import os
import sys
import threading
import time

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import gst_audio  # noqa: E402


class _Enum:
    OK, FLUSHING, ERROR = "OK", "FLUSHING", "ERROR"
    PLAYING, NULL, FAILURE = "PLAYING", "NULL", "FAILURE"
    EOS, ERR = 1, 2


class FakeSrc:
    def __init__(self):
        self.pushed, self.events = [], []

    def emit(self, name, arg=None):
        if name == "push-buffer":
            self.pushed.append(arg)
            return _Enum.OK
        self.events.append(name)


class FakeBus:
    def timed_pop_filtered(self, *_a):
        return None


class FakeQuery:
    def parse_latency(self):
        return True, 150_000_000, 300_000_000


class FakePipe:
    def __init__(self, desc):
        self.desc, self.src, self.states = desc, FakeSrc(), []

    def get_by_name(self, n):
        return self.src

    def set_state(self, st):
        self.states.append(st)
        return "OK"

    def get_bus(self):
        return FakeBus()

    def query(self, _q):
        return True


class FakeGst:
    State = _Enum
    StateChangeReturn = _Enum
    FlowReturn = _Enum
    MessageType = type("MT", (), {"EOS": 1, "ERROR": 2})
    pipes = []

    class Buffer:
        @staticmethod
        def new_wrapped(data):
            return bytes(data)

    class Query:
        @staticmethod
        def new_latency():
            return FakeQuery()

    class ElementFactory:
        missing = set()

        @classmethod
        def find(cls, name):
            return None if name in cls.missing else object()

    @classmethod
    def parse_launch(cls, desc):
        p = FakePipe(desc)
        cls.pipes.append(p)
        return p


class Listener:
    def __init__(self, fire_at_call=None):
        self.n, self.fire_at = 0, fire_at_call

    @property
    def fired(self):
        self.n += 1
        return self.fire_at is not None and self.n >= self.fire_at


class Ref:
    def __init__(self):
        self.aborted, self.pushes, self.warmed = 0, 0, []

    def sync(self):
        return True

    def warm(self, rate):
        self.warmed.append(rate)

    def push(self, *_a):
        self.pushes += 1

    def abort(self):
        self.aborted += 1


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    FakeGst.pipes = []
    FakeGst.ElementFactory.missing = set()
    monkeypatch.delenv("CJ_GST_SINK", raising=False)
    monkeypatch.delenv("CJ_SENT_PRIME_S", raising=False)
    monkeypatch.delenv("CJ_SENTENCE_PLAYER", raising=False)


def _player(rate=24000, secs=0.2, **kw):
    a = (np.ones(int(rate * secs)) * 1000).astype(np.int16)
    p = gst_audio.GstSentenceOut(load_wav=lambda _p: (rate, a), trim_edges=lambda x, r: x,
                                 gst=FakeGst, **kw)
    return p


def test_pipeline_description_names_route_and_window():
    d = gst_audio.pipeline_description(24000)
    assert "appsrc name=src" in d and "rate=24000" in d and "channels=1" in d
    assert "max-bytes=14400" in d                       # 0.3 s of S16 mono at 24 kHz
    assert "alsasink device=audio_out_route name=sink sync=false" in d
    assert "buffer-time=150000" in d


def test_cj_gst_sink_replaces_the_sink(monkeypatch):
    monkeypatch.setenv("CJ_GST_SINK", "pipewiresink")
    d = gst_audio.pipeline_description(16000)
    assert "! pipewiresink name=sink" in d and "alsasink" not in d and "buffer-time" not in d


def test_one_pipeline_serves_every_sentence():
    p = _player()
    assert p.play("a.wav", Listener()) is False
    assert p.play("b.wav", Listener()) is False
    assert len(FakeGst.pipes) == 1
    assert p.stats["sentences"] == 2 and p.stats["latency_s"] == 0.15
    p.close()


def test_new_sample_rate_reopens():
    p = _player()
    p.play("a.wav", Listener())
    p._load_wav = lambda _p: (16000, np.ones(1600, dtype=np.int16))
    p.play("b.wav", Listener())
    assert len(FakeGst.pipes) == 2
    p.close()


def test_sentence_is_pushed_in_50ms_chunks():
    p = _player(rate=24000, secs=0.2)
    p.play("a.wav", Listener())
    # keep-alive silence may add chunks of the same size; speech chunks are 2400 bytes*... 1200 samples = 2400 B
    sizes = {len(b) for b in FakeGst.pipes[0].src.pushed}
    assert sizes == {1200 * 2}
    assert len(FakeGst.pipes[0].src.pushed) >= 4          # 0.2 s / 50 ms
    p.close()


def test_stop_word_cuts_the_sentence_and_tells_aec():
    ref = Ref()
    p = _player(ref_feed=ref)
    assert p.play("a.wav", Listener(fire_at_call=3)) is True
    assert ref.aborted == 1
    assert p.pipeline is None
    assert "NULL" in FakeGst.pipes[0].states
    assert "end-of-stream" not in FakeGst.pipes[0].src.events   # abort does not drain


def test_close_drains_with_end_of_stream():
    p = _player()
    p.play("a.wav", Listener())
    p.close()
    assert "end-of-stream" in FakeGst.pipes[0].src.events
    assert FakeGst.pipes[0].states[-1] == "NULL"


def test_dry_run_plays_nothing():
    p = _player(secs=0.1, dry_run=lambda: True)
    assert p.play("a.wav", Listener()) is False
    assert FakeGst.pipes == []


def test_dual_route_is_refused_so_caller_falls_back():
    p = _player(dual_route=lambda: True)
    with pytest.raises(RuntimeError, match="dual route"):
        p.play("a.wav", Listener())


def test_bluetooth_route_is_primed_with_silence():
    p = _player(bt_route=lambda: True)
    p.play("a.wav", Listener())
    first = FakeGst.pipes[0].src.pushed[0]
    assert len(first) == int(24000 * 0.25) * 2 and not any(first)
    p.close()


def test_aec_reference_follows_every_chunk():
    ref = Ref()
    p = _player(ref_feed=ref)
    p.play("a.wav", Listener())
    assert ref.warmed == [24000] and ref.pushes >= 4
    p.close()


def test_available_false_without_gst(monkeypatch):
    monkeypatch.setattr(gst_audio, "_load_gst", lambda: None)
    assert gst_audio.available() is False
    with pytest.raises(RuntimeError):
        gst_audio.GstSentenceOut(load_wav=None, trim_edges=None)


def test_available_false_when_an_element_is_missing():
    assert gst_audio.available(FakeGst) is True
    FakeGst.ElementFactory.missing = {"alsasink"}
    assert gst_audio.available(FakeGst) is False


def test_enabled_follows_cj_sentence_player(monkeypatch):
    assert gst_audio.GstSentenceOut.enabled() is True
    monkeypatch.setenv("CJ_SENTENCE_PLAYER", "aplay")
    assert gst_audio.GstSentenceOut.enabled() is False
