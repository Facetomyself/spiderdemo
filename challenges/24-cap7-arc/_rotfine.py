"""Refine the piece rotation around the best coarse match."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

root = Path(__file__).parent
bg = np.array(Image.open(root / "sample_overlay.webp").convert("RGB"))
piece = np.array(Image.open(root / "sample_masked.png").convert("RGBA"))
ph, pw = piece.shape[:2]


def rotate(image: np.ndarray, angle: float) -> np.ndarray:
    matrix = cv2.getRotationMatrix2D((pw / 2, ph / 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (pw, ph), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


for angle in range(150, 171):
    turned = rotate(piece, angle)
    score = cv2.matchTemplate(
        bg,
        turned[:, :, :3],
        cv2.TM_CCOEFF_NORMED,
        mask=(turned[:, :, 3] > 128).astype(np.uint8) * 255,
    )
    _, value, _, loc = cv2.minMaxLoc(score)
    print(angle, round(float(value), 4), loc)
