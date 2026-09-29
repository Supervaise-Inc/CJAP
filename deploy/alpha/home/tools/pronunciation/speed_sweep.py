"""Speed sweep A/B: same sentence rendered at several ElevenLabs speeds,
played back-to-back on the robot speaker. Usage:
  python3 speed_sweep.py [outdir] [speed ...]
Defaults: outdir=/dev/shm/speed_sweep, speeds 0.85 0.92 1.0 1.08 1.15.
Set SWEEP_TEXT to change the sentence. Set SWEEP_NOPLAY=1 to render only."""
import sys, os, time, subprocess
from pathlib import Path
root = Path.home() / "Supervaise-Reachy-Mini-Project-main"
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "app"))
os.chdir(root / "app")
from dotenv import load_dotenv; load_dotenv(root / "app" / ".env")
import numpy as np, soundfile as sf
from voice import audio as v_audio
from voice.speak import synthesize, effective_settings

out = Path(sys.argv[1] if len(sys.argv) > 1 else "/dev/shm/speed_sweep"); out.mkdir(exist_ok=True)
speeds = [float(s) for s in sys.argv[2:]] or [0.85, 0.92, 1.0, 1.08, 1.15]
text = os.environ.get("SWEEP_TEXT") or (
    "The rule of law is not a slogan. It is the daily discipline of judges, "
    "lawyers, and citizens who choose to be bound by it.")
SR = v_audio.SYNTH_SAMPLE_RATE

def beeps(n, sr=SR):
    """n short 880 Hz pips so the listener knows which variant is next."""
    t = np.arange(int(0.08 * sr)) / sr
    pip = (0.25 * np.sin(2 * np.pi * 880 * t) * np.hanning(len(t))).astype(np.float32)
    gap = np.zeros(int(0.10 * sr), np.float32)
    return np.concatenate([np.concatenate([pip, gap]) for _ in range(n)] + [np.zeros(int(0.4 * sr), np.float32)])

paths = []
for i, sp in enumerate(speeds):
    st = effective_settings(sp)
    pcm = v_audio.process(synthesize(text, settings=st), SR)
    clip = np.concatenate([beeps(i + 1), pcm])
    p = out / f"{i+1}_speed{sp:.2f}.wav"
    sf.write(str(p), clip, SR, subtype="PCM_16")
    paths.append(p)
    print(f"{i+1} beep(s) = speed {sp:.2f}  ({len(pcm)/SR:.1f}s)", flush=True)

if os.environ.get("SWEEP_NOPLAY") == "1":
    sys.exit(0)
for p in paths:
    for _ in range(4):
        if subprocess.run(["aplay", "-q", str(p)], stderr=subprocess.DEVNULL).returncode == 0:
            break
        time.sleep(1.5)
    time.sleep(2.0)
print("done")
