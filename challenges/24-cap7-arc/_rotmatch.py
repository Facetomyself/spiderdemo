"""Rotate the piece and find where its pixels still match the background."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

root = Path(__file__).parent
meta = json.loads((root / "sample_meta.json").read_text(encoding="utf-8"))
points = np.array(meta["points"], dtype=np.float64)
bg = np.array(Image.open(root / "sample_overlay.webp").convert("RGB"))
piece = np.array(Image.open(root / "sample_masked.png").convert("RGBA"))
ph, pw = piece.shape[:2]


def rotate(image: np.ndarray, angle: float) -> np.ndarray:
    center = (pw / 2, ph / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (pw, ph),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


best = []
for angle in range(0, 360, 5):
    turned = rotate(piece, angle)
    rgb = turned[:, :, :3]
    mask = turned[:, :, 3]
    if int((mask > 128).sum()) < 1000:
        continue
    score = cv2.matchTemplate(bg, rgb, cv2.TM_CCOEFF_NORMED, mask=(mask > 128).astype(np.uint8) * 255)
    _, value, _, loc = cv2.minMaxLoc(score)
    best.append((float(value), angle, int(loc[0]), int(loc[1])))

best.sort(reverse=True)
print("top")
for row in best[:8]:
    value, angle, x, y = row
    cx = x + pw / 2
    cy = y + ph / 2
    delta = points - np.array([cx, cy])
    dist = np.hypot(delta[:, 0], delta[:, 1])
    idx = int(np.argmin(dist))
    print(
        "score",
        round(value, 4),
        "angle",
        angle,
        "loc",
        x,
        y,
        "center",
        round(cx, 1),
        round(cy, 1),
        "arc",
        idx,
        "arc_dist",
        round(float(dist[idx]), 1),
    )
