"""Retest slide fraction using the ink center and a length-safe track."""

from __future__ import annotations

import base64
import io
import math
import random

from PIL import Image

from modules.runtime import SpiderSession

from _btoa_check import btoa
from _try_slide import CHALLENGE, CONTAINER_H, CONTAINER_W, REFERER, js_number, permutation, public_body, restore


def ink_center(image: Image.Image) -> float:
    pixels = image.load()
    width, height = image.size
    bg = pixels[width // 2, 2]
    sin_sum = 0.0
    cos_sum = 0.0
    total = 0.0
    for x in range(width):
        weight = 0
        for y in range(0, height, 2):
            red, green, blue = pixels[x, y]
            if abs(red - bg[0]) + abs(green - bg[1]) + abs(blue - bg[2]) > 40:
                weight += 1
        if weight < 4:
            continue
        angle = math.tau * x / width
        sin_sum += math.sin(angle) * weight
        cos_sum += math.cos(angle) * weight
        total += weight
    angle = math.atan2(sin_sum, cos_sum)
    return (angle / math.tau) % 1.0


def encode_track(fraction: float) -> str:
    final_x = (fraction % 1.0) * 350.0
    points = []
    for step in range(1, 25):
        progress = step / 24
        eased = 1 - (1 - progress) ** 2
        points.append((final_x * eased, 480 + (step % 3) - 1, 16 + (step % 5)))
    points[-1] = (final_x, 480, 18)
    body = "[" + ",".join(
        '{"x":%s,"y":%s,"timestamp":%s}' % (js_number(x), js_number(y), js_number(ts))
        for x, y, ts in points
    ) + "]"
    while len(body) % 3:
        body += " "
    encoded = btoa(body)
    return encoded


def main() -> None:
    random.seed(3)
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER}) as client:
        hits = 0
        for attempt in range(3):
            image = client.get(
                "/captcha/api/slide_cylinder_challenge/captcha_image/",
                params={"t": 700 + attempt},
            )
            payload = image.json()
            server_time = image.cookies.get("server_time", "")
            picture = Image.open(io.BytesIO(base64.b64decode(payload["bg"]))).convert("RGB")
            restored = restore(picture, permutation(payload["order"], server_time))
            center = ink_center(restored)
            offset = float(payload["offset"])
            fraction = (offset - center) % 1.0
            response = client.post(
                "/captcha/api/slide_cylinder_challenge/page/",
                json={
                    "captcha_id": payload["captchaId"],
                    "page_num": 5,
                    "challenge_type": CHALLENGE,
                    "track": encode_track(fraction),
                    "container_width": CONTAINER_W,
                    "container_height": CONTAINER_H,
                },
            )
            body = response.json()
            ok = body.get("success") is True
            hits += int(ok)
            print(
                "try",
                attempt,
                "off",
                round(offset, 4),
                "center",
                round(center, 4),
                "frac",
                round(fraction, 4),
                public_body(body),
            )
        print("hits", hits)


if __name__ == "__main__":
    main()
