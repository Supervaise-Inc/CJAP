"""Fallback: Wav2Lip 256 (from LiveTalking) over a prepared base video.

LICENCE: Wav2Lip is research/non-commercial only (Rudrabha/Wav2Lip, trained on
LRS2), and LiveTalking's wav2lip256.pth ships with no licence. Use this engine
for internal tests only, never for a public or paid exhibit.

The base video (5-10 s of the face, mouth closed, slight motion, 25 fps) is
prepared once by prepare_wav2lip.py into AVATAR_W2L_DIR:
    full/00000000.png ...   the frames
    face/00000000.png ...   256x256 face crops
    coords.json             [[y1, y2, x1, x2], ...]
It plays ping-pong (forward, then backward), so it needs no seamless loop.

Per frame: 200 ms of mel window starting at the frame's own time (16 kHz audio,
80 mels, hop 200), so the engine renders ~225 ms ahead of what it returns.
"""
from __future__ import annotations

import collections
import json
import os
import sys

import numpy as np

from .base import SPF, Engine, env_path

W2L_CODE = env_path("AVATAR_W2L_CODE", "/opt/livetalking")   # LiveTalking checkout
SR16, HOP, WIN, CTX = 16000, 200, 16, 3200                    # 3200 = 200 ms of context
SPF16 = SR16 // 25                                            # 640


def _mirror(n, i):
    t, r = divmod(i, n)
    return r if t % 2 == 0 else n - r - 1


class Wav2LipEngine(Engine):
    name = "wav2lip"

    def __init__(self):
        super().__init__()
        import cv2
        import torch
        from scipy.signal import resample_poly
        # LiveTalking's avatars/wav2lip/{audio.py, hparams.py, models/}: imported as a
        # package first; if its package __init__ pulls in the rest of LiveTalking,
        # fall back to importing the two modules from their folder.
        sys.path.insert(0, W2L_CODE)
        try:
            from avatars.wav2lip import audio as w2l_audio
            from avatars.wav2lip.models import Wav2Lip
        except Exception:
            sys.path.insert(0, os.path.join(W2L_CODE, "avatars", "wav2lip"))
            import audio as w2l_audio
            from models import Wav2Lip
        self.cv2, self.torch, self.resample = cv2, torch, resample_poly
        self.mel = w2l_audio.melspectrogram
        ckpt = env_path("AVATAR_W2L_CKPT", "/models/wav2lip/wav2lip256.pth")
        sd = torch.load(ckpt, map_location="cpu", weights_only=False)
        sd = sd.get("state_dict", sd)
        m = Wav2Lip()
        m.load_state_dict({k.replace("module.", ""): v for k, v in sd.items()})
        self.m = m.cuda().eval().half()
        d = env_path("AVATAR_W2L_DIR", "/avatar/wav2lip")
        self.coords = json.load(open(os.path.join(d, "coords.json")))
        names = sorted(os.listdir(os.path.join(d, "full")))
        self.full = [cv2.imread(os.path.join(d, "full", n)) for n in names]
        self.face = [cv2.imread(os.path.join(d, "face", n)) for n in names]
        self.N = len(self.full)
        self.height, self.width = self.full[0].shape[:2]
        self.B = int(os.environ.get("AVATAR_W2L_BATCH", "4"))
        self.vidx = 0
        self._idle_next = 0.0
        self._ready = collections.deque()
        self._pcm16 = np.zeros(CTX, np.float32)        # running 16 kHz copy of the clip audio
        self._pending = collections.deque()            # (pcm24 slice, first) awaiting a frame
        with torch.inference_mode():                   # warm-up
            self.m(torch.zeros(1, 1, 80, 16).cuda().half(), torch.zeros(1, 6, 256, 256).cuda().half())

    def interrupt(self):
        super().interrupt()
        self._ready.clear()
        self._pending.clear()
        self._pcm16 = np.zeros(CTX, np.float32)

    def _idle(self):
        import time
        now = time.monotonic()
        if self._idle_next > now:                       # idle frames at 25 fps
            time.sleep(self._idle_next - now)
        self._idle_next = max(now, self._idle_next) + 0.04
        i = _mirror(self.N, self.vidx)
        self.vidx += 1
        return self.cv2.cvtColor(self.full[i], self.cv2.COLOR_BGR2RGB)

    def _render(self):
        """Pull audio slices, render a small batch of speaking frames."""
        while len(self._pending) < self.B:
            pcm, first = self.audio.take(SPF)
            if pcm is None:
                break
            x16 = self.resample(pcm.astype(np.float32) / 32768.0, 2, 3).astype(np.float32)
            self._pcm16 = np.concatenate([self._pcm16, x16])
            self._pending.append((pcm, first))
        if not self._pending:
            return
        # lookahead: pad with what follows (or silence at a clip end)
        fut = self.audio.peek_future(int(SPF * 6))
        fut16 = self.resample(fut.astype(np.float32) / 32768.0, 2, 3).astype(np.float32) if fut.size else np.zeros(0, np.float32)
        tail = np.concatenate([fut16, np.zeros(WIN * HOP + CTX, np.float32)])
        pcm16 = np.concatenate([self._pcm16, tail])
        b = len(self._pending)
        start = len(self._pcm16) - b * SPF16
        mels, idx = [], []
        for j in range(b):
            p = start + j * SPF16
            seg = pcm16[max(0, p - CTX):p + WIN * HOP + CTX]
            mel = self.mel(seg)
            mels.append(mel[:, CTX // HOP:CTX // HOP + WIN])
            idx.append(_mirror(self.N, self.vidx + j))
        f = np.stack([self.face[i] for i in idx])
        mk = f.copy()
        mk[:, 128:] = 0
        t = self.torch
        img = t.from_numpy(np.concatenate([mk, f], 3).transpose(0, 3, 1, 2) / 255.0).cuda().half()
        mel = t.from_numpy(np.stack(mels)[:, None].astype(np.float32)).cuda().half()
        with t.inference_mode():
            pred = (self.m(mel, img).float().clamp(0, 1) * 255).byte().permute(0, 2, 3, 1).cpu().numpy()
        for j, i in enumerate(idx):
            y1, y2, x1, x2 = self.coords[i]
            fr = self.full[i].copy()
            fr[y1:y2, x1:x2] = self.cv2.resize(pred[j], (x2 - x1, y2 - y1))
            pcm, first = self._pending.popleft()
            self._ready.append((self.cv2.cvtColor(fr, self.cv2.COLOR_BGR2RGB), pcm, first))
        self.vidx += b
        keep = CTX + WIN * HOP                          # trim the 16 kHz history
        if len(self._pcm16) > keep * 4:
            self._pcm16 = self._pcm16[-keep * 2:]

    def next_frame(self):
        if not self._ready:
            self._render()
        self._tick_fps()
        if self._ready:
            return self._ready.popleft()
        return self._idle(), None, False
