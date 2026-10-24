"""Confirm bbox center minus offset on two fresh captchas."""

from __future__ import annotations

import base64
import hashlib
import io
import itertools
import json
import random

from PIL import Image

from modules.runtime import SpiderSession

from _try_slide import (
    CHALLENGE,
    CONTAINER_H,
    CONTAINER_W,
    REFERER,
    centers,
    permutation,
    public_body,
    restore,
    track_for,
)


def main() -> None:
    random.seed(7)
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER}) as client:
        init = client.get(
            "/captcha/api/slide_cylinder_challenge/init/",
            params={"challenge_type": CHALLENGE},
        )
        print("init", init.status_code, public_body(init.json()))
        hits = 0
        for attempt in range(3):
            image = client.get(
                "/captcha/api/slide_cylinder_challenge/captcha_image/",
                params={"t": 100 + attempt},
            )
            payload = image.json()
            server_time = image.cookies.get("server_time", "")
            picture = Image.open(io.BytesIO(base64.b64decode(payload["bg"]))).convert("RGB")
            print("img", picture.size)
            restored = restore(picture, permutation(payload["order"], server_time))
            bbox, com = centers(restored)
            offset = float(payload["offset"])
            fraction = (bbox - offset) % 1.0
            response = client.post(
                "/captcha/api/slide_cylinder_challenge/page/",
                json={
                    "captcha_id": payload["captchaId"],
                    "page_num": 3 + attempt,
                    "challenge_type": CHALLENGE,
                    "track": track_for(fraction),
                    "container_width": CONTAINER_W,
                    "container_height": CONTAINER_H,
                },
            )
            body = response.json()
            ok = isinstance(body, dict) and body.get("success") is True
            hits += int(ok)
            print(
                "confirm",
                attempt,
                "page",
                3 + attempt,
                "off",
                round(offset, 4),
                "bbox",
                round(bbox, 4),
                "com",
                round(com, 4),
                "frac",
                round(fraction, 4),
                "http",
                response.status_code,
                public_body(body),
            )
        print("hits", hits)


if __name__ == "__main__":
    main()
