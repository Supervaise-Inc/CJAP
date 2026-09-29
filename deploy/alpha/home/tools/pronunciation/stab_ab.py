"""Stability A/B: one neutral passage rendered at several ElevenLabs
stability / similarity settings at the live CJ_SPEED_BASE pace, played
back-to-back with N pips before variant N. Usage:
  python3 stab_ab.py [outdir] [stab[:style[:sim]] ...]
Defaults: outdir=~/stab_ab, variants 0.50 0.65 0.80:0:0.85, speed from
CJ_SPEED_BASE in the live drop-in (fallback 0.91). STAB_TEXT overrides the
passage; STAB_NOPLAY=1 renders only. Apply a pick with
CJ_VOICE_NEUTRAL="stab:style" in wakeword.conf (2026-08-31)."""
import sys, os, re, time, subprocess
from pathlib import Path
root = Path.home() / "Supervaise-Reachy-Mini-Project-main"
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "app"))
os.chdir(root / "app")
from dotenv import load_dotenv; load_dotenv(root / "app" / ".env")
import numpy as np, soundfile as sf
from voice import audio as v_audio
from voice.speak import synthesize, effective_settings

CONF = "/etc/systemd/system/supervaise.service.d/wakeword.conf"
def live_speed():
    try:
        m = re.search(r"^Environment=CJ_SPEED_BASE=([0-9.]+)", open(CONF).read(), re.M)
        return float(m.group(1)) if m else 0.91
    except OSError:
        return 0.91

out = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "stab_ab"); out.mkdir(exist_ok=True)
specs = sys.argv[2:] or ["0.50", "0.65", "0.80:0:0.85"]
speed = float(os.environ.get("STAB_SPEED") or live_speed())
text = os.environ.get("STAB_TEXT") or (
    "You ask about my favorite book. I have always returned to the ones that "
    "taught me how to think, not what to think. A good book, like a good "
    "judgment, should leave the reader wiser and a little more humble.")
SR = v_audio.SYNTH_SAMPLE_RATE

def beeps(n, sr=SR):
    t = np.arange(int(0.08 * sr)) / sr
    pip = (0.25 * np.sin(2 * np.pi * 880 * t) * np.hanning(len(t))).astype(np.float32)
    gap = np.zeros(int(0.10 * sr), np.float32)
    return np.concatenate([np.concatenate([pip, gap]) for _ in range(n)] + [np.zeros(int(0.4 * sr), np.float32)])

paths = []
for i, spec in enumerate(specs):
    parts = spec.split(":")
    stab = float(parts[0]); style = float(parts[1]) if len(parts) > 1 else 0.0
    sim = float(parts[2]) if len(parts) > 2 else None
    st = effective_settings(speed); st["stability"] = stab; st["style"] = style
    if sim is not None:
        st["similarity_boost"] = sim
    pcm = v_audio.process(synthesize(text, settings=st), SR)
    clip = np.concatenate([beeps(i + 1), pcm])
    p = out / f"{i+1}_stab{stab:.2f}_style{style:.2f}_sim{st['similarity_boost']:.2f}_sp{speed:.2f}.wav"
    sf.write(str(p), clip, SR, subtype="PCM_16")
    paths.append(p)
    print(f"{i+1} pip(s) = stability {stab:.2f} style {style:.2f} sim {st['similarity_boost']:.2f} speed {speed:.2f} ({len(pcm)/SR:.1f}s) -> {p.name}", flush=True)

if os.environ.get("STAB_NOPLAY") == "1":
    sys.exit(0)
for p in paths:
    for _ in range(4):
        if subprocess.run(["aplay", "-q", str(p)], stderr=subprocess.DEVNULL).returncode == 0:
            break
        time.sleep(1.5)
    time.sleep(2.0)
print("done")
