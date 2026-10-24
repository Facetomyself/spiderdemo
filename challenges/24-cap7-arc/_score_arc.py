"""Score each arc index by comparing the rotated piece to that point."""

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


def rotate(angle: float) -> np.ndarray:
    matrix = cv2.getRotationMatrix2D((pw / 2, ph / 2), angle, 1.0)
    return cv2.warpAffine(piece, matrix, (pw, ph), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def ncc(turned: np.ndarray, x: int, y: int) -> float:
    if x < 0 or y < 0 or x + pw > bg.shape[1] or y + ph > bg.shape[0]:
        return -1.0
    patch = bg[y : y + ph, x : x + pw].astype(np.float32)
    rgb = turned[:, :, :3].astype(np.float32)
    mask = turned[:, :, 3] > 128
    if int(mask.sum()) < 500:
        return -1.0
    src = rgb[mask]
    dst = patch[mask]
    src = src - src.mean()
    dst = dst - dst.mean()
    denom = float(np.linalg.norm(src) * np.linalg.norm(dst))
    if denom < 1e-6:
        return -1.0
    return float((src * dst).sum() / denom)


scores = []
for index, (cx, cy) in enumerate(points):
    angle = index / (len(points) - 1) * 360.0
    turned = rotate(angle)
    x = int(round(cx - pw / 2))
    y = int(round(cy - ph / 2))
    scores.append(ncc(turned, x, y))
order = np.argsort(scores)[::-1]
for index in order[:6]:
    print(int(index), round(float(scores[index]), 4), "angle", round(index / 99 * 360, 3))
