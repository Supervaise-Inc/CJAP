#!/usr/bin/env python3
"""barge_in_sweep.py — Phase 3: find XVF3800 settings that let the stop
phrase survive answer playback on the EXTERNAL (Bluetooth) speaker.

Run it while the robot is idle, sit near the robot with the BT speaker on:

    ~/Supervaise-Reachy-Mini-Project-main/app/.venv/bin/python ~/tools/barge_in_sweep.py

For each combo it: applies the chip params, tells you to (1) wake CJ and ask
any question, (2) say the STOP PHRASE mid-answer, then waits for Enter and
records the peak stop score from the journal plus a copy of
/dev/shm/cj_stop_last.wav into ~/barge_sweep/<combo>/. Original chip values
are restored at the end (and on Ctrl+C). Pick the combo with the highest
real-stop peak vs bleed; then raise CJ_STOP_OWW_THRESHOLD from 0.01.

Combos (chip defaults first = baseline):
  PP_DTSENSITIVE  0|1   double-talk sensitivity (1 = favour near-end talker)
  PP_NLAEC_MODE   0|1|2 non-linear echo suppression aggressiveness
  PP_AGCMAXGAIN   64|32 lower max AGC gain = less speaker-bleed amplification
"""
import os, shutil, subprocess, time
from reachy_mini.media.audio_control_utils import init_respeaker_usb

COMBOS = [  # (dtsensitive, nlaec_mode, agcmaxgain)
    (0, 0, 64.0),   # baseline (current chip state 2026-08-31)
    (1, 0, 64.0),
    (1, 1, 64.0),
    (1, 2, 64.0),
    (1, 1, 32.0),
]
OUT = os.path.expanduser("~/barge_sweep")

def peak_from_journal():
    try:
        out = subprocess.run(["journalctl", "-u", "supervaise", "--since", "-3min",
                              "--no-pager", "-g", "peak"], capture_output=True, text=True).stdout
        return out.strip().splitlines()[-1] if out.strip() else "(no peak line found)"
    except Exception as e:
        return f"(journal read failed: {e})"

r = init_respeaker_usb()
orig = {n: list(r.read(n))[:c] for n, c in
        (("PP_DTSENSITIVE", 1), ("PP_NLAEC_MODE", 1), ("PP_AGCMAXGAIN", 1))}
print("originals:", orig)
os.makedirs(OUT, exist_ok=True)
try:
    for dt, nl, agc in COMBOS:
        tag = f"dt{dt}_nl{nl}_agc{int(agc)}"
        r.write("PP_DTSENSITIVE", [dt]); r.write("PP_NLAEC_MODE", [nl])
        r.write("PP_AGCMAXGAIN", [agc])
        print(f"\n=== {tag} applied. Wake CJ, ask a question, say the STOP "
              f"PHRASE mid-answer. Press Enter when the turn is over "
              f"(or type s+Enter to skip) ===")
        if input().strip().lower() == "s":
            continue
        d = os.path.join(OUT, tag); os.makedirs(d, exist_ok=True)
        try:
            shutil.copy("/dev/shm/cj_stop_last.wav", os.path.join(d, "stop_last.wav"))
        except OSError:
            print("  (no cj_stop_last.wav)")
        line = peak_from_journal()
        open(os.path.join(d, "peak.txt"), "w").write(line + "\n")
        print("  peak:", line)
finally:
    for n, v in orig.items():
        try: r.write(n, v)
        except Exception as e: print(f"restore {n} FAILED: {e} — power-cycle resets it")
    r.close()
    print("\noriginal chip values restored. Results in", OUT)
