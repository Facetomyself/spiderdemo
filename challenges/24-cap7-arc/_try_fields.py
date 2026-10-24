"""See which field changes the trajectory error."""

from __future__ import annotations

import base64
import json
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


def track(arc: list) -> list[dict]:
    index = 50
    n = 22
    chosen = [round(i * index / (n - 1)) for i in range(n)]
    gaps = [28 + (6 if i % 2 == 0 else -2) for i in range(n - 1)]
    end = int(time.time() * 1000) - 40
    cursor = end - sum(gaps)
    rows = []
    for point_index, gap in zip(chosen, gaps + [0]):
        rows.append(
            {
                "x": arc[point_index][0] * SCALE + 2,
                "y": OFFSET_Y + arc[point_index][1] * SCALE + 2,
                "t": cursor,
            }
        )
        cursor += gap
    return rows


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        base = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        rows = track(base["arc_path"]["points"])
        encoded = encode(rows)
        last_x = rows[-1]["x"]
        normal = int(round(50.5 / 99 * MAX_DRAG))
        plans = {
            "zero": (0, 0),
            "normal": (normal, normal / MAX_DRAG * 360),
            "lastx": (last_x, last_x / MAX_DRAG * 360),
            "huge": (500, 10),
            "rot0": (normal, 0),
            "rotbig": (normal, 400),
        }
        for name, (distance, rotation) in plans.items():
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            body = {
                "distance": distance,
                "trajectory_encoded": encoded,
                "rotation_angle": rotation,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(name, "error", payload.get("error"))


if __name__ == "__main__":
    main()
