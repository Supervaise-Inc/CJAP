"""Fallback prep, step 2: face crops for the Wav2Lip engine (research-only weights).

    python prepare_wav2lip.py FRAMES_DIR OUT_DIR

FRAMES_DIR: 25 fps PNG frames of the base clip (make_base_video.py). Detects the
face in every frame with LiveTalking's S3FD (avatars/wav2lip/face_detection),
pads 10 px below the chin, smooths the boxes over 5 frames and writes
OUT_DIR/full/*.png, OUT_DIR/face/*.png (256x256) and OUT_DIR/coords.json
([[y1, y2, x1, x2], ...]) — what engines/wav2lip.py loads.
"""
import json
import os
import shutil
import sys

import cv2
import numpy as np

W2L_CODE = os.environ.get("AVATAR_W2L_CODE", "/opt/livetalking")


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    sys.path.insert(0, W2L_CODE)          # FaceAlignment imports avatars.wav2lip.face_detection.*
    from avatars.wav2lip import face_detection
    names = sorted(n for n in os.listdir(src) if n.endswith(".png"))
    frames = [cv2.imread(os.path.join(src, n)) for n in names]
    det = face_detection.FaceAlignment(face_detection.LandmarksType._2D, flip_input=False,
                                       device="cuda")
    boxes = []
    for i in range(0, len(frames), 8):
        boxes += det.get_detections_for_batch(np.array(frames[i:i + 8]))
    rows = []
    for fr, b in zip(frames, boxes):
        if b is None:
            print("a frame has no detectable face: the base clip must show the face in every frame")
            return 1
        h, w = fr.shape[:2]
        x1, y1, x2, y2 = (int(v) for v in b[:4])
        rows.append([max(0, y1), min(h, y2 + 10), max(0, x1), min(w, x2)])
    arr = np.array(rows, dtype=np.float64)
    sm = np.array([arr[max(0, i - 2):i + 3].mean(axis=0) for i in range(len(arr))]).astype(int)
    for d in ("full", "face"):
        shutil.rmtree(os.path.join(out, d), ignore_errors=True)
        os.makedirs(os.path.join(out, d))
    for n, fr, (y1, y2, x1, x2) in zip(names, frames, sm):
        cv2.imwrite(os.path.join(out, "full", n), fr)
        cv2.imwrite(os.path.join(out, "face", n), cv2.resize(fr[y1:y2, x1:x2], (256, 256)))
    json.dump(sm.tolist(), open(os.path.join(out, "coords.json"), "w"))
    print(f"{len(names)} frames prepared in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
