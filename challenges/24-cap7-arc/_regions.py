"""Find unnatural patches: puzzle hole and dark blocks."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

root = Path(__file__).parent
rgb = np.array(Image.open(root / "sample_overlay.webp").convert("RGB"))
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
smooth = cv2.medianBlur(gray, 31)
delta = gray.astype(np.int16) - smooth.astype(np.int16)
# Darkened patches are strongly negative.
dark = (delta < -25).astype(np.uint8) * 255
dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
n, labels, stats, centroids = cv2.connectedComponentsWithStats(dark)
print("components", n - 1)
order = np.argsort(stats[1:, cv2.CC_STAT_AREA])[::-1]
for rank, idx in enumerate(order[:8], start=1):
    i = int(idx) + 1
    x, y, w, h, area = [int(v) for v in stats[i]]
    if area < 200:
        continue
    print(rank, "xywh", x, y, w, h, "area", area, "centroid", [round(float(c), 1) for c in centroids[i]])
preview = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
preview[dark > 0] = (0, 0, 255)
cv2.imwrite(str(root / "dark_preview.png"), cv2.resize(preview, (630, 405)))
