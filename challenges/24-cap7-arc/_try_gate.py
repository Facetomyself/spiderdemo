"""Split the trajectory gate: same timing, different geometry."""

from __future__ import annotations

import base64
import json
import math
import random
import time

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
HEADERS = {
    "Referer": REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json; charset=utf-8",
}
SCALE = 400 / 840
OFFSET_Y = (240 - 540 * SCALE) / 2
MAX_DRAG = 400 - 120 * SCALE


def encode(points: list[dict]) -> str:
    raw = json.dumps(points, separators=(",", ":"), ensure_ascii=False).encode()
    return base64.b64encode(raw).decode()


def times(n: int, span: int) -> list[int]:
    end = int(time.time() * 1000) - 60
    start = end - span
    rows = [start]
    cursor = start
    for i in range(1, n - 1):
        frac = i / (n - 1)
        base = 10 + int(28 * (0.25 + abs(frac - 0.5)))
        gap = base + random.choice([0, 0, 4, 9, 14, 40, 70])
        cursor += gap
        rows.append(min(end - (n - i) * 8, cursor))
    rows.append(end)
    for i in range(1, n):
        if rows[i] <= rows[i - 1]:
            rows[i] = rows[i - 1] + random.randint(8, 16)
    rows[-1] = max(rows[-1], rows[-2] + 12)
    return rows


def arc_points(arc: list, index: int, n: int, border: float) -> list[tuple[float, float]]:
    chosen = [round(i * index / (n - 1)) for i in range(n)]
    coords = []
    for point_index in chosen:
        x = border + arc[point_index][0] * SCALE
        y = border + OFFSET_Y + arc[point_index][1] * SCALE
        coords.append((x, y))
    return coords


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        arc = cap["arc_path"]["points"]
        index = 60
        distance = int(round((index + 0.5) / 99 * MAX_DRAG))
        rotation = distance / MAX_DRAG * 360
        plans = {}
        stamp = times(70, 1400)
        plans["arc70"] = [
            {"x": x, "y": y, "t": t} for (x, y), t in zip(arc_points(arc, index, 70, 2), stamp)
        ]
        plans["arc0"] = [
            {"x": x, "y": y, "t": t} for (x, y), t in zip(arc_points(arc, index, 70, 0), times(70, 1500))
        ]
        wild_t = times(70, 1400)
        plans["wild"] = [
            {"x": i * distance / 69, "y": random.uniform(20, 220), "t": wild_t[i]} for i in range(70)
        ]
        image_t = times(70, 1600)
        chosen = [round(i * index / 69) for i in range(70)]
        plans["image"] = [
            {"x": arc[point][0], "y": arc[point][1], "t": image_t[i]} for i, point in enumerate(chosen)
        ]
        plans["button"] = [
            {"x": i * distance / 69, "y": 25 + math.sin(i) * 1.5, "t": t}
            for i, t in enumerate(times(70, 1300))
        ]
        for name, rows in plans.items():
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
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
            response = client.post("/captcha/api/cap7_challenge/page/", content=json.dumps(body, separators=(",", ":")))
            payload = response.json()
            print(name, "n", len(rows), "ok", payload.get("success"), "error", payload.get("error"))


if __name__ == "__main__":
    main()
