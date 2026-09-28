"""/maintain API keys card (2026-09-28): add / replace / remove the keys in
app/.env. A key value goes in and never comes back out."""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dashboard"))
import ui_common  # noqa: E402

FAKE = "sk-test-abcdefghijklmnop1234"


@pytest.fixture
def env(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("# secrets\nANTHROPIC_API_KEY=sk-ant-old-000000000000WXYZ\nCJ_TTS_ORDER=fish\n")
    monkeypatch.setattr(ui_common, "APP_ENV", str(p))
    restarts = []
    monkeypatch.setattr(ui_common, "_restart_app", lambda: restarts.append(1))
    monkeypatch.setattr(ui_common, "_probe_key", lambda env, key: ("ok", "accepted"))
    return p, restarts


def test_listing_never_carries_a_value(env):
    out = ui_common.api_keys()
    row = next(k for k in out["keys"] if k["env"] == "ANTHROPIC_API_KEY")
    assert row["set"] and row["hint"] == "…WXYZ"
    assert "sk-ant-old" not in str(out)
    assert not next(k for k in out["keys"] if k["env"] == "FISH_API_KEY")["set"]


def test_add_replace_keeps_other_lines(env):
    p, restarts = env
    ok, msg = ui_common.api_key_set({"env": "FISH_API_KEY", "value": FAKE})
    assert ok and "1234" in msg and restarts == [1]
    ok, _ = ui_common.api_key_set({"env": "ANTHROPIC_API_KEY", "value": FAKE})
    text = p.read_text()
    assert f"FISH_API_KEY={FAKE}" in text and f"ANTHROPIC_API_KEY={FAKE}" in text
    assert "# secrets" in text and "CJ_TTS_ORDER=fish" in text
    assert (p.parent / ".env.bak-keys").exists()


def test_remove(env):
    p, restarts = env
    ok, _ = ui_common.api_key_set({"env": "ANTHROPIC_API_KEY", "remove": True})
    assert ok and "ANTHROPIC_API_KEY" not in p.read_text() and restarts == [1]
    ok, msg = ui_common.api_key_set({"env": "ANTHROPIC_API_KEY", "remove": True})
    assert ok and "no change" in msg and restarts == [1]


def test_refused_and_unknown_and_injection(env, monkeypatch):
    p, restarts = env
    before = p.read_text()
    assert not ui_common.api_key_set({"env": "PATH", "value": FAKE})[0]
    assert not ui_common.api_key_set({"env": "OPENAI_API_KEY", "value": FAKE + "\nCJ_X=1"})[0]
    monkeypatch.setattr(ui_common, "_probe_key", lambda env, key: ("rejected", "HTTP 401"))
    ok, msg = ui_common.api_key_set({"env": "OPENAI_API_KEY", "value": FAKE})
    assert not ok and "not saved" in msg
    assert p.read_text() == before and restarts == []


def test_unverified_needs_force(env, monkeypatch):
    p, _ = env
    monkeypatch.setattr(ui_common, "_probe_key", lambda env, key: ("unverified", "URLError"))
    ok, out = ui_common.api_key_set({"env": "OPENAI_API_KEY", "value": FAKE})
    assert not ok and out["need_force"] and "OPENAI_API_KEY" not in p.read_text()
    ok, msg = ui_common.api_key_set({"env": "OPENAI_API_KEY", "value": FAKE, "force": True})
    assert ok and "NOT checked" in msg and f"OPENAI_API_KEY={FAKE}" in p.read_text()
