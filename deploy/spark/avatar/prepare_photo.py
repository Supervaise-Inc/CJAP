"""Make the avatar's source photo: a W x H PNG, the face centred, room for hair and shoulders.

    python prepare_photo.py IN.jpg OUT.png [W H]      (default 1280 720, AVTR-1's frame)

AVTR-1 renders the face at 512 and pastes it back onto this photo, then mattes
the person and puts them on the chosen background (AVATAR_BG), so the photo's
own background doesn't show. The photo must already be the stream's size
(AVTR-1 would stretch it otherwise). Finds the largest face with OpenCV's bundled
Haar detector and frames it so the face is about a third of the height; where the
photo is too narrow or short for that frame, it pads with white (matted away
later). With no face found it centre-crops. Prints what it did, so you can check
the framing.
"""
import sys

import cv2
import numpy as np


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    W = int(sys.argv[3]) if len(sys.argv) > 3 else 1280
    H = int(sys.argv[4]) if len(sys.argv) > 4 else 720
    if W % 2 or H % 2:
        print("W and H must be even (the stream is YUV 4:2:0)")
        return 2
    if not dst.lower().endswith(".png"):
        print("OUT must be a .png (AVTR-1 loads PNG portraits)")
        return 2
    img = cv2.imread(src)
    if img is None:
        print(f"cannot read {src}")
        return 1
    h, w = img.shape[:2]
    faces = ()
    if hasattr(cv2, "CascadeClassifier"):         # OpenCV 4 (the image pins < 5)
        det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = det.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 5,
                                     minSize=(max(64, w // 10), max(64, h // 10)))
    if len(faces):
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        ch = int(fh / 0.33)                      # frame height: the face is ~1/3 of it
        cw = ch * W // H
        cx, cy = x + fw // 2, y + int(fh * 0.62)  # face a little above the middle
        x0, y0 = cx - cw // 2, cy - ch // 2
        how = f"face {fw}x{fh} at ({x},{y}); frame {cw}x{ch} at ({x0},{y0})"
    else:
        if w * H > h * W:
            cw, ch = h * W // H, h
        else:
            cw, ch = w, w * H // W
        x0, y0 = (w - cw) // 2, (h - ch) // 2
        how = "no face found: centre crop"
    canvas = np.full((ch, cw, 3), 255, np.uint8)      # white where the photo ends
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(w, x0 + cw), min(h, y0 + ch)
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    padded = (sx0 - x0, sy0 - y0, x0 + cw - sx1, y0 + ch - sy1)
    out = cv2.resize(canvas, (W, H), interpolation=cv2.INTER_AREA if cw >= W else cv2.INTER_CUBIC)
    cv2.imwrite(dst, out)
    print(f"{src} {w}x{h} -> {dst} {W}x{H} ({how})")
    if any(padded):
        print(f"padded with white (left, top, right, bottom px of the source frame): {padded}")
    if len(faces) and fh < 256:
        print("WARNING: the face is under 256 px in the original; a larger photo will look sharper")
    return 0


if __name__ == "__main__":
    sys.exit(main())
