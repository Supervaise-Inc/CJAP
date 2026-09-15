"""/stage and /monitor — two read-only display views (2026-09-14).

/stage    full-bleed face only, for a visitor. No text, no chrome, no cursor,
          no error state ever. The four states — idle, listening, thinking,
          speaking — must be legible at two metres with no labels, which is
          the whole job of the view.
/monitor  BOTH robots side by side, in the /audience gallery look, for an
          operator (2026-09-15): state, camera, question, answer, scrollback.
/display  one robot as a screen, in the same look (2026-09-15): avatar and
          camera in two gilt frames above the question and answer plaques.

/stage consumes ONE endpoint, /api/display, and nothing else. /monitor consumes
/api/monitor, which is this machine's /api/display document plus the other
machine's, fetched by this dashboard from that one. /api/display is
read-only: it reads the same /dev/shm files the dashboard already reads and
the console object already in this process. It starts no LiveAvatar session,
issues no command, writes no file, and calls nothing in the pipeline.

Three things learned from reading the existing avatar page, which shaped all
of this (see docs — ~/display_notes.docx):

  * avatar_session() (ui_page_face.py:855) creates a NEW PAID session on every
    call, with no registry and no reference count. Three pages open would be
    three paid sessions. Neither view here ever calls it.
  * the existing page WRITES: a 5 s heartbeat, a global avatar_cmd file where a
    Stop meant for one screen stops all of them, and an idle-loop recorder.
    These views write nothing, so they cannot disturb a turn or another screen.
  * EXHIBIT_JS hard-binds DOM ids with no null guards (its own comment says so
    at ui_page_audience.py:290). Reusing it piecemeal is how you get a blank
    page, so /stage carries its own small renderer instead.

The avatar picture itself: with no live session there is NO face image anywhere
on disk — the "portrait still" on /face-avatar is a canvas the page snapshots
out of the live video, so it is black until a session has run in that same
browser. The backdrop here is therefore PLUGGABLE: drop a file at
assets/portrait.{jpg,png,webp,mp4,webm} and both views use it; with no file
they fall back to a non-photographic form that carries the same four states.
Nothing needs to change in this file when the portrait appears.
"""
from __future__ import annotations

import json
import os
import re
import socket
import threading
import time
import urllib.parse
import urllib.request

from ui_common import (ASSETS, DASH_KEY, MUTED_FLAG, SPEAKING, TRANSCRIPT, TURN_META,
                       UI_REV, WAKE_LIVE, _read_json, _tail_jsonl, _health,
                       camera_off, cam_backend, motion_get)

STAGE_DOC = "/dev/shm/cj_stage.json"

# A backdrop, if one has been provided. Checked per request (cheap: one stat)
# so a portrait can be dropped in without restarting the dashboard.
PORTRAIT_NAMES = ("portrait.webm", "portrait.mp4", "portrait.webp",
                  "portrait.png", "portrait.jpg", "portrait.jpeg")
_VIDEO_EXT = (".webm", ".mp4")


def portrait():
    """-> {"file", "kind": "video"|"image", "v", ["eyes"]} or None when none is present.
    `v` changes whenever the file is replaced, so a page reloads the picture;
    `eyes` (see clean_eyes) is there only when it was stored with this very file."""
    try:
        for n in PORTRAIT_NAMES:
            path = os.path.join(ASSETS, n)
            if os.path.exists(path):
                st = os.stat(path)
                doc = {"file": n, "kind": "video" if n.endswith(_VIDEO_EXT) else "image",
                       "v": st.st_mtime_ns // 1_000_000}
                eyes = _stored_eyes(n, st.st_size)
                if eyes:
                    doc["eyes"] = eyes
                return doc
    except OSError:
        pass
    return None


# The face the /face-avatar page captures (2026-09-15, user: "why does the
# avatar not appear in the other UI"). The live face only exists inside that
# page's paid LiveAvatar session, and only one session may run, so /display,
# /monitor and /stage had nothing to show but the orb. The page already takes a
# still of the face for itself; it now also sends it here, where it becomes
# assets/portrait.jpg and every avatar frame draws it. It is forwarded to the
# other robot's dashboard so both serve the same face. An operator-provided
# portrait.webm/.mp4/.webp/.png still wins (PORTRAIT_NAMES order).
PORTRAIT_UPLOAD_MAX = 4_000_000
_JPEG_MAGIC = b"\xff\xd8\xff"


PORTRAIT_FACE = "portrait.json"   # the eyes of portrait.jpg, and the byte size they belong to


def clean_eyes(e):
    """Eye geometry from a browser, checked: 1-2 eyes of {c1: [x, y], c2: [x, y],
    up, lo} — corners and mid lids, all 0..1 of the picture, lower lid below the
    upper. -> the cleaned list, or None. It drives the blink (FACE_ANIM_JS)."""
    if not isinstance(e, list) or not 1 <= len(e) <= 2:
        return None

    def num(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            raise ValueError("not a 0..1 number")
        return round(float(v), 5)
    out = []
    try:
        for x in e:
            c1, c2 = list(x["c1"]), list(x["c2"])
            if len(c1) != 2 or len(c2) != 2:
                return None
            eye = {"c1": [num(c1[0]), num(c1[1])], "c2": [num(c2[0]), num(c2[1])],
                   "up": num(x["up"]), "lo": num(x["lo"])}
            if eye["lo"] <= eye["up"] or eye["c1"][0] == eye["c2"][0]:
                return None
            out.append(eye)
    except (KeyError, TypeError, ValueError):
        return None
    return out


def _stored_eyes(name, size):
    if name != "portrait.jpg":
        return None
    try:
        with open(os.path.join(ASSETS, PORTRAIT_FACE)) as f:
            d = json.load(f)
        return clean_eyes(d.get("eyes")) if d.get("size") == size else None
    except (OSError, ValueError, AttributeError):
        return None


def portrait_put(data, forward=True, con=None, post=None, eyes=None):
    """Store a captured face as assets/portrait.jpg, and its eyes beside it
    when the page found them. -> (ok, message)."""
    if not data or len(data) > PORTRAIT_UPLOAD_MAX or not data.startswith(_JPEG_MAGIC):
        return False, "not a JPEG portrait"
    eyes = clean_eyes(eyes)
    try:
        os.makedirs(ASSETS, exist_ok=True)
        tmp = os.path.join(ASSETS, ".portrait.jpg.part")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, os.path.join(ASSETS, "portrait.jpg"))
        face = os.path.join(ASSETS, PORTRAIT_FACE)
        if eyes:
            with open(face + ".part", "w") as f:
                json.dump({"size": len(data), "eyes": eyes}, f)
            os.replace(face + ".part", face)
        elif os.path.exists(face):
            os.unlink(face)
    except OSError as e:
        return False, f"could not save the portrait: {e}"
    if forward:
        threading.Thread(target=_portrait_forward, args=(data, con, post, eyes),
                         daemon=True, name="portrait-forward").start()
    return True, f"portrait saved ({len(data) // 1024} kB, {'eyes found' if eyes else 'no eyes'})"


def _http_post(url, data, timeout=4):
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "image/jpeg"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(4096)


def _portrait_forward(data, con=None, post=None, eyes=None):
    """Best effort: the other robot's dashboard gets the same face. Marked
    forwarded=1 so it is not sent back. A failure is logged, never raised."""
    try:
        if con is None:
            import console as con
        sources = con.ConfigSources()
        slots = sources.robots().get("slots") or {}
        me = my_slot(slots)
        extra = ("&eyes=" + urllib.parse.quote(json.dumps(eyes, separators=(",", ":")), safe="")
                 if eyes else "")
        for slot, machine in slots.items():
            if slot == me or slot not in SLOTS or not machine:
                continue
            url = (_peer_base(sources, str(machine)) + "/api/avatar-portrait?forwarded=1&key="
                   + urllib.parse.quote(DASH_KEY) + extra)
            try:
                (post or _http_post)(url, data)
                print(f"[portrait] forwarded to {slot}", flush=True)
            except Exception as e:
                print(f"[portrait] forward to {slot} failed: {type(e).__name__}: {e}", flush=True)
    except Exception as e:
        print(f"[portrait] forward skipped: {type(e).__name__}: {e}", flush=True)


def portrait_upload(h, params):
    """POST /api/avatar-portrait?key=[&eyes=<json>][&forwarded=1], raw JPEG bytes."""
    try:
        n = int(h.headers.get("Content-Length", 0))
    except (TypeError, ValueError):
        n = 0
    if n <= 0 or n > PORTRAIT_UPLOAD_MAX:
        h.close_connection = True   # do not read a body we refuse
        return False, "portrait missing or too large"
    data = h.rfile.read(n)
    eyes = None
    if params.get("eyes"):
        try:
            eyes = json.loads(urllib.parse.unquote(params["eyes"]))
        except ValueError:
            eyes = None
    return portrait_put(data, forward=params.get("forwarded") != "1", eyes=eyes)


# ---------------------------------------------------------------------------
# Robot state — one definition, server side
# ---------------------------------------------------------------------------
# A server-side mirror of robotMode() from ui_page_maintenance.py:936, so that
# /stage and /monitor cannot drift apart from each other or from /maintain, and
# so neither has to re-implement the brittle version in the browser.
_STEP_ORDER = ("transcribe", "route", "compose", "fidelity")
_STEP_FIELDS = ("state", "detail", "t", "topic", "confidence", "scope", "reason")


def _robot_state(sp, stg, turns, health, muted, now):
    """-> {"st", "since", "detail"} where st is one of
    down | speaking | listening | thinking | muted | idle."""
    if health.get("supervaise") is False:
        return {"st": "down", "since": None, "detail": "the voice app is not running"}

    users = [t for t in turns if t.get("role") == "user"]
    cjs = [t for t in turns if t.get("role") == "cj"]
    last_u = users[-1] if users else None
    last_c = cjs[-1] if cjs else None
    steps = (stg or {}).get("steps") or {}
    tr = steps.get("transcribe") or {}

    spoken = (sp or {}).get("spoken") or []
    if sp and not sp.get("done") and spoken:
        return {"st": "speaking", "since": sp.get("play_ts") or sp.get("ts"),
                "detail": f"sentence {len(spoken)}"}

    listening = (tr.get("state") == "active"
                 and stg and (now - (stg.get("ts") or 0)) < 60)
    q_now = bool(last_u and stg and last_u.get("ts", 0) >= (stg.get("turn_ts") or 0) - 1)
    if listening and not q_now:
        return {"st": "listening", "since": stg.get("ts"),
                "detail": tr.get("detail") or "mic open"}

    if last_u and (not sp or last_u.get("ts", 0) > (sp.get("ts") or 0)) \
            and (not last_c or last_u.get("ts", 0) > last_c.get("ts", 0)):
        active = [k for k in _STEP_ORDER
                  if (steps.get(k) or {}).get("state") == "active"]
        return {"st": "thinking", "since": last_u.get("ts"),
                "detail": (active[-1] if active else "working")}

    if muted:
        return {"st": "muted", "since": None, "detail": "microphone muted"}

    end_ts = (sp or {}).get("ts") if (sp and sp.get("done") and spoken) else (
        last_c.get("ts") if last_c else None)
    return {"st": "idle", "since": end_ts, "detail": ""}


# ---------------------------------------------------------------------------
# Turn assembly — question, answer, gates, latency
# ---------------------------------------------------------------------------
# A gate leaves its mark as a transcript NOTE (main_voice_robot.py:3107-3120
# for the answer gate and the fidelity audit, and :3268 for a premise decline),
# so the notes are matched back to the turn they belong to rather than invented.
_GATE_MARKS = (
    ("answer gate blocked", "answer gate"),
    ("full-answer audit", "answer audit"),
    ("fidelity audit flagged", "fidelity"),
    ("premise declined", "declined"),
    ("offline during compose", "offline"),
    ("API error during compose", "api error"),
    ("canned answer", "curated"),
    ("interrupted by wake phrase", "interrupted"),
    ("raw ASR", None),        # carries the pre-correction transcript; never public
)


def _gate_tags(note_text):
    out = []
    low = (note_text or "").lower()
    for needle, tag in _GATE_MARKS:
        if tag and needle.lower() in low:
            out.append(tag)
    return out


def _turns(turns, metas, public):
    """Fold the flat transcript feed into [{ts, q, a, gates, raw, latency_s}],
    oldest first. The transcript is a TAIL, not a log — /dev/shm holds what the
    running process has published, so this is a session scrollback and does not
    survive a reboot."""
    composed = {}
    for m in metas:
        if m.get("phase") == "composed" and m.get("question"):
            composed[m["question"]] = m

    out, cur = [], None
    for t in turns:
        role, text, ts = t.get("role"), t.get("text") or "", t.get("ts")
        if role == "user":
            if cur:
                out.append(cur)
            cur = {"ts": ts, "q": text, "a": "", "gates": [], "raw": None,
                   "latency_s": None}
        elif role == "cj" and cur is not None:
            cur["a"] = text
        elif role == "note" and cur is not None:
            if "raw ASR" in text:
                cur["raw"] = text
            cur["gates"].extend(_gate_tags(text))
    if cur:
        out.append(cur)

    for t in out:
        m = composed.get(t["q"])
        if m:
            t["latency_s"] = m.get("first_audio_s")
        t["gates"] = sorted(set(t["gates"]))
        if public:
            # A misheard question rendered on screen is worse than a misheard
            # one spoken, because it is legible and photographable. In public
            # mode a question appears only once the robot has answered it, and
            # never if a guardrail fired on that turn.
            t.pop("raw", None)
            t.pop("latency_s", None)
            if t["gates"] or not t["a"]:
                t["q"], t["a"] = "", ""
            t["gates"] = []
    return [t for t in out if t["q"] or t["a"]]


# ---------------------------------------------------------------------------
# The document
# ---------------------------------------------------------------------------
def display_doc(public=False, console=None):
    """Everything /stage and /monitor need, and nothing else.

    ~1-3 KB against /api/state's 11.7 KB, because a wall display polling for
    four hours should not pull the whole maintenance document to read six
    fields."""
    now = time.time()
    sp = _read_json(SPEAKING) or {}
    stg = _read_json(STAGE_DOC) or {}
    turns = _tail_jsonl(TRANSCRIPT, 80)
    metas = _tail_jsonl(TURN_META, 24)
    health = _health() or {}
    muted = os.path.exists(MUTED_FLAG)
    st = _robot_state(sp, stg, turns, health, muted, now)

    doc = {
        "ts": now,
        "rev": UI_REV,
        "public": bool(public),
        "state": st["st"],
        "state_since": st["since"],
        "portrait": portrait(),
        # the caption feed, trimmed to what a view renders
        "speaking": {
            "current": sp.get("current"),
            "n": len(sp.get("spoken") or []),
            "done": bool(sp.get("done", True)),
            "interrupted": bool(sp.get("interrupted")),
            "words": sp.get("words"),
            "wav": sp.get("wav"),
            "dur": sp.get("dur"),
            # the moment audio TRULY started, on the robot's clock
            # (speech_streaming.py:119) — the anchor the envelope syncs to
            "play_ts": sp.get("play_ts"),
            "ts": sp.get("ts"),
        },
        "turns": _turns(turns, metas, public),
        "camera": bool(cam_backend()) and not camera_off(),
    }
    # the two presentation knobs the browser acts on, so /stage and /monitor
    # pick up a /tune change without being reloaded (the robot's own head knobs
    # are not sent — nothing in a browser can act on them)
    try:
        m = motion_get()
        doc["motion"] = {"lipsync_gain": m.get("lipsync_gain", 1.0),
                         "avatar_offset": m.get("avatar_offset", 0.0)}
    except Exception:
        doc["motion"] = {"lipsync_gain": 1.0, "avatar_offset": 0.0}
    if not public:
        doc["state_detail"] = st["detail"]
        doc["muted"] = muted
        doc["health"] = {"supervaise": health.get("supervaise")}
        w = _read_json(WAKE_LIVE) or {}
        doc["wake_armed"] = bool(w.get("ts") and (now - w["ts"]) < 3)
        # the intake rows /audience draws under the question (routed, composed,
        # fidelity), trimmed to the fields a plaque renders
        steps = (stg or {}).get("steps") or {}
        doc["steps"] = {k: {f: v[f] for f in _STEP_FIELDS if v.get(f) is not None}
                        for k, v in steps.items()
                        if k in _STEP_ORDER and isinstance(v, dict)}
        doc["turn_ts"] = (stg or {}).get("turn_ts")

    # Which robot THIS is and what it plays. Everything above is read from this
    # machine's own /dev/shm, so the label must name this machine. Until
    # 2026-09-15 it named whichever robot played Panganiban, so with the roles
    # swapped alpha's /monitor read "reachy-2 · Panganiban" over alpha's own
    # Host turns. Only the authority knows roles; on the other machine role
    # stays None and /api/monitor takes it from the authority's document.
    try:
        host = _hostname()
        slots = (console.ConfigSources().robots().get("slots") or {}) if console is not None else {}
        me = my_slot(slots)
        doc["robot"] = {"slot": me, "machine": host, "role": None, "label": host}
        if console is not None and console.is_authority():
            c = console.get_console()
            if me:
                doc["robot"].update(machine=c.sources.machine_of(me),
                                    role=c.role_of(me), label=c.name(me))
                doc["online"] = ((c.observed or {}).get(me) or {}).get("online")
            doc["cjap_is"] = c.cjap_is
            doc["floor"] = c.floor
            doc["mode"] = c.mode
            doc["profile"] = c.profile
    except Exception:
        doc["robot"] = None          # never let the console break a display
    return doc


# ---------------------------------------------------------------------------
# /api/monitor — both robots in one document
# ---------------------------------------------------------------------------
# The other robot's document is fetched HERE, dashboard to dashboard, rather
# than by the browser: one origin means no CORS, and no mixed-content block
# when the page is opened on the https port. Robots still never talk to each
# other — this is two read-only dashboards, and a dead peer only greys out its
# column.
SLOTS = ("alpha", "beta")
PEER_TIMEOUT_S = 1.2
PEER_TTL_S = 0.8        # one fetch per interval, however many monitors are open
_peer = {}              # (slot, public) -> {"at", "ok_at", "doc", "error"}
_peer_lock = threading.Lock()
_WAV_NAME = re.compile(r"cj_sent_[0-9]+\.wav")


def _hostname():
    return socket.gethostname().split(".")[0].strip().lower()


def my_slot(slots):
    """'alpha' | 'beta' | None — the same rule as app/floor_lease.robot_slot():
    CJ_ROBOT_SLOT (legacy CJ_ROBOT_ROLE) first, then the hostname in slots."""
    for var in ("CJ_ROBOT_SLOT", "CJ_ROBOT_ROLE"):
        r = os.environ.get(var, "").strip().lower()
        if r in SLOTS:
            return r
    host = _hostname()
    for slot, name in (slots or {}).items():
        if slot in SLOTS and str(name).strip().lower() == host:
            return slot
    return None


def _peer_base(sources, machine):
    """http://<machine>.local:<port> — every dashboard listens on the
    authority's port. The authority's fixed address is used when robots.json
    gives one, since mDNS is the part guest networks break."""
    a = sources.authority()
    if a.get("ip") and machine.lower() == str(a.get("host") or "").lower():
        return f"http://{a['ip']}:{a['port']}"
    return a["url_template"].format(host=machine, port=a["port"])


def _http_get(url, timeout=PEER_TIMEOUT_S, limit=2_000_000):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read(limit)


def _peer_doc(slot, base, public, fetch, now):
    key = (slot, bool(public))
    with _peer_lock:
        hit = _peer.get(key)
        if hit and now - hit["at"] < PEER_TTL_S:
            return hit
        hit = dict(hit or {"doc": None, "ok_at": None, "error": None})
        hit["at"] = now
        try:
            d = json.loads(fetch(base + "/api/display"
                                 + ("?public_display=1" if public else "")))
            if not isinstance(d, dict):
                raise ValueError("not a display document")
            hit.update(doc=d, ok_at=now, error=None)
        except Exception as e:
            hit["error"] = f"{type(e).__name__}: {e}"[:160]   # keep the last good doc
        _peer[key] = hit
        return hit


def monitor_doc(public=False, console=None, fetch=_http_get, local=None):
    """{ts, rev, robots: [{slot, machine, role, label, local, reachable, age_s,
    has_floor, doc}], cjap_is, floor, mode, profile}. `doc` is that robot's own
    /api/display document; for an unreachable robot it is the last one seen."""
    now = time.time()
    local_doc = (local or display_doc)(public=public, console=console)
    sources = console.ConfigSources()
    cfg = sources.robots()
    slots = cfg.get("slots") or {}
    me = (local_doc.get("robot") or {}).get("slot") or my_slot(slots)

    robots = []
    for slot in SLOTS:
        machine = str(slots.get(slot) or slot)
        if slot == me:
            robots.append({"slot": slot, "machine": machine, "local": True,
                           "reachable": True, "age_s": 0.0, "doc": local_doc})
            continue
        base = _peer_base(sources, machine)
        hit = _peer_doc(slot, base, public, fetch, now)
        e = {"slot": slot, "machine": machine, "local": False,
             "reachable": hit["error"] is None and hit["doc"] is not None,
             "age_s": round(now - hit["ok_at"], 1) if hit["ok_at"] else None,
             "doc": hit["doc"],
             # a LAN address of that robot's own dashboard; /display needs it
             # in the public mode too
             "camera_url": base + "/api/camera.mjpg"}
        if not public:
            e["error"] = hit["error"]
        robots.append(e)

    # roles, floor and mode come from the authority's document, wherever it
    # is — never from a stale copy of it
    auth = next((r["doc"] for r in robots
                 if r["reachable"] and r["doc"] and r["doc"].get("cjap_is") in SLOTS), None) or {}
    cjap_is = auth.get("cjap_is")
    labels = cfg.get("labels") or {}
    for r in robots:
        r["role"] = ("cjap" if r["slot"] == cjap_is else "host") if cjap_is else None
        r["label"] = str(labels.get(r["role"]) or "") if r["role"] else ""
        r["has_floor"] = bool(auth) and auth.get("floor") == r["slot"]
    return {"ts": now, "rev": UI_REV, "public": bool(public), "robots": robots,
            "cjap_is": cjap_is, "floor": auth.get("floor"),
            "mode": auth.get("mode"), "profile": auth.get("profile")}


def peer_sentence_wav(slot, name, console=None, fetch=None):
    """The other robot's sentence clip, through this dashboard, so /monitor can
    measure its envelope from one origin. -> bytes, or None."""
    if slot not in SLOTS or not _WAV_NAME.fullmatch(name or ""):
        return None
    try:
        sources = console.ConfigSources()
        machine = str((sources.robots().get("slots") or {}).get(slot) or "")
        if not machine:
            return None
        f = fetch or (lambda u: _http_get(u, timeout=3, limit=8_000_000))
        return f(_peer_base(sources, machine) + "/api/sentence.wav?name=" + name)
    except Exception:
        return None


# ===========================================================================
# The state layer — shared by both views
# ===========================================================================
# This is the product for /stage: a visitor must tell idle from listening from
# thinking from speaking with no labels and no text, at two metres. So the four
# states are carried on THREE independent channels — colour, motion character
# and brightness — not on colour alone, which fails at distance and for a
# colour-blind viewer.
#
#   idle       deep indigo    slow breath only                  dim
#   listening  cool cyan      breath + a ring expanding outward  medium
#   thinking   warm amber     breath + an arc orbiting           medium
#   speaking   warm gold      breath + the envelope of the voice bright
#
# Breathing runs in ALL FOUR, including speaking, and never stops: a portrait
# that stops moving reads as a crashed screen, which is the failure this view
# exists to avoid.
# ===========================================================================
# A living portrait — shared by /stage, /monitor, /display and /face-avatar
# ===========================================================================
FACE_ANIM_JS = r"""
// ---- a living portrait ---------------------------------------------------
// 2026-09-15 (user: "make the avatar breathing and randomly closing its eyes",
// "and moving the head a bit"). A still of the face, kept alive in a canvas:
//   breath  14 a minute with a slow wander; the shoulders and chest lift on the
//           in-breath and the head rides on them (body(), below)
//   head    a drift of under half a degree, from sines that never line up, and
//           a slow side-to-side sway over the shoulders (body(), below)
//   blink   no two alike (newBlink): mostly full, about a quarter only part
//           way, a rare slow one; the two lids a few ms and a little depth
//           apart; 1.8-7 s between them with the odd long gap, sometimes twice
// The blink moves the real upper lid: per column of the eye, the skin above the
// lash line stretches down and the lash line rides on the lid edge, over as
// much of the eye as the lid has reached. It needs the eyes — per eye
// {c1:[x,y], c2:[x,y], up, lo}: the corners and the mid upper and lower lid,
// normalised to the picture — which /face-avatar finds once with MediaPipe and
// stores beside the portrait. Without them the face breathes and drifts but
// does not blink. Motion eases in over 1.5 s from the exact still, so it can
// take over from a live frame without a jump.
function validEyes(e){
  if(!Array.isArray(e)||!e.length||e.length>2) return null;
  const n=(v)=>typeof v==='number'&&v>=0&&v<=1;
  for(const x of e){
    if(!x||!Array.isArray(x.c1)||!Array.isArray(x.c2)||!n(x.c1[0])||!n(x.c1[1])||!n(x.c2[0])||!n(x.c2[1])||
       !n(x.up)||!n(x.lo)||x.lo<=x.up||x.c1[0]===x.c2[0]) return null;
  }
  return e;
}
function FaceAnim(canvas){
  const ctx=canvas.getContext('2d');
  const work=document.createElement('canvas'), wctx=work.getContext('2d');
  const t0=performance.now()-Math.random()*60000;   // two screens never breathe in step
  let src=null, eyes=null, on=true, since=0, lastDraw=0, dirty=null, pv=null;
  let blinkAt=0, blink=null, second=false;
  const ease=(x)=>x*x*(3-2*x);
  // 2026-09-15 (user: "make the eyelids close a bit random"): a fixed blink at
  // a random interval still reads as a mechanism after the third one
  function schedule(now){
    blinkAt=now+(Math.random()<0.08 ? 9000+Math.random()*4000 : 1800+Math.random()*5200);
  }
  function newBlink(now){
    const r=Math.random(), j=()=>0.8+Math.random()*0.45;     // every phase +/- ~20%
    const slow=r<0.06, part=!slow&&r<0.32;
    const depth=part ? 0.45+Math.random()*0.35 : 0.9+Math.random()*0.1;
    const other=depth*(0.9+Math.random()*0.1), lag=Math.random()*18, flip=Math.random()<0.5;
    return {t0:now, depth:flip?[depth,other]:[other,depth], lag:flip?[0,lag]:[lag,0],
            close:(slow?0.16:0.09)*j(), hold:(slow?0.2:(part?0.01:0.05))*j(), open:(slow?0.32:0.17)*j()};
  }
  // -> [left lid, right lid] closure 0..1, or null between blinks
  function closure(now){
    if(!blink){ if(!eyes||now<blinkAt) return null; blink=newBlink(now); }
    const out=[0,0]; let live=false;
    for(let i=0;i<2;i++){
      const s=(now-blink.t0-blink.lag[i])/1000, b=blink;
      let c=0;
      if(s<0) live=true;
      else if(s<b.close){ c=ease(s/b.close); live=true; }
      else if(s<b.close+b.hold){ c=1; live=true; }
      else if(s<b.close+b.hold+b.open){ c=1-ease((s-b.close-b.hold)/b.open); live=true; }
      out[i]=c*b.depth[i];
    }
    if(live) return out;
    blink=null;
    if(!second&&Math.random()<0.15){ second=true; blinkAt=now+120+Math.random()*120; }
    else { second=false; schedule(now); }
    return null;
  }
  function restore(){
    if(dirty&&src) wctx.drawImage(src,dirty[0],dirty[1],dirty[2],dirty[3],dirty[0],dirty[1],dirty[2],dirty[3]);
    dirty=null;
  }
  function lids(cs){
    restore();
    if(!eyes||!cs) return;
    const W=work.width, H=work.height;
    let x0=W, y0=H, x1=0, y1=0;
    for(let i=0;i<eyes.length;i++){
      const e=eyes[i], c=cs[i]||0;
      if(c<=0.001) continue;
      const ax=e.c1[0]*W, ay=e.c1[1]*H, bx=e.c2[0]*W, by=e.c2[1]*H;
      const w=Math.abs(bx-ax); if(w<6) continue;
      const cx=(ax+bx)/2, half=w/2*1.04, slope=(by-ay)/(bx-ax);
      const midY=(ay+by)/2, upOff=e.up*H-midY, loOff=e.lo*H-midY;
      const h=Math.max(loOff-upOff, w*0.18), lash=0.2*h, topOff=upOff-0.45*h;
      for(let x=Math.floor(cx-half); x<=Math.ceil(cx+half); x++){
        const u=(x+0.5-cx)/half; if(u<=-1||u>=1) continue;
        const cc=c*Math.pow(1-u*u,0.6); if(cc<0.002) continue;
        const base=ay+(x+0.5-ax)*slope, top=base+topOff, U=base+upOff, L=U+cc*(loOff-upOff);
        // the skin above the lash line, stretched down with the lid. Sampled 5
        // columns wide into 1: a thin band stretched column by column streaks
        wctx.drawImage(src, x-2,top,5,U-lash-top, x,top,1,L-lash-top+0.5);
        // the lash line itself, riding on the lid edge
        wctx.drawImage(src, x,U-lash,1,lash, x,L-lash,1,lash);
      }
      x0=Math.min(x0,cx-half-2); x1=Math.max(x1,cx+half+2);
      y0=Math.min(y0,Math.min(ay,by)+topOff-2); y1=Math.max(y1,Math.max(ay,by)+loOff+2);
    }
    x0=Math.max(0,Math.floor(x0)); y0=Math.max(0,Math.floor(y0));
    x1=Math.min(W,Math.ceil(x1)); y1=Math.min(H,Math.ceil(y1));
    if(x1>x0&&y1>y0) dirty=[x0,y0,x1-x0,y1-y0];
  }
  // body geometry from the eyes: [centre line x, the neck the head turns about
  // (~2.6 eye-distances below the eyes), the shoulder line (~2.2)]
  function pivot(W,H){
    if(!eyes||eyes.length<2) return [W*0.5,H*0.9,H*0.72];
    const c=(e)=>[(e.c1[0]+e.c2[0])/2*W,(e.c1[1]+e.c2[1])/2*H];
    const a=c(eyes[0]), b=c(eyes[1]), d=Math.hypot(a[0]-b[0],a[1]-b[1]), my=(a[1]+b[1])/2;
    return [(a[0]+b[0])/2, Math.min(H,my+2.6*d), Math.min(H*0.92,Math.max(H*0.3,my+2.2*d))];
  }
  // THE BODY BREATHES (2026-09-15, user: "make the avatar body move as it
  // breathes"). The shoulders and chest lift on the in-breath and everything
  // above them, head included, rides up with them; the chest widens a touch;
  // the bottom of the picture (the lap) stays where it sits. Drawn as 4 px
  // strips, each lifted and widened by a smooth amount, so no seam shows; the
  // part above the shoulders goes in one piece. ~5 px at 1080p, 0.4% wider.
  // The same strips carry the head's SIDE-TO-SIDE sway (2026-09-15, user: "add
  // the side to side movement of the head by a bit"): `sway` px for everything
  // above the shoulders, fading out over the upper chest, so the head moves
  // over still shoulders instead of the whole picture sliding.
  const RISE=0.005, WIDEN=0.004, STRIP=4;
  function body(W,H,bb,sway){
    const sh=Math.max(STRIP,Math.min(H-STRIP,Math.round(pv[2])));
    const rise=RISE*H*bb, cx=pv[0], span=H-sh;
    const lift=(y)=>y<=sh ? rise : rise*(1-ease(Math.min(1,(y-sh)/span)));
    const shift=(y)=>y<=sh ? sway : sway*(1-ease(Math.min(1,(y-sh)/(span*0.6))));
    ctx.drawImage(work, 0,0,W,sh, sway,-rise,W,sh+0.6);
    for(let y=sh; y<H; y+=STRIP){
      const y2=Math.min(H,y+STRIP), d0=y-lift(y), d1=y2-lift(y2);
      const kx=1+WIDEN*bb*Math.sin(Math.PI*((y+y2)/2-sh)/span);
      ctx.drawImage(work, 0,y,W,y2-y, cx-cx*kx+shift((y+y2)/2),d0,W*kx,d1-d0+0.6);
    }
  }
  function frame(now,force){
    if(!src||(!on&&!force)) return;
    if(!force&&now-lastDraw<33) return;               // ~30 fps is plenty for this
    lastDraw=now;
    lids(closure(now));
    const W=canvas.width, H=canvas.height, t=(now-t0)/1000, s=Math.sin;
    const k=ease(Math.min(1,(now-since)/1500));
    const wb=2*Math.PI*14/60, phb=wb*(1+0.07*s(0.033*t+0.5))*t;
    const b=s(phb)+0.16*s(2*phb+0.7);                 // out-breath a little faster than in
    const rot=k*(0.30*s(0.21*t)+0.12*s(0.53*t+1.3)+0.05*s(1.27*t+0.4))*Math.PI/180;
    const tx=k*W*(0.0012*s(0.17*t+0.9)+0.0006*s(0.61*t+2.1));   // trimmed: the sway below moves the head
    // side to side: ~14 s and ~38 s swings that never line up, up to 0.6% of the width
    const sway=k*W*(0.0045*s(2*Math.PI*0.07*t+0.3)+0.0015*s(2*Math.PI*0.026*t+1.9));
    const ty=k*H*0.0008*s(0.13*t+2.7);
    const over=1+k*0.03;                               // overscan: no edge ever shows
    const want=pivot(W,H);
    if(!pv) pv=want; else for(let i=0;i<3;i++) pv[i]+=(want[i]-pv[i])*0.05;
    ctx.setTransform(1,0,0,1,0,0);
    ctx.clearRect(0,0,W,H);
    ctx.translate(W/2,H/2); ctx.scale(over,over); ctx.translate(-W/2,-H/2);
    ctx.translate(pv[0]+tx,pv[1]+ty); ctx.rotate(rot); ctx.translate(-pv[0],-pv[1]);
    body(W,H,k*b,sway);                                // the breath and the sway live in the body
    ctx.setTransform(1,0,0,1,0,0);
  }
  function setSource(s){
    const w=s&&(s.naturalWidth||s.videoWidth||s.width), h=s&&(s.naturalHeight||s.videoHeight||s.height);
    dirty=null; blink=null; pv=null;
    if(!w||!h){ src=null; return; }
    src=s;
    canvas.width=work.width=w; canvas.height=work.height=h;
    wctx.drawImage(s,0,0,w,h);
    since=performance.now(); schedule(since);
    frame(since,true);
  }
  function setEyes(e){ restore(); eyes=validEyes(e); blink=null; schedule(performance.now()); }
  (function tick(now){ try{ frame(now); }catch(err){} requestAnimationFrame(tick); })(performance.now());
  return {setSource:setSource, setEyes:setEyes, active:(v)=>{ on=!!v; }};
}

// ---- the avatar's portrait behind the state layer --------------------------
// assets/portrait.* on /stage, /monitor and /display. A picture is drawn living
// (FaceAnim above); a video plays as it is. Absent or broken, the layer stands
// alone.
function Backdrop(img, vid){
  let shown=null, cv=null, anim=null, eyes=null, wantImg=null;
  function face(show){
    if(show&&!cv){
      cv=document.createElement('canvas'); cv.className='facecv';
      cv.style.cssText='position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block';
      img.insertAdjacentElement('afterend', cv); anim=FaceAnim(cv);
    }
    if(cv){ cv.style.display=show?'block':'none'; anim.active(show); }
  }
  img.onload=()=>{ if(!wantImg||img.getAttribute('src')!==wantImg) return; face(true); anim.setSource(img); anim.setEyes(eyes); };
  img.onerror=()=>{ img.style.display='none'; face(false); };
  vid.onerror=()=>{ vid.style.display='none'; };
  return function(p){
    const want=p?(p.file+'@'+(p.v||0)+'@'+(p.eyes?JSON.stringify(p.eyes):'')):null;
    if(want===shown) return;
    shown=want;
    // over a face the orb is a glow on it, not a disc in front of it
    img.parentElement.classList.toggle('hasface', !!p);
    eyes=(p&&p.eyes)||null;
    img.style.display='none';
    if(!p){ wantImg=null; vid.style.display='none'; face(false); return; }
    const src='/assets/portrait?v='+(p.v||0);
    if(p.kind==='video'){ wantImg=null; vid.src=src; vid.style.display='block'; face(false); return; }
    vid.style.display='none';
    if(wantImg===src&&img.complete&&img.naturalWidth){ face(true); anim.setEyes(eyes); }
    else { wantImg=src; img.src=src; }
  };
}
"""


DISPLAY_JS = FACE_ANIM_JS + r"""
// ---- state layer -------------------------------------------------------
// Draws into a canvas sized to its parent. Works with no backdrop, over a
// portrait image/video, and over live avatar video if one is ever present:
// it only ever composites ON TOP, never replaces.
function StateLayer(canvas, opts){
  opts = opts || {};
  const ctx = canvas.getContext('2d');
  let st='idle', env=0, envTarget=0, t0=performance.now(), raf=null, alive=Date.now(), last=performance.now();
  // 2026-09-15 (user: "not glitchy"): each state has a weight that eases toward
  // 1 when it is current and 0 when not, so colour, rings, arcs and the voice
  // band dissolve into each other over ~half a second instead of switching on
  // one frame. Smoothing is by elapsed time, so a slow screen eases the same.
  const W8={idle:1, listening:0, thinking:0, speaking:0, muted:0, down:0};
  const PAL = {
    idle:      {r:146, g:112, b:216, glow:0.42},
    listening: {r:72,  g:190, b:210, glow:0.56},
    thinking:  {r:236, g:166, b:74,  glow:0.56},
    speaking:  {r:246, g:198, b:110, glow:0.78},
    muted:     {r:120, g:120, b:130, glow:0.26},
    down:      {r:120, g:120, b:130, glow:0.26}
  };
  function fit(){
    const d = Math.max(1, window.devicePixelRatio||1);
    const w = canvas.clientWidth||window.innerWidth, h = canvas.clientHeight||window.innerHeight;
    if(canvas.width!==Math.round(w*d)||canvas.height!==Math.round(h*d)){
      canvas.width=Math.round(w*d); canvas.height=Math.round(h*d);
    }
  }
  function draw(now){
    alive = Date.now();
    fit();
    const W=canvas.width, H=canvas.height, t=(now-t0)/1000;
    const dt=Math.min(0.1, Math.max(0, (now-last)/1000)); last=now;
    const kS=1-Math.exp(-dt/0.16);
    let wsum=0;
    for(const k in W8){ W8[k]+=((k===st?1:0)-W8[k])*kS; wsum+=W8[k]; }
    const cx=W/2, cy=H*(opts.centerY||0.5), R=Math.min(W,H)*(opts.scale||0.34);
    // BREATHING — every state, always. ~0.22 Hz, and it is never gated.
    const breath = 1 + 0.055*Math.sin(t*2*Math.PI*0.22) + 0.014*Math.sin(t*2*Math.PI*0.37);
    // idle carries the breath in BRIGHTNESS too — at rest there is no other
    // motion, and an unlit form reads as a screen that has failed
    const bGlow = 1 + 0.22*W8.idle*Math.sin(t*2*Math.PI*0.22);
    // the voice: quick to open, slower to close, as a mouth is
    env += (envTarget-env)*(1-Math.exp(-dt/(envTarget>env?0.05:0.13)));
    const p={r:0,g:0,b:0,glow:0};
    for(const k in W8){ const w=W8[k]/(wsum||1), q=PAL[k]; p.r+=q.r*w; p.g+=q.g*w; p.b+=q.b*w; p.glow+=q.glow*w; }
    p.r=Math.round(p.r); p.g=Math.round(p.g); p.b=Math.round(p.b);
    ctx.clearRect(0,0,W,H);

    // the field: a soft radial bloom, brightness carries state
    const speak = W8.speaking*env;
    const glow = p.glow*(1 + speak*0.85)*bGlow;
    const rad = R*breath*(1 + speak*0.10);
    let g = ctx.createRadialGradient(cx,cy,rad*0.10, cx,cy,rad*1.95);
    g.addColorStop(0,   'rgba('+p.r+','+p.g+','+p.b+','+(glow).toFixed(3)+')');
    g.addColorStop(0.45,'rgba('+p.r+','+p.g+','+p.b+','+(glow*0.30).toFixed(3)+')');
    g.addColorStop(1,   'rgba('+p.r+','+p.g+','+p.b+',0)');
    ctx.fillStyle=g; ctx.beginPath(); ctx.arc(cx,cy,rad*1.95,0,7); ctx.fill();

    // the core, so there is a definite form and not only a haze
    ctx.beginPath(); ctx.arc(cx,cy,rad*0.52,0,7);
    ctx.fillStyle='rgba('+p.r+','+p.g+','+p.b+','+(0.16+speak*0.34).toFixed(3)+')';
    ctx.fill();

    // LISTENING — rings travelling outward. Reads as "open, waiting".
    if(W8.listening>0.01){
      for(let i=0;i<3;i++){
        const ph=((t*0.45)+i/3)%1;
        ctx.beginPath(); ctx.arc(cx,cy,rad*(0.55+ph*1.25),0,7);
        ctx.lineWidth=Math.max(3,R*0.034*(1-ph*0.55));
        ctx.strokeStyle='rgba(150,240,255,'+(0.80*(1-ph)*W8.listening).toFixed(3)+')';
        ctx.stroke();
      }
    }
    // THINKING — an arc orbiting. Reads as "working", and cannot be mistaken
    // for the rings because it travels around rather than outward.
    if(W8.thinking>0.01){
      const a=t*1.5;
      for(let i=0;i<3;i++){
        ctx.beginPath();
        ctx.arc(cx,cy,rad*(0.88+i*0.20), a+i*2.1, a+i*2.1+1.5);
        ctx.lineWidth=Math.max(3,R*0.038); ctx.lineCap='round';
        ctx.strokeStyle='rgba(255,214,150,'+((0.82-i*0.20)*W8.thinking).toFixed(3)+')';
        ctx.stroke();
      }
    }
    // SPEAKING — the voice itself. A band across the form that opens with the
    // amplitude of what is being said right now.
    if(W8.speaking>0.01){
      const bw=rad*(1.05), bh=Math.max(R*0.012, rad*0.30*env);
      const bg=ctx.createLinearGradient(cx-bw,cy,cx+bw,cy);
      bg.addColorStop(0,'rgba('+p.r+','+p.g+','+p.b+',0)');
      bg.addColorStop(0.5,'rgba(255,236,196,'+((0.30+env*0.55)*W8.speaking).toFixed(3)+')');
      bg.addColorStop(1,'rgba('+p.r+','+p.g+','+p.b+',0)');
      ctx.fillStyle=bg;
      ctx.beginPath();
      if(ctx.ellipse) ctx.ellipse(cx,cy+rad*0.20,bw*0.55,bh,0,0,7);
      else ctx.arc(cx,cy+rad*0.20,bh,0,7);
      ctx.fill();
    }
    raf=requestAnimationFrame(draw);
  }
  raf=requestAnimationFrame(draw);
  return {
    set:(s)=>{ if(PAL[s]) st=s; },
    envelope:(v)=>{ envTarget=Math.max(0,Math.min(1,v||0)); },
    state:()=>st,
    lastFrame:()=>alive
  };
}

// When no measured clip is available, a voiced motion that reads as speech:
// two smooth syllable-rate pulses. It replaced 0.28+0.22*|sin|, whose kink at
// every zero crossing made the band tick rather than move (2026-09-15).
function voiced(){
  const t=performance.now()/1000;
  return 0.30+0.16*(0.5-0.5*Math.cos(t*2*Math.PI*2.2))+0.07*(0.5-0.5*Math.cos(t*2*Math.PI*3.7+1.0));
}

// ---- envelope from the sentence actually being spoken -------------------
// The browser fetches the same wav the robot is playing (/api/sentence.wav)
// and measures it locally. Nothing is added to the pipeline and no audio is
// played here — this is analysis only, the sound comes from the robot.
//
// Sync anchor: speaking.play_ts is the moment audio TRULY started, on the
// robot's clock (app/speech_streaming.py:119). The dashboard runs on the same
// machine as the robot, so doc.ts and play_ts share a clock; elapsed time is
// taken from that and then advanced locally. OFFSET_MS trims the rest — the
// speaker path differs between the internal speaker and an external one, so
// it is a URL parameter, never a constant.
// wavUrl(name) is optional: /monitor passes one so the OTHER robot's clip comes
// through this dashboard (/api/monitor/sentence.wav).
function Envelope(offsetMs, wavUrl){
  let frames=null, dur=0, startedAt=0, name=null, ac=null, busy=false;
  const HZ=60;
  function ctxOf(){
    if(!ac){ try{ ac=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ ac=null; } }
    return ac;
  }
  async function load(wav){
    if(!wav || wav===name || busy) return;
    busy=true;
    try{
      const a=ctxOf(); if(!a) return;
      const r=await fetch(wavUrl?wavUrl(wav):'/api/sentence.wav?name='+encodeURIComponent(wav),{cache:'no-store'});
      if(!r.ok) return;
      const buf=await a.decodeAudioData(await r.arrayBuffer());
      const ch=buf.getChannelData(0), step=Math.max(1,Math.floor(buf.sampleRate/HZ));
      const out=new Float32Array(Math.ceil(ch.length/step));
      let peak=1e-6;
      for(let i=0,k=0;i<ch.length;i+=step,k++){
        let s=0; const end=Math.min(ch.length,i+step);
        for(let j=i;j<end;j++) s+=ch[j]*ch[j];
        out[k]=Math.sqrt(s/Math.max(1,end-i)); if(out[k]>peak) peak=out[k];
      }
      for(let i=0;i<out.length;i++) out[i]=Math.min(1,(out[i]/peak)*1.15);
      frames=out; dur=buf.duration; name=wav;
      startedAt=0;                      // not started: waiting for play_ts
    }catch(e){ /* a display never shows an error */ }
    finally{ busy=false; }
  }
  // Anchor to the moment audio TRULY began, on the robot's clock. Called only
  // once play_ts appears; before that the envelope stays silent rather than
  // running ahead of the voice.
  function start(elapsed){
    if(!frames || startedAt) return;
    startedAt=performance.now()-Math.max(0,(elapsed||0)*1000);
  }
  function value(){
    if(!frames || !startedAt) return null;
    const tms=performance.now()-startedAt-(offsetMs()||0);
    if(tms<0) return 0;
    const i=Math.floor((tms/1000)*HZ);
    if(i>=frames.length) return null;        // clip finished; caller falls back
    return frames[i];
  }
  return {load, start, value,
          clear:()=>{frames=null;name=null;startedAt=0;}, name:()=>name};
}

// ---- the feed ----------------------------------------------------------
// One endpoint, /api/display. On failure it keeps the last good document and
// backs off; it never renders an error, and it recovers on its own when the
// backend comes back, with no refresh.
function Feed(url, onDoc, onHealth){
  let last=null, fails=0, timer=null, stop=false;
  async function tick(){
    if(stop) return;
    try{
      const r=await fetch(url+(url.indexOf('?')<0?'?':'&')+'t='+Date.now(),{cache:'no-store'});
      if(!r.ok) throw new Error('http '+r.status);
      const d=await r.json();
      last=d; fails=0; onDoc(d); if(onHealth) onHealth(true,0);
    }catch(e){
      fails++;
      if(onHealth) onHealth(false,fails);
      // hold the last good document; after ~30 s with no backend, settle to
      // idle rather than freeze on a stale "speaking"
      if(fails>30 && last){ last.state='idle'; last.speaking={done:true}; onDoc(last); }
    }
    const wait = fails===0 ? 1000 : Math.min(8000, 1000*Math.pow(1.6,Math.min(fails,6)));
    timer=setTimeout(tick, wait);
  }
  tick();
  return {stop:()=>{stop=true; if(timer)clearTimeout(timer);}, last:()=>last};
}

// ---- keeping a display awake and alive ---------------------------------
async function keepAwake(){
  try{
    if('wakeLock' in navigator){
      let lock=await navigator.wakeLock.request('screen');
      document.addEventListener('visibilitychange', async ()=>{
        if(document.visibilityState==='visible'){
          try{ lock=await navigator.wakeLock.request('screen'); }catch(e){}
        }
      });
    }
  }catch(e){ /* older browser: the venue note says disable sleep in the OS */ }
}
// If the page throws or the animation stalls, come back by itself. Nobody is
// standing at these screens with a keyboard.
function selfHeal(layer){
  window.addEventListener('error', ()=>setTimeout(()=>location.reload(), 5000));
  window.addEventListener('unhandledrejection', ()=>setTimeout(()=>location.reload(), 5000));
  setInterval(()=>{ if(Date.now()-layer.lastFrame()>30000) location.reload(); }, 10000);
}
"""


# ===========================================================================
# /stage — the visitor's view
# ===========================================================================
STAGE_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>CJAP</title>
<style>
  html,body{margin:0;padding:0;height:100%;width:100%;overflow:hidden;background:#000}
  body.transparent,body.transparent #wrap{background:transparent}
  /* full bleed at ANY aspect ratio: the backdrop covers, the layer overlays.
     No letterboxing and no scrollbars at 16:9, 4:3, 21:9 or portrait. */
  #wrap{position:fixed;inset:0;background:#000;overflow:hidden}
  #back{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none}
  #layer{position:absolute;inset:0;width:100%;height:100%;display:block}
  #wrap.hasface #layer{mix-blend-mode:screen;opacity:.6}
  /* a visitor never sees a pointer on an exhibit screen */
  body.hidecursor,body.hidecursor *{cursor:none!important}
</style></head><body>
<div id="wrap">
  <img id="back" alt=""><video id="backv" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none" muted loop playsinline autoplay></video>
  <canvas id="layer"></canvas>
</div>
<script>
""" + DISPLAY_JS + r"""
(function(){
  const Q=new URLSearchParams(location.search);
  if((Q.get('bg')||'black')==='transparent') document.body.classList.add('transparent');
  const URLOFF=Q.has('offset')?(parseInt(Q.get('offset'),10)||0):null;
  let OFFSET=URLOFF||0, GAIN=1;   // /tune sets these live unless the URL pins them

  const layer=StateLayer(document.getElementById('layer'),{scale:0.34});
  const env=Envelope(()=>OFFSET);
  keepAwake(); selfHeal(layer);

  // hide the cursor after 3 s without movement
  let curTimer=null;
  function armCursor(){
    document.body.classList.remove('hidecursor');
    clearTimeout(curTimer);
    curTimer=setTimeout(()=>document.body.classList.add('hidecursor'),3000);
  }
  ['mousemove','touchstart','pointerdown'].forEach(e=>window.addEventListener(e,armCursor,{passive:true}));
  armCursor();

  // backdrop, if one has been provided. Absent, the state layer stands alone.
  const backdrop=Backdrop(document.getElementById('back'), document.getElementById('backv'));

  let lastWav=null;
  Feed('/api/display?public_display=1', function(d){
    // muted and down are operator concerns; a visitor should simply see a
    // resting exhibit, never a fault
    const s=d.state==='muted'||d.state==='down'?'idle':d.state;
    layer.set(s);
    backdrop(d.portrait);
    const mo=d.motion||{};
    if(URLOFF===null && mo.avatar_offset!=null) OFFSET=Math.round(mo.avatar_offset*1000);
    if(mo.lipsync_gain!=null) GAIN=mo.lipsync_gain;
    const sp=d.speaking||{};
    if(s==='speaking' && sp.wav){
      if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }   // decode now
      if(sp.play_ts && d.ts) env.start(Math.max(0, d.ts-sp.play_ts));  // start on real audio
    } else if(s!=='speaking'){ lastWav=null; env.clear(); }
  });

  // drive the envelope every frame; when the measured clip runs out (or was
  // never available — a curated line has no per-sentence wav) fall back to a
  // gentle voiced motion so SPEAKING still reads as speaking.
  (function pump(){
    const st=layer.state();
    if(st==='speaking'){
      const v=env.value();
      layer.envelope((v===null ? voiced() : v)*GAIN);
    } else layer.envelope(0);
    requestAnimationFrame(pump);
  })();
})();
</script></body></html>"""


# ===========================================================================
# The gallery look — shared by /monitor and /display
# ===========================================================================
# The /audience palette, gilt frame, ivory plaques, state pill and intake rows,
# written as classes. The EXHIBIT_* pieces in ui_page_audience.py are not
# reused: they bind fixed ids (#cam, #a, #rs) and /monitor has two of each.
GALLERY_FONTS = r"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">"""

GALLERY_CSS = r"""
  :root{--wall:#1c1916;--ink:#2b2418;--ink2:#5a4d3a;--faint:#8a7b64;--ivory:#f4eddc;--ivory2:#eadfc6;
    --maroon:#6e1f2b;--brass:#c9a961;--brass2:#8f7332;--ok:#4f7d4a;--warn:#a8642a;--blue:#3b5b8a;
    --label:#e8dcc0;--label2:#cbb98f}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{color:var(--ink);font-family:'EB Garamond',Georgia,'Times New Roman',serif;
    background:var(--wall) radial-gradient(ellipse 80% 55% at 50% 22%,rgba(214,190,140,.18) 0%,
      rgba(214,190,140,.05) 50%,rgba(0,0,0,0) 78%) fixed}

  /* the gilt frame: the /audience #cam moulding */
  .frame{position:relative;aspect-ratio:16/9;max-width:100%;overflow:hidden;
    background:radial-gradient(ellipse at 50% 40%,#2a241b,#120f0b 75%);
    border:1.1vh solid #b8944f;
    border-image:linear-gradient(160deg,#f3e4b4 0%,#c8a55c 18%,#8f7332 34%,#e6cf8f 50%,#a5813f 66%,#f0dda6 84%,#8a6d2c 100%) 1;
    box-shadow:0 0 0 .3vh #2a2115,0 0 0 1.4vh #efe4c8,0 0 0 1.7vh #6b5323,0 0 0 1.9vh #d9c07a,
      0 3vh 7vh rgba(0,0,0,.75),inset 0 0 0 .45vh #12100c;
    transition:box-shadow .8s ease}
  .frame.live{box-shadow:0 0 0 .3vh #2a2115,0 0 0 1.4vh #efe4c8,0 0 0 1.7vh #6b5323,0 0 0 1.9vh #d9c07a,
      0 3vh 7vh rgba(0,0,0,.75),0 0 8vh 1.5vh rgba(230,200,130,.3),inset 0 0 0 .45vh #12100c}
  .frame canvas,.frame .fill{position:absolute;inset:0;width:100%;height:100%}
  .frame canvas{transition:opacity .6s}
  .frame.hasface canvas:not(.facecv){mix-blend-mode:screen;opacity:.6}
  .frame .fill{object-fit:cover;display:none;background:#000}
  /* what a frame shows when it has nothing: the /audience idle plaque */
  .plate{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
    gap:1vh;padding:1rem;text-align:center;color:var(--label2);font-size:clamp(13px,1.9vh,19px);z-index:2}
  .plate b{font-family:'Playfair Display',Georgia,serif;font-weight:500;color:var(--brass);letter-spacing:.24em;
    text-transform:uppercase;font-size:1.25em}

  /* state pill: /audience #rs */
  .pill{display:flex;align-items:center;gap:.7em;padding:.5em 1.1em;border-radius:999px;
    background:rgba(20,16,12,.74);border:1px solid rgba(201,169,97,.45);box-shadow:0 .6vh 2vh rgba(0,0,0,.5);
    font-family:'Playfair Display',Georgia,serif;letter-spacing:.2em;text-transform:uppercase;
    font-size:clamp(11px,1.5vh,15px);color:var(--label)}
  .pill .dot{width:1.1em;height:1.1em;border-radius:50%;background:#7a7368;flex:0 0 auto}
  .pill.listening{border-color:rgba(63,185,80,.6)}
  .pill.listening .dot{background:#3fb950;box-shadow:0 0 1.2vh .2vh rgba(63,185,80,.55);animation:rspulse 1.2s ease-in-out infinite}
  .pill.thinking .dot{background:#c9a961;box-shadow:0 0 1.2vh .1vh rgba(201,169,97,.5);animation:rspulse 1.2s ease-in-out infinite}
  .pill.speaking{border-color:rgba(229,72,77,.6)}
  .pill.speaking .dot{background:#e5484d;box-shadow:0 0 1.2vh .2vh rgba(229,72,77,.55);animation:rspulse .6s ease-in-out infinite}
  .pill.muted,.pill.down,.pill.offline{border-color:rgba(229,72,77,.6)}
  .pill.muted .dot,.pill.down .dot{background:#e5484d}
  .pill.offline .dot{background:#4a433b}
  @keyframes rspulse{50%{transform:scale(.78);opacity:.65}}

  /* the plaques: ivory fading downward */
  .card{display:flex;flex-direction:column;min-width:0;padding:1.7vh 1.6vw 2vh;border-radius:.6vh;color:var(--ink);
    background:linear-gradient(180deg,rgba(247,241,227,.97) 0%,rgba(244,237,220,.92) 40%,rgba(234,223,198,.78) 100%)}
  .card h3{display:flex;align-items:center;gap:1vw;margin-bottom:1vh;font-family:'Playfair Display',Georgia,serif;
    font-weight:500;font-size:clamp(11px,1.5vh,15px);letter-spacing:.24em;text-transform:uppercase;color:var(--maroon)}
  .card h3::after{content:'';flex:1;order:1;height:1px;background:linear-gradient(90deg,var(--brass2),rgba(143,115,50,0))}
  .card h3 .ago{order:2;font-family:'EB Garamond',Georgia,serif;letter-spacing:.03em;text-transform:none;
    color:var(--faint);font-size:1.1em}
  .card h3.big{font-weight:600;color:#4f121c;letter-spacing:.26em}
  .qt{font-size:clamp(16px,2.5vh,25px);line-height:1.35;color:#1e1810;font-weight:600;max-height:14vh;overflow-y:auto}
  .ans{position:relative;font-size:clamp(16px,2.6vh,26px);line-height:1.5;min-height:8vh;max-height:28vh;
    overflow-y:auto;scrollbar-width:none}
  .ans::-webkit-scrollbar{display:none}
  .ans .w{opacity:0;transition:opacity .16s ease-out}
  .ans .w.on{opacity:1}
  .ans .w.now,.ans .cur{color:var(--maroon)}
  .idle{font-style:italic;color:var(--faint);font-weight:400}
  .idle em{color:var(--maroon);font-style:normal;white-space:nowrap}
  .think::after{content:'';animation:dots 1.5s steps(4,end) infinite}
  @keyframes dots{0%{content:''}25%{content:'.'}50%{content:'..'}75%{content:'...'}}

  /* intake rows, as /audience */
  .rows{display:flex;flex-direction:column;gap:.6vh}
  .rows:not(:empty){margin-top:1.1vh}
  .row{display:grid;grid-template-columns:1.5em minmax(0,1fr) auto;gap:.2vh .8vw;align-items:start;
    padding:.7vh .8vw;border-radius:.4vh;background:rgba(120,95,50,.07);font-size:clamp(12px,1.75vh,17px);line-height:1.4}
  .row.done{background:rgba(79,125,74,.09)} .row.active{background:rgba(201,169,97,.16)}
  .row.flagged{background:rgba(168,100,42,.14)}
  .row .ck{text-align:center;color:var(--faint)} .row.done .ck{color:var(--ok)} .row.flagged .ck{color:var(--warn)}
  .row.active .ck{color:var(--brass2);animation:blink 1.1s ease-in-out infinite}
  .row .lb{font-family:'Playfair Display',Georgia,serif;font-size:.74em;letter-spacing:.18em;text-transform:uppercase;
    color:var(--maroon);margin-right:.6vw;white-space:nowrap}
  .row.active .lb{color:var(--brass2)} .row.flagged .lb{color:var(--warn)}
  .row code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em;padding:.1em .45em;border-radius:.3em;
    background:rgba(79,125,74,.14);color:#2f5a2b}
  .row .conf{color:var(--blue)}
  .row .t{color:var(--faint);font-variant-numeric:tabular-nums;white-space:nowrap}
  @keyframes blink{50%{opacity:.25}}
  .gate{display:inline-block;font-family:'Playfair Display',Georgia,serif;font-size:.74em;letter-spacing:.14em;
    text-transform:uppercase;color:var(--warn);border:1px solid rgba(168,100,42,.55);border-radius:.3em;
    padding:0 .45em;margin:0 .45em .2em 0}
  .meta{font-size:clamp(12px,1.6vh,15px);color:var(--faint);margin-top:.5vh}
  .public .rows,.public .meta,.public .gate{display:none!important}
"""

GALLERY_JS = r"""
// ---- gallery helpers (/monitor and /display) ----------------------------
const esc=(s)=>(s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const quote=(s)=>'&ldquo;'+esc(s)+'&rdquo;';
function ago(s){
  s=Math.max(0,Math.round(s||0));
  return s<60?s+' s':(s<3600?Math.round(s/60)+' min':Math.round(s/3600)+' h');
}
function rowHtml(state,label,body,t){
  const ck=state==='done'?'&#10003;':state==='flagged'?'&#9888;':state==='active'?'&#9679;':'&#9675;';
  const ts=(t!=null&&state!=='active')?(+t).toFixed(1)+'s':'';
  return '<div class="row '+state+'"><span class="ck">'+ck+'</span><div class="b"><span class="lb">'+label+
         '</span>'+body+'</div><span class="t">'+ts+'</span></div>';
}
// the intake rows, as /audience renderRows() draws them
function rowsHtml(s){
  s=s||{};
  const rt=s.route||{}, cp=s.compose||{}, fd=s.fidelity||{}, p=[];
  if(rt.scope) p.push(rowHtml('done','Scope','<code>'+esc(rt.scope)+'</code>'));
  if(rt.state==='active') p.push(rowHtml('active','Routed','<span class="think">'+esc(rt.detail||'choosing the topic')+'</span>'));
  else if(rt.state==='done') p.push(rowHtml('done','Routed','<code>'+esc(rt.topic||rt.detail||'')+'</code>'+
    (rt.confidence?' <span class="conf">('+esc(rt.confidence)+')</span>':''),rt.t));
  if(cp.state==='active') p.push(rowHtml('active','Composed','<span class="think">'+esc(cp.detail||'writing')+'</span>'));
  else if(cp.state==='done') p.push(rowHtml('done','Composed',esc(cp.detail||''),cp.t));
  if(fd.state==='active') p.push(rowHtml('active','Fidelity','<span class="think">'+esc(fd.detail||'checking')+'</span>'));
  else if(fd.state==='done'||fd.state==='flagged') p.push(rowHtml(fd.state,'Fidelity',esc(fd.detail||'')+
    (fd.state==='flagged'&&fd.reason?' <span class="conf">'+esc(fd.reason)+'</span>':''),fd.t));
  return p.join('');
}
// gate tags, latency and the raw transcript under a turn — operator only
function metaHtml(t){
  if(!t) return '';
  const g=(t.gates||[]).map(x=>'<span class="gate">'+esc(x)+'</span>').join('');
  const lat=(t.latency_s!=null)?'first audio '+(+t.latency_s).toFixed(1)+' s':'';
  const raw=t.raw?'<div class="meta">'+esc(t.raw)+'</div>':'';
  return ((g||lat)?'<div class="meta">'+g+esc(lat)+'</div>':'')+raw;
}
// what the Panganiban plaque says with nothing to show, by mode
function waitingLine(top){
  top=top||{};
  if(top.mode==='duet') return 'The Chief Justice and his Host, in conversation';
  if(top.profile==='event') return 'Ask your question at the microphone';
  return 'Approach and say <em>&ldquo;Hi, Cee-Jap&rdquo;</em>';
}
// this robot's sentence clip is served here; the other robot's comes through
// /api/monitor/sentence.wav
function clipUrl(local, slot, name){
  return local ? '/api/sentence.wav?name='+encodeURIComponent(name)
               : '/api/monitor/sentence.wav?slot='+encodeURIComponent(slot)+'&name='+encodeURIComponent(name);
}
// the other robot's camera is only reachable directly over plain http
function cameraUrl(e){
  return e.local ? '/api/camera.mjpg' : (location.protocol==='http:' ? (e.camera_url||null) : null);
}
// Word-by-word reveal, as /audience: each word hidden until the audio reaches
// it. Anchored to play_ts (the moment audio truly began, robot clock), carried
// forward locally between polls. show() -> false when the sentence has no word
// timings, and the caller shows the whole sentence instead.
function WordReveal(box){
  let ww={key:''};
  return {
    show:function(sp, docTs){
      if(!(sp&&sp.current&&sp.words&&sp.words.length)){ ww={key:''}; return false; }
      const key=sp.wav||sp.current;
      if(key!==ww.key){
        ww={key:key, words:sp.words, play:0, perf:0, robot:0, last:-1};
        box.innerHTML=sp.words.map(w=>'<span class="w">'+esc(w[0])+'</span>').join(' ');
      }
      if(sp.play_ts){ if(!ww.play) ww.play=sp.play_ts; ww.robot=docTs; ww.perf=performance.now(); }
      return true;
    },
    clear:function(){ ww={key:''}; },
    tick:function(){
      if(!ww.key||!ww.play) return;
      const spans=box.getElementsByClassName('w');
      const elapsed=Math.max(0,(performance.now()-ww.perf)/1000+(ww.robot-ww.play));
      let last=-1;
      for(let i=0;i<spans.length;i++){
        const on=elapsed>=(ww.words[i]?ww.words[i][1]:0);
        spans[i].classList.toggle('on',on); spans[i].classList.remove('now');
        if(on) last=i;
      }
      if(last>=0){
        spans[last].classList.add('now');
        if(ww.last!==last){ ww.last=last; box.scrollTop=Math.max(0,spans[last].offsetTop-box.clientHeight/2); }
      }
    }
  };
}
"""


# ===========================================================================
# /monitor — the operator's view of BOTH robots, in the /audience look
# ===========================================================================
# 2026-09-15 (user: "make for both ... the theme as the same as the audience
# UI"). One column per robot, Panganiban first whichever machine plays him:
# the gilt frame (state layer, camera inset when there is one, state pill),
# then the Question and Answer plaques, then the session scrollback. The Host
# has no avatar (2026-09-15, user): its frame is its camera, full size, and
# follows a role swap like everything else here. It reads
# /api/monitor only, so the page is the same whichever robot's dashboard
# serves it.
MONITOR_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CJAP monitor</title>
""" + GALLERY_FONTS + r"""
<style>""" + GALLERY_CSS + r"""
  html,body{min-height:100%}
  body{padding:1.8vh max(16px,2.2vw) 2.4vh}
  .chips{display:flex;gap:.5rem;flex-wrap:wrap}
  .chips:not(:empty){margin-bottom:1.4vh}
  .chip{font-family:'Playfair Display',Georgia,serif;font-size:12px;letter-spacing:.14em;text-transform:uppercase;
    padding:.35em 1em;border-radius:999px;border:1px solid rgba(201,169,97,.45);color:var(--label);
    background:rgba(20,16,12,.6)}
  .chip.warn{border-color:rgba(229,72,77,.7);color:#f1b7b9}
  #robots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2.6vw;align-items:start}
  @media(max-width:900px){#robots{grid-template-columns:1fr;gap:5vh}}
  .robot{display:flex;flex-direction:column;gap:1.5vh;min-width:0}
  .robot .frame{width:calc(100% - 4.4vh);margin:2.2vh auto}
  .robot .pill{position:absolute;top:1.2vh;left:1.2vh;z-index:3}
  .camin{position:absolute;right:1.2vh;bottom:1.2vh;width:32%;aspect-ratio:16/9;object-fit:cover;display:none;
    background:#000;border:.35vh solid #c8a55c;box-shadow:0 .6vh 2vh rgba(0,0,0,.6);z-index:2}
  .frame .off,.frame .hostplate{display:none}
  .robot.gone .frame canvas{opacity:.25}
  .robot.gone .frame .off{display:flex}
  .flag{position:absolute;top:1.2vh;right:1.2vh;z-index:3;display:flex;gap:.4em;flex-wrap:wrap;
    justify-content:flex-end;max-width:55%}
  .flag span{padding:.4em .9em;border-radius:999px;background:rgba(20,16,12,.74);border:1px solid rgba(201,169,97,.45);
    font-family:'Playfair Display',Georgia,serif;letter-spacing:.14em;text-transform:uppercase;
    font-size:clamp(10px,1.3vh,13px);color:var(--label)}
  details.card summary{list-style:none;cursor:pointer}
  details.card summary::-webkit-details-marker{display:none}
  details.card summary h3{margin-bottom:0}
  details[open].card summary h3{margin-bottom:1vh}
  details.card summary h3 span:first-child::before{content:'\25B8\00a0\00a0'}
  details[open].card summary h3 span:first-child::before{content:'\25BE\00a0\00a0'}
  .log{max-height:32vh;overflow-y:auto;font-size:clamp(14px,1.9vh,18px);line-height:1.45}
  .turn{padding:.9vh 0;border-bottom:1px solid rgba(143,115,50,.22)}
  .turn:last-child{border-bottom:0}
  .turn .tq{font-weight:600;color:#1e1810}
  .turn .ta{color:var(--ink2)}
  footer{margin-top:3vh;text-align:center;font-size:12px;letter-spacing:.06em;color:var(--faint)}
  footer a{color:var(--label2)}
  .public .flag,.public footer{display:none!important}
</style></head><body>
<div class="chips" id="chips"></div>
<main id="robots"></main>
<footer>Read-only &middot; nothing on this page changes what the robots do &middot;
  <a href="/display">visitor display</a> &middot; <a href="/tune">motion tuning</a></footer>
<script>
""" + DISPLAY_JS + GALLERY_JS + r"""
(function(){
  const Q=new URLSearchParams(location.search);
  const PUB=(Q.get('public_display')||'').toLowerCase();
  const isPublic=PUB==='1'||PUB==='true'||PUB==='yes';
  if(isPublic) document.body.classList.add('public');
  const $=(id)=>document.getElementById(id);
  const LABEL={idle:'Idle',listening:'Listening',thinking:'Thinking',speaking:'Speaking',
               muted:'Mic muted',down:'App down',offline:'Not answering'};
  let OFFSET=0, GAIN=1, REV=null, healed=false, lastTop=null;
  const panels={};

  function Panel(slot){
    const el=document.createElement('section');
    el.className='robot'; el.dataset.slot=slot;
    el.innerHTML=
      '<div class="frame"><img class="fill back" alt="">'+
        '<video class="fill backv" muted loop playsinline autoplay></video>'+
        '<canvas class="orb"></canvas><img class="camin" alt="">'+
        '<div class="plate hostplate"><b>Host</b><span>no camera on this robot</span></div>'+
        '<div class="pill idle"><span class="dot"></span><span class="lbl">Idle</span></div>'+
        '<div class="flag"></div>'+
        '<div class="plate off"><b>Not answering</b><span class="why"></span></div></div>'+
      '<div class="card"><h3><span>The Question</span><span class="ago"></span></h3>'+
        '<div class="qt"></div><div class="rows"></div><div class="qmeta"></div></div>'+
      '<div class="card"><h3><span class="ah">The Answer</span></h3><div class="ans"></div></div>'+
      '<details class="card"><summary><h3><span>Earlier this session</span><span class="ago cnt"></span></h3></summary>'+
        '<div class="log"></div></details>';
    const q=(s)=>el.querySelector(s);
    const layer=StateLayer(q('canvas.orb'),{scale:0.30});
    let local=false;
    const env=Envelope(()=>OFFSET, (name)=>clipUrl(local, slot, name));
    const words=WordReveal(q('.ans'));
    let lastWav=null, logKey=null, cam=null, camRetry=0;
    const shown={};
    function put(sel,h){ if(shown[sel]!==h){ shown[sel]=h; q(sel).innerHTML=h; } }
    const backdrop=Backdrop(q('.back'), q('.backv'));
    const img=q('.camin');
    // an MJPEG that fails is hidden and retried quietly, never a black box
    img.onerror=()=>{ img.style.display='none'; cam=null; camRetry=Date.now()+15000; };

    function update(e, top, portrait){
      local=!!e.local;
      const d=e.doc||{}, gone=!e.reachable, role=e.role;
      el.classList.toggle('gone', gone);
      el.style.order=role==='cjap'?'0':(role==='host'?'1':'2');
      q('.ah').textContent=role==='cjap'?'The Chief Justice Answers':(role==='host'?'The Host Says':'The Answer');

      const st=gone?'offline':(d.state||'idle');
      const pill=q('.pill');
      if(pill.dataset.st!==st){ pill.dataset.st=st; pill.className='pill '+st; q('.lbl').textContent=LABEL[st]||st; }
      layer.set(st==='offline'?'down':st);
      q('.frame').classList.toggle('live', st==='speaking');
      // the Host has no avatar: no orb, and its camera fills the frame
      const avatar=role!=='host';
      q('canvas.orb').style.display=avatar?'block':'none';
      backdrop(avatar?portrait:null);
      const flags=[];
      if(!gone&&e.has_floor) flags.push('holds the floor');
      if(!gone&&d.online===false) flags.push('no internet');
      put('.flag', flags.map(f=>'<span>'+esc(f)+'</span>').join(''));
      q('.why').textContent=!gone?'':
        ((e.age_s!=null?'last heard from '+ago(e.age_s)+' ago':'not reached yet')+
         (!isPublic&&e.error?' — '+e.error:''));

      // the question: while a NEW one is being taken, the last turn on file is
      // the previous question, so it is not shown as if it were this one
      const turns=d.turns||[], cur=turns.length?turns[turns.length-1]:null;
      const fresh=!!(cur&&(d.turn_ts==null||cur.ts>=d.turn_ts-1));
      const taking=st==='listening'&&!fresh;
      if(taking) put('.qt','<span class="idle think">Listening</span>');
      else if(cur&&cur.q) put('.qt',quote(cur.q));
      else put('.qt','<span class="idle">No question yet this session</span>');
      q('.ago').textContent=(!isPublic&&cur&&!taking&&d.ts)?ago(d.ts-cur.ts)+' ago':'';
      put('.rows', (fresh||taking||st==='thinking')?rowsHtml(d.steps):'');
      put('.qmeta', (cur&&!taking&&!isPublic)?metaHtml(cur):'');

      // the answer: word by word as the audio reaches each word
      const sp=d.speaking||{};
      if(st==='speaking'&&sp.current){
        if(words.show(sp, d.ts)) shown['.ans']=null;
        else put('.ans','<span class="cur">'+esc(sp.current)+'</span>');
      } else {
        words.clear();
        if(st==='thinking') put('.ans','<span class="idle think">'+(role==='host'?'Getting ready':'The Chief Justice is considering')+'</span>');
        else if(taking) put('.ans','<span class="idle">Waiting for the question to finish</span>');
        else if(cur&&cur.a) put('.ans', esc(cur.a));
        else if(role==='cjap') put('.ans','<span class="idle">'+waitingLine(top)+'</span>');
        else put('.ans','<span class="idle">Nothing said yet this session</span>');
      }

      // the clip only drives the orb, so a robot with no avatar fetches none
      if(avatar&&st==='speaking'&&sp.wav){
        if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }
        if(sp.play_ts&&d.ts) env.start(Math.max(0,d.ts-sp.play_ts));
      } else if(!avatar||st!=='speaking'){ lastWav=null; env.clear(); }

      const url=cameraUrl(e);
      const want=(!gone&&d.camera&&url)?url:null;
      img.className=avatar?'camin':'fill';        // inset beside the avatar, or the whole frame
      if(want!==cam&&(!want||Date.now()>=camRetry)){
        cam=want;
        if(want){ img.src=want+'?t='+Date.now(); img.style.display='block'; }
        else { img.removeAttribute('src'); img.style.display='none'; }
      }
      q('.hostplate b').textContent=e.label||'Host';
      q('.hostplate').style.display=(!avatar&&!gone&&!cam)?'flex':'none';

      const older=turns.slice(0,-1).reverse();
      const key=older.map(t=>t.ts).join(',');
      if(key!==logKey){
        logKey=key;
        q('.cnt').textContent=older.length?String(older.length):'';
        q('.log').innerHTML=older.map(t=>'<div class="turn"><div class="tq">'+esc(t.q)+'</div>'+
          '<div class="ta">'+esc(t.a)+'</div>'+(isPublic?'':metaHtml(t))+'</div>').join('')||
          '<div class="meta">Nothing earlier yet.</div>';
      }
    }

    function tick(){
      if(layer.state()==='speaking'){
        const v=env.value();
        layer.envelope((v===null?voiced():v)*GAIN);
      } else layer.envelope(0);
      words.tick();
    }
    return {el:el, layer:layer, update:update, tick:tick};
  }

  function chips(top, ok, fails){
    const c=[];
    if(!isPublic&&top&&!top.cjap_is) c.push('<span class="chip warn">roles unknown &mdash; console not reachable</span>');
    if(!isPublic&&!ok&&fails>2) c.push('<span class="chip warn">dashboard unreachable &mdash; holding last state</span>');
    $('chips').innerHTML=c.join('');
  }

  Feed('/api/monitor'+(isPublic?'?public_display=1':''), function(top){
    // a dashboard update reloads the page, as /audience does
    if(REV===null) REV=top.rev||'';
    else if(top.rev&&top.rev!==REV){ location.reload(); return; }
    lastTop=top;
    const lo=(top.robots||[]).find(r=>r.local);
    const mo=(lo&&lo.doc&&lo.doc.motion)||{};
    if(mo.avatar_offset!=null) OFFSET=Math.round(mo.avatar_offset*1000);
    if(mo.lipsync_gain!=null) GAIN=mo.lipsync_gain;
    for(const e of (top.robots||[])){
      if(!panels[e.slot]){
        panels[e.slot]=Panel(e.slot);
        $('robots').appendChild(panels[e.slot].el);
        if(!healed){ healed=true; selfHeal(panels[e.slot].layer); }
      }
      // one robot's bad document must not blank the other's column
      try{ panels[e.slot].update(e, top, lo&&lo.doc?lo.doc.portrait:null); }catch(err){ console.error(err); }
    }
    chips(top, true, 0);
  }, function(ok, fails){ if(!ok) chips(lastTop, false, fails); });

  (function pump(){
    for(const k in panels){ try{ panels[k].tick(); }catch(err){} }
    requestAnimationFrame(pump);
  })();
  keepAwake();
})();
</script></body></html>"""


# ===========================================================================
# /display — avatar, camera, question and answer, in the /audience look
# ===========================================================================
# 2026-09-15 (user: "a UI display for the monitor that contains the camera,
# avatar and the question and answer with the same theme"). A screen, not a
# console: the /audience layout — two gilt frames above two ivory plaques —
# with the avatar (the /stage state layer, over assets/portrait.* when one is
# provided) in the left frame and the camera in the right. The Host has no
# avatar (2026-09-15, user): pinned to it with ?robot=, the screen is the camera
# frame alone.
#
#   ?robot=alpha|beta   pin a robot; default is whoever plays Panganiban, so a
#                       role swap moves the screen with him
#   ?public_display=1   the stricter visitor mode: a question appears only once
#                       it has been answered, never if a guardrail fired
#   ?idle=<s>           seconds after an answer before the opening display
#                       returns (default 8, 0 = never), as /audience
#
# Without ?public_display the question shows live, as /audience does: the
# answer's text is published only after it has been spoken
# (main_voice_robot.py _publish_transcript("cj", ...)), so the strict mode
# cannot show the question while he is answering it.
DISPLAY_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Chief Justice Artemio V. Panganiban</title>
""" + GALLERY_FONTS + r"""
<style>""" + GALLERY_CSS + r"""
  html,body{height:100%;overflow:hidden}
  #title{position:fixed;top:2.3vh;left:0;right:0;text-align:center;pointer-events:none;
    font-family:'Playfair Display',Georgia,serif;font-weight:500;font-size:2.1vh;letter-spacing:.26em;
    text-transform:uppercase;color:var(--brass)}
  #pill{position:fixed;top:1.8vh;left:2vw;z-index:5}
  #frames{position:fixed;top:8.5vh;left:0;right:0;display:flex;justify-content:center;align-items:flex-start;gap:4.5vw}
  #frames .frame{width:min(43vw,calc(46vh * 16 / 9))}
  #bar{position:fixed;left:2vw;right:2vw;bottom:2.6vh;display:flex;gap:2vw;align-items:stretch}
  #bar .card{min-height:22vh;max-height:34vh;padding:2vh 1.8vw 2.6vh;overflow:hidden}
  #qbox{flex:0 1 40%} #abox{flex:1 1 60%}
  #qbox h3,#abox h3{font-size:2vh}
  #qt{font-size:2.8vh;max-height:12vh;flex:0 0 auto}
  #rows{flex:1 1 auto;min-height:0;overflow-y:auto;scrollbar-width:none}
  #ans{font-size:3vh;max-height:none;flex:1 1 auto;min-height:0}
  body.hidecursor,body.hidecursor *{cursor:none!important}
  @media (orientation:portrait){
    #frames{flex-direction:column;align-items:center;top:6vh;gap:3.5vh}
    #frames .frame{width:min(86vw,calc(22vh * 16 / 9))}
    #bar{flex-direction:column;gap:1.6vh}
    #bar .card{min-height:0}
    #qbox{flex:0 0 auto;max-height:15vh} #abox{flex:1 1 auto;max-height:22vh}
  }
</style></head><body>
<div id="title">Chief Justice Artemio V. Panganiban</div>
<div class="pill idle" id="pill"><span class="dot"></span><span id="pilllbl">Idle</span></div>
<div id="frames">
  <div class="frame" id="avatar">
    <img id="back" class="fill" alt=""><video id="backv" class="fill" muted loop playsinline autoplay></video>
    <canvas id="orb"></canvas>
  </div>
  <div class="frame" id="camera">
    <img id="camimg" class="fill" alt="">
    <div class="plate" id="camplate"><b>CJAP</b><span>Chief Justice Artemio V. Panganiban</span></div>
  </div>
</div>
<div id="bar">
  <div class="card" id="qbox"><h3 class="big">The Question</h3><div class="qt" id="qt"></div><div class="rows" id="rows"></div></div>
  <div class="card" id="abox"><h3 class="big" id="ah">The Chief Justice Answers</h3><div class="ans" id="ans"></div></div>
</div>
<script>
""" + DISPLAY_JS + GALLERY_JS + r"""
(function(){
  const Q=new URLSearchParams(location.search);
  const PUB=(Q.get('public_display')||'').toLowerCase();
  const isPublic=PUB==='1'||PUB==='true'||PUB==='yes';
  if(isPublic) document.body.classList.add('public');
  const PIN=(Q.get('robot')||'').toLowerCase();
  const IDLE_AFTER_S=(()=>{const v=parseFloat(Q.get('idle'));return v>=0?v:8;})();
  const $=(id)=>document.getElementById(id);
  const LABEL={idle:'Idle',listening:'Listening',thinking:'Thinking',speaking:'Speaking',muted:'Mic muted'};
  const ABOUT='A recreation of Chief Justice Panganiban, built only from what he has published';
  let OFFSET=0, GAIN=1, REV=null, slot=null, local=false, lastWav=null;
  const shown={};
  function put(id,h){ if(shown[id]!==h){ shown[id]=h; $(id).innerHTML=h; } }

  const layer=StateLayer($('orb'),{scale:0.32});
  const env=Envelope(()=>OFFSET, (name)=>clipUrl(local, slot, name));
  const words=WordReveal($('ans'));
  keepAwake(); selfHeal(layer);

  // a screen has no pointer: hide it after 3 s without movement, as /stage
  let curTimer=null;
  function armCursor(){
    document.body.classList.remove('hidecursor');
    clearTimeout(curTimer);
    curTimer=setTimeout(()=>document.body.classList.add('hidecursor'),3000);
  }
  ['mousemove','touchstart','pointerdown'].forEach(ev=>window.addEventListener(ev,armCursor,{passive:true}));
  armCursor();

  // the avatar's backdrop, if this installation has one (as /stage)
  const backdrop=Backdrop($('back'), $('backv'));

  // the camera: the shown robot's if it has one, else any robot's (this one
  // first). A failed stream shows the idle plaque and retries quietly.
  let cam=null, camRetry=0;
  const camimg=$('camimg');
  function camShow(on){ camimg.style.display=on?'block':'none'; $('camplate').style.display=on?'none':'flex'; }
  camimg.onerror=()=>{ camShow(false); cam=null; camRetry=Date.now()+15000; };
  function camera(robots, e){
    const order=[e].concat(robots.filter(r=>r!==e&&r.local), robots.filter(r=>r!==e&&!r.local));
    let want=null;
    for(const r of order){
      const u=cameraUrl(r);
      if(r.reachable&&r.doc&&r.doc.camera&&u){ want=u; break; }
    }
    if(want!==cam&&(!want||Date.now()>=camRetry)){
      cam=want;
      if(want){ camimg.src=want+'?t='+Date.now(); camShow(true); }
      else { camimg.removeAttribute('src'); camShow(false); }
    }
  }

  Feed('/api/monitor'+(isPublic?'?public_display=1':''), function(top){
    if(REV===null) REV=top.rev||'';
    else if(top.rev&&top.rev!==REV){ location.reload(); return; }
    const robots=top.robots||[];
    const lo=robots.find(r=>r.local);
    const mo=(lo&&lo.doc&&lo.doc.motion)||{};
    if(mo.avatar_offset!=null) OFFSET=Math.round(mo.avatar_offset*1000);
    if(mo.lipsync_gain!=null) GAIN=mo.lipsync_gain;
    backdrop(lo&&lo.doc?lo.doc.portrait:null);

    const e=robots.find(r=>r.slot===PIN)||robots.find(r=>r.role==='cjap')||lo||robots[0];
    if(!e) return;
    slot=e.slot; local=!!e.local;
    camera(robots, e);

    // a robot that has stopped answering, or whose app is down, reads as a
    // resting exhibit here — the fault belongs on /monitor, not on this screen
    const d=(e.reachable&&e.doc)?e.doc:{};
    let st=d.state||'idle';
    if(st==='down'||(isPublic&&st==='muted')) st='idle';
    layer.set(st);
    const pill=$('pill');
    if(pill.dataset.st!==st){ pill.dataset.st=st; pill.className='pill '+st; $('pilllbl').textContent=LABEL[st]||'Idle'; }
    $('avatar').classList.toggle('live', st==='speaking');
    $('camera').classList.toggle('live', st==='speaking');
    const cj=e.role!=='host';
    $('ah').textContent=cj?'The Chief Justice Answers':'The Host Says';
    $('avatar').style.display=cj?'':'none';     // the Host has no avatar: the camera frame alone

    const turns=d.turns||[], cur=turns.length?turns[turns.length-1]:null;
    const fresh=!!(cur&&(d.turn_ts==null||cur.ts>=d.turn_ts-1));
    const sp=d.speaking||{};
    // in the strict mode the question being answered is not in the feed yet,
    // so the last turn on file is the PREVIOUS one: never pair it with this answer
    const liveQ=(!isPublic&&cur&&cur.q&&fresh)?quote(cur.q):'';
    const waiting='<span class="idle">'+waitingLine(top)+'</span>';
    const endTs=(sp.done&&sp.n)?sp.ts:(cur?cur.ts:0);
    const opening=!cur||(IDLE_AFTER_S>0&&endTs>0&&(d.ts-endTs)>=IDLE_AFTER_S);

    if(st==='speaking'&&sp.current){
      put('qt', liveQ||waiting);
      put('rows', liveQ?rowsHtml(d.steps):'');
      if(words.show(sp, d.ts)) shown.ans=null;
      else put('ans','<span class="cur">'+esc(sp.current)+'</span>');
    } else {
      words.clear();
      if(st==='listening'&&!fresh){
        put('qt','<span class="idle think">Listening</span>'); put('rows','');
        put('ans','<span class="idle">'+(cj?'The Chief Justice is listening':'Listening')+'</span>');
      } else if(st==='thinking'){
        put('qt', liveQ||'<span class="idle think">Listening</span>');
        put('rows', liveQ?rowsHtml(d.steps):'');
        put('ans','<span class="idle think">'+(cj?'The Chief Justice is considering':'Getting ready')+'</span>');
      } else if(opening){
        put('qt', waiting); put('rows','');
        put('ans','<span class="idle">'+(cj?ABOUT:waitingLine(top))+'</span>');
      } else {
        put('qt', cur.q?quote(cur.q):waiting);
        put('rows', isPublic?'':rowsHtml(d.steps));
        put('ans', cur.a?esc(cur.a):'<span class="idle">'+ABOUT+'</span>');
      }
    }

    if(cj&&st==='speaking'&&sp.wav){
      if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }
      if(sp.play_ts&&d.ts) env.start(Math.max(0,d.ts-sp.play_ts));
    } else if(!cj||st!=='speaking'){ lastWav=null; env.clear(); }
  });

  (function pump(){
    if(layer.state()==='speaking'){
      const v=env.value();
      layer.envelope((v===null?voiced():v)*GAIN);
    } else layer.envelope(0);
    try{ words.tick(); }catch(err){}
    requestAnimationFrame(pump);
  })();
})();
</script></body></html>"""


# ===========================================================================
# /tune — the motion tuning panel
# ===========================================================================
# Sliders that apply to the RUNNING robot with no restart: each drag POSTs to
# /api/motion, which writes /dev/shm/cj_motion.json, which the robot's breath
# loop re-reads every cycle (app/main_voice_robot.py:_motion, mtime-cached).
#
# The preview beside them is the /stage state layer, NOT the robot's head — it
# shows what the browser-side knobs (lip-sync, response delay) do and lets you
# step through the four states without waiting for a turn. The head knobs
# (sway, breath, voice emphasis) act on the robot itself: watch the robot for
# those, which is why this panel is meant to be open next to it.
TUNE_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CJAP motion</title>
<style>
  :root{--bg:#12131a;--panel:#191b24;--line:#2b2e3c;--ink:#e8e6e1;--dim:#9aa0ae;
        --ok:#6ad39f;--warn:#e3b341;--bad:#e5747c}
  *{box-sizing:border-box}
  html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink);
    font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  #wrap{display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,460px);
    gap:14px;padding:14px;align-items:start}
  @media(max-width:820px){#wrap{grid-template-columns:1fr}}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
  h1{font-size:18px;margin:0 0 4px} h2{font-size:14px;margin:0 0 10px;color:var(--dim);
    text-transform:uppercase;letter-spacing:.06em}
  #prev{position:relative;aspect-ratio:16/10;background:#000;border-radius:8px;overflow:hidden}
  #layer{position:absolute;inset:0;width:100%;height:100%}
  .states{display:flex;gap:6px;margin:10px 0 4px;flex-wrap:wrap}
  .states button{flex:1 1 auto;padding:8px 6px;background:#20232e;color:var(--ink);
    border:1px solid var(--line);border-radius:7px;font-size:13px;cursor:pointer}
  .states button.on{border-color:var(--ok);color:var(--ok)}
  .row{margin:13px 0}
  .row label{display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px}
  .row .v{color:var(--ok);font-variant-numeric:tabular-nums}
  .row input[type=range]{width:100%}
  .row .h{font-size:11.5px;color:var(--dim);margin-top:2px}
  .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
  button.act{padding:9px 13px;background:#20232e;color:var(--ink);border:1px solid var(--line);
    border-radius:8px;cursor:pointer;font-size:13px}
  button.act:hover{border-color:var(--ok)}
  select,input[type=text]{background:#20232e;color:var(--ink);border:1px solid var(--line);
    border-radius:7px;padding:8px;font-size:13px}
  #msg{margin-top:10px;font-size:13px;color:var(--dim);min-height:1.3em}
  .note{font-size:12px;color:var(--dim);margin-top:8px;line-height:1.5}
  .warn{color:var(--warn)}
</style></head><body>
<div id="wrap">
  <div class="panel">
    <h1>Motion</h1>
    <div class="note" style="margin-top:0">Sliders apply to the running robot immediately &mdash;
    no restart. <b>Watch the robot</b> for head sway, breathing and voice emphasis; the preview
    here shows the state layer and what lip-sync and response delay do.</div>
    <div id="sliders"></div>
    <div class="btns">
      <button class="act" id="reset">Reset to defaults</button>
      <select id="presets"></select>
      <button class="act" id="load">Apply preset</button>
    </div>
    <div class="btns">
      <input type="text" id="pname" placeholder="preset name" style="flex:1">
      <button class="act" id="save">Save preset &rarr; repo</button>
    </div>
    <div id="msg"></div>
    <div class="note" id="pnote"></div>
  </div>
  <div class="panel">
    <h2>preview &mdash; state layer</h2>
    <div id="prev"><canvas id="layer"></canvas></div>
    <div class="states">
      <button data-s="idle">idle</button><button data-s="listening">listening</button>
      <button data-s="thinking">thinking</button><button data-s="speaking">speaking</button>
      <button data-s="live">follow robot</button>
    </div>
    <div class="note">
      <b>Response delay</b> is the one to set by ear: play a real answer, then drag until the
      mouth stops leading or trailing the voice. It differs per audio route &mdash; the internal
      speaker and an external one are not the same path &mdash; so note the value for each in
      <code>config/avatar_motion.json</code>.<br><br>
      <span class="warn">Breathing stops when the microphone is muted.</span> That is deliberate:
      the robot has no lights, so going still is how it shows it is muted.
    </div>
  </div>
</div>
<script>
""" + DISPLAY_JS + r"""
(function(){
  const $=(id)=>document.getElementById(id);
  const KEY=new URLSearchParams(location.search).get('key')||localStorage.getItem('cjkey')||'';
  let KNOBS={}, VAL={}, follow=true, forced=null;
  const dirty=new Set();
  function mark(){
    for(const k of Object.keys(KNOBS)){
      const v=$('v-'+k); if(!v) continue;
      v.style.color = dirty.has(k) ? 'var(--warn)' : 'var(--ok)';
      v.title = dirty.has(k) ? 'unsaved — release the slider to save' : 'saved';
    }
  }

  const layer=StateLayer($('layer'),{scale:0.32});
  const env=Envelope(()=>((VAL.avatar_offset||0)*1000));
  selfHeal(layer);

  function msg(t,cls){ $('msg').innerHTML='<span class="'+(cls||'')+'">'+t+'</span>'; }

  async function post(body){
    const r=await fetch('/api/motion',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(Object.assign({key:KEY},body))});
    return r.json();
  }
  async function load(){
    const r=await fetch('/api/motion?key='+encodeURIComponent(KEY));
    if(!r.ok){ msg('bad key — open this page as /tune?key=…','warn'); return; }
    const d=await r.json();
    KNOBS=d.knobs; VAL=d.motion;
    $('presets').innerHTML=Object.keys(d.presets||{}).map(n=>
      '<option'+(n===d.active?' selected':'')+'>'+n+'</option>').join('');
    $('pnote').textContent=(d.preset_notes||{})[d.active]||'';
    draw();
  }
  function draw(){
    $('sliders').innerHTML=Object.keys(KNOBS).map(k=>{
      const [lo,hi,def,lbl]=KNOBS[k];
      const step=(hi-lo)/200;
      return '<div class="row"><label><span>'+lbl+'</span>'+
             '<span class="v" id="v-'+k+'"></span></label>'+
             '<input type="range" id="s-'+k+'" min="'+lo+'" max="'+hi+'" step="'+step+'">'+
             '<div class="h">default '+def+'</div></div>';
    }).join('');
    for(const k of Object.keys(KNOBS)) bind(k);
    mark();
  }
  function show(k){
    const v=VAL[k];
    $('v-'+k).textContent=(k==='motion_scale')?Math.round(v*100)+'%'
      :(k==='avatar_offset')?(v>=0?'+':'')+Math.round(v*1000)+' ms'
      :(+v).toFixed( (KNOBS[k][1]-KNOBS[k][0])>5?2:3 );
  }
  function bind(k){
    const el=$('s-'+k); el.value=VAL[k]; show(k);
    let t=null;
    // Drag = live but UNSAVED (and the value says so). Release = persisted to
    // the active preset, so a number tuned by ear survives a reboot.
    el.addEventListener('input',()=>{
      VAL[k]=parseFloat(el.value); show(k); dirty.add(k); mark();
      clearTimeout(t);
      t=setTimeout(async()=>{                      // coalesce a drag into one write
        const o={}; o[k]=VAL[k];
        const d=await post(o);
        msg(d.ok?'live — release to save':('FAILED — '+(d.output||'')), d.ok?'warn':'warn');
      },120);
    });
    const commit=async()=>{
      if(!dirty.has(k)) return;
      const o={}; o[k]=VAL[k]; o.persist=true;
      const d=await post(o);
      if(d.ok){ dirty.delete(k); mark(); }
      msg(d.ok?(d.output||'saved'):('FAILED — '+(d.output||'')), d.ok?'':'warn');
    };
    el.addEventListener('change', commit);
    el.addEventListener('pointerup', commit);
  }
  $('reset').onclick=async()=>{ const d=await post({reset:true}); msg(d.output||''); load(); };
  $('load').onclick=async()=>{ const d=await post({preset_load:$('presets').value});
    msg(d.output||''); load(); };
  $('save').onclick=async()=>{
    const n=$('pname').value.trim()||$('presets').value;
    const d=await post({preset_save:n}); msg(d.output||'', d.ok?'':'warn'); load();
  };
  document.querySelectorAll('.states button').forEach(b=>{
    b.onclick=()=>{
      document.querySelectorAll('.states button').forEach(x=>x.classList.remove('on'));
      b.classList.add('on');
      const s=b.dataset.s;
      if(s==='live'){ follow=true; forced=null; }
      else { follow=false; forced=s; layer.set(s); }
    };
  });

  let lastWav=null;
  Feed('/api/display', function(d){
    if(follow){
      const s=(d.state==='muted'||d.state==='down')?'idle':d.state;
      layer.set(s);
    }
    const sp=d.speaking||{};
    if(d.state==='speaking'&&sp.wav){
      if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }
      if(sp.play_ts&&d.ts) env.start(Math.max(0,d.ts-sp.play_ts));
    } else if(d.state!=='speaking'){ lastWav=null; env.clear(); }
  });

  (function pump(){
    const st=layer.state();
    const g=(VAL.lipsync_gain==null?1:VAL.lipsync_gain);
    if(st==='speaking'){
      const v=env.value();
      const base=(v===null?voiced():v);
      layer.envelope(base*g);
    } else layer.envelope(0);
    requestAnimationFrame(pump);
  })();
  load();
})();
</script></body></html>"""
