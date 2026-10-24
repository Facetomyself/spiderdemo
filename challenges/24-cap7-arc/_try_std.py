"""On-arc tracks with the smallest non-uniform timing."""

from __future__ import annotations

import base64
import json
import statistics
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


def clock(n: int) -> list[int]:
    gaps = [32 + (4 if i % 2 == 0 else -4) for i in range(n - 1)]
    end = int(time.time() * 1000) - 40
    start = end - sum(gaps)
    rows = [start]
    for gap in gaps:
        rows.append(rows[-1] + gap)
    return rows


def build(arc: list, kind: str) -> tuple[list[dict], int, float]:
    index = 55
    n = 24
    chosen = [round(i * index / (n - 1)) for i in range(n)]
    stamps = clock(n)
    rows = []
    for point_index, stamp in zip(chosen, stamps):
        if kind == "image":
            x, y = arc[point_index][0], arc[point_index][1]
        elif kind == "plus2":
            x = arc[point_index][0] * SCALE + 2
            y = OFFSET_Y + arc[point_index][1] * SCALE + 2
        elif kind == "cover":
            x = arc[point_index][0] * SCALE
            y = OFFSET_Y + arc[point_index][1] * SCALE
        else:
            x = point_index / 99 * 200
            y = 120
        rows.append({"x": x, "y": y, "t": stamp})
    distance = int(round((index + 0.5) / 99 * MAX_DRAG))
    rotation = distance / MAX_DRAG * 360
    return rows, distance, rotation


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        sample = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        arc = sample["arc_path"]["points"]
        for kind in ("straight", "cover", "plus2", "image"):
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            rows, distance, rotation = build(fresh["arc_path"]["points"], kind)
            delta = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, len(rows))]
            body = {
                "distance": distance,
                "trajectory_encoded": encode(rows),
                "rotation_angle": rotation,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(kind, "std", round(statistics.pstdev(delta), 2), "n", len(rows), "error", payload.get("error"))
        _ = arc


if __name__ == "__main__":
    main()
