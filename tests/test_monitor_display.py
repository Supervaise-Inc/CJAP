"""/monitor shows both robots (2026-09-15).

This machine comes from its own files, the other from its own dashboard's
/api/display, and every label names the machine whose data it is — the old
view named whoever played Panganiban over this machine's turns.
"""
from __future__ import annotations

import json
import pathlib
import sys
import types

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dashboard"))
import ui_routes as ui  # noqa: E402
import ui_page_display as disp  # noqa: E402

SLOTS = {"alpha": "reachy-cjap", "beta": "reachy-2"}


class _Sources:
    def robots(self):
        return {"slots": SLOTS, "labels": {"cjap": "Panganiban", "host": "Host"}}

    def authority(self):
        return {"host": "reachy-cjap", "port": 8080, "bind": "0.0.0.0", "ip": "",
                "url_template": "http://{host}.local:{port}",
                "url": "http://reachy-cjap.local:8080"}

    def machine_of(self, slot):
        return SLOTS[slot]


class _Console:
    def __init__(self, cjap_is):
        self.cjap_is = self.floor = cjap_is
        self.mode, self.profile = "direct", "kiosk"
        self.observed = {"alpha": {"online": True}, "beta": {"online": False}}
        self.sources = _Sources()

    def role_of(self, slot):
        return "cjap" if slot == self.cjap_is else "host"

    def name(self, slot):
        return f"{SLOTS[slot]} · {'Panganiban' if self.role_of(slot) == 'cjap' else 'Host'}"


def _console_module(authority=True, cjap_is="beta"):
    c = _Console(cjap_is)
    return types.SimpleNamespace(ConfigSources=_Sources,
                                 is_authority=lambda: authority,
                                 get_console=lambda: c)


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    for name in ("SPEAKING", "TRANSCRIPT", "TURN_META", "MUTED_FLAG", "WAKE_LIVE", "STAGE_DOC"):
        monkeypatch.setattr(disp, name, str(tmp_path / name))
    monkeypatch.setattr(disp, "_health", lambda: {"supervaise": True})
    monkeypatch.setattr(disp, "cam_backend", lambda: None)
    monkeypatch.delenv("CJ_ROBOT_SLOT", raising=False)
    monkeypatch.delenv("CJ_ROBOT_ROLE", raising=False)
    disp._peer.clear()


def _on(monkeypatch, host):
    monkeypatch.setattr(disp, "_hostname", lambda: host)


def test_label_names_this_machine_not_whoever_plays_panganiban(monkeypatch):
    _on(monkeypatch, "reachy-cjap")
    d = disp.display_doc(console=_console_module(cjap_is="beta"))
    assert d["robot"] == {"slot": "alpha", "machine": "reachy-cjap", "role": "host",
                          "label": "reachy-cjap · Host"}
    assert d["cjap_is"] == "beta" and d["floor"] == "beta"
    assert d["online"] is True                  # alpha's own observation, not beta's


def test_the_other_machine_knows_its_slot_but_not_its_role(monkeypatch):
    _on(monkeypatch, "reachy-2")
    d = disp.display_doc(console=_console_module(authority=False))
    assert d["robot"]["slot"] == "beta" and d["robot"]["role"] is None
    assert "cjap_is" not in d


def _peer(slot, **extra):
    return json.dumps({"state": "speaking", "turns": [],
                       "robot": {"slot": slot, "machine": SLOTS[slot], "role": None}, **extra}).encode()


def test_monitor_merges_this_robot_and_the_other(monkeypatch):
    _on(monkeypatch, "reachy-cjap")
    urls = []
    fetch = lambda u: urls.append(u) or _peer("beta")
    m = disp.monitor_doc(console=_console_module(cjap_is="beta"), fetch=fetch)
    by = {r["slot"]: r for r in m["robots"]}
    assert urls == ["http://reachy-2.local:8080/api/display"]
    assert by["alpha"]["local"] and by["alpha"]["role"] == "host"
    assert by["beta"]["reachable"] and by["beta"]["role"] == "cjap"
    assert by["beta"]["label"] == "Panganiban" and by["beta"]["has_floor"]
    assert by["beta"]["doc"]["state"] == "speaking"
    assert m["cjap_is"] == "beta" and m["mode"] == "direct"


def test_served_from_beta_the_roles_come_from_alphas_document(monkeypatch):
    _on(monkeypatch, "reachy-2")
    urls = []
    fetch = lambda u: urls.append(u) or _peer("alpha", cjap_is="alpha", floor="alpha",
                                              mode="duet", profile="event")
    m = disp.monitor_doc(console=_console_module(authority=False), fetch=fetch)
    by = {r["slot"]: r for r in m["robots"]}
    assert urls == ["http://reachy-cjap.local:8080/api/display"]
    assert by["beta"]["local"] and by["beta"]["role"] == "host"
    assert by["alpha"]["role"] == "cjap" and by["alpha"]["has_floor"]
    assert m["mode"] == "duet"


def test_a_dead_peer_keeps_its_last_document_and_says_so(monkeypatch):
    _on(monkeypatch, "reachy-cjap")
    con = _console_module()
    disp.monitor_doc(console=con, fetch=lambda u: _peer("beta"))
    disp._peer[("beta", False)]["at"] = 0          # past the cache interval

    def down(u):
        raise OSError("timed out")
    beta = {r["slot"]: r for r in disp.monitor_doc(console=con, fetch=down)["robots"]}["beta"]
    assert not beta["reachable"] and "timed out" in beta["error"]
    assert beta["doc"]["state"] == "speaking" and beta["age_s"] is not None


def test_many_monitors_share_one_fetch_of_the_peer(monkeypatch):
    _on(monkeypatch, "reachy-cjap")
    calls = []
    fetch = lambda u: calls.append(u) or _peer("beta")
    for _ in range(3):
        disp.monitor_doc(console=_console_module(), fetch=fetch)
    assert len(calls) == 1


def test_public_monitor_leaks_no_error_text_but_keeps_the_camera(monkeypatch):
    _on(monkeypatch, "reachy-cjap")
    m = disp.monitor_doc(public=True, console=_console_module(), fetch=lambda u: _peer("beta"))
    beta = {r["slot"]: r for r in m["robots"]}["beta"]
    assert "error" not in beta
    assert beta["camera_url"] == "http://reachy-2.local:8080/api/camera.mjpg"   # /display shows it


def test_peer_sentence_wav_only_fetches_a_real_clip_name():
    urls = []
    fetch = lambda u: urls.append(u) or b"RIFF"
    con = _console_module()
    assert disp.peer_sentence_wav("gamma", "cj_sent_1.wav", con, fetch) is None
    assert disp.peer_sentence_wav("beta", "../../etc/passwd", con, fetch) is None
    assert urls == []
    assert disp.peer_sentence_wav("beta", "cj_sent_12.wav", con, fetch) == b"RIFF"
    assert urls == ["http://reachy-2.local:8080/api/sentence.wav?name=cj_sent_12.wav"]


class _H:
    def _send(self, code, body, ctype="application/json"):
        self.code, self.body = code, body


def test_monitor_page_is_the_exhibit_look_over_both_robots():
    h = _H()
    assert ui.handle_get(h, "/monitor", {}) and h.code == 200
    assert "Playfair Display" in h.body and "border-image" in h.body   # the /audience frame
    assert "/api/monitor" in h.body and "The Chief Justice Answers" in h.body
    h = _H()
    assert ui.handle_get(h, "/api/monitor/sentence.wav", {"slot": "x", "name": "y"})
    assert h.code == 404


def test_display_page_has_avatar_camera_and_both_plaques():
    h = _H()
    assert ui.handle_get(h, "/display", {}) and h.code == 200
    for piece in ('id="avatar"', 'id="orb"', 'id="camera"', 'id="camimg"',
                  'id="qt"', 'id="ans"', "The Question", "The Chief Justice Answers"):
        assert piece in h.body, piece
    assert "Playfair Display" in h.body and "border-image" in h.body   # same look as /audience
    assert "/api/monitor" in h.body and "/api/state" not in h.body     # read-only feed
    # the shared look is one definition, not a copy per page
    assert disp.GALLERY_CSS in h.body and disp.GALLERY_CSS in disp.MONITOR_PAGE


def test_the_host_has_no_avatar_on_either_page():
    # 2026-09-15: only Panganiban has an avatar; decided by role, so a swap follows
    assert "$('avatar').style.display=cj?'':'none'" in disp.DISPLAY_PAGE
    assert "const avatar=role!=='host'" in disp.MONITOR_PAGE
    assert 'class="plate hostplate"' in disp.MONITOR_PAGE              # camera-less Host frame
    assert "img.className=avatar?'camin':'fill'" in disp.MONITOR_PAGE  # Host camera fills the frame


def test_monitor_has_no_heading_name_row_or_mode_chip():
    # 2026-09-15, user: drop "Chief Justice Panganiban monitor", the
    # Panganiban/Host name row and the "direct · kiosk" chip
    page = disp.MONITOR_PAGE
    assert "<h1>" not in page and "<small>monitor</small>" not in page
    assert 'class="name"' not in page and "q('.mach')" not in page
    assert "top.mode)+" not in page and "top.profile?" not in page


def test_every_avatar_frame_draws_the_portrait_behind_the_layer():
    # one Backdrop() for both gallery pages, as /stage draws it
    assert disp.DISPLAY_JS.count("function Backdrop(") == 1 and "function Backdrop(" not in disp.GALLERY_JS
    assert "Backdrop($('back'), $('backv'))" in disp.DISPLAY_PAGE
    assert "Backdrop(q('.back'), q('.backv'))" in disp.MONITOR_PAGE
    assert "backdrop(avatar?portrait:null)" in disp.MONITOR_PAGE     # never behind the Host
    assert "backdrop(d.portrait)" in disp.STAGE_PAGE


def test_face_camera_page_is_the_avatar_page_with_the_camera_beside_it():
    import ui_page_face as face
    h = _H()
    assert ui.handle_get(h, "/face-camera", {}) and h.code == 200
    body = h.body
    assert body == face.FACE_CAMERA_PAGE
    assert 'id="vid"' in body and "/api/avatar-session" in body          # the live face
    assert 'id="cam2img"' in body and "/api/camera.mjpg" in body         # and the camera
    assert body.index('id="cam"') < body.index('id="cam2"')              # face first
    assert "Host" not in body and "cjap_is" not in body                  # no host concept
    assert body.rstrip().endswith("</script></body></html>")


def test_face_avatar_layers_dissolve_and_the_idle_loop_has_no_seam():
    # 2026-09-15, user: "improve the movement of the avatar and not glitchy"
    import ui_page_face as face
    for page in (face.FACE_AVATAR_PAGE, face.FACE_CAMERA_PAGE):
        assert 'id="idle2"' in page and "function idleSwap(" in page     # two copies, cross-faded
        assert "loop = true" not in page                                  # no hard loop seam
        assert '$("still").style.display' not in page                     # layers fade, never cut
        assert "snap(stillCache)" in page                                 # re-takes stay off screen
        assert "setListening(!speakingNow && Date.now() >= busyUntil)" in page


def test_the_orb_eases_between_states_on_every_page():
    assert "const W8=" in disp.DISPLAY_JS and "function voiced(" in disp.DISPLAY_JS
    for page in (disp.STAGE_PAGE, disp.MONITOR_PAGE, disp.DISPLAY_PAGE, disp.TUNE_PAGE):
        assert "Math.abs(Math.sin(performance.now()/240))" not in page
        assert "function voiced(" in page


class _Upload:
    def __init__(self, data, length=None):
        import io
        self.rfile = io.BytesIO(data)
        self.headers = {"Content-Length": str(len(data) if length is None else length)}
        self.close_connection = False


def test_the_captured_face_becomes_the_portrait_and_goes_to_the_other_robot(monkeypatch, tmp_path):
    # 2026-09-15, user: "why does the avatar not appear in the other UI"
    monkeypatch.setattr(disp, "ASSETS", str(tmp_path))
    _on(monkeypatch, "reachy-cjap")
    sent = []
    jpeg = b"\xff\xd8\xff\xe0" + b"x" * 2000
    ok, _ = disp.portrait_put(jpeg, forward=False)
    assert ok and (tmp_path / "portrait.jpg").read_bytes() == jpeg
    p = disp.portrait()
    assert p["file"] == "portrait.jpg" and p["kind"] == "image" and p["v"] > 0

    disp._portrait_forward(jpeg, con=_console_module(), post=lambda u, d: sent.append((u, d)))
    assert sent == [("http://reachy-2.local:8080/api/avatar-portrait?forwarded=1&key="
                     + disp.DASH_KEY, jpeg)]                      # to beta only, never back to alpha

    assert disp.portrait_put(b"<html>", forward=False)[0] is False  # only a JPEG is stored
    h = _Upload(jpeg, length=disp.PORTRAIT_UPLOAD_MAX + 1)
    assert disp.portrait_upload(h, {})[0] is False and h.close_connection
    ok, _ = disp.portrait_upload(_Upload(jpeg), {"forwarded": "1"})   # a forwarded copy stops here
    assert ok


def test_every_page_with_an_avatar_shows_the_shared_face():
    import ui_page_face as face
    for page in (face.FACE_AVATAR_PAGE, face.FACE_CAMERA_PAGE):
        assert "/api/avatar-portrait?key=" in page and page.count("sendPortrait(") >= 3
    assert "classList.toggle('hasface', !!p)" in disp.DISPLAY_JS          # /monitor, /display, /stage
    assert "classList.toggle('hasface', !!p)" in disp.STAGE_PAGE
    assert "'/assets/portrait?v='" in disp.DISPLAY_JS and "'/assets/portrait?v='" in disp.STAGE_PAGE


EYES = [{"c1": [0.43229, 0.41852], "c2": [0.46354, 0.42315], "up": 0.40648, "lo": 0.42315},
        {"c1": [0.51927, 0.39537], "c2": [0.55573, 0.39167], "up": 0.38241, "lo": 0.39815}]


def test_the_portrait_keeps_its_eyes_only_for_the_file_they_were_found_in(monkeypatch, tmp_path):
    # 2026-09-15, user: "make the avatar breathing and randomly closing its eyes"
    import urllib.parse
    monkeypatch.setattr(disp, "ASSETS", str(tmp_path))
    _on(monkeypatch, "reachy-cjap")
    jpeg = b"\xff\xd8\xff\xe0" + b"x" * 3000
    ok, msg = disp.portrait_put(jpeg, forward=False, eyes=EYES)
    assert ok and "eyes found" in msg and disp.portrait()["eyes"] == EYES
    disp.portrait_put(jpeg + b"y", forward=False)                  # a new face, no eyes
    assert "eyes" not in disp.portrait()

    bad = [None, [], "x", [EYES[0]] * 3,
           [{"c1": [0.1, 0.1], "c2": [0.2, 0.1], "up": 0.5, "lo": 0.4}],      # lids upside down
           [{"c1": [2, 0.1], "c2": [0.2, 0.1], "up": 0.1, "lo": 0.2}],        # off the picture
           [{"c1": [True, 0.1], "c2": [0.2, 0.1], "up": 0.1, "lo": 0.2}],
           [{"c1": [0.1], "c2": [0.2, 0.1], "up": 0.1, "lo": 0.2}]]
    for b in bad:
        assert disp.clean_eyes(b) is None, b

    ok, _ = disp.portrait_upload(_Upload(jpeg), {"forwarded": "1",
                                                 "eyes": urllib.parse.quote(json.dumps(EYES))})
    assert ok and disp.portrait()["eyes"] == EYES
    ok, _ = disp.portrait_upload(_Upload(jpeg + b"z"), {"forwarded": "1", "eyes": "%7Bnot json"})
    assert ok and "eyes" not in disp.portrait()

    sent = []
    disp._portrait_forward(jpeg, con=_console_module(), post=lambda u, d: sent.append(u), eyes=EYES)
    assert len(sent) == 1 and json.loads(urllib.parse.unquote(sent[0].split("&eyes=")[1])) == EYES


def test_every_portrait_breathes_moves_and_blinks():
    import ui_page_face as face
    for page in (disp.STAGE_PAGE, disp.MONITOR_PAGE, disp.DISPLAY_PAGE, disp.TUNE_PAGE,
                 face.FACE_AVATAR_PAGE, face.FACE_CAMERA_PAGE):
        assert page.count("function FaceAnim(") == 1
    assert "anim=FaceAnim(cv)" in disp.DISPLAY_JS                          # the portrait behind the orb
    assert 'FaceAnim($("still"))' in face.FACE_AVATAR_PAGE                  # the parked still
    assert "@mediapipe/tasks-vision@1.0.1" in face.FACE_AVATAR_PAGE         # pinned, not @latest
    assert "canvas.orb" in disp.MONITOR_PAGE and "q('canvas')" not in disp.MONITOR_PAGE
    # 2026-09-15: the body breathes (strips lifted under the head), and no two blinks match
    js = disp.FACE_ANIM_JS
    assert "function body(W,H,bb,sway)" in js and "body(W,H,k*b,sway)" in js
    assert "0,0,W,sh, sway,-rise" in js                                    # the head sways over the shoulders
    assert "ctx.scale(1+(sy-1)*0.4,sy)" not in js                        # the old whole-frame breath
    assert "function newBlink(now)" in js and "blinkT" not in js and "CLOSE" not in js
