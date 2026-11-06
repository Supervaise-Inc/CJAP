"""Gate X2: can an engine keep up? Runs the engine alone (no LiveKit, no browser).

    python avatar_bench.py ENGINE WAV [SECONDS]      e.g. avatar_bench.py ditto /bench/sentence.wav 30

Feeds WAV (24 kHz mono PCM16, e.g. a Qwen3-TTS sentence) as one clip every few
seconds, with silence between, and pulls frames as fast as the engine makes them
for SECONDS. Prints:
  * engine fps (must be >= 25 for live use; aim for >= 28 with TTS running);
  * start lag: from pushing a clip to its first speaking frame;
  * worst frame gap.
Writes $AVATAR_BENCH_OUT/bench_<engine>.mp4 (video only) and .wav (default /avatar/bench) (the audio the
frames carried), to check lip-sync by eye: mux them on the laptop or play side by side.
"""
import os
import sys
import time
import wave

import numpy as np

from engines import load_engine


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    name, wav_path = sys.argv[1], sys.argv[2]
    seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
    with wave.open(wav_path, "rb") as w:
        assert w.getframerate() == 24000 and w.getnchannels() == 1 and w.getsampwidth() == 2, \
            "WAV must be 24 kHz mono 16-bit (a cjap-tts sentence)"
        clip = w.readframes(w.getnframes())
    clip_s = len(clip) / 48000
    t0 = time.monotonic()
    eng = load_engine(name)
    print(f"{name}: loaded in {time.monotonic() - t0:.1f} s, frames {eng.width}x{eng.height}")
    import cv2
    out = os.environ.get("AVATAR_BENCH_OUT", "/avatar/bench")
    os.makedirs(out, exist_ok=True)
    vw = cv2.VideoWriter(f"{out}/bench_{name}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 25,
                         (eng.width, eng.height))
    audio_out = []
    gaps, starts, pushed_at, speak_t = [], [], [], []
    next_push, frames, last = time.monotonic() + 1.0, 0, time.monotonic()
    t_start = time.monotonic()
    while time.monotonic() - t_start < seconds:
        now = time.monotonic()
        if now >= next_push:                         # push one clip, the way the page does
            step = 24000                              # 0.5 s chunks
            for i in range(0, len(clip), step):
                eng.push_audio(clip[i:i + step])
            eng.end_clip()
            pushed_at.append(now)
            next_push = now + clip_s + 2.0
        t_call = time.monotonic()
        rgb, pcm, first = eng.next_frame()
        t = time.monotonic()
        if pcm is not None:
            speak_t.append(t - t_call)
        gaps.append(t - last)
        last = t
        frames += 1
        if first and pushed_at:
            starts.append(t - pushed_at[len(starts)] if len(starts) < len(pushed_at) else float("nan"))
        vw.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        audio_out.append(pcm if pcm is not None else np.zeros(960, np.int16))
    vw.release()
    with wave.open(f"{out}/bench_{name}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(np.concatenate(audio_out).astype(np.int16).tobytes())
    wall = time.monotonic() - t_start
    fps = frames / wall
    print(f"engine fps {fps:.1f} over {wall:.0f} s ({frames} frames)   pass: >= 25, aim >= 28")
    if starts:
        print("start lag per clip (s): " + ", ".join(f"{s:.2f}" for s in starts))
    if speak_t:
        print(f"speaking frames: {len(speak_t)}, mean {1000 * sum(speak_t) / len(speak_t):.1f} ms each "
              f"(must stay under 40 ms on average)")
    print(f"worst frame gap {max(gaps[25:] or gaps):.3f} s")
    print(f"wrote {out}/bench_{name}.mp4 and {out}/bench_{name}.wav")
    rc = 0 if fps >= 25 else 1
    getattr(eng, "shutdown", lambda: None)()
    return rc


if __name__ == "__main__":
    sys.stdout.flush()
    os._exit(main())          # Ditto's worker threads are not daemons
