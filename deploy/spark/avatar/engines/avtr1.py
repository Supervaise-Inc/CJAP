"""Primary: AVTR-1 (avaturn-live/avtr-1 @ eb1e5a8), live, from one photo.

How it is driven (from the repo's Pipeline.process_chunk and scripts/generate_offline.py):
  * Two endless 16 kHz mono streams. "speech": the clip audio when there is
    some, silence otherwise. "listen": the robot's microphone while the face is
    silent (MicTap), silence while it speaks or when no microphone is set.
    AVTR-1 makes talking motion from the first and active listening / idle
    motion from the second; with both silent the head idles and blinks.
  * Each call takes a 6480-sample window ((5 + 5) x 640 + 80) and returns the 5
    frames (200 ms) of the window's first 3200 samples; the window then moves
    3200 samples, so frames need 200 ms of audio after them (Ditto needed ~0.9 s).
    480 zero samples go in front of the stream once: the 80-sample shift, plus
    400 (25 ms) that cover the 24 -> 16 kHz resampler's output buffering, so a
    block can usually be rendered as soon as the next one is fed. The cost: the
    lips trail the voice by 30 ms, below what people notice (~45 ms).
  * A ledger pairs each rendered frame with the 24 kHz slice it was made from
    (None for silence) and whether it starts a clip, so lips and voice leave
    together and agent.speak_started goes out with the clip's first frame.
  * Frames come out as I420 (YUV 4:2:0) at AVATAR_W x AVATAR_H; LiveKit takes
    them as they are (pixfmt "i420").
  * Interrupt: the frames already rendered and the block in flight keep their
    motion but lose their audio, so the voice stops at once and the mouth
    settles within ~0.4 s.

Settings: AVTR1_LOCAL_STORAGE (/models/avtr1: weights + engines, see the runbook),
AVATAR_PHOTO (/avatar/portrait.png, AVATAR_W x AVATAR_H, from prepare_photo.py),
AVATAR_W / AVATAR_H (1280 / 720), AVATAR_BG (plain_white: one of AVTR-1's
backgrounds, or a .png path), AVATAR_AVTR1_STEPS (5 ODE steps; fewer is faster),
AVATAR_CFG_SELF / AVATAR_CFG_OTHER (2.0 / 2.0: how strongly speech / listening
drive the motion), and the microphone (engines/listen.py).
"""
from __future__ import annotations

import collections
import os
import threading
import time

import numpy as np

from .base import SPF, Engine, env_path

WIN16, HOP16, SHIFT16 = 6480, 3200, 80     # window, hop, the 80-sample shift
LEAD16 = 400                                # 25 ms head start for the resampler (see above)
BLOCK = 5                                   # frames per AVTR-1 chunk (200 ms)
QUIET_AFTER_SPEECH_S = 1.5                  # mic ignored this long after the face spoke


class _Chunk:                               # stand-in for avtr1_renderer.Chunk in tests
    def __init__(self, audio_speech, audio_listen):
        self.audio_speech, self.audio_listen = audio_speech, audio_listen


def _no_grad():
    try:
        import torch
        return torch.inference_mode()
    except ImportError:
        import contextlib
        return contextlib.nullcontext()


class Avtr1Engine(Engine):
    name = "avtr1"
    pixfmt = "i420"

    def __init__(self, pipeline=None, avatar=None, options=None, listen=None):
        """pipeline/avatar/options/listen are injected by tests; normally built here."""
        super().__init__()
        import soxr
        self.width = int(env_path("AVATAR_W", "1280"))
        self.height = int(env_path("AVATAR_H", "720"))
        if pipeline is None:
            pipeline, avatar, options = self._load()
        if listen is None:
            from .listen import MicTap
            listen = MicTap.from_env()
        self._pipe, self._avatar, self._opts, self._mic = pipeline, avatar, options, listen
        try:
            from avtr1_renderer import Chunk
        except ImportError:                    # tests, with a stub pipeline
            Chunk = _Chunk
        self._Chunk = Chunk
        self._rs = soxr.ResampleStream(24000, 16000, 1, dtype="float32")
        self._speech16 = np.zeros(SHIFT16 + LEAD16, np.float32)
        self._listen16 = np.zeros(SHIFT16 + LEAD16, np.float32)
        self._state = None
        self._pending = collections.deque()   # (pcm24 | None, first) per fed, unrendered frame
        self._ready = collections.deque()     # (i420 frame, pcm24 | None, first)
        self._lock = threading.Lock()
        self._quiet_until = 0.0
        self._icount = 0                      # interrupts so far
        self.chunk_ms = collections.deque(maxlen=500)
        self._silence24 = np.zeros(SPF, np.float32)

    def _load(self):
        import tensorrt  # noqa: F401  pip's libnvinfer first, so the GridSample3D plugin binds to it
        from avtr1_renderer import Pipeline, RenderOptions
        photo = env_path("AVATAR_PHOTO", "/avatar/portrait.png")
        if not photo.lower().endswith(".png") or not os.path.isfile(photo):
            raise FileNotFoundError(f"AVATAR_PHOTO must be an existing .png: {photo}")
        bg = env_path("AVATAR_BG", "plain_white")
        if bg.lower().endswith(".png"):
            backgrounds, bg_id = {"custom": bg}, "custom"
        else:
            backgrounds, bg_id = None, bg
        avatar_id = os.path.splitext(os.path.basename(photo))[0]
        pipe, registry = Pipeline.from_artifacts(
            avatar_ids=[avatar_id], portraits_dir=os.path.dirname(photo),
            background_paths=backgrounds, out_size=(self.height, self.width))
        mg = pipe._motion_generator
        assert (mg.chunk_size, mg.future_size, mg.frame_len, mg.audio_shift) == (BLOCK, 5, 640, 80), \
            "AVTR-1's chunk layout changed; update engines/avtr1.py"
        # the time grid has n points, so n - 1 decode passes: 2 is the least that works
        mg.n_ode_steps = max(2, int(env_path("AVATAR_AVTR1_STEPS", str(mg.n_ode_steps))))
        opts = RenderOptions(pixel_format="yuv_i420", bg_id=bg_id, stream_frames=False,
                             cfg_self_audio=float(env_path("AVATAR_CFG_SELF", "2.0")),
                             cfg_other_audio=float(env_path("AVATAR_CFG_OTHER", "2.0")))
        return pipe, registry[avatar_id], opts

    # -- one 200 ms step ---------------------------------------------------------
    def _feed_block(self):
        icount = self._icount
        block, entries = [], []
        for _ in range(BLOCK):
            pcm, first = self.audio.take(SPF)
            if pcm is None:
                block.append(self._silence24)
                entries.append((None, False))
            else:
                block.append(pcm.astype(np.float32) / 32768.0)
                entries.append((pcm, first))
        now = time.monotonic()
        speaking = any(p is not None for p, _ in entries)
        if speaking:
            self._quiet_until = now + QUIET_AFTER_SPEECH_S
        with self._lock:
            if icount != self._icount:                # interrupted while we took it: mute it
                entries = [(None, False)] * len(entries)
                block = [self._silence24] * len(block)
                speaking = False
            self._pending.extend(entries)
        x16 = np.asarray(self._rs.resample_chunk(np.concatenate(block)), np.float32)
        n = len(x16)
        l16 = self._mic.read(n) if self._mic is not None else None
        if l16 is None or speaking or now < self._quiet_until:   # no mic, or the face (just) spoke:
            l16 = np.zeros(n, np.float32)            # don't listen to our own voice
        self._speech16 = np.concatenate([self._speech16, x16])
        self._listen16 = np.concatenate([self._listen16, l16])

    def _render(self):
        while len(self._speech16) >= WIN16 and len(self._listen16) >= WIN16:
            chunk = self._Chunk(audio_speech=np.ascontiguousarray(self._speech16[:WIN16]),
                                audio_listen=np.ascontiguousarray(self._listen16[:WIN16]))
            t0 = time.perf_counter()
            with _no_grad():
                self._state, frames = self._pipe.process_chunk(self._avatar, chunk, self._state,
                                                               self._opts)
                frames = list(frames)
            self.chunk_ms.append((time.perf_counter() - t0) * 1000.0)
            self._speech16 = self._speech16[HOP16:]
            self._listen16 = self._listen16[HOP16:]
            with self._lock:
                for f in frames:
                    pcm, first = self._pending.popleft() if self._pending else (None, False)
                    self._ready.append((f.data, pcm, first))

    # -- page events ---------------------------------------------------------------
    def interrupt(self):
        super().interrupt()                                   # drop unfed clip audio
        with self._lock:                                      # mute what is fed or rendered
            self._icount += 1
            self._pending = collections.deque((None, False) for _ in self._pending)
            self._ready = collections.deque((d, None, False) for d, _, _ in self._ready)

    def healthy(self) -> bool:
        return True

    # -- frames ----------------------------------------------------------------------
    def next_frame(self):
        while True:
            with self._lock:
                if self._ready:
                    item = self._ready.popleft()
                    break
            self._feed_block()
            self._render()
        self._tick_fps()
        return item
