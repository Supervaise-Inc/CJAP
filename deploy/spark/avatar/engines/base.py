"""What every engine shares: the clip audio buffer and the frame contract.

The page sends each sentence as agent.speak chunks (base64 PCM16, 24 kHz mono)
and closes it with agent.speak_end. ClipAudio keeps them as a FIFO of clips, so
an engine can take exactly one 960-sample slice per video frame and know when a
slice is the FIRST of a clip (that frame triggers agent.speak_started, which the
page uses to measure the face's lag).
"""
from __future__ import annotations

import collections
import os
import threading
import time

import numpy as np

SR = 24000
FPS = 25
SPF = SR // FPS          # 960


class ClipAudio:
    def __init__(self):
        self._lock = threading.Lock()
        self._clips = collections.deque()      # [ [np.int16 buffer, read_pos, ended, started] ]
        self._open = False

    def push(self, pcm16: bytes):
        x = np.frombuffer(pcm16, dtype=np.int16)
        if x.size == 0:
            return
        with self._lock:
            if not self._open:
                self._clips.append([x.copy(), 0, False, False])
                self._open = True
            else:
                c = self._clips[-1]
                c[0] = np.concatenate([c[0], x])

    def end(self):
        with self._lock:
            if self._open and self._clips:
                self._clips[-1][2] = True
            self._open = False

    def clear(self):
        with self._lock:
            self._clips.clear()
            self._open = False

    def available(self) -> int:
        """Samples ready to play in the current clip."""
        with self._lock:
            if not self._clips:
                return 0
            c = self._clips[0]
            return c[0].size - c[1]

    def take(self, n: int = SPF, pad_end: bool = True):
        """(slice int16[n] | None, first: bool). A clip's tail shorter than n is
        padded with zeros once the clip has ended; an open clip waits for more."""
        with self._lock:
            while self._clips:
                buf, pos, ended, started = self._clips[0]
                left = buf.size - pos
                if left >= n or (ended and left > 0):
                    out = buf[pos:pos + n]
                    if out.size < n and pad_end:
                        out = np.concatenate([out, np.zeros(n - out.size, np.int16)])
                    self._clips[0][1] = pos + n
                    self._clips[0][3] = True
                    return out, not started
                if ended:                       # fully consumed
                    self._clips.popleft()
                    continue
                return None, False              # open clip, waiting for more audio
            return None, False

    def peek_future(self, n: int) -> np.ndarray:
        """Up to n samples from the current read position onward (for lookahead)."""
        with self._lock:
            if not self._clips:
                return np.zeros(0, np.int16)
            buf, pos, _, _ = self._clips[0]
            return buf[pos:pos + n].copy()


class Engine:
    """Subclasses set name/width/height (and pixfmt if not RGB24) and implement next_frame()."""
    name = "base"
    pixfmt = "rgb24"          # or "i420": (3H/2, W) uint8, planar YUV 4:2:0
    width = 1280
    height = 720

    def __init__(self):
        self.audio = ClipAudio()
        self.listening = False
        self.fps_measured = 0.0
        self._t_last = None

    # page events
    def push_audio(self, pcm16: bytes):
        self.audio.push(pcm16)

    def end_clip(self):
        self.audio.end()

    def interrupt(self):
        self.audio.clear()

    def set_listening(self, on: bool):
        self.listening = bool(on)

    def healthy(self) -> bool:
        return True

    # frame contract: (frame, pcm int16[960] | None, first_of_clip: bool);
    # frame is RGB uint8 HxWx3, or I420 uint8 (3H/2)xW when pixfmt == "i420"
    def next_frame(self):
        raise NotImplementedError

    def _tick_fps(self):
        now = time.monotonic()
        if self._t_last is not None:
            dt = max(1e-4, now - self._t_last)
            self.fps_measured = 0.9 * self.fps_measured + 0.1 * (1.0 / dt) if self.fps_measured else 1.0 / dt
        self._t_last = now


def frame_size() -> tuple[int, int]:
    """(width, height) of the stream: AVATAR_W x AVATAR_H, default 1280 x 720."""
    return int(os.environ.get("AVATAR_W", "1280")), int(os.environ.get("AVATAR_H", "720"))


def load_rgb(path: str, width: int, height: int) -> np.ndarray:
    """An RGB image at width x height (centre crop to that aspect, then resize)."""
    import cv2
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    h, w = img.shape[:2]
    if w * height > h * width:                 # too wide: crop the sides
        cw, ch = h * width // height, h
    else:                                      # too tall: crop top and bottom
        cw, ch = w, w * height // width
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    img = cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (width, height), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def frame_to_bgr(engine, frame) -> np.ndarray:
    """An engine frame as BGR HxWx3 (for cv2 writers), whatever the engine's pixfmt."""
    import cv2
    if getattr(engine, "pixfmt", "rgb24") == "i420":
        yuv = np.asarray(frame, np.uint8).reshape(engine.height * 3 // 2, engine.width)
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
    return cv2.cvtColor(np.asarray(frame, np.uint8), cv2.COLOR_RGB2BGR)


def env_path(name: str, default: str) -> str:
    return os.environ.get(name, default)
