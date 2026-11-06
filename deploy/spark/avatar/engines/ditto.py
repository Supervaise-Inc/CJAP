"""Primary: Ditto (antgroup/ditto-talkinghead @ c3e47ee), live, from one photo.

How it is driven (from the repo's stream_pipeline_online.StreamSDK):
  * One endless 16 kHz audio stream per process: the clip audio when there is
    some, silence otherwise. Silence gives a calm idle head; blinks come from
    Ditto's own eye template (every ~60-100 frames), not from the audio.
  * Audio goes in as 6480-sample windows every 3200 samples (200 ms = 5 frames,
    chunksize (3, 5, 2)); video frame k matches stream frame k (40 ms), after a
    1920-sample left pad. Frames come out of Ditto's writer stage as HxWx3 RGB
    at the source photo's size (the 512 render is pasted back on the photo).
  * Ditto needs ~0.88 s of audio beyond a frame before it emits it
    (overlap_v2=70), so the feeder keeps AHEAD frames (default 28 = 1.12 s) in
    flight. A sentence therefore starts on screen ~1.1-1.3 s after its audio
    arrives; the page measures this (agent.speak_started) and CJAP waits for it.
  * A ledger holds, for every frame fed, its 24 kHz audio slice (or None for
    silence) and whether it starts a clip; next_frame() pairs each frame Ditto
    emits with the next ledger entry, so lips and voice leave together.
  * Interrupt: frames already in Ditto's pipeline can't be recalled. The audio of
    every fed-but-unplayed frame is muted at once and the feeder switches to
    silence, so the voice stops immediately and the mouth settles within ~1 s.

Settings: AVATAR_DITTO_CODE (/opt/ditto), AVATAR_DITTO_DATA (/models/ditto/ditto_trt_spark),
AVATAR_DITTO_CFG (/models/ditto/ditto_cfg/v0.4_hubert_cfg_trt_online.pkl),
AVATAR_PHOTO (/avatar/portrait.jpg, square, prepared by prepare_photo.py),
AVATAR_DITTO_STEPS (10), AVATAR_DITTO_OVERLAP (70), AVATAR_DITTO_AHEAD (28).
"""
from __future__ import annotations

import collections
import ctypes
import os
import queue
import sys
import threading
import time

import numpy as np

from .base import SPF, Engine, env_path

WIN16, HOP16, PAD16 = 6480, 3200, 1920
CHUNKSIZE = (3, 5, 2)


class DittoEngine(Engine):
    name = "ditto"

    def __init__(self):
        super().__init__()
        import cv2
        import soxr
        code = env_path("AVATAR_DITTO_CODE", "/opt/ditto")
        data = env_path("AVATAR_DITTO_DATA", "/models/ditto/ditto_trt_spark")
        cfg = env_path("AVATAR_DITTO_CFG", "/models/ditto/ditto_cfg/v0.4_hubert_cfg_trt_online.pkl")
        photo = env_path("AVATAR_PHOTO", "/avatar/portrait.jpg")
        plugin = env_path("AVATAR_DITTO_PLUGIN", "/models/ditto/ditto_onnx/libgrid_sample_3d_plugin.so")
        import tensorrt  # noqa: F401  load pip's libnvinfer first, so the plugin binds to it
        if os.path.exists(plugin):          # the warp engine needs GridSample3D registered
            ctypes.CDLL(plugin, mode=ctypes.RTLD_GLOBAL)
        img = cv2.imread(photo)
        if img is None:
            raise FileNotFoundError(photo)
        self.height, self.width = img.shape[:2]
        sys.path.insert(0, code)
        import stream_pipeline_online as spo

        self._out: "queue.Queue" = queue.Queue(maxsize=64)
        out = self._out

        class _Sink:                         # replaces Ditto's mp4 writer
            def __init__(self, *a, **k):
                pass

            def __call__(self, frame, fmt="rgb"):
                out.put(frame)

            def close(self):
                pass

        spo.VideoWriterByImageIO = _Sink
        self.sdk = spo.StreamSDK(cfg, data)
        self.sdk.setup(photo, "/tmp/ditto_unused.mp4", online_mode=True,
                       sampling_timesteps=int(os.environ.get("AVATAR_DITTO_STEPS", "10")),
                       overlap_v2=int(os.environ.get("AVATAR_DITTO_OVERLAP", "70")),
                       emo=4, max_size=max(self.width, self.height))
        self._rs = soxr.ResampleStream(24000, 16000, 1, dtype="float32")
        self._buf16 = np.zeros(PAD16, np.float32)
        self._ledger = collections.deque()          # (pcm24 | None, first) per fed frame
        self._llock = threading.Lock()
        self._fed = 0
        self._emitted = 0
        self._ahead = int(os.environ.get("AVATAR_DITTO_AHEAD", "28"))
        self._silence24 = np.zeros(SPF, np.float32)
        self._icount = 0                            # interrupts so far
        threading.Thread(target=self._feeder, daemon=True, name="ditto-feed").start()

    # -- feeding -------------------------------------------------------------
    def _push16(self, x16: np.ndarray):
        self._buf16 = np.concatenate([self._buf16, x16])
        while len(self._buf16) >= WIN16:
            self.sdk.run_chunk(np.ascontiguousarray(self._buf16[:WIN16], np.float32), CHUNKSIZE)
            self._buf16 = self._buf16[HOP16:]

    def _feeder(self):
        while True:
            if self.sdk.worker_exception is not None:
                time.sleep(0.5)
                continue
            with self._llock:
                ahead = self._fed - self._emitted
            if ahead >= self._ahead:
                time.sleep(0.005)
                continue
            icount = self._icount
            block, entries = [], []
            for _ in range(5):                       # one 200 ms Ditto hop
                pcm, first = self.audio.take(SPF)
                if pcm is None:
                    block.append(self._silence24)
                    entries.append((None, False))
                else:
                    block.append(pcm.astype(np.float32) / 32768.0)
                    entries.append((pcm, first))
            with self._llock:
                if icount != self._icount:          # interrupted while we took it
                    entries = [(None, False)] * len(entries)
                    block = [self._silence24] * len(block)
                self._ledger.extend(entries)
                self._fed += len(entries)
            x16 = self._rs.resample_chunk(np.concatenate(block))
            self._push16(np.asarray(x16, np.float32))

    # -- page events ---------------------------------------------------------
    def interrupt(self):
        super().interrupt()                          # drop unfed clip audio
        with self._llock:                            # mute what is already fed
            self._icount += 1
            self._ledger = collections.deque((None, False) for _ in self._ledger)

    def healthy(self) -> bool:
        return self.sdk.worker_exception is None

    def shutdown(self):
        self.sdk.stop_event.set()

    # -- frames --------------------------------------------------------------
    def next_frame(self):
        try:
            frame = self._out.get(timeout=5.0)
        except queue.Empty:
            raise RuntimeError(f"Ditto produced no frame for 5 s "
                               f"(worker_exception={self.sdk.worker_exception!r})")
        with self._llock:
            pcm, first = self._ledger.popleft() if self._ledger else (None, False)
            self._emitted += 1
        self._tick_fps()
        return frame, pcm, first
