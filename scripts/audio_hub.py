#!/usr/bin/env python3
"""Prefer the microphone and speaker on a USB hub while one is plugged in.

2026-09-15, user: "make sure to prioritize [the devices] connected to the hub
when the hub is connected, like for the audio, the mic and the speakers".

Runs as audio-hub.service on each robot and asks PipeWire every POLL_S. Any
USB sound device that is not the robot's own Reachy Mini Audio counts. That is
what a hub's audio jack or a USB microphone shows up as. A hub with no sound
chip (the one plugged in on 2026-09-15 carries only Ethernet) changes nothing.

speaker     It appears -> `~/bin/audio-out dac`, remembering the route it
            replaced. It goes -> that route back, or the internal speaker when
            it cannot be restored. Appearing is edge-triggered and remembered
            across restarts (STATE), so an operator who picks another output
            while it is still plugged in is not overridden until it is plugged
            in again.
microphone  While one is present, ~/.asoundrc.inroute points pcm.audio_in_route
            (what the voice app records from, see patch_asoundrc) at its
            PipeWire source. Otherwise the file is removed and ~/.asoundrc's
            fallback, the robot's XMOS beam, applies. The voice app re-reads the
            ALSA config before every capture open
            (main_voice_robot._input_route_sync), so the next turn uses it
            without a restart.

What it costs: the XMOS array does echo cancellation, beamforming and speaker
direction, and a USB microphone does none of that. The robot hears its own
voice through it, and its level differs from the XMOS beam the loudness
thresholds in config/modes/*.json were tuned on. Check both at the venue with
the hub's devices in place.

    python3 scripts/audio_hub.py                  watch (what the service runs)
    python3 scripts/audio_hub.py --once           one pass, then exit
    python3 scripts/audio_hub.py --patch-asoundrc route capture through audio_in_route
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
AUDIO_OUT = os.path.join(HOME, "bin", "audio-out")
ROUTE_FILE = os.path.join(HOME, ".asoundrc.route")
INROUTE_FILE = os.path.join(HOME, ".asoundrc.inroute")
STATE = os.path.join(HOME, ".cache", "cj_audio_hub.json")
POLL_S = 2.0
OWN_CARD = "Reachy_Mini_Audio"
# USB sound devices whose playback side is never the hall speaker: a wireless
# microphone receiver's headphone-monitor jack would otherwise take every
# answer, inaudibly. Substrings of the PipeWire node name, comma-separated.
SPEAKER_DENY = [s for s in os.environ.get("CJ_HUB_SPEAKER_DENY", "BOYA").split(",") if s.strip()]


def external(nodes, kind):
    """PipeWire nodes (`pactl -f json list sinks|sources`) -> [{name, label}]
    of USB sound devices other than the robot's own card, in pactl's order.
    The monitor of a sink is not a microphone."""
    prefix = "alsa_output.usb-" if kind == "sink" else "alsa_input.usb-"
    out = []
    for n in nodes or []:
        name = str(n.get("name") or "")
        props = n.get("properties") or {}
        if not name.startswith(prefix) or OWN_CARD in name:
            continue
        if kind == "sink" and any(d.strip().lower() in name.lower() for d in SPEAKER_DENY):
            continue
        if kind == "source" and (name.endswith(".monitor") or props.get("device.class") == "monitor"):
            continue
        label = n.get("description") or props.get("device.description") or name
        out.append({"name": name, "label": str(label).replace("\n", " ").strip()})
    return out


def inroute_text(source):
    """~/.asoundrc.inroute for a USB microphone; None when there is none."""
    if not source:
        return None
    return ("# Written by scripts/audio_hub.py - do not edit by hand.\n"
            f"# Input: usb {source['label']}\n"
            "pcm.!audio_in_route {\n"
            "    type pulse\n"
            f"    device \"{source['name'].replace(chr(34), '')}\"\n"
            "}\n")


def route_of(text):
    """(primary, secondary) from the ~/bin/audio-out route file header. A
    legacy file with no header is the internal speaker, or its Bluetooth device."""
    text = text or ""
    p = re.search(r"^# Primary: (\S+)", text, re.M)
    s = re.search(r"^# Secondary: (\S+)", text, re.M)
    if p:
        return p.group(1), (s.group(1) if s else "none")
    if "type bluealsa" in text:
        m = re.search(r'device "([0-9A-Fa-f:]{17})"', text)
        if m:
            return m.group(1), "none"
    return "internal", "none"


def restore_args(saved):
    """audio-out arguments that put a remembered route back."""
    p, s = (list(saved) + ["none"])[:2]
    if p in (None, "", "dac"):
        return ["internal"]
    return ["dual", p, s] if s not in (None, "", "none") else [p]


def plan_output(seen, sinks, route, saved):
    """-> (audio-out argv or None, sink names now, route to restore later or None).

    seen   names of the USB speakers present at the last pass
    sinks  external() speakers present now
    route  (primary, secondary) of the output right now
    saved  the route a switch to the DAC replaced, or None
    """
    names = [x["name"] for x in sinks]
    primary = route[0]
    if names:
        new = [n for n in names if n not in (seen or [])]
        if new and primary != "dac":
            return ["dac"], names, (saved or list(route))
        return None, names, saved
    if primary == "dac":
        return restore_args(saved or ["internal", "none"]), names, None
    if saved and primary == "internal" and saved[0] != "internal":
        # the app's playback-failure path (`audio-out ensure`) already fell
        # back to the internal speaker: still put the remembered one back
        return restore_args(saved), names, None
    return None, names, None


def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def _write_inroute(text):
    """Make ~/.asoundrc.inroute say `text` (None = no file). -> True if changed."""
    if text is None:
        if os.path.exists(INROUTE_FILE):
            os.unlink(INROUTE_FILE)
            return True
        return False
    if _read(INROUTE_FILE) == text:
        return False
    tmp = INROUTE_FILE + ".part"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, INROUTE_FILE)
    return True


def _pactl(kind):
    r = subprocess.run(["pactl", "-f", "json", "list", kind + "s"],
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "pactl failed").strip()[:160])
    return json.loads(r.stdout or "[]")


def _run(argv, sink=None):
    env = dict(os.environ)
    if sink:
        env["CJ_DAC_SINK"] = sink        # audio-out routes to THIS sink, not its own first pick
    try:
        r = subprocess.run([AUDIO_OUT] + argv, capture_output=True, text=True, timeout=45, env=env)
    except Exception as e:
        print(f"[audio-hub] audio-out {' '.join(argv)}: {type(e).__name__}: {e}", flush=True)
        return False
    for line in (r.stdout + r.stderr).strip().splitlines()[-4:]:
        print(f"[audio-hub]   {line}", flush=True)
    return r.returncode == 0


def step(state, pactl=_pactl, run=_run, log=print):
    """One pass. Raises when PipeWire cannot be asked, and then nothing changes,
    so a PipeWire restart never drops the hub's microphone by mistake."""
    sinks = external(pactl("sink"), "sink")
    sources = external(pactl("source"), "source")
    route = route_of(_read(ROUTE_FILE))
    argv, seen, saved = plan_output(state.get("seen") or [], sinks, route, state.get("saved"))
    if argv:
        why = (f"USB speaker {sinks[0]['label']} plugged in" if sinks
               else "USB speaker gone")
        log(f"[audio-hub] {why}: audio-out {' '.join(argv)}", flush=True)
        ok = run(argv, sinks[0]["name"]) if argv == ["dac"] and run is _run else run(argv)
        if not ok and argv != ["internal"]:
            log("[audio-hub] that failed: audio-out internal", flush=True)
            run(["internal"])
    mic = sources[0] if sources else None
    if _write_inroute(inroute_text(mic)):
        log(f"[audio-hub] microphone: {'USB ' + mic['label'] if mic else 'the robot (XMOS beam)'}",
            flush=True)
    return {"seen": seen, "saved": saved}


def _load_state():
    try:
        d = json.loads(_read(STATE) or "{}")
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def _save_state(state):
    if json.dumps(state, sort_keys=True) == json.dumps(_load_state(), sort_keys=True):
        return
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE + ".part", "w") as f:
        json.dump(state, f)
    os.replace(STATE + ".part", STATE)


def patch_asoundrc(text, home=HOME):
    """~/.asoundrc with the voice app's capture routed through pcm.audio_in_route.
    -> (text, changed). Idempotent. Raises ValueError, and nothing should be
    written, when the file is not shaped like this installation's."""
    if "pcm.audio_in_route" in text:
        return text, False
    plug = re.compile(r'(pcm\.reachymini_audio_src_plug\s*\{\s*type plug\s*slave\.pcm\s*)"reachymini_audio_src_left"')
    if len(plug.findall(text)) != 1:
        raise ValueError("pcm.reachymini_audio_src_plug -> reachymini_audio_src_left not found exactly once")
    if text.count("@hooks [") != 1:
        raise ValueError("expected exactly one @hooks block")
    text = plug.sub(r'\1"audio_in_route"', text)
    route = f'"{home}/.asoundrc.route"'
    m = re.search(r"^([ \t]*)" + re.escape(route) + r"[ \t]*$", text, re.M)
    if not m:
        raise ValueError("the @hooks include of ~/.asoundrc.route was not found")
    text = text[:m.end()] + "\n" + m.group(1) + f'"{home}/.asoundrc.inroute"' + text[m.end():]
    fallback = ("# 2026-09-15 capture route (scripts/audio_hub.py): the voice app records from\n"
                "# pcm.audio_in_route. This fallback is the robot's own XMOS beam; while a USB\n"
                "# microphone is plugged in, ~/.asoundrc.inroute (included below) overrides it.\n"
                "pcm.audio_in_route {\n"
                "    type plug\n"
                "    slave.pcm \"reachymini_audio_src_left\"\n"
                "}\n")
    i = text.index("@hooks [")
    return text[:i] + fallback + text[i:], True


def _patch_file(path=None):
    path = path or os.path.join(HOME, ".asoundrc")
    new, changed = patch_asoundrc(_read(path))
    if not changed:
        print("~/.asoundrc already routes capture through audio_in_route")
        return
    backup = path + ".bak-inroute-" + time.strftime("%Y%m%d")
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    with open(path + ".part", "w") as f:
        f.write(new)
    os.replace(path + ".part", path)
    print(f"~/.asoundrc patched (backup {backup})")


def main(argv):
    if "--patch-asoundrc" in argv:
        _patch_file()
        return 0
    state = _load_state()
    print(f"[audio-hub] preferring USB-hub audio; checking every {POLL_S:.0f} s", flush=True)
    while True:
        try:
            state = step(state)
            _save_state(state)
        except Exception as e:
            print(f"[audio-hub] pass skipped: {type(e).__name__}: {e}", flush=True)
        if "--once" in argv:
            return 0
        time.sleep(POLL_S)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
