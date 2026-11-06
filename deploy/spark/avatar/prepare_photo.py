"""Make the avatar's source photo: a square, centred portrait at SIZE px.

    python prepare_photo.py IN.jpg OUT.jpg [SIZE]      (SIZE default 720)

Ditto renders the face at 512 and pastes it back onto this photo, so the photo's
size is the stream's size. Finds the largest face with OpenCV's bundled Haar
detector and crops a square around it with room for hair and shoulders; with no
face found it centre-crops. Prints what it did, so you can check the framing.
"""
import sys

import cv2


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 720
    img = cv2.imread(src)
    if img is None:
        print(f"cannot read {src}")
        return 1
    h, w = img.shape[:2]
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = det.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 5,
                                 minSize=(max(64, w // 10), max(64, h // 10)))
    if len(faces):
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        side = int(min(max(fw, fh) * 2.6, h, w))
        cx, cy = x + fw // 2, y + int(fh * 0.55)
        x0 = min(max(0, cx - side // 2), w - side)
        y0 = min(max(0, cy - side // 2), h - side)
        how = f"face {fw}x{fh} at ({x},{y}); square {side}px at ({x0},{y0})"
    else:
        side = min(h, w)
        x0, y0 = (w - side) // 2, (h - side) // 2
        how = "no face found: centre crop"
    crop = cv2.resize(img[y0:y0 + side, x0:x0 + side], (size, size), interpolation=cv2.INTER_AREA)
    cv2.imwrite(dst, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"{src} {w}x{h} -> {dst} {size}x{size} ({how})")
    if side < 512:
        print("WARNING: the face region is under 512 px in the original; a larger photo will look sharper")
    return 0


if __name__ == "__main__":
    sys.exit(main())
