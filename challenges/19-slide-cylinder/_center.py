"""Measure the restored character center as a texture fraction."""

import json
from pathlib import Path

from PIL import Image

image = Image.open(Path(__file__).with_name("_restored.jpg")).convert("RGB")
pixels = image.load()
width, height = image.size
bg = pixels[width - 1, height // 2]
print("bg", bg)

min_x, min_y, max_x, max_y = width, height, 0, 0
count = 0
for y in range(0, height, 1):
    for x in range(width):
        red, green, blue = pixels[x, y]
        if abs(red - bg[0]) + abs(green - bg[1]) + abs(blue - bg[2]) > 30:
            count += 1
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
center = (min_x + max_x) / 2
print("box", min_x, min_y, max_x, max_y, "center", center, "frac", center / width, "count", count)
payload = json.loads(Path(__file__).with_name("_sample.json").read_text(encoding="utf-8"))
print("offset", payload["offset"])
