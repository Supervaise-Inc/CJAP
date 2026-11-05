"""Build the voice-clone reference for cjap-tts from CJAP's filler clips.

    python make_ref.py FILLER_DIR OUT_DIR [N N N]

Joins the chosen numbered clips (default 01 03 07) with 0.4 s of silence into
OUT_DIR/ref.wav (24 kHz mono PCM_16) and writes their exact text to
OUT_DIR/ref.txt. The texts are the ones the clips were rendered from
(deploy/alpha/home/gen_voice_wavs_eleven.py, FILLER_TEXTS, 2026-08-19), so the
transcript matches the audio word for word.

Prints the total length; aim for 10-15 s.
"""
import os
import sys

import numpy as np
import soundfile as sf

TEXTS = {
    "01": "Ah — a fine question. Allow me a moment to consult what my record holds.",
    "03": "A thoughtful question. Permit me to gather my recollections properly.",
    "06": "Well now, that is worth answering with care. Bear with me a moment.",
    "07": "I should like to answer this properly, so let me consult my record first.",
    "11": "Ah, yes. Let me look back through my years on the bench for this one.",
    "15": "Let me search my memory; fifty years of law leaves many pages to turn.",
    "20": "Let me weigh this as I would have weighed a case — carefully.",
    "26": "The law taught me never to speak before thinking. A moment, please.",
}
SR = 24000


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    picks = sys.argv[3:] or ["01", "03", "07"]
    bad = [p for p in picks if p not in TEXTS]
    if bad:
        print(f"no transcript for clip(s) {bad}; choose from {sorted(TEXTS)}")
        return 2
    gap = np.zeros(int(0.4 * SR), dtype=np.float32)
    parts = []
    for p in picks:
        pcm, sr = sf.read(os.path.join(src, f"{p}.wav"), dtype="float32", always_2d=False)
        if pcm.ndim > 1:
            pcm = pcm.mean(axis=1)
        if sr != SR:
            print(f"{p}.wav is {sr} Hz, expected {SR}")
            return 1
        parts += [pcm.astype(np.float32), gap]
    audio = np.concatenate(parts[:-1])
    os.makedirs(out, exist_ok=True)
    sf.write(os.path.join(out, "ref.wav"), audio, SR, subtype="PCM_16")
    with open(os.path.join(out, "ref.txt"), "w", encoding="utf-8") as f:
        f.write(" ".join(TEXTS[p] for p in picks) + "\n")
    print(f"ref.wav {audio.size / SR:.1f} s from clips {' '.join(picks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
