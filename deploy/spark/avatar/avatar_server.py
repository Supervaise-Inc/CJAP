"""cjap-avatar — a self-hosted stand-in for HeyGen LiveAvatar (LITE mode) on the DGX Spark.

CJAP's /face-avatar page (dashboard/ui_page_face.py) drives LiveAvatar through
four REST calls and one WebSocket. With CJ_LIVEAVATAR_URL pointing here, the page
and the dashboard talk to this server instead, unchanged, and the face comes from
a talking-head model on the Spark's GPU, streamed through a local LiveKit server.

REST (the subset ui_page_face.py uses; shapes copied from its parser):
    POST /v1/sessions/token   X-API-KEY  {mode, avatar_id, is_sandbox} -> {"data": {"session_token"}}
    POST /v1/sessions/start   Bearer     -> {"data": {livekit_url, livekit_client_token, ws_url, session_id}}
    POST /v1/sessions/stop    Bearer     {reason} -> {"data": {}}
    GET  /v1/avatars/{id}     X-API-KEY  -> {"data": {id, name, status, preview_url, default_voice, is_expired}}
    GET  /health
Errors come back as HTTP 4xx with {"data": [{"message": ...}]}, the shape the
dashboard reads the reasons from.

WebSocket ws_url (/v1/ws?session=TOKEN), JSON messages:
    page -> here: agent.speak {audio: base64 PCM16 24 kHz mono}, agent.speak_end,
                  agent.interrupt, agent.start_listening, agent.stop_listening,
                  session.keep_alive
    here -> page: session.state_updated {state: "connected"} once the avatar is
                  publishing; agent.speak_started when the first frame of a clip
                  goes out (the page measures the lag from it and CJAP delays or
                  mutes the robot by that much); agent.speak_ended; keep_alive acks.

Media: one LiveKit room per session; this server joins it as "avatar" and
publishes one audio track (24 kHz mono) and one video track (25 fps), each video
frame pushed together with its own 40 ms audio slice through rtc.AVSynchronizer,
so the browser plays lips and voice together.

Settings (environment):
    AVATAR_API_KEY      the key CJAP's assets/liveavatar.json carries (required)
    AVATAR_ID           the avatar id it carries (hex UUID, required)
    AVATAR_NAME         shown on /maintain (default "Panganiban (Spark)")
    AVATAR_ENGINE       ditto | wav2lip | still (default ditto)
    AVATAR_PUBLIC_HOST  host the BROWSER uses for ws_url / livekit_url (e.g. 192.168.1.201)
    AVATAR_PORT         this server's port (default 8092)
    LIVEKIT_URL         default ws://<AVATAR_PUBLIC_HOST>:7880
    LIVEKIT_API_KEY / LIVEKIT_API_SECRET   from livekit.yaml
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import queue
import secrets
import threading
import time
from datetime import timedelta

import numpy as np
from fastapi import FastAPI, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from livekit import api, rtc

from engines import load_engine

API_KEY = os.environ["AVATAR_API_KEY"]
AVATAR_ID = os.environ["AVATAR_ID"].lower()
AVATAR_NAME = os.environ.get("AVATAR_NAME", "Panganiban (Spark)")
PUBLIC_HOST = os.environ["AVATAR_PUBLIC_HOST"]
PORT = int(os.environ.get("AVATAR_PORT", "8092"))
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", f"ws://{PUBLIC_HOST}:7880")
LK_KEY = os.environ["LIVEKIT_API_KEY"]
LK_SECRET = os.environ["LIVEKIT_API_SECRET"]
SR = 24000
FPS = 25
SPF = SR // FPS            # 960 samples = 40 ms per video frame

app = FastAPI(title="cjap-avatar")
ENGINE = None              # loaded once at startup, kept for every session
STATE = {"session": None, "room": None, "ws": None, "epoch": 0, "frames": 0,
         "speak_started": 0, "late_frames": 0, "loaded_s": None, "error": None}
_frames: "queue.Queue" = queue.Queue(maxsize=8)   # ~320 ms jitter buffer engine -> publisher
_lock = threading.Lock()


def _err(status: int, message: str) -> JSONResponse:
    return JSONResponse({"code": status, "message": message, "data": [{"message": message}]},
                        status_code=status)


def _bearer(auth: str | None) -> str:
    return (auth or "").removeprefix("Bearer ").strip()


def _mint(identity: str, room: str, publish: bool) -> str:
    return (api.AccessToken(LK_KEY, LK_SECRET).with_identity(identity).with_name(identity)
            .with_ttl(timedelta(hours=8))
            .with_grants(api.VideoGrants(room_join=True, room=room, can_publish=publish,
                                         can_subscribe=True, can_publish_data=publish))
            .to_jwt())


# ── engine thread: produce one (rgb, pcm|None, first) item per frame ─────────────
def _engine_loop():
    while True:
        try:
            epoch = STATE["epoch"]
            rgb, pcm, first = ENGINE.next_frame()
            STATE["error"] = None
            _frames.put((epoch, rgb, pcm, first))        # blocks when the publisher is behind
        except Exception as e:                            # keep the face alive, report it
            STATE["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            time.sleep(0.04)


# ── publisher: one LiveKit room per session ───────────────────────────────────────
async def _publish(room_name: str, connected: asyncio.Event):
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, _mint("avatar", room_name, True),
                       rtc.RoomOptions(auto_subscribe=False))
    asrc = rtc.AudioSource(SR, 1, queue_size_ms=100)
    vsrc = rtc.VideoSource(ENGINE.width, ENGINE.height)
    lp = room.local_participant
    await lp.publish_track(rtc.LocalAudioTrack.create_audio_track("avatar_audio", asrc),
                           rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))
    await lp.publish_track(
        rtc.LocalVideoTrack.create_video_track("avatar_video", vsrc),
        rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_CAMERA, simulcast=False,
                                video_codec=rtc.VideoCodec.VP8,
                                video_encoding=rtc.VideoEncoding(max_bitrate=2_000_000,
                                                                 max_framerate=FPS)))
    av = rtc.AVSynchronizer(audio_source=asrc, video_source=vsrc, video_fps=FPS,
                            video_queue_size_ms=100)
    STATE["room"], STATE["av"] = room, av
    connected.set()
    loop = asyncio.get_running_loop()
    try:
        while STATE["room"] is room:
            epoch, rgb, pcm, first = await loop.run_in_executor(None, _frames.get)
            if epoch != STATE["epoch"]:
                continue                                   # rendered before an interrupt
            frame = rtc.VideoFrame(ENGINE.width, ENGINE.height, rtc.VideoBufferType.RGB24,
                                   np.ascontiguousarray(rgb, dtype=np.uint8).tobytes())
            await av.push(frame)
            if pcm is not None:
                await av.push(rtc.AudioFrame(np.ascontiguousarray(pcm, dtype=np.int16).tobytes(),
                                             SR, 1, SPF))
            STATE["frames"] += 1
            if first:
                STATE["speak_started"] += 1
                await _ws_send({"type": "agent.speak_started", "event_id": str(time.time())})
    finally:
        try:
            await av.aclose()
        except Exception:
            pass
        await room.disconnect()


async def _ws_send(msg: dict):
    ws = STATE.get("ws")
    if ws is not None:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            pass


async def _interrupt():
    STATE["epoch"] += 1
    ENGINE.interrupt()
    while True:                                            # drop frames already rendered
        try:
            _frames.get_nowait()
        except queue.Empty:
            break
    av = STATE.get("av")
    if av is not None:
        try:
            await av.clear_queue()        # a coroutine in livekit 1.2.x
        except Exception:
            pass


async def _end_session():
    room = STATE["room"]
    task = STATE.get("task")
    STATE.update(session=None, room=None, av=None, task=None)
    await _interrupt()
    if task is not None and not task.done():
        task.cancel()
    ws = STATE.get("ws")
    STATE["ws"] = None
    if ws is not None:
        try:
            await ws.close()
        except Exception:
            pass
    if room is not None:
        try:
            await room.disconnect()
        except Exception:
            pass


# ── REST ─────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def _startup():
    global ENGINE
    t0 = time.monotonic()
    ENGINE = load_engine(os.environ.get("AVATAR_ENGINE", "ditto"))
    STATE["loaded_s"] = round(time.monotonic() - t0, 1)
    threading.Thread(target=_engine_loop, daemon=True, name="engine").start()
    print(f"[cjap-avatar] engine {ENGINE.name} {ENGINE.width}x{ENGINE.height} ready "
          f"in {STATE['loaded_s']} s", flush=True)


@app.get("/health")
def health():
    ok = ENGINE is not None and ENGINE.healthy() and STATE["error"] is None
    return {"ok": ok, "engine": getattr(ENGINE, "name", None),
            "size": [getattr(ENGINE, "width", 0), getattr(ENGINE, "height", 0)],
            "session": bool(STATE["session"]), "frames": STATE["frames"],
            "speak_started": STATE["speak_started"], "loaded_s": STATE["loaded_s"],
            "engine_fps": round(getattr(ENGINE, "fps_measured", 0.0), 1),
            "error": STATE["error"]}


@app.post("/v1/sessions/token")
async def token(request: Request, x_api_key: str | None = Header(None)):
    if x_api_key != API_KEY:
        return _err(401, "invalid API key")
    body = await request.json()
    if str(body.get("avatar_id", "")).lower() != AVATAR_ID:
        return _err(404, "You dont have access to this avatar")
    return {"code": 1000, "data": {"session_token": secrets.token_urlsafe(24)}}


@app.post("/v1/sessions/start")
async def start(authorization: str | None = Header(None)):
    tok = _bearer(authorization)
    if len(tok) < 16:
        return _err(401, "missing session token")
    if STATE["session"] and STATE["session"] != tok:
        await _end_session()                              # CJAP allows one page; newest wins
    room_name = "cjap-" + tok[:10]
    STATE["session"] = tok
    connected = asyncio.Event()
    STATE["task"] = asyncio.get_running_loop().create_task(_publish(room_name, connected))
    try:
        await asyncio.wait_for(connected.wait(), timeout=10)
    except asyncio.TimeoutError:
        STATE["session"] = None
        STATE["task"].cancel()
        return _err(503, f"could not join LiveKit at {LIVEKIT_URL}")
    return {"code": 1000, "data": {
        "session_id": room_name,
        "livekit_url": LIVEKIT_URL,
        "livekit_client_token": _mint("viewer-" + secrets.token_hex(3), room_name, False),
        "ws_url": f"ws://{PUBLIC_HOST}:{PORT}/v1/ws?session={tok}",
    }}


@app.post("/v1/sessions/stop")
async def stop(authorization: str | None = Header(None)):
    if STATE["session"] and _bearer(authorization) == STATE["session"]:
        await _end_session()
    return {"code": 1000, "data": {}}


@app.get("/v1/avatars/{avatar_id}")
def avatar(avatar_id: str, x_api_key: str | None = Header(None)):
    if x_api_key != API_KEY:
        return _err(401, "invalid API key")
    if avatar_id.lower() != AVATAR_ID:
        return _err(404, "avatar not found")
    return {"code": 1000, "data": {"id": AVATAR_ID, "name": AVATAR_NAME, "status": "ACTIVE",
                                   "preview_url": None, "default_voice": {"name": "CJAP voice"},
                                   "is_expired": False}}


# ── control socket ───────────────────────────────────────────────────────────────
@app.websocket("/v1/ws")
async def control(ws: WebSocket, session: str = ""):
    await ws.accept()
    if not session or session != STATE["session"]:
        await ws.close(code=4401)
        return
    old = STATE.get("ws")
    STATE["ws"] = ws
    if old is not None and old is not ws:
        try:
            await old.close()
        except Exception:
            pass
    await ws.send_text(json.dumps({"type": "session.state_updated", "state": "connected"}))
    try:
        while True:
            raw = await ws.receive_text()
            try:
                m = json.loads(raw)
            except ValueError:
                continue                                  # not JSON: ignore it
            t = m.get("type") if isinstance(m, dict) else None
            if t == "agent.speak":
                ENGINE.push_audio(base64.b64decode(m.get("audio", "")))
            elif t == "agent.speak_end":
                ENGINE.end_clip()
                await ws.send_text(json.dumps({"type": "agent.speak_end_ack"}))
            elif t == "agent.interrupt":
                await _interrupt()
                await ws.send_text(json.dumps({"type": "agent.speak_ended", "interrupted": True}))
            elif t in ("agent.start_listening", "agent.stop_listening"):
                ENGINE.set_listening(t == "agent.start_listening")
            elif t == "session.keep_alive":
                await ws.send_text(json.dumps({"type": "session.keep_alive",
                                               "event_id": m.get("event_id")}))
    except WebSocketDisconnect:
        pass
    except Exception as e:                                 # closed server-side, bad audio, ...
        print(f"[cjap-avatar] control socket closed: {type(e).__name__}: {str(e)[:120]}", flush=True)
    finally:
        if STATE.get("ws") is ws:
            STATE["ws"] = None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, workers=1)
