"""Restore a few captchas and print circular content centers. No ids."""

from __future__ import annotations

import base64
import io
import math

from PIL import Image

from modules.runtime import SpiderSession

from _try_slide import REFERER, centers, permutation, restore


def column_weights(image: Image.Image) -> list[int]:
    pixels = image.load()
    width, height = image.size
    bg = pixels[width // 2, 2]
    weights = []
    for x in range(width):
        count = 0
        for y in range(height):
            red, green, blue = pixels[x, y]
            if abs(red - bg[0]) + abs(green - bg[1]) + abs(blue - bg[2]) > 40:
                count += 1
        weights.append(count)
    return weights


def circular_center(weights: list[int]) -> float:
    width = len(weights)
    sin_sum = 0.0
    cos_sum = 0.0
    total = 0.0
    for x, weight in enumerate(weights):
        if weight <= 0:
            continue
        angle = math.tau * x / width
        sin_sum += math.sin(angle) * weight
        cos_sum += math.cos(angle) * weight
        total += weight
    if total <= 0:
        return 0.5
    angle = math.atan2(sin_sum, cos_sum)
    return (angle / math.tau) % 1.0


def gap_center(weights: list[int]) -> tuple[float, int]:
    width = len(weights)
    quiet = [weight < 8 for weight in weights]
    best_start = 0
    best_len = 0
    index = 0
    while index < width * 2 and best_len < width:
        if quiet[index % width]:
            start = index
            while index < start + width and quiet[index % width]:
                index += 1
            length = index - start
            if length > best_len:
                best_len = length
                best_start = start
        else:
            index += 1
    content_start = (best_start + best_len) % width
    content_len = width - best_len
    center = (content_start + content_len / 2) % width
    return center / width, best_len


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER}) as client:
        for attempt in range(3):
            image = client.get(
                "/captcha/api/slide_cylinder_challenge/captcha_image/",
                params={"t": 400 + attempt},
            )
            payload = image.json()
            server_time = image.cookies.get("server_time", "")
            picture = Image.open(io.BytesIO(base64.b64decode(payload["bg"]))).convert("RGB")
            restored = restore(picture, permutation(payload["order"], server_time))
            restored.save(__file__.replace("_inspect_img.py", f"_look_{attempt}.jpg"), quality=85)
            weights = column_weights(restored)
            bbox, com = centers(restored)
            circ = circular_center(weights)
            gap, gap_len = gap_center(weights)
            active = sum(1 for weight in weights if weight >= 8)
            print(
                attempt,
                "off",
                round(float(payload["offset"]), 4),
                "bbox",
                round(bbox, 4),
                "com",
                round(com, 4),
                "circ",
                round(circ, 4),
                "gap",
                round(gap, 4),
                "gap_len",
                gap_len,
                "active_cols",
                active,
                "edge",
                weights[0],
                weights[-1],
            )


if __name__ == "__main__":
    main()
