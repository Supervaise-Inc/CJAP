"""The local video avatar on the DGX Spark (2026-11-06): deploy/spark/avatar.

cjap-avatar stands in for HeyGen LiveAvatar: CJAP's /face-avatar page and the
dashboard make the same calls (dashboard/ui_page_face.py), now to
CJ_LIVEAVATAR_URL. What is asserted:

  * ui_page_face's LiveAvatar base URL follows CJ_LIVEAVATAR_URL (default unchanged);
  * ClipAudio slices clips into 960-sample frames, flags each clip's first slice,
    pads a clip's tail, and clears on interrupt;
  * the AVTR-1 engine (with a stub pipeline in place of AVTR-1) feeds 6480-sample
    windows, pairs frame k with clip slice k, flags the clip's first frame, keeps
    the microphone out of the listen track while the face speaks, and mutes
    rendered frames on interrupt;
  * I420 frames convert for the bench's video writer; prepare_photo writes W x H;
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


# ---- the AVTR-1 engine, with a stub pipeline -------------------------------------
class _Frame:
    def __init__(self, data):
        self.data = data


class _StubPipeline:
    """Records each window; returns 5 frames whose pixels carry their frame index."""
    def __init__(self):
        self.calls = []

    def process_chunk(self, avatar, chunk, state, options):
        n = state or 0
        self.calls.append((len(chunk.audio_speech), len(chunk.audio_listen),
                           float(np.abs(chunk.audio_listen).max())))
        return n + 1, iter([_Frame(np.full((6, 4), 5 * n + j, np.uint8)) for j in range(5)])


class _Mic:
    def read(self, n):
        return np.full(n, 0.5, np.float32)


def _avtr1(monkeypatch, quiet_s=1.5):
    pytest.importorskip("soxr")
    from engines import avtr1
    monkeypatch.setattr(avtr1, "QUIET_AFTER_SPEECH_S", quiet_s)
    pipe = _StubPipeline()
    return avtr1.Avtr1Engine(pipeline=pipe, avatar=object(), options=None, listen=_Mic()), pipe


def _clip(n_frames):
    """A clip whose frame i slice is all (i + 1)."""
    return np.concatenate([np.full(960, i + 1, np.int16) for i in range(n_frames)]).tobytes()


def test_avtr1_engine_pairs_frames_with_their_audio(monkeypatch):
    eng, pipe = _avtr1(monkeypatch, quiet_s=0.0)
    eng.push_audio(_clip(12))
    eng.end_clip()
    got = [eng.next_frame() for _ in range(25)]
    assert [int(img[0, 0]) for img, _, _ in got] == list(range(25))      # frames in order
    assert [None if p is None else int(p[0]) for _, p, _ in got] == list(range(1, 13)) + [None] * 13
    assert [f for _, _, f in got] == [True] + [False] * 24                # clip start flagged once
    assert all(c[:2] == (6480, 6480) for c in pipe.calls)
    assert pipe.calls[0][2] == 0.0                     # speaking: the mic is not in the listen track
    assert pipe.calls[-1][2] == 0.5                    # silent again: the visitor is


def test_avtr1_engine_interrupt_mutes_rendered_frames(monkeypatch):
    eng, _ = _avtr1(monkeypatch)
    eng.push_audio(_clip(40))
    eng.end_clip()
    _, pcm, first = eng.next_frame()
    assert pcm is not None and first
    eng.interrupt()
    rest = [eng.next_frame() for _ in range(15)]
    assert all(p is None and not f for _, p, f in rest)


def test_frame_to_bgr_handles_i420():
    pytest.importorskip("cv2")
    from engines.base import frame_to_bgr
    eng = types.SimpleNamespace(pixfmt="i420", width=4, height=2)
    assert frame_to_bgr(eng, np.zeros((3, 4), np.uint8)).shape == (2, 4, 3)


def test_prepare_photo_makes_the_stream_size(tmp_path, monkeypatch):
    cv2 = pytest.importorskip("cv2")
    import prepare_photo
    src, dst = tmp_path / "s.jpg", tmp_path / "p.png"
    cv2.imwrite(str(src), np.full((300, 200, 3), 90, np.uint8))
    monkeypatch.setattr(sys, "argv", ["prepare_photo.py", str(src), str(dst), "128", "72"])
    assert prepare_photo.main() == 0
    assert cv2.imread(str(dst)).shape == (72, 128, 3)


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
                 "AVATAR_PHOTO": str(photo), "AVATAR_W": "64", "AVATAR_H": "48"}.items():
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
