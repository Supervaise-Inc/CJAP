import sys, os, time, subprocess
from pathlib import Path
root = Path.home() / "Supervaise-Reachy-Mini-Project-main"
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "app"))
os.chdir(root / "app")
from dotenv import load_dotenv; load_dotenv(root / "app" / ".env")
import soundfile as sf
from voice import audio as v_audio
from voice.speak import synthesize, effective_settings
out = Path(sys.argv[1]); out.mkdir(exist_ok=True)
cands = sys.argv[2:]
paths = []
for i, c in enumerate(cands):
    txt = f"I am Artemio {c}, retired Chief Justice of the Philippines."
    pcm = v_audio.process(synthesize(txt, settings=effective_settings(None)), v_audio.SYNTH_SAMPLE_RATE)
    p = out / f"{chr(65+i)}.wav"
    sf.write(str(p), pcm, v_audio.SYNTH_SAMPLE_RATE, subtype="PCM_16")
    paths.append(p); print(chr(65+i), c, f"{len(pcm)/v_audio.SYNTH_SAMPLE_RATE:.1f}s", flush=True)
for p in paths:
    for t in range(4):
        if subprocess.run(["aplay", "-q", str(p)], stderr=subprocess.DEVNULL).returncode == 0: break
        time.sleep(1.5)
    time.sleep(2.5)
