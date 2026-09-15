"""USB-hub audio preference (2026-09-15): scripts/audio_hub.py, the app and /maintain.

User: "make sure to prioritize [the devices] connected to the hub when the hub
is connected, like for the audio, the mic and the speakers".
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import audio_hub as hub  # noqa: E402

OWN_SINK = {"name": "alsa_output.usb-Pollen_Robotics_Reachy_Mini_Audio_1-00.analog-stereo",
            "description": "Reachy Mini Audio Analog Stereo", "properties": {"device.class": "sound"}}
OWN_SRC = {"name": "alsa_input.usb-Pollen_Robotics_Reachy_Mini_Audio_1-00.analog-stereo",
           "properties": {"device.class": "sound"}}
OWN_MON = {"name": OWN_SINK["name"] + ".monitor", "properties": {"device.class": "monitor"}}
HUB_SINK = {"name": "alsa_output.usb-C-Media_USB_Audio_Device-00.analog-stereo",
            "description": "USB Audio Device Analog Stereo", "properties": {"device.class": "sound"}}
HUB_SRC = {"name": "alsa_input.usb-C-Media_USB_Audio_Device-00.mono-fallback",
           "description": "USB Audio Device Mono", "properties": {"device.class": "sound"}}
HUB_MON = {"name": HUB_SINK["name"] + ".monitor", "description": "Monitor of USB Audio Device",
           "properties": {"device.class": "monitor"}}
HDMI = {"name": "alsa_output.platform-fef00700.hdmi.hdmi-stereo", "properties": {}}
SINK = [{"name": HUB_SINK["name"], "label": "USB Audio Device Analog Stereo"}]
BT, LAPTOP = "04:21:44:84:1F:C1", "24:EE:9A:B2:13:D9"


def test_only_usb_sound_devices_other_than_the_robots_own_count():
    assert hub.external([OWN_SINK, HDMI, HUB_SINK], "sink") == SINK
    assert [s["name"] for s in hub.external([OWN_SRC, OWN_MON, HUB_MON, HUB_SRC], "source")] == [HUB_SRC["name"]]
    assert hub.external(None, "sink") == []


def test_route_header_and_legacy_route_files():
    assert hub.route_of("# Primary: dac\n# Secondary: none\n") == ("dac", "none")
    assert hub.route_of("# Route: internal speaker (XMOS) via PipeWire default sink.\n"
                        "pcm.!audio_out_route {\n    type pulse\n}\n") == ("internal", "none")   # beta's today
    legacy_bt = 'pcm.!audio_out_route {\n type plug\n slave { pcm { type bluealsa\n device "50:1B:6A:8B:16:F2"\n } }\n}\n'
    assert hub.route_of(legacy_bt) == ("50:1B:6A:8B:16:F2", "none")
    assert hub.route_of("") == ("internal", "none")


def test_plugging_in_switches_once_and_unplugging_puts_the_old_route_back():
    argv, seen, saved = hub.plan_output([], SINK, ("internal", "none"), None)
    assert argv == ["dac"] and seen == [HUB_SINK["name"]] and saved == ["internal", "none"]
    assert hub.plan_output(seen, SINK, ("dac", "none"), saved) == (None, seen, saved)      # still in: nothing
    assert hub.plan_output(seen, SINK, ("internal", "none"), saved)[0] is None             # operator's choice stands
    assert hub.plan_output(seen, [], ("dac", "none"), saved) == (["internal"], [], None)


def test_a_bluetooth_or_dual_route_comes_back_even_after_audio_out_ensure_moved_it():
    seen = [HUB_SINK["name"]]
    assert hub.plan_output(seen, [], ("dac", "none"), [BT, LAPTOP])[0] == ["dual", BT, LAPTOP]
    # the app's playback-failure path already fell back to internal: still restored
    assert hub.plan_output(seen, [], ("internal", "none"), [BT, "none"])[0] == [BT]
    # the operator picked another speaker meanwhile: left alone
    assert hub.plan_output(seen, [], ("50:1B:6A:8B:16:F2", "none"), [BT, "none"]) == (None, [], None)
    assert hub.restore_args(["dac", "none"]) == ["internal"]


def test_replugging_after_an_operator_override_switches_again():
    argv, seen, saved = hub.plan_output([HUB_SINK["name"]], [], ("internal", "none"), None)
    assert argv is None and seen == []
    assert hub.plan_output(seen, SINK, ("internal", "none"), saved)[0] == ["dac"]


@pytest.fixture
def files(monkeypatch, tmp_path):
    route, inroute = tmp_path / "route", tmp_path / "inroute"
    route.write_text("# Primary: internal\n# Secondary: none\n")
    monkeypatch.setattr(hub, "ROUTE_FILE", str(route))
    monkeypatch.setattr(hub, "INROUTE_FILE", str(inroute))
    return route, inroute


def _quiet(*a, **k):
    pass


def test_the_hub_mic_and_speaker_are_used_while_plugged_in_and_dropped_after(files):
    route, inroute = files
    nodes = {"sink": [OWN_SINK, HUB_SINK], "source": [OWN_SRC, HUB_MON, HUB_SRC]}
    ran = []

    def run(argv):
        ran.append(argv)
        route.write_text(f"# Primary: {argv[0]}\n# Secondary: none\n")
        return True
    state = hub.step({}, pactl=lambda k: nodes[k], run=run, log=_quiet)
    assert ran == [["dac"]]
    text = inroute.read_text()
    assert "pcm.!audio_in_route" in text and "type pulse" in text
    assert f'device "{HUB_SRC["name"]}"' in text and "# Input: usb USB Audio Device Mono" in text
    state = hub.step(state, pactl=lambda k: nodes[k], run=run, log=_quiet)
    assert ran == [["dac"]]                                                   # no flapping
    nodes = {"sink": [OWN_SINK], "source": [OWN_SRC, OWN_MON]}
    hub.step(state, pactl=lambda k: nodes[k], run=run, log=_quiet)
    assert ran == [["dac"], ["internal"]] and not inroute.exists()


def test_nothing_changes_while_pipewire_cannot_be_asked(files):
    _, inroute = files
    inroute.write_text(hub.inroute_text({"name": HUB_SRC["name"], "label": "Mic"}))

    def down(kind):
        raise RuntimeError("pactl: Connection refused")
    with pytest.raises(RuntimeError):
        hub.step({"seen": [HUB_SINK["name"]]}, pactl=down, run=lambda a: True, log=_quiet)
    assert inroute.exists()


def test_a_failed_restore_falls_back_to_the_internal_speaker(files):
    route, _ = files
    route.write_text("# Primary: dac\n# Secondary: none\n")
    ran = []
    hub.step({"seen": [HUB_SINK["name"]], "saved": [BT, "none"]}, pactl=lambda k: [],
             run=lambda a: ran.append(a) or a == ["internal"], log=_quiet)
    assert ran == [[BT], ["internal"]]


ASOUNDRC = '''pcm.reachymini_audio_sink {
    type plug
    slave.pcm "audio_out_route"
}
pcm.audio_out_route {
    type pulse
}
@hooks [
    {
        func load
        files [
            "/home/pollen/.asoundrc.route"
        ]
        errors false
    }
]
# card 0 card 1 card 2 card 3 card 4
pcm.reachymini_audio_src_plug {
    type plug
    slave.pcm "reachymini_audio_src_left"
}
'''


def test_asoundrc_patch_routes_capture_through_audio_in_route_and_is_idempotent():
    new, changed = hub.patch_asoundrc(ASOUNDRC, home="/home/pollen")
    assert changed
    assert 'slave.pcm "audio_in_route"' in new
    assert new.count('"reachymini_audio_src_left"') == 1                       # now only the fallback
    assert '"/home/pollen/.asoundrc.route"\n            "/home/pollen/.asoundrc.inroute"' in new
    assert new.index("pcm.audio_in_route {") < new.index("@hooks [")
    assert "card 0 card 1 card 2 card 3 card 4" in new                         # the daemon's boot check
    assert hub.patch_asoundrc(new, home="/home/pollen") == (new, False)
    with pytest.raises(ValueError):
        hub.patch_asoundrc("pcm.!default { type hw }\n", home="/home/pollen")


def test_the_app_follows_the_capture_route_and_drops_the_xmos_reference(monkeypatch, tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "app"))
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    import main_voice_robot as mvr
    f = tmp_path / "inroute"
    monkeypatch.setattr(mvr, "INROUTE_FILE", str(f))
    monkeypatch.setattr(mvr, "_in_route", {"mtime": None, "usb": False, "label": "robot mic",
                                           "source": None, "synced": None, "device": None})
    refreshed = []
    monkeypatch.setattr(mvr, "_alsa_config_refresh", lambda: refreshed.append(1))
    monkeypatch.setattr(mvr, "_ROBOT_MIC_DEVICE", "reachymini_audio_src_left")
    present = {HUB_SRC["name"]}
    monkeypatch.setattr(mvr, "_pulse_source_present", lambda name: name in present)
    monkeypatch.delenv("PULSE_SOURCE", raising=False)
    saved_device = mvr.sd.default.device
    mvr._input_route_sync()
    assert refreshed == [] and not mvr._input_route_usb()
    f.write_text(hub.inroute_text({"name": HUB_SRC["name"], "label": "Hub Mic"}))
    mvr._input_route_sync()
    assert refreshed == [1] and mvr._input_route_usb()
    # 2026-09-15: the app must RECORD from it, not only log it — through PipeWire
    assert os.environ.get("PULSE_SOURCE") == HUB_SRC["name"] and mvr.sd.default.device[0] == "pulse"
    mvr._input_route_sync()
    assert refreshed == [1]                                                   # once per change
    present.clear()                                                           # unplugged, file not yet updated
    mvr._input_route_sync()
    assert "PULSE_SOURCE" not in os.environ and mvr.sd.default.device[0] == "reachymini_audio_src_left"
    present.add(HUB_SRC["name"])
    mvr._input_route_sync()
    assert mvr.sd.default.device[0] == "pulse"
    monkeypatch.setenv("CJ_AEC_REF_FEED", "1")
    monkeypatch.setattr(mvr, "_bt_route", lambda: True)
    assert mvr._RefFeed.wanted() is False                                     # XMOS is not the mic
    f.unlink()
    mvr._input_route_sync()
    assert refreshed == [1, 1] and not mvr._input_route_usb() and mvr._RefFeed.wanted() is True
    assert "PULSE_SOURCE" not in os.environ and mvr.sd.default.device[0] == "reachymini_audio_src_left"
    mvr.sd.default.device = saved_device


def test_the_maintenance_page_names_the_microphone_in_use(monkeypatch, tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "dashboard"))
    import ui_common
    import ui_page_maintenance
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ui_common._audio_input() == "robot mic"
    (tmp_path / ".asoundrc.inroute").write_text(hub.inroute_text({"name": HUB_SRC["name"], "label": "Hub Mic"}))
    assert ui_common._audio_input() == "USB mic Hub Mic"
    assert "s.audio_input" in ui_page_maintenance.MAINTAIN_PAGE


def test_a_wireless_mic_receivers_headphone_jack_is_not_the_hall_speaker(monkeypatch):
    boya_sink = {"name": "alsa_output.usb-Shenzhen_jiayz_photo_industrial_ltd_BOYA_mini_2-02.analog-stereo",
                 "properties": {"device.class": "sound"}}
    assert hub.external([OWN_SINK, boya_sink], "sink") == []
    assert hub.external([OWN_SINK, boya_sink, HUB_SINK], "sink") == SINK
    monkeypatch.setattr(hub, "SPEAKER_DENY", [])
    assert len(hub.external([OWN_SINK, boya_sink], "sink")) == 1


def test_the_mic_tap_reopens_on_a_route_change_and_raises_on_a_stall(monkeypatch, tmp_path):
    import queue
    import types
    sys.path.insert(0, os.path.join(ROOT, "app"))
    import main_voice_robot as mvr
    tap = mvr._MicTap.__new__(mvr._MicTap)
    tap.q, tap._rem, tap.stream = queue.Queue(), None, types.SimpleNamespace(active=True)
    monkeypatch.setattr(mvr._MicTap, "STALL_EMPTIES", 2)
    with pytest.raises(mvr.sd.PortAudioError, match="stalled"):
        tap.read(16)
    f = tmp_path / "inroute"
    monkeypatch.setattr(mvr, "INROUTE_FILE", str(f))
    monkeypatch.setattr(mvr, "_in_route", {"mtime": None, "usb": False, "label": "robot mic",
                                           "source": None, "synced": None, "device": None})
    calls = []
    tap.reopen = lambda: calls.append("reopen")
    released = []
    monkeypatch.setitem(mvr._voice_lock, "lock", types.SimpleNamespace(release=lambda: released.append(1)))
    mvr._follow_input_route(tap)                    # nothing changed: nothing happens
    assert calls == []
    f.write_text(hub.inroute_text({"name": HUB_SRC["name"], "label": "Hub Mic"}))
    mvr._follow_input_route(tap)
    assert calls == ["reopen"] and released == [1]
    tap.stream = None
    f.unlink()
    mvr._follow_input_route(tap)                    # a closed tap is the lease thread's business
    assert calls == ["reopen"]
