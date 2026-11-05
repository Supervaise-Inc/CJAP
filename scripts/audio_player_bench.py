#!/usr/bin/env python3
"""Compare the three sentence players on the robot (2026-11-05). Run ON a Reachy.

    cd ~/Supervaise-Reachy-Mini-Project-main/app
    python3 ../scripts/audio_player_bench.py --sentences 6 --json player_bench.json

Players:
    aplay   one `aplay` process per sentence (the old path, CJ_SENTENCE_PLAYER=aplay)
    stream  one PortAudio stream for the answer (the default)
    gst     one GStreamer pipeline for the answer (CJ_SENTENCE_PLAYER=gst)

It plays N identical tone-burst "sentences" back to back through each player
and reports, per player:

    open_ms        time from the first play() call until the first samples were handed over
    wall_s         total time for all N sentences
    ideal_s        N x burst length
    excess_s       wall_s - ideal_s
    per_boundary_ms  excess_s / N x 1000

A gapless player buffers ahead of the speaker, so its excess can be small or even
negative (the writer runs ahead of the sound); a player that pays a process spawn
and a device re-open per sentence shows 150-400 ms per boundary. These are
SOFTWARE-side numbers. The acoustic gap between sentences, and the delay from
write to sound, need an outside measurement (a phone or recorder next to the
speaker): the robot's own microphone cannot be used, because its echo canceller
removes the robot's own playback.

The bursts are loud enough to hear. Run it with the speaker volume set low.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import wave

import numpy as np

RATE = 24000


def make_burst(path, secs):
    t = np.arange(int(RATE * secs)) / RATE
    a = (0.2 * 32767 * np.sin(2 * np.pi * 440 * t)).astype(np.int16)
    n = int(RATE * 0.01)                       # 10 ms fades: no clicks
    a[:n] = (a[:n] * np.linspace(0, 1, n)).astype(np.int16)
    a[-n:] = (a[-n:] * np.linspace(1, 0, n)).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(a.tobytes())


class _NeverFires:
    fired = False


def run_aplay(m, wav, n):
    t_first = None
    t0 = time.monotonic()
    for _ in range(n):
        if t_first is None:
            t_first = time.monotonic() - t0
        subprocess.run(m._aplay_cmd(wav), check=False)
    return t_first, time.monotonic() - t0


def run_player(player, wav, n):
    t0 = time.monotonic()
    t_first = None
    try:
        for _ in range(n):
            player.play(wav, _NeverFires(), trim=False)
            if t_first is None:
                t_first = time.monotonic() - t0
    finally:
        player.close()
    return t_first, time.monotonic() - t0


def bench(m, which, wav, n, secs, repeats):
    rows = []
    for _ in range(repeats):
        if which == "aplay":
            first, wall = run_aplay(m, wav, n)
        elif which == "stream":
            first, wall = run_player(m._SentenceOut(), wav, n)
        else:
            import gst_audio
            if not gst_audio.available():
                return {"player": which, "error": "GStreamer (appsrc, alsasink) not available"}
            player = gst_audio.GstSentenceOut(
                load_wav=m._load_wav_mono_int16, trim_edges=m._trim_edges,
                ref_feed=m._REF_FEED, dry_run=m._dry_run,
                dual_route=m._dual_route, bt_route=m._bt_route,
                alsa_refresh=m._alsa_config_refresh)
            first, wall = run_player(player, wav, n)
        ideal = n * secs
        rows.append({"first_s": first, "wall_s": wall, "excess_s": wall - ideal})
    med = lambda k: statistics.median(r[k] for r in rows)    # noqa: E731
    return {"player": which, "repeats": repeats, "sentences": n,
            "open_ms": round(med("first_s") * 1000, 1), "wall_s": round(med("wall_s"), 3),
            "ideal_s": round(n * secs, 3), "excess_s": round(med("excess_s"), 3),
            "per_boundary_ms": round(med("excess_s") / n * 1000, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sentences", type=int, default=6)
    ap.add_argument("--burst-s", type=float, default=0.6)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--players", default="aplay,stream,gst")
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
    import main_voice_robot as m           # the robot's own helpers and route detection
    tmp = tempfile.mkdtemp(prefix="playerbench_")
    wav = os.path.join(tmp, "burst.wav")
    make_burst(wav, a.burst_s)
    results = []
    for which in [p.strip() for p in a.players.split(",") if p.strip()]:
        print(f"-- {which} ...", flush=True)
        r = bench(m, which, wav, a.sentences, a.burst_s, a.repeats)
        results.append(r)
        print("   " + (r.get("error") or
              f"open {r['open_ms']} ms, wall {r['wall_s']} s vs ideal {r['ideal_s']} s, "
              f"{r['per_boundary_ms']} ms per boundary"))
        time.sleep(1.0)
    if a.json:
        json.dump({"results": results, "route": os.environ.get("CJ_SENTENCE_PLAYER", "stream")},
                  open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
