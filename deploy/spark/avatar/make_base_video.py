"""Fallback prep, step 1: an 8 s base clip of the portrait for Wav2Lip, made by Ditto.

    python make_base_video.py OUT_DIR [SECONDS]

Runs the Ditto engine on silence (a calm idle head, blinks, closed mouth) and
saves the frames as OUT_DIR/00000000.png ... at 25 fps. Then run
prepare_wav2lip.py on OUT_DIR. Needs the Ditto engine to work (it does not need
to be real-time: this runs once, offline).
"""
import os
import sys

import cv2

from engines import load_engine


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
    os.makedirs(out, exist_ok=True)
    eng = load_engine("ditto")
    n = int(seconds * 25)
    for _ in range(25):                     # let the idle motion settle
        eng.next_frame()
    for i in range(n):
        rgb, _, _ = eng.next_frame()
        cv2.imwrite(os.path.join(out, f"{i:08d}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    print(f"wrote {n} frames ({seconds:.0f} s) to {out}", flush=True)
    getattr(eng, "shutdown", lambda: None)()
    return 0


if __name__ == "__main__":
    os._exit(main())          # Ditto's worker threads are not daemons
