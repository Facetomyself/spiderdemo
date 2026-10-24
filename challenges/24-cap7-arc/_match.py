"""Find the puzzle hole and the nearest arc point. No image bytes printed."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

root = Path(__file__).parent
meta = json.loads((root / "sample_meta.json").read_text(encoding="utf-8"))
points = np.array(meta["points"], dtype=np.float64)
bg = cv2.cvtColor(np.array(Image.open(root / "sample_overlay.webp").convert("RGB")), cv2.COLOR_RGB2GRAY)
piece = np.array(Image.open(root / "sample_masked.png").convert("RGBA"))
alpha = piece[:, :, 3]
mask = (alpha > 128).astype(np.uint8) * 255
print("mask bbox area", int((mask > 0).sum()), "slider_y", meta["slider_y"])
edges = cv2.Canny(bg, 40, 120)
kernel = np.ones((3, 3), np.uint8)
mask_edge = cv2.dilate(mask, kernel) - cv2.erode(mask, kernel)
result = cv2.matchTemplate(edges, mask_edge, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(result)
print("edge match", round(float(max_val), 4), "loc", max_loc)
# Also match the raw alpha as a bright blob against inverted darkness.
ys, xs = np.where(mask > 0)
print("piece opaque bbox", int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
cx = max_loc[0] + (xs.min() + xs.max()) / 2
cy = max_loc[1] + (ys.min() + ys.max()) / 2
print("hole center", round(cx, 1), round(cy, 1))
delta = points - np.array([cx, cy])
dist = np.hypot(delta[:, 0], delta[:, 1])
order = np.argsort(dist)[:5]
for idx in order:
    print("arc", int(idx), "pt", [round(float(v), 1) for v in points[idx]], "dist", round(float(dist[idx]), 2))

preview = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
x, y = max_loc
h, w = mask.shape
cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 0, 255), 2)
best = int(order[0])
cv2.circle(preview, (int(points[best][0]), int(points[best][1])), 8, (0, 255, 0), 2)
small = cv2.resize(preview, (420, 270))
cv2.imwrite(str(root / "match_preview.png"), small)
print("wrote match_preview.png")
