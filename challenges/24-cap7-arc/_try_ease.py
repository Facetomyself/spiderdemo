"""Physics ease track on the client arc."""

from __future__ import annotations

import base64
import io
import json
import math
import random
import statistics
import time

import cv2
import numpy as np
from PIL import Image

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


def rotate(piece: np.ndarray, angle: float) -> np.ndarray:
    height, width = piece.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        piece, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )


def score_at(bg: np.ndarray, piece: np.ndarray, angle: int) -> tuple[float, int, int]:
    turned = rotate(piece, angle)
    mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
    if int(mask.sum()) < 40:
        return -1.0, 0, 0
    scored = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
    _, value, _, loc = cv2.minMaxLoc(scored)
    return float(value), int(loc[0]), int(loc[1])


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int, int]:
    small_bg = cv2.resize(bg, (420, 270), interpolation=cv2.INTER_AREA)
    small_piece = cv2.resize(piece, (60, 50), interpolation=cv2.INTER_AREA)
    coarse = max((score_at(small_bg, small_piece, angle)[0], angle) for angle in range(0, 360, 6))
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse[1] - 6, coarse[1] + 7):
        value, x, y = score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def locate(arc: np.ndarray, drag: float) -> tuple[float, float]:
    progress = min(1.0, max(0.0, drag / MAX_DRAG))
    index = min(99, int(math.floor(progress * 99)))
    return 2 + float(arc[index, 0]) * SCALE, 2 + OFFSET_Y + float(arc[index, 1]) * SCALE


def physics(arc: np.ndarray, distance: int) -> list[dict]:
    rows = []
    current = 0.0
    velocity = 0.0
    elapsed = 0
    mid = distance * 0.72
    previous = None
    while current < distance - 0.5 and len(rows) < 48:
        accel = random.uniform(1.6, 2.4) if current < mid else random.uniform(-3.2, -1.8)
        velocity = max(0.4, velocity + accel)
        current = min(distance, current + velocity)
        elapsed += random.randint(12, 22)
        x, y = locate(arc, current)
        if previous is not None and math.hypot(x - previous[0], y - previous[1]) < 3:
            continue
        rows.append((x, y, elapsed))
        previous = (x, y)
    x, y = locate(arc, distance)
    if not rows or math.hypot(rows[-1][0] - x, rows[-1][1] - y) >= 3:
        rows.append((x, y, elapsed + random.randint(16, 28)))
    end = int(time.time() * 1000) - 40
    start = end - rows[-1][2]
    return [{"x": item[0], "y": item[1], "t": start + item[2]} for item in rows]


def smooth(arc: np.ndarray, distance: int) -> list[dict]:
    rows = []
    previous = None
    samples = []
    duration = 1280
    for tick in range(0, duration + 1, 16):
        frac = tick / duration
        eased = frac * frac * (3 - 2 * frac)
        samples.append((tick, min(distance, eased * distance)))
    samples.append((duration, distance))
    for tick, drag in samples:
        x, y = locate(arc, drag)
        if previous is not None and math.hypot(x - previous[0], y - previous[1]) < 3:
            continue
        rows.append((x, y, tick))
        previous = (x, y)
        if len(rows) >= 50:
            break
    end = int(time.time() * 1000) - 40
    start = end - rows[-1][2]
    return [{"x": item[0], "y": item[1], "t": start + item[2]} for item in rows]


def encode(points: list[dict]) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for name, builder in (("physics", physics), ("smooth", smooth)):
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            value, angle, x, y = best_pose(bg, piece)
            found = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
            index = int(np.argmin(np.hypot(*(arc - found).T)))
            lo = max(1, math.ceil(index / 99 * MAX_DRAG - 1e-9))
            hi = min(int(MAX_DRAG), math.floor((index + 1) / 99 * MAX_DRAG - 1e-9))
            if hi < lo:
                hi = lo
            distance = min(range(lo, hi + 1), key=lambda item: abs(item - angle / 360 * MAX_DRAG))
            rows = builder(arc, distance)
            delta = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, len(rows))]
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
            print(
                name,
                "match",
                round(value, 3),
                "arc",
                index,
                "dist",
                distance,
                "n",
                len(rows),
                "span",
                rows[-1]["t"] - rows[0]["t"],
                "std",
                round(statistics.pstdev(delta), 2) if len(delta) > 1 else 0,
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
