import sys, os, json, time, subprocess, shutil
from pathlib import Path
root = Path.home() / "Supervaise-Reachy-Mini-Project-main"
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / "app")); os.chdir(root / "app")
from dotenv import load_dotenv; load_dotenv(root / "app" / ".env")
import speech_engines
from text_entities import process_tts_sentence
from voice import cache as v_cache
from voice.speak import effective_settings
d = json.load(open(root / "data/entities/canned_answers.json"))
keep = {}
for e in d["entries"]:
    for i, a in enumerate(e.get("answers") or [e.get("answer")]):
        if a and "anganiban" in a:
            t = process_tts_sentence(a)
            key = v_cache.cache_key(v_cache.normalize_text(speech_engines.apply_forced_respellings(t)), effective_settings(None))
            fresh = v_cache.get(key) is None
            t0 = time.time(); wav = speech_engines.tts_elevenlabs_wav(t); dt = time.time() - t0
            print(f"{e['id']}[{i}] {'RENDERED' if fresh else 'cached '} {dt:.1f}s key={key[:10]}")
            if (e["id"], i) == ("who_are_you", 1): keep["wav"] = wav
            else: os.unlink(wav)
out = Path(sys.argv[1]); out.mkdir(exist_ok=True); shutil.move(keep["wav"], out / "who_are_you_1.wav")
for t in range(4):
    if subprocess.run(["aplay", "-q", str(out / "who_are_you_1.wav")], stderr=subprocess.DEVNULL).returncode == 0: break
    time.sleep(1.5)
