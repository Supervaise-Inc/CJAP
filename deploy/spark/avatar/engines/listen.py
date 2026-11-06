"""The listen track for AVTR-1: the robot's microphone, shared with CJAP.

The Spark's ~/.asoundrc (deploy/spark/home/.asoundrc) exposes the Reachy Lite's
XVF3800 beam as a dsnoop (ipc_key 4242), so a second reader can record at the
same time as CJAP's voice app. This runs `arecord` on it (16 kHz mono S16) in a
thread and keeps the last second in a ring; read(n) hands out the oldest n
samples (zeros if there are fewer). If the device can't be opened, the face
simply listens to silence (it still idles); the error goes to the log once and
it retries every 10 s.

The container needs /dev/snd, the audio group, the host's IPC namespace (the
dsnoop's shared memory) and ~/.asoundrc (docker-compose.yml sets all four).

Settings: AVATAR_LISTEN_PCM (plug:reachymini_audio_src_left; empty = off),
AVATAR_LISTEN_GAIN (1.0).
"""
from __future__ import annotations

import os
import subprocess
import threading
import time

import numpy as np

SR16 = 16000
KEEP = SR16                        # at most 1 s buffered: the face reacts to now, not to backlog


class MicTap:
    def __init__(self, pcm: str, gain: float = 1.0):
        self.pcm, self.gain = pcm, gain
        self._buf = np.zeros(0, np.float32)
        self._lock = threading.Lock()
        self.error = None
        threading.Thread(target=self._run, daemon=True, name="mic-tap").start()

    @classmethod
    def from_env(cls):
        pcm = os.environ.get("AVATAR_LISTEN_PCM", "plug:reachymini_audio_src_left").strip()
        if not pcm:
            return None
        return cls(pcm, float(os.environ.get("AVATAR_LISTEN_GAIN", "1.0")))

    def _run(self):
        cmd = ["arecord", "-q", "-D", self.pcm, "-f", "S16_LE", "-r", str(SR16), "-c", "1",
               "-t", "raw", "--buffer-time=100000"]
        while True:
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                while True:
                    raw = p.stdout.read(640)              # 20 ms
                    if not raw:
                        break
                    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
                    x = np.clip(x * self.gain, -1.0, 1.0)
                    with self._lock:
                        self._buf = np.concatenate([self._buf, x])[-KEEP:]
                err = (p.stderr.read() or b"").decode(errors="replace").strip()
                p.wait()
                msg = f"arecord -D {self.pcm} ended (rc {p.returncode}): {err[:160]}"
            except Exception as e:                        # arecord missing, ...
                msg = f"mic tap failed: {type(e).__name__}: {e}"
            if msg != self.error:
                print(f"[cjap-avatar] listen: {msg}; listening to silence, retry in 10 s", flush=True)
                self.error = msg
            with self._lock:
                self._buf = np.zeros(0, np.float32)
            time.sleep(10)

    def read(self, n: int) -> np.ndarray:
        with self._lock:
            got, self._buf = self._buf[:n], self._buf[n:]
        if got.size < n:
            got = np.concatenate([np.zeros(n - got.size, np.float32), got])
        return got
