"""Differential trajectory shapes. No image matching."""

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
}


def encode(points: list[dict]) -> str:
    raw = json.dumps(points, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def stamps(n: int, span: int, jitter: bool) -> list[int]:
    now = int(time.time() * 1000)
    rows = []
    last = now
    for i in range(n):
        frac = i / max(1, n - 1)
        base = now + int(frac * span)
        if jitter:
            base += random.randint(-4, 9)
        base = max(last + (random.randint(8, 24) if jitter else 16), base)
        rows.append(base)
        last = base
    return rows


def line(n: int, span: int, x0: float, x1: float, y0: float, y1: float, jitter: bool, t0: int | None = None) -> list[dict]:
    times = stamps(n, span, jitter)
    if t0 is not None:
        times = [t0 + (item - times[0]) for item in times]
    rows = []
    for i, stamp in enumerate(times):
        frac = i / max(1, n - 1)
        rows.append({"x": round(x0 + (x1 - x0) * frac, 3), "y": round(y0 + (y1 - y0) * frac, 3), "t": stamp})
    return rows


def arc_like(n: int, span: int) -> list[dict]:
    times = stamps(n, span, True)
    rows = []
    for i, stamp in enumerate(times):
        frac = i / max(1, n - 1)
        x = 84 + frac * 160
        y = 115 + math.sin(frac * math.pi) * -12
        rows.append({"x": round(x, 3), "y": round(y, 3), "t": stamp})
    return rows


def main() -> None:
    session = SpiderSession()
    shapes = {
        "short_uniform": line(12, 200, 0, 180, 120, 120, False),
        "human_xdist": line(48, 1100, 0, 180, 120, 108, True),
        "human_from0": line(48, 1100, 0, 180, 120, 108, True, t0=0),
        "human_seconds": None,
        "arc48": arc_like(48, 1200),
        "few": line(4, 900, 0, 180, 100, 110, True),
        "backtrack": None,
    }
    human = line(40, 1000, 20, 200, 100, 130, True)
    back = human[:-3] + [
        {"x": human[-3]["x"] - 8, "y": human[-3]["y"] + 1, "t": human[-3]["t"] + 40},
        {"x": human[-1]["x"], "y": human[-1]["y"], "t": human[-1]["t"] + 80},
    ]
    shapes["backtrack"] = back
    seconds = line(40, 1200, 0, 180, 110, 120, True)
    shapes["human_seconds"] = [
        {"x": row["x"], "y": row["y"], "t": round(row["t"] / 1000, 3)} for row in seconds
    ]
    with session.client(headers=HEADERS) as client:
        cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        print("cap_keys", sorted(cap.keys()))
        print("arc_n", len(cap["arc_path"]["points"]), "info_keys", sorted(cap["image_info"].keys()))
        for name, rows in shapes.items():
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            body = {
                "distance": 180,
                "trajectory_encoded": encode(rows),
                "rotation_angle": 90,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            response = client.post("/captcha/api/cap7_challenge/page/", json=body)
            payload = response.json()
            print(name, "n", len(rows), "http", response.status_code, "ok", payload.get("success"), "error", payload.get("error"))
        _ = cap


if __name__ == "__main__":
    main()
