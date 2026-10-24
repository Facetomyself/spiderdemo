"""Save a side-by-side of the piece and the visible hole crop."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

root = Path(__file__).parent
bg = np.array(Image.open(root / "sample_overlay.webp").convert("RGB"))
piece = np.array(Image.open(root / "sample_masked.png").convert("RGBA"))
crop = bg[110:230, 140:270]
canvas = np.full((140, 280, 3), 255, np.uint8)
thumb = cv2.resize(crop, (130, 120))
canvas[10:130, 10:140] = thumb
rgb = piece[:, :, :3]
alpha = piece[:, :, 3:4] / 255.0
fitted = (rgb * alpha + 255 * (1 - alpha)).astype(np.uint8)
fitted = cv2.resize(fitted, (120, 100))
canvas[20:120, 155:275] = fitted
cv2.imwrite(str(root / "compare.png"), cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
print("crop", crop.shape, "piece", piece.shape)
