"""Show non-secret fields from one failed page response."""

from __future__ import annotations

import base64
import io

from PIL import Image

from modules.runtime import SpiderSession

from _confirm2 import encode_track, ink_center
from _try_slide import CHALLENGE, CONTAINER_H, CONTAINER_W, REFERER, permutation, restore


def brief(value, depth=0):
    if isinstance(value, dict):
        return {key: brief(item, depth + 1) for key, item in value.items() if "id" not in key.lower() and key != "bg"}
    if isinstance(value, list):
        if value and all(isinstance(item, (int, float)) for item in value):
            return [f"nums*{len(value)}"]
        return [brief(item, depth + 1) for item in value[:6]]
    if isinstance(value, str):
        if len(value) > 80:
            return f"str*{len(value)}"
        return value
    return value


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER}) as client:
        image = client.get("/captcha/api/slide_cylinder_challenge/captcha_image/", params={"t": 1})
        payload = image.json()
        print("image_keys", sorted(payload))
        for key, value in payload.items():
            if key in {"bg", "captchaId", "order"}:
                print(key, type(value).__name__, len(str(value)))
            else:
                print(key, value)
        server_time = image.cookies.get("server_time", "")
        picture = Image.open(io.BytesIO(base64.b64decode(payload["bg"]))).convert("RGB")
        restored = restore(picture, permutation(payload["order"], server_time))
        center = ink_center(restored)
        offset = float(payload["offset"])
        fraction = (center - offset) % 1.0
        response = client.post(
            "/captcha/api/slide_cylinder_challenge/page/",
            json={
                "captcha_id": payload["captchaId"],
                "page_num": 6,
                "challenge_type": CHALLENGE,
                "track": encode_track(fraction),
                "container_width": CONTAINER_W,
                "container_height": CONTAINER_H,
            },
        )
        body = response.json()
        print("http", response.status_code)
        print("body", brief(body))


if __name__ == "__main__":
    main()
