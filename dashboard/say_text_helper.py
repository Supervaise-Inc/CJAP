"""Synthesize text in the CJ voice (app's tts-1/echo pipeline) to a wav.

Usage: .../app/.venv/bin/python say_text_helper.py "text" /path/out.wav
Run by the dashboard's /api/say-text endpoint; needs internet.
"""
import os
import subprocess
import sys
import tempfile

APP = os.path.expanduser("~/Supervaise-Reachy-Mini-Project-main/app")
sys.path.insert(0, APP)
for line in open(os.path.join(APP, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Optional 3rd arg: an ElevenLabs voice id to synthesize WITH, instead of the
# default cloned voice — used by the Guest voice test box (2026-09-12), which
# speaks in ELEVEN_HOST_VOICE_ID so you can hear the Host without a duet.
text, out = sys.argv[1], sys.argv[2]
_voice_override = sys.argv[3] if len(sys.argv) > 3 else ""
if _voice_override:
    os.environ["ELEVEN_VOICE_ID"] = _voice_override   # voice/config reads this at import
    # A voice id is an ElevenLabs address and the Guest/Host voice exists ONLY
    # there — the Fish account holds one model, "CJAP". Falling through to Fish
    # here would answer a Host voice test in PANGANIBAN's voice, i.e. the wrong
    # person, which is worse than a plain failure. Pin the engine (2026-09-16).
    os.environ["CJ_TTS_ORDER"] = "elevenlabs"

import shutil  # noqa: E402

import speech_engines  # noqa: E402
from speech_engines import tts_concatenate_parallel  # noqa: E402
if getattr(speech_engines, "TTS_BACKEND", "openai") == "elevenlabs":
    try:
        kw = {}
        if not _voice_override and speech_engines.pinned_name_in(text):   # name pin is CJAP-only
            kw = {"voice_settings": speech_engines.name_pin_voice_settings(), "seed": speech_engines.name_pin_seed()}
        src, _eng = speech_engines.tts_cloned_wav(text, where="say-text", **kw)
        if src is not None:
            shutil.move(src, out)
            try:   # alignment sidecar rides along (deleted with the wav)
                shutil.move(src + ".align.json", out + ".align.json")
            except OSError:
                pass
            if _eng != "elevenlabs":
                print(f"[say-text] spoken by the {_eng} clone")
            sys.exit(0)
        print("[say-text] no clone could speak — openai fallback "
              "(CJ_ALLOW_VOICE_SUBSTITUTION is on)")
    except speech_engines.VoiceUnavailable as e:
        # This is the box an operator uses to TEST a voice, so a silent swap is
        # worse here than anywhere: it would sound like the voice is fine.
        print(f"[say-text] NOT spoken — {e}. No clone of Panganiban's voice is "
              "available and no other voice may stand in. Top up the voice service, "
              "or set CJ_ALLOW_VOICE_SUBSTITUTION=1 to override.")
        sys.exit(3)
    except Exception as e:
        print(f"[say-text] unexpected synth failure ({type(e).__name__}) — openai fallback")
mp3 = tts_concatenate_parallel(text)
with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
    f.write(mp3)
    p = f.name
try:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "quiet", "-i", p, out], check=True)
finally:
    os.unlink(p)
