"""A/B: per-sentence dynamic speed, jumping (A, old) vs slewed (B, new).
Same sentences, same previous_text stitching. 1 beep = A, 2 beeps = B."""
import sys, os, time, subprocess
from pathlib import Path
root = Path.home() / "Supervaise-Reachy-Mini-Project-main"
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "app"))
os.chdir(root / "app")
from dotenv import load_dotenv; load_dotenv(root / "app" / ".env")
import numpy as np, soundfile as sf
import speech_engines
from speech_streaming import classify_emotion
SR = 24000
sents = ["We mourn the passing of a great jurist, a friend of forty years.",
         "But let me be clear: the Constitution does not bend to grief!",
         "Ha, my grandchildren tease me that I still read decisions at breakfast.",
         "Is that not what a judge owes the people?",
         "In the end, the law is a solemn covenant, kept quietly, every single day."]
def beeps(n):
    t = np.arange(int(0.08*SR))/SR
    pip = (0.25*np.sin(2*np.pi*880*t)*np.hanning(len(t))).astype(np.float32)
    return np.concatenate([np.concatenate([pip, np.zeros(int(0.1*SR), np.float32)]) for _ in range(n)]+[np.zeros(int(0.4*SR), np.float32)])
out = Path("/dev/shm/slew_ab"); out.mkdir(exist_ok=True)
paths = []
for label, slew in (("A_jump", False), ("B_slew", True)):
    parts, prev_text, cur = [beeps(1 if not slew else 2)], None, None
    plan = []
    for s in sents:
        tgt = speech_engines.emotion_speed(classify_emotion(s))
        spd = speech_engines.smooth_speed(tgt, cur) if slew else tgt
        cur = spd
        plan.append(spd)
        wav = speech_engines.tts_elevenlabs_wav(s, speed=spd, previous_text=prev_text)
        pcm, sr = sf.read(wav, dtype="float32")
        parts.append(pcm); parts.append(np.zeros(int(0.25*SR), np.float32))
        prev_text = s
    clip = np.concatenate(parts)
    p = out / f"{label}.wav"; sf.write(str(p), clip, SR, subtype="PCM_16"); paths.append(p)
    print(label, "speeds:", plan, f"{len(clip)/SR:.1f}s", flush=True)
if os.environ.get("SWEEP_NOPLAY") != "1":
    for p in paths:
        subprocess.run(["aplay", "-q", str(p)], stderr=subprocess.DEVNULL); time.sleep(2.0)
print("done")
