"""Talking-head engines for cjap-avatar. Each produces 25 fps RGB frames, each frame
paired with its own 40 ms (960-sample, 24 kHz) slice of the clip audio.

    avtr1    AVTR-1 (avaturn-live/avtr-1), live, from one photo, listens too  — primary
    wav2lip  Wav2Lip 256 over a base video (research-only weights)           — fallback
    still    the portrait, audio passed through, no lip motion               — plumbing test

Frames are RGB24 (HxWx3) unless the engine sets pixfmt = "i420" (AVTR-1).
"""


def load_engine(name: str):
    name = (name or "avtr1").strip().lower()
    if name == "avtr1":
        from .avtr1 import Avtr1Engine
        return Avtr1Engine()
    if name == "wav2lip":
        from .wav2lip import Wav2LipEngine
        return Wav2LipEngine()
    if name == "still":
        from .still import StillEngine
        return StillEngine()
    raise ValueError(f"unknown AVATAR_ENGINE {name!r} (avtr1 | wav2lip | still)")
