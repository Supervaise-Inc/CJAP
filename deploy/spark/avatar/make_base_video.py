"""Fallback prep, step 1: an 8 s base clip of the portrait for Wav2Lip, made by AVTR-1.

    python make_base_video.py OUT_DIR [SECONDS]

Runs the AVTR-1 engine on silence, without the microphone (a calm idle head,
blinks, closed mouth) and saves the frames as OUT_DIR/00000000.png ... at 25 fps.
Then run prepare_wav2lip.py on OUT_DIR. Needs the AVTR-1 engine to work (it does
not need to be real-time: this runs once, offline).
"""
import os
import sys

import cv2

from engines import load_engine
from engines.base import frame_to_bgr


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
    os.makedirs(out, exist_ok=True)
    os.environ["AVATAR_LISTEN_PCM"] = ""          # silence only: no reactions to the room
    eng = load_engine("avtr1")
    n = int(seconds * 25)
    for _ in range(25):                     # let the idle motion settle
        eng.next_frame()
    for i in range(n):
        img, _, _ = eng.next_frame()
        cv2.imwrite(os.path.join(out, f"{i:08d}.png"), frame_to_bgr(eng, img))
    print(f"wrote {n} frames ({seconds:.0f} s) to {out}", flush=True)
    getattr(eng, "shutdown", lambda: None)()
    return 0


if __name__ == "__main__":
    os._exit(main())          # don't wait for engine threads
