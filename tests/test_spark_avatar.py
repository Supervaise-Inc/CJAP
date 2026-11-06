"""The local video avatar on the DGX Spark (2026-11-06): deploy/spark/avatar.

cjap-avatar stands in for HeyGen LiveAvatar: CJAP's /face-avatar page and the
dashboard make the same calls (dashboard/ui_page_face.py), now to
CJ_LIVEAVATAR_URL. What is asserted:

  * ui_page_face's LiveAvatar base URL follows CJ_LIVEAVATAR_URL (default unchanged);
  * ClipAudio slices clips into 960-sample frames, flags each clip's first slice,
    pads a clip's tail, and clears on interrupt;
  * the server answers the page's contract end to end, with LiveKit stubbed and
    the "still" engine: token (key and avatar checked) -> start (livekit_url,
    client token, ws_url) -> the control socket says "connected", answers
    keep_alive, turns a clip into agent.speak_started -> interrupt -> stop;
    /v1/avatars/{id} gives what /maintain validates.

Needs fastapi + httpx for the server part (the cjap-avatar image has them; CJAP's
app venv may not, then that part is skipped).

Run:  app/.venv/bin/python -m pytest tests/test_spark_avatar.py -q
"""
from __future__ import annotations

import base64
import importlib
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
AV = ROOT / "deploy" / "spark" / "avatar"
sys.path.insert(0, str(AV))
sys.path.insert(0, str(ROOT / "dashboard"))


def test_liveavatar_url_follows_environment(monkeypatch):
    import ui_page_face
    monkeypatch.delenv("CJ_LIVEAVATAR_URL", raising=False)
    importlib.reload(ui_page_face)
    assert ui_page_face.LIVEAVATAR_URL == "https://api.liveavatar.com"
    monkeypatch.setenv("CJ_LIVEAVATAR_URL", "http://127.0.0.1:8092/")
    importlib.reload(ui_page_face)
    assert ui_page_face.LIVEAVATAR_URL == "http://127.0.0.1:8092"
    monkeypatch.delenv("CJ_LIVEAVATAR_URL")
    importlib.reload(ui_page_face)


def test_clip_audio_frames_clips():
    from engines.base import ClipAudio
    a = ClipAudio()
    a.push(np.ones(1500, np.int16).tobytes())
    a.push(np.ones(500, np.int16).tobytes())
    a.end()
    a.push((2 * np.ones(960, np.int16)).tobytes())       # second clip, still open
    got = [a.take() for _ in range(5)]
    assert [(None if s is None else len(s), f) for s, f in got] == \
        [(960, True), (960, False), (960, False), (960, True), (None, False)]
    assert got[2][0][-1] == 0                             # tail padded with silence
    a.push(np.ones(10, np.int16).tobytes())
    a.clear()
    assert a.take() == (None, False) and a.available() == 0


# ---- the server, with LiveKit stubbed ------------------------------------------
class _Any:
    """Accepts any attribute, call or chain."""
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, name):
        return _Any()

    def __call__(self, *a, **k):
        return _Any()


def _livekit_stub():
    lk = types.ModuleType("livekit")
    api = types.SimpleNamespace()

    class AccessToken:
        def __init__(self, k, s):
            self.parts = []

        def __getattr__(self, name):
            def f(*a, **k):
                self.parts.append(name)
                return self
            return f

        def to_jwt(self):
            return "jwt-" + "-".join(self.parts)

    api.AccessToken = AccessToken
    api.VideoGrants = _Any
    rtc = types.SimpleNamespace()

    class Room:
        def __init__(self):
            self.local_participant = types.SimpleNamespace(publish_track=self._pub)

        async def _pub(self, *a, **k):
            return None

        async def connect(self, *a, **k):
            return None

        async def disconnect(self):
            return None

    class AVSynchronizer:
        def __init__(self, **k):
            pass

        async def push(self, frame):
            return None

        def clear_queue(self):
            pass

        async def aclose(self):
            pass

    rtc.Room, rtc.AVSynchronizer = Room, AVSynchronizer
    for n in ("RoomOptions", "AudioSource", "VideoSource", "TrackPublishOptions",
              "VideoEncoding", "VideoFrame", "AudioFrame"):
        setattr(rtc, n, _Any)
    rtc.LocalAudioTrack = rtc.LocalVideoTrack = _Any()
    rtc.TrackSource = rtc.VideoCodec = rtc.VideoBufferType = _Any()
    lk.api, lk.rtc = api, rtc
    return lk


@pytest.fixture
def client(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    cv2 = pytest.importorskip("cv2")
    from fastapi.testclient import TestClient
    photo = tmp_path / "p.jpg"
    cv2.imwrite(str(photo), np.full((64, 64, 3), 128, np.uint8))
    monkeypatch.setitem(sys.modules, "livekit", _livekit_stub())
    for k, v in {"AVATAR_API_KEY": "k" * 32, "AVATAR_ID": "c0ffee00-0000-4000-8000-000000000001",
                 "AVATAR_PUBLIC_HOST": "192.168.1.201", "LIVEKIT_API_KEY": "avatarkey",
                 "LIVEKIT_API_SECRET": "s" * 32, "AVATAR_ENGINE": "still",
                 "AVATAR_PHOTO": str(photo), "AVATAR_SIZE": "64"}.items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("avatar_server", None)
    import avatar_server
    with TestClient(avatar_server.app) as c:
        c.srv = avatar_server
        yield c


def test_server_speaks_the_liveavatar_contract(client):
    key = {"X-API-KEY": "k" * 32}
    aid = "c0ffee00-0000-4000-8000-000000000001"
    assert client.post("/v1/sessions/token", json={"avatar_id": aid}, headers={"X-API-KEY": "no"}).status_code == 401
    bad = client.post("/v1/sessions/token", json={"avatar_id": "deadbeef"}, headers=key)
    assert bad.status_code == 404 and bad.json()["data"][0]["message"]
    av = client.get(f"/v1/avatars/{aid}", headers=key).json()["data"]
    assert av["id"] == aid and av["status"] == "ACTIVE" and av["is_expired"] is False

    tok = client.post("/v1/sessions/token", json={"mode": "LITE", "avatar_id": aid,
                                                  "is_sandbox": False}, headers=key).json()["data"]["session_token"]
    sd = client.post("/v1/sessions/start", headers={"Authorization": "Bearer " + tok}).json()["data"]
    assert sd["livekit_url"] == "ws://192.168.1.201:7880"
    assert sd["livekit_client_token"].startswith("jwt-")
    assert sd["ws_url"] == f"ws://192.168.1.201:8092/v1/ws?session={tok}"

    with client.websocket_connect(f"/v1/ws?session={tok}") as ws:
        assert json.loads(ws.receive_text()) == {"type": "session.state_updated", "state": "connected"}
        ws.send_text(json.dumps({"type": "session.keep_alive", "event_id": "1"}))
        assert json.loads(ws.receive_text())["type"] == "session.keep_alive"
        pcm = np.ones(24000 // 2, np.int16).tobytes()           # 0.5 s clip
        ws.send_text(json.dumps({"type": "agent.speak", "audio": base64.b64encode(pcm).decode()}))
        ws.send_text(json.dumps({"type": "agent.speak_end", "event_id": "2"}))
        seen = []
        for _ in range(6):
            m = json.loads(ws.receive_text())
            seen.append(m["type"])
            if m["type"] == "agent.speak_started":
                break
        assert "agent.speak_started" in seen
        ws.send_text(json.dumps({"type": "agent.interrupt"}))
        types_after = [json.loads(ws.receive_text())["type"] for _ in range(1)]
        assert "agent.speak_ended" in types_after or "agent.speak_started" in types_after

    assert client.post("/v1/sessions/stop", json={"reason": "USER_CLOSED"},
                       headers={"Authorization": "Bearer " + tok}).status_code == 200
    assert client.srv.STATE["session"] is None
    h = client.get("/health").json()
    assert h["ok"] and h["engine"] == "still" and h["speak_started"] >= 1
