"""The local clone on the DGX Spark (2026-11-05): engine "spark" = voice/qwen.py.

CJAP moved onto a DGX Spark with a Reachy Mini Lite; Panganiban's voice is a
Qwen3-TTS clone served on the Spark's GPU (cjap-tts), and CJ_TTS_ORDER=spark
makes it the only voice. What is asserted:

  * engine_order() offers "spark" only when CJ_QWEN_TTS_URL is set, and in the
    order CJ_TTS_ORDER gives;
  * voice/config.py no longer refuses to import without ElevenLabs credentials
    when CJ_TTS_ORDER does not list "elevenlabs" (it still does when it does) —
    otherwise every `from voice import ...` fails on the Spark, the local clone
    included;
  * voice.qwen spreads the sentence's own tokens over the clip, punctuation
    riding on the word before it, ending at the clip's length;
  * a JSON-wrapped transcript from LiteLLM is unwrapped, a plain one untouched;
  * the dashboard ports can be moved by environment, defaults unchanged.

Run:  app/.venv/bin/python -m pytest tests/test_spark_voice.py -q
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))


def _fresh_config(monkeypatch, order, key=""):
    monkeypatch.setenv("CJ_TTS_ORDER", order)
    monkeypatch.setenv("ELEVEN_API_KEY", key)
    monkeypatch.setenv("ELEVEN_VOICE_ID", "x" if key else "")
    sys.modules.pop("voice.config", None)
    return importlib.import_module("voice.config")


def test_config_imports_without_elevenlabs_when_order_is_spark(monkeypatch):
    cfg = _fresh_config(monkeypatch, "spark")
    assert cfg.ELEVEN_API_KEY == ""


def test_config_still_requires_elevenlabs_when_listed(monkeypatch):
    with pytest.raises(RuntimeError):
        _fresh_config(monkeypatch, "spark,elevenlabs")
    sys.modules.pop("voice.config", None)


def test_engine_order_offers_spark_only_when_configured(monkeypatch):
    import speech_engines as se
    monkeypatch.setenv("CJ_TTS_ORDER", "spark")
    monkeypatch.delenv("CJ_QWEN_TTS_URL", raising=False)
    assert se.engine_order() == []
    monkeypatch.setenv("CJ_QWEN_TTS_URL", "http://127.0.0.1:8091")
    assert se.engine_order() == ["spark"]


def test_spread_words_covers_the_clip(monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "spark")   # importable without ElevenLabs keys
    from voice import qwen
    w = qwen.spread_words("Good afternoon — I am Artemio Panganiban.", 3.0)
    assert [x[0] for x in w] == ["Good", "afternoon —", "I", "am", "Artemio", "Panganiban."]
    assert w[0][1] == 0.0 and w[-1][2] == 3.0
    assert all(a[2] <= b[1] + 1e-9 for a, b in zip(w, w[1:]))


def test_spread_words_empty(monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "spark")
    from voice import qwen
    assert qwen.spread_words("", 2.0) == []
    assert qwen.spread_words("Hello.", 0.0) == []


def test_qwen_not_configured_without_url(monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "spark")
    from voice import qwen
    monkeypatch.delenv("CJ_QWEN_TTS_URL", raising=False)
    assert not qwen.configured()
    with pytest.raises(qwen.QwenError) as e:
        qwen.synthesize("Hello.")
    assert e.value.reason == "error"


class _FakeClient:
    def __init__(self, reply):
        self.reply = reply
        outer = self

        class _T:
            def create(self, **kw):
                return outer.reply

        class _A:
            transcriptions = _T()

        self.audio = _A()


@pytest.mark.parametrize("reply, want", [
    ('{"text": "What is the rule of law?"}', "What is the rule of law?"),
    ("What is the rule of law?", "What is the rule of law?"),
])
def test_transcript_json_is_unwrapped(tmp_path, monkeypatch, reply, want):
    import wave
    import speech_engines as se
    wav = tmp_path / "q.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)
    monkeypatch.setattr(se, "_sync_client", lambda: _FakeClient(reply))
    assert se.transcribe_openai(wav, prompt="") == want


def test_dashboard_ports_follow_environment():
    src = (ROOT / "dashboard" / "ui_server.py").read_text(encoding="utf-8")
    assert 'os.environ.get("CJ_DASH_PORT", "").strip() or 8080' in src
    assert 'os.environ.get("CJ_DASH_HTTPS_PORT", "").strip() or 8443' in src


def test_robots_json_path_follows_environment(monkeypatch):
    """CJ_ROBOTS_JSON selects another machine map (the Spark's) for BOTH the
    robot (floor_lease) and the lease authority (console); unset = config/."""
    import floor_lease
    spark = ROOT / "deploy" / "spark" / "robots.json"
    monkeypatch.setenv("CJ_ROBOTS_JSON", str(spark))
    importlib.reload(floor_lease)
    assert Path(floor_lease.ROBOTS_PATH) == spark
    assert floor_lease.robots_config(spark)["authority"]["port"] == 8180
    monkeypatch.delenv("CJ_ROBOTS_JSON")
    importlib.reload(floor_lease)
    assert Path(floor_lease.ROBOTS_PATH) == ROOT / "config" / "robots.json"


def test_spark_dropin_carries_the_spark_settings():
    """The Spark's wakeword.conf is the one drop-in console.py reads, so every
    Spark setting must be in it, and nothing may still point at /home/pollen."""
    conf = (ROOT / "deploy" / "spark" / "systemd" / "supervaise.service.d"
            / "wakeword.conf").read_text(encoding="utf-8")
    for line in ("Environment=CJ_TTS_ORDER=spark", "Environment=OPENAI_STT_MODEL=whisper",
                 "Environment=CJ_REACHY_PORT=8010", "Environment=CJ_AEC_REF_FEED=0",
                 "Environment=CJ_QWEN_TTS_URL=http://127.0.0.1:8091"):
        assert line in conf
    assert "/home/pollen" not in conf


def test_reachy_port_is_optional_in_the_robot():
    src = (ROOT / "app" / "main_voice_robot.py").read_text(encoding="utf-8")
    assert 'os.environ.get("CJ_REACHY_PORT", "").strip()' in src
    assert 'ReachyMini(media_backend="no_media")' in src     # default path unchanged
