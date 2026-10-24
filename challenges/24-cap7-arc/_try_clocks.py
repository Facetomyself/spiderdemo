"""Sweep drag clocks through the real page recorder."""

from __future__ import annotations

import base64
import json
import random
import time

from modules.runtime import SpiderSession

from _try_liveclient import HEADERS, client_track

DISTANCE = 160


def ease_events(duration: int, frame: float, jitter: float, steps: int) -> list[list[float]]:
    events = []
    for i in range(1, steps + 1):
        frac = i / steps
        eased = frac * frac * (3 - 2 * frac)
        gap = max(6, int(random.gauss(frame, jitter)))
        events.append([gap, round(eased * DISTANCE, 3)])
    events[-1][1] = DISTANCE
    return events


def clocks() -> dict[str, list[list[float]]]:
    random.seed(7)
    linear = []
    cursor = 0.0
    while cursor < DISTANCE:
        cursor = min(DISTANCE, cursor + random.uniform(2.5, 7.5))
        linear.append([random.randint(12, 48), round(cursor, 3)])
    slow = []
    for i in range(1, 36):
        frac = i / 35
        gap = int(28 + 50 * (frac - 0.5) ** 2 + random.randint(-4, 6))
        eased = frac * frac * (3 - 2 * frac)
        slow.append([gap, round(eased * DISTANCE, 3)])
    slow[-1][1] = DISTANCE
    return {
        "gauss16": ease_events(1100, 16, 3.5, 70),
        "tight16": ease_events(900, 16, 0.8, 55),
        "linear": linear,
        "slow": slow,
        "fast": ease_events(420, 11, 4, 32),
        "long": ease_events(2400, 28, 8, 80),
    }


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for name, events in clocks().items():
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            start_ms = int(time.time() * 1000) + 40
            info = client_track(cap["arc_path"]["points"], DISTANCE, start_ms, events)
            encoded = info.get("b64")
            if not encoded:
                print(name, "nosim", info.get("jserr"), info.get("stderr"))
                continue
            raw = json.loads(base64.b64decode(encoded))
            wait = int(raw[-1]["t"]) + 80 - int(time.time() * 1000)
            if wait > 0:
                time.sleep(wait / 1000)
            body = {
                "distance": DISTANCE,
                "trajectory_encoded": encoded,
                "rotation_angle": DISTANCE / (400 - 120 * 400 / 840) * 360.0,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": cap["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(
                name,
                "stat",
                info.get("stat"),
                "delta",
                info.get("delta"),
                "ok",
                payload.get("success"),
                "error",
                payload.get("error"),
            )


if __name__ == "__main__":
    main()
