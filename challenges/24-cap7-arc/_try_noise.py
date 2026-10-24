"""Noise levels on the same arc timing."""

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
SCALE = 400 / 840
OFFSET_Y = (240 - 540 * SCALE) / 2
MAX_DRAG = 400 - 120 * SCALE


def encode(points: list[dict]) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for noise in (0, 2, 5, 8, 15):
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            arc = fresh["arc_path"]["points"]
            index = 58
            n = 28
            chosen = [round(i * index / (n - 1)) for i in range(n)]
            gaps = [30 + (5 if i % 2 == 0 else -3) for i in range(n - 1)]
            end = int(time.time() * 1000) - 40
            cursor = end - sum(gaps)
            rng = random.Random(noise + 3)
            rows = []
            for point_index, gap in zip(chosen, gaps + [0]):
                x = arc[point_index][0] * SCALE + 2
                y = OFFSET_Y + arc[point_index][1] * SCALE + 2
                if noise:
                    x += rng.uniform(-noise, noise)
                    y += rng.uniform(-noise, noise)
                rows.append({"x": round(x, 3), "y": round(y, 3), "t": cursor})
                cursor += gap
            distance = int(round((index + 0.5) / 99 * MAX_DRAG))
            body = {
                "distance": distance,
                "trajectory_encoded": encode(rows),
                "rotation_angle": distance / MAX_DRAG * 360,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print("noise", noise, "error", payload.get("error"))


if __name__ == "__main__":
    main()
