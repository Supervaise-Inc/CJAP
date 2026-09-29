import os, subprocess, sys
sys.path.insert(0, os.path.expanduser("~/Supervaise-Reachy-Mini-Project-main/app"))
from voice_io import _sync_client  # reuses app/.env OPENAI_API_KEY via cj_chat's dotenv
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/Supervaise-Reachy-Mini-Project-main/app/.env"))

TEXTS = [
    "Ah — a fine question. Allow me a moment to consult what my record holds.",
    "Yes; let me give that the consideration it deserves — a moment, if you please.",
    "A thoughtful question. Permit me to gather my recollections properly.",
    "Let me reflect on that for a moment; a proper answer deserves a proper pause.",
    "Hmm — allow me to draw the threads together before I speak.",
    "Well now, that is worth answering with care. Bear with me a moment.",
    "I should like to answer this properly, so let me consult my record first.",
    "A moment, if you would — I prefer to weigh my words before I offer them.",
    "Let me think this through as it deserves; I shall be with you shortly.",
    "Ah — give me just a moment to marshal my thoughts on this.",
    "Ah, yes. Let me look back through my years on the bench for this one.",
    "One moment po — I want to give you an answer worthy of the question.",
    "Hmm. There is something in my record that speaks to this; let me recall it properly.",
    "Patience, my friend — good judgment is never rushed.",
    "Let me search my memory; fifty years of law leaves many pages to turn.",
    "A moment po. Even on the Court, I never answered without reflection.",
    "That touches something I have written about; allow me to find the thread.",
    "Give me a breath to set my thoughts in order.",
    "Ah — I have opinions on this, in both senses of the word. One moment.",
    "Let me weigh this as I would have weighed a case — carefully.",
    "Hmm, a question after my own heart. Bear with me briefly.",
    "I am gathering my recollections — the archive of an old jurist is vast.",
    "Steady now — the right words are worth a short wait.",
    "Yes, I recall something on this. Let me bring it into focus.",
    "Allow an old Chief Justice a moment of deliberation.",
    "The law taught me never to speak before thinking. A moment, please.",
    "Let me consult the record of my years — it rarely fails me.",
    "Ah, this deserves more than a quick reply. Give me a moment po.",
    "I shall answer presently — deliberation first, pronouncement after.",
    "Hold on briefly — I want to be precise, as a judge must be.",
    "Hmm — let me turn this over once or twice before I speak.",
    "There is wisdom in the pause; allow me mine.",
    "A fine point. I am drawing on many years to answer it well.",
    "Sandali lamang po — a careful answer is a kind answer.",
    "Let me marshal the relevant memories; they are many.",
    "Ah, you test my recollection — pleasantly so. One moment.",
    "Every good ruling begins with quiet thought. Grant me a little.",
    "I am consulting my own precedents, so to speak.",
    "Bear with me po; I would rather be right than quick.",
    "Yes — I know just where to look for this. A brief moment.",
]

outdir = os.path.expanduser("~/fillers")
os.makedirs(outdir, exist_ok=True)
client = _sync_client()
for i, text in enumerate(TEXTS, 1):
    mp3 = f"{outdir}/{i:02d}.mp3"
    wav = f"{outdir}/{i:02d}.wav"
    if os.path.exists(wav):   # keep already-generated clips; only fill the gaps
        print(f"  skip {i:02d} (exists)")
        continue
    resp = client.audio.speech.create(model="tts-1", voice="echo", speed=1.25, input=text)
    with open(mp3, "wb") as f:
        f.write(resp.content)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "quiet", "-i", mp3, wav], check=True)
    os.unlink(mp3)
    print(f"  ok {i:02d}: {text[:40]}...")
print("done ->", outdir)
