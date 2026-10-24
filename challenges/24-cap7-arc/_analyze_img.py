"""Locate the puzzle hole without printing image bytes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

root = Path(__file__).parent
bg = Image.open(root / "sample_overlay.webp").convert("RGBA")
piece = Image.open(root / "sample_masked.png").convert("RGBA")
print("bg", bg.size, bg.mode)
print("piece", piece.size, piece.mode)
ba = np.array(bg)
pa = np.array(piece)
print("bg alpha min/max", int(ba[:, :, 3].min()), int(ba[:, :, 3].max()))
print("piece alpha zero", int((pa[:, :, 3] == 0).sum()), "nonzero", int((pa[:, :, 3] > 0).sum()))
# Dark translucent hole: low saturation or a gray overlay.
rgb = ba[:, :, :3].astype(np.int16)
alpha = ba[:, :, 3]
# Look for near-gray pixels that are darker than neighbors.
gray = rgb.mean(axis=2)
# Puzzle holes in these captchas are often a semi-transparent black rectangle.
dark = (gray < 80) & (alpha > 200)
print("dark pixels", int(dark.sum()))
ys, xs = np.where(dark)
if len(xs):
    print("dark bbox", int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
# Also check a mid-gray mask (the screenshot looked like a dark blue rectangle).
mask = (gray < 140) & (gray > 40) & (alpha > 200)
print("mid-dark", int(mask.sum()))
ys, xs = np.where(mask)
if len(xs):
    print("mid bbox", int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), "center", int(xs.mean()), int(ys.mean()))
