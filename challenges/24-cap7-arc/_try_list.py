"""Object versus array trajectory points."""

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


def encode(points: list) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        plans = {
            "obj_uniform": "obj",
            "arr_uniform": "arr",
            "arr_ease": "arr_ease",
            "obj_int": "int",
        }
        for name, kind in plans.items():
            fresh = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            n = 24
            end = int(time.time() * 1000) - 40
            rows = []
            cursor = end - (36 * (n - 1) if "ease" not in kind else 1100)
            for i in range(n):
                frac = i / (n - 1)
                eased = frac * frac * (3 - 2 * frac)
                x = round(eased * 180, 3)
                y = round(120 + (1 - frac) * 6, 3)
                if kind == "int":
                    x, y = int(x), int(y)
                stamp = end - int((1 - (frac if "ease" not in kind else eased)) * 1000) if "ease" in kind else cursor
                if kind == "arr_uniform":
                    rows.append([x, y, cursor])
                elif kind == "arr_ease":
                    rows.append([x, y, stamp])
                else:
                    rows.append({"x": x, "y": y, "t": stamp if "ease" in kind else cursor})
                cursor += 36
            body = {
                "distance": 180,
                "trajectory_encoded": encode(rows),
                "rotation_angle": 180,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": fresh["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(name, payload.get("error"))


if __name__ == "__main__":
    main()
