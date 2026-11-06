"""Plumbing test: the portrait, with the clip audio passed through at 25 fps.

No model, no GPU. Proves LiveKit, the page, agent.speak_started and the voice
modes before a talking-head model is involved (runbook Gate X1)."""
import time

from .base import SPF, Engine, env_path, load_rgb


class StillEngine(Engine):
    name = "still"

    def __init__(self):
        super().__init__()
        self.width = self.height = int(env_path("AVATAR_SIZE", "512"))
        self.img = load_rgb(env_path("AVATAR_PHOTO", "/avatar/portrait.jpg"), self.width)
        self._next = time.monotonic()

    def next_frame(self):
        self._next += 0.04                       # 25 fps on its own clock
        delay = self._next - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            self._next = time.monotonic()
        pcm, first = self.audio.take(SPF)
        self._tick_fps()
        return self.img, pcm, first
