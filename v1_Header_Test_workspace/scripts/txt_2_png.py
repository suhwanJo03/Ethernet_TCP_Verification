import numpy as np
import cv2

# ---- Config ----
txt_file = "bicubic_output_frame1.txt"   # bottom-up RGBA8888 text file (hex, "R G B A")
out_png_with_alpha = "bicubic_output_frame1.png"
out_png_opaque_bgr = "bicubic_output_frame1_opague.png"

IMG_W = 1280
IMG_H = 720

# ---- Load RGBA from text (hex strings like '7F', '00', 'FF') ----
pixels = []
with open(txt_file, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Invalid line: {line}")
        # Parse hex tokens to ints (R G B A)
        R, G, B, A = [int(x, 16) for x in parts]
        pixels.append([R, G, B, A])

pixels = np.asarray(pixels, dtype=np.uint8)

# ---- Sanity checks ----
expected = IMG_W * IMG_H
if pixels.shape[0] != expected:
    raise ValueError(f"Pixel count mismatch: got {pixels.shape[0]} != {expected}")

# ---- Reshape & flip (bottom-up -> top-down) ----
img_rgba = pixels.reshape((IMG_H, IMG_W, 4))
img_rgba = np.flipud(img_rgba)

# ---- Quick diagnostics ----
A = img_rgba[..., 3]
a_zero_ratio = np.mean(A == 0) * 100.0
print(f"[Diag] A==0 ratio: {a_zero_ratio:.2f}% | A min/max: {A.min()} / {A.max()}")

# ---- Convert RGBA -> BGRA for OpenCV I/O ----
# OpenCV uses BGR(A) channel order when encoding/decoding.
img_bgra = img_rgba[..., [2, 1, 0, 3]]  # swap R<->B, keep G and A

# ---- If alpha is mostly zero (fully transparent), force opaque for a visible PNG ----
if a_zero_ratio > 90.0:
    print("[Info] Alpha looks mostly zero. Saving an opaque BGR version as well.")
    # Drop alpha and save as opaque BGR (visible in all viewers)
    img_bgr_opaque = img_bgra[..., :3].copy()
    cv2.imwrite(out_png_opaque_bgr, img_bgr_opaque)
    print(f"[Saved] {out_png_opaque_bgr}")

# ---- Save 4-channel PNG (will look transparent if A==0) ----
cv2.imwrite(out_png_with_alpha, img_bgra)
print(f"[Saved] {out_png_with_alpha}")
