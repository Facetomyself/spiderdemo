"""Post tracks whose timestamps sit after the captcha response."""

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
SLIDER_W = 120 * SCALE
SLIDER_H = 100 * SCALE


def encode(points: list[dict]) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def gaps() -> list[int]:
    raw = []
    for i in range(28):
        frac = i / 27
        base = 16 + int(28 * (frac - 0.45) ** 2)
        raw.append(base + ((i * 7) % 5) - 2)
    return raw


def place(kind: str, arc: list, drag: float) -> tuple[float, float]:
    progress = min(1.0, max(0.0, drag / MAX_DRAG))
    index = min(99, int(progress * 99))
    px, py = arc[index]
    if kind == "image":
        return float(px), float(py)
    cx = float(px) * SCALE
    cy = OFFSET_Y + float(py) * SCALE
    if kind == "topleft":
        return cx - SLIDER_W / 2, cy - SLIDER_H / 2
    border = 2.0 if kind == "plus2" else 0.0
    return border + cx, border + cy


def build(kind: str, arc: list, distance: int, start: int) -> list[dict]:
    rows = []
    cursor = start
    step = distance / 28
    for i, gap in enumerate(gaps()):
        drag = min(distance, step * i)
        x, y = place(kind, arc, drag)
        rows.append({"x": round(x, 4), "y": round(y, 4), "t": cursor})
        cursor += gap
    x, y = place(kind, arc, distance)
    rows.append({"x": round(x, 4), "y": round(y, 4), "t": cursor})
    return rows


def post(client, cap: dict, rows: list[dict], distance: int) -> dict:
    last = rows[-1]["t"]
    wait = last + 80 - int(time.time() * 1000)
    if wait > 0:
        time.sleep(wait / 1000)
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
    response = client.post("/captcha/api/cap7_challenge/page/", json=body)
    if response.status_code == 429:
        time.sleep(2)
        response = client.post("/captcha/api/cap7_challenge/page/", json=body)
    try:
        payload = response.json()
    except Exception:
        payload = {"error": f"http {response.status_code}"}
    return payload


def main() -> None:
    session = SpiderSession()
    distance = 180
    with session.client(headers=HEADERS) as client:
        for kind in ("plus2", "border0", "image", "topleft", "plus2-past"):
            response = client.get("/captcha/api/cap7_challenge/captcha_image/")
            cap = response.json()
            fetched = int(time.time() * 1000)
            arc = cap["arc_path"]["points"]
            if kind.endswith("past"):
                rows = build("plus2", arc, distance, fetched - 1400)
            else:
                rows = build(kind, arc, distance, fetched + 60)
            delta = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, len(rows))]
            payload = post(client, cap, rows, distance)
            posted = int(time.time() * 1000)
            print(
                kind,
                "n",
                len(rows),
                "std",
                round(statistics.pstdev(delta), 2),
                "lead",
                rows[0]["t"] - fetched,
                "lag",
                posted - rows[-1]["t"],
                "keys",
                ",".join(payload.keys()),
                "ok",
                payload.get("success"),
                "error",
                payload.get("error"),
                "msg",
                payload.get("message"),
            )
            if payload.get("success"):
                print("unlocked", len(payload.get("page_data") or []))
                break


if __name__ == "__main__":
    main()
