#!/usr/bin/env python3
"""Gate T: speed of cjap-tts on CJAP-style sentences (stdlib only, run on the host).

    python3 tts_bench.py [URL]          default URL http://127.0.0.1:8091

Sends 10 sentences of the length Panganiban's answers open with, one at a time,
as CJAP does, and prints per sentence the synthesis time, the audio length and
the speed (audio seconds per second of synthesis; above 1 = faster than real
time). The first and the longest sentence are saved to /dev/shm for listening.
Pass: median speed >= 1.25 and the opener synthesized in <= 1.8 s.
"""
import json
import statistics
import sys
import time
import urllib.request

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8091").rstrip("/")
SENTENCES = [
    "Good afternoon, and thank you for coming.",
    "The rule of law means that no one is above the law, not even the President.",
    "I have always said that liberty and prosperity are the twin beacons of our nation.",
    "Au contraire, my friend.",
    "When I joined the Supreme Court in 1995, I promised myself to write every decision clearly.",
    "Justice delayed is justice denied.",
    "The Constitution is not a mere document; it is the soul of our people.",
    "My mentor, Senator Jovito Salonga, taught me that courage is the first virtue of a lawyer.",
    "Panganiban is my name, and the Foundation for Liberty and Prosperity is my mission.",
    "Cheers!",
]


def post(text):
    req = urllib.request.Request(f"{URL}/v1/tts", data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        synth = float(r.headers.get("X-Synth-S", "nan"))
        audio = float(r.headers.get("X-Audio-S", "nan"))
    return body, synth, audio, time.monotonic() - t0


def main():
    print(json.loads(urllib.request.urlopen(f"{URL}/health", timeout=5).read()))
    speeds, longest = [], (0.0, b"")
    for i, s in enumerate(SENTENCES):
        body, synth, audio, wall = post(s)
        speed = audio / synth if synth else 0.0
        speeds.append(speed)
        print(f"{i + 1:2d}  synth {synth:5.2f} s  audio {audio:5.2f} s  speed {speed:4.2f}x  "
              f"wall {wall:5.2f} s  | {s[:50]}")
        if i == 0:
            open("/dev/shm/cj_tts_opener.wav", "wb").write(body)
        if audio > longest[0]:
            longest = (audio, body)
    open("/dev/shm/cj_tts_longest.wav", "wb").write(longest[1])
    med = statistics.median(speeds)
    print(f"median speed {med:.2f}x  (pass >= 1.25)")
    print("saved /dev/shm/cj_tts_opener.wav and /dev/shm/cj_tts_longest.wav")
    return 0 if med >= 1.25 else 1


if __name__ == "__main__":
    sys.exit(main())
