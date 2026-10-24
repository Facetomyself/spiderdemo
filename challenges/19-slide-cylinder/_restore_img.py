"""Restore one cylinder captcha locally and print the content center."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image

FOLDER = Path(__file__).parent
TILE_W = 255
TILE_H = 185


def permutation(order: str, server_time: str) -> list[int]:
    for perm in itertools.permutations(range(8)):
        text = json.dumps(list(perm), separators=(",", ":")) + server_time
        if hashlib.md5(text.encode()).hexdigest() == order:
            return list(perm)
    raise RuntimeError("permutation not found")


def restore(image: Image.Image, perm: list[int]) -> Image.Image:
    canvas = Image.new("RGB", image.size)
    for source, dest in enumerate(perm):
        sx = (source % 4) * TILE_W
        sy = (source // 4) * TILE_H
        dx = (dest % 4) * TILE_W
        dy = (dest // 4) * TILE_H
        canvas.paste(image.crop((sx, sy, sx + TILE_W, sy + TILE_H)), (dx, dy))
    return canvas


def content_center(image: Image.Image) -> tuple[int, int, int, int]:
    pixels = image.load()
    width, height = image.size
    min_x, min_y, max_x, max_y = width, height, 0, 0
    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            if abs(red - 255) + abs(green - 244) + abs(blue - 184) > 40:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    return min_x, min_y, max_x, max_y


def main() -> None:
    payload = json.loads((FOLDER / "_sample.json").read_text(encoding="utf-8"))
    server_time = (FOLDER / "_server_time.txt").read_text(encoding="utf-8").strip()
    perm = permutation(payload["order"], server_time)
    source = Image.open(FOLDER / "_bg.jpg")
    # refresh bg from the latest sample
    import base64

    source = Image.open(__import__("io").BytesIO(base64.b64decode(payload["bg"])))
    restored = restore(source, perm)
    restored.save(FOLDER / "_restored.jpg", quality=90)
    box = content_center(restored)
    center_x = (box[0] + box[2]) / 2
    print("perm", perm, "size", restored.size, "box", box, "center_x", round(center_x, 2), "offset", payload["offset"])


if __name__ == "__main__":
    main()
