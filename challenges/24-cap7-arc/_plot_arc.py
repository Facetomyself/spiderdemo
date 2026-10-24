"""Draw the server arc on the background and save a small preview."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

root = Path(__file__).parent
meta = json.loads((root / "sample_meta.json").read_text(encoding="utf-8"))
points = np.array(meta["points"], dtype=np.int32)
bg = cv2.cvtColor(np.array(Image.open(root / "sample_overlay.webp").convert("RGB")), cv2.COLOR_RGB2BGR)
cv2.polylines(bg, [points.reshape(-1, 1, 2)], False, (0, 0, 255), 3)
for idx in (0, 25, 50, 75, 99):
    x, y = points[idx]
    cv2.circle(bg, (int(x), int(y)), 6, (0, 255, 0), -1)
    cv2.putText(bg, str(idx), (int(x) + 6, int(y) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
print("y range", int(points[:, 1].min()), int(points[:, 1].max()), "x range", int(points[:, 0].min()), int(points[:, 0].max()))
small = cv2.resize(bg, (630, 405))
cv2.imwrite(str(root / "arc_preview.png"), small)
