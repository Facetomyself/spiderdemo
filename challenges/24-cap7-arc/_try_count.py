"""Find which point counts change the trajectory error."""

from __future__ import annotations

import base64
import json
import random
import time

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
HEADERS = {
    "Referer": REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def encode(points: list[dict]) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def line(n: int) -> list[dict]:
    end = int(time.time() * 1000) - 80
    start = end - 1200
    rows = []
    for i in range(n):
        frac = i / (n - 1)
        rows.append(
            {
                "x": round(frac * 180 + random.uniform(-0.4, 0.4), 3),
                "y": round(110 + random.uniform(-2, 2), 3),
                "t": start + int(frac * 1200) + i,
            }
        )
    return rows


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for n in (9, 10, 11, 12, 48, 49, 50, 51, 52, 53, 54):
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            rows = line(n)
            body = {
                "distance": 180,
                "trajectory_encoded": encode(rows),
                "rotation_angle": 180 / (400 - 120 * 400 / 840) * 360,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(n, payload.get("success"), payload.get("error"))


if __name__ == "__main__":
    main()
