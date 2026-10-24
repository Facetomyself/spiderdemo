"""Sweep timing shapes on one straight track."""

from __future__ import annotations

import base64
import json
import math
import statistics
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


def track(gaps: list[int]) -> list[dict]:
    end = int(time.time() * 1000) - 30
    start = end - sum(gaps)
    rows = []
    cursor = start
    n = len(gaps) + 1
    for i in range(n):
        frac = i / (n - 1)
        rows.append({"x": round(frac * 200, 3), "y": round(120 + math.sin(frac * math.pi) * 8, 3), "t": cursor})
        if i < len(gaps):
            cursor += gaps[i]
    rows[-1]["t"] = end
    return rows


def shapes() -> dict[str, list[int]]:
    n = 23
    ease = []
    for i in range(n):
        frac = i / (n - 1)
        ease.append(int(18 + 22 * (frac - 0.5) ** 2 * 4))
    return {
        "uniform": [36] * n,
        "pm1": [36 + (1 if i % 2 == 0 else -1) for i in range(n)],
        "pm4": [36 + (4 if i % 2 == 0 else -4) for i in range(n)],
        "two": [18] * 12 + [42] * 11,
        "ease": ease,
        "pause": [22] * 10 + [90] + [22] * 12,
    }


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for name, gaps in shapes().items():
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            rows = track(gaps)
            delta = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, len(rows))]
            body = {
                "distance": 200,
                "trajectory_encoded": encode(rows),
                "rotation_angle": 200 / (400 - 120 * 400 / 840) * 360,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(
                name,
                "std",
                round(statistics.pstdev(delta), 2),
                "span",
                rows[-1]["t"] - rows[0]["t"],
                "error",
                payload.get("error"),
            )


if __name__ == "__main__":
    main()
