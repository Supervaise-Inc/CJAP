"""LiveAvatar sessions (2026-09-15): a page that is gone must not lock the others out.

User: "why is CJAP avatar not there". A reloaded face page kept its session on
the dashboard for 15 minutes and every avatar page after it was refused.
"""
from __future__ import annotations

import pathlib
import sys
import time

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dashboard"))
import ui_page_face as face  # noqa: E402


@pytest.fixture
def api(monkeypatch):
    calls, stops = [], []

    def req(path, payload, headers):
        calls.append(path)
        if path.endswith("/sessions/token"):
            return {"data": {"session_token": f"session-token-{len(calls):06d}"}}
        if path.endswith("/sessions/start"):
            return {"data": {"livekit_url": "wss://example", "livekit_client_token": "c"}}
        return {}
    monkeypatch.setattr(face, "_liveavatar_request", req)
    monkeypatch.setattr(face, "_read_json", lambda p: {"api_key": "k", "avatar_id": "a", "sandbox": True})
    monkeypatch.setattr(face, "_stop_later", stops.append)
    face.avatar_session_release()
    yield stops
    face.avatar_session_release()


def test_a_second_page_is_refused_while_the_first_still_reports(api):
    ok, sd = face.avatar_session()
    assert ok
    face.avatar_session_seen(sd["session_token"][-12:])
    ok2, msg = face.avatar_session()
    assert not ok2 and "already live" in msg and api == []


def test_a_just_opened_session_is_protected_before_its_first_report(api):
    assert face.avatar_session()[0]
    assert not face.avatar_session()[0]


def test_a_reloaded_or_closed_page_no_longer_locks_the_avatar_out(api):
    ok, sd = face.avatar_session()
    tok = sd["session_token"]
    face._LIVE_SESSION.update(at=time.time() - 400, seen=time.time() - 60)   # silent for a minute
    ok2, sd2 = face.avatar_session()
    assert ok2 and sd2["session_token"] != tok
    assert api == [tok]                                   # the abandoned one is stopped, not billed on


def test_only_the_holders_heartbeat_counts_and_pagehide_hands_it_back(api):
    ok, sd = face.avatar_session()
    tok = sd["session_token"]
    face._LIVE_SESSION.update(at=time.time() - 60, seen=0.0)
    face.avatar_session_seen("another-page-tail")
    face.avatar_session_seen("")
    face.avatar_session_seen(None)
    assert face._LIVE_SESSION["seen"] == 0.0
    face.avatar_stop(tok)                                 # what the pagehide beacon calls
    assert face._LIVE_SESSION["token"] is None
    page = face.FACE_AVATAR_PAGE
    assert 'addEventListener("pagehide"' in page and "session: sessTok ? sessTok.slice(-12) : null" in page
    assert '"/api/avatar-stop"' in page and face.FACE_CAMERA_PAGE.count('addEventListener("pagehide"') == 1


def test_the_robot_does_not_hold_an_answer_for_a_page_whose_start_was_refused(monkeypatch, tmp_path):
    import os
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    import json
    import main_voice_robot as mvr
    f = tmp_path / "page.json"
    monkeypatch.setattr(mvr, "AVATAR_PAGE_STATUS", str(f))
    monkeypatch.setattr(mvr, "_avatar_mode", lambda: True)
    monkeypatch.setenv("CJ_AVATAR_READY_WAIT_S", "0.3")

    def report(**kw):
        f.write_text(json.dumps({"ts": time.time(), "ready": False, "stopped": False, **kw}))
    report(session=None, starting=False, status="session failed: already live on another page")
    assert mvr._avatar_wait_ready() == 0.0                     # refused page: no hold at all
    report(session="abcdefghijkl", starting=False)
    assert mvr._avatar_wait_ready() >= 0.25                    # holder still connecting: held
    report(starting=True)
    assert mvr._avatar_wait_ready() >= 0.25                    # a start in flight: held
    report()                                                   # an old page without the keys: as before
    assert mvr._avatar_wait_ready() >= 0.25


def test_a_session_that_never_connects_is_handed_back():
    page = face.FACE_AVATAR_PAGE
    assert "const up = await connected;" in page and "if (!up){" in page
    assert "if (!ready && !sessTok) return;" in page           # an unready session still parks when idle
    assert "starting: !!startP" in page


def test_a_sandbox_avatar_page_never_becomes_the_shared_face():
    page = face.FACE_AVATAR_PAGE
    assert "confSandbox = !!(stt.avatar_conf && stt.avatar_conf.sandbox)" in page
    assert "if (confSandbox){ portraitSent = true;" in page
