"""Talking-head engines for cjap-avatar. Each produces 25 fps RGB frames, each frame
paired with its own 40 ms (960-sample, 24 kHz) slice of the clip audio.

    ditto    Ditto (antgroup/ditto-talkinghead), live, from one photo        — primary
    wav2lip  Wav2Lip 256 over a base video (research-only weights)           — fallback
    still    the portrait, audio passed through, no lip motion               — plumbing test
"""


def load_engine(name: str):
    name = (name or "ditto").strip().lower()
    if name == "ditto":
        from .ditto import DittoEngine
        return DittoEngine()
    if name == "wav2lip":
        from .wav2lip import Wav2LipEngine
        return Wav2LipEngine()
    if name == "still":
        from .still import StillEngine
        return StillEngine()
    raise ValueError(f"unknown AVATAR_ENGINE {name!r} (ditto | wav2lip | still)")
