"""Retry a non-uniform arc track with a browser user agent."""

from __future__ import annotations

import base64
import json
import time

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
HEADERS = {
    "Referer": REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
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
        for name, uniform in (("uniform", True), ("arc", False)):
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            arc = fresh["arc_path"]["points"]
            n = 24
            index = 60
            chosen = [round(i * index / (n - 1)) for i in range(n)]
            gap = 36 if uniform else None
            gaps = [36] * (n - 1) if uniform else [32 + (5 if i % 2 == 0 else -5) for i in range(n - 1)]
            end = int(time.time() * 1000) - 40
            cursor = end - sum(gaps)
            rows = []
            for point_index, step in zip(chosen, gaps + [0]):
                rows.append(
                    {
                        "x": arc[point_index][0] * SCALE + 2,
                        "y": OFFSET_Y + arc[point_index][1] * SCALE + 2,
                        "t": cursor,
                    }
                )
                cursor += step
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
            print(name, payload.get("error"), "gap", gap)


if __name__ == "__main__":
    main()
