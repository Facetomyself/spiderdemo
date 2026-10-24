"""See whether a mixed on-arc track reaches the deviation counter."""

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
GAPS = [19, 27, 16, 24, 33, 18, 29, 21, 36, 17, 26, 22, 31, 20, 28, 15, 34, 23, 18, 30, 21, 27, 16, 25]


def encode(points: list) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def point_at(kind: str, arc: list, index: int) -> tuple[float, float]:
    px, py = arc[index]
    if kind == "image":
        return float(px), float(py)
    if kind == "button":
        return index / 99 * MAX_DRAG, 25.0
    return 2 + float(px) * SCALE, 2 + OFFSET_Y + float(py) * SCALE


def build(kind: str, arc: list, start: int, spoil: bool) -> list[dict]:
    indexes = list(range(0, 100, 4))
    rows = []
    cursor = start
    for nth, index in enumerate(indexes):
        x, y = point_at(kind, arc, index)
        if spoil and nth % 2 == 0:
            y += 90
        rows.append({"x": round(x, 3), "y": round(y, 3), "t": cursor})
        if nth < len(GAPS):
            cursor += GAPS[nth]
    return rows


def main() -> None:
    delta = GAPS
    print("std", round(statistics.pstdev(delta), 2), "span", sum(delta))
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for kind in ("display", "image", "button"):
            for spoil in (False, True):
                cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
                fetched = int(time.time() * 1000)
                rows = build(kind, cap["arc_path"]["points"], fetched + 50, spoil)
                wait = rows[-1]["t"] + 60 - int(time.time() * 1000)
                if wait > 0:
                    time.sleep(wait / 1000)
                distance = 180
                body = {
                    "distance": distance,
                    "trajectory_encoded": encode(rows),
                    "rotation_angle": distance / MAX_DRAG * 360.0,
                    "page_num": 2,
                    "challenge_type": "cap7_challenge",
                    "captcha_id": cap["captcha_id"],
                    "container_width": 400,
                    "container_height": 240,
                }
                payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
                print(kind, "spoil" if spoil else "exact", "error", payload.get("error"), "msg", payload.get("message"), "ok", payload.get("success"))


if __name__ == "__main__":
    main()
