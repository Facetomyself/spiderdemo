"""Matched pose, client arc, timestamps after the captcha was issued."""

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
    for angle in range(coarse[1] - 8, coarse[1] + 9):
        value, x, y = score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def locate(arc: np.ndarray, drag: float) -> tuple[float, float]:
    progress = min(1.0, max(0.0, drag / MAX_DRAG))
    index = min(99, int(math.floor(progress * 99)))
    return 2 + float(arc[index, 0]) * SCALE, 2 + OFFSET_Y + float(arc[index, 1]) * SCALE


def track(arc: np.ndarray, distance: int, start: int) -> list[dict]:
    rows = []
    previous = None
    cursor = start
    drag = 0.0
    while drag < distance - 0.4 and len(rows) < 42:
        frac = drag / distance
        pace = 0.55 + 2.1 * math.sin(math.pi * frac) ** 1.2
        drag = min(distance, drag + pace * random.uniform(2.2, 4.4))
        x, y = locate(arc, drag)
        if previous is not None and math.hypot(x - previous[0], y - previous[1]) < 3:
            cursor += random.randint(14, 28)
            continue
        rows.append({"x": x, "y": y, "t": cursor})
        previous = (x, y)
        cursor += random.randint(12, 36) if 0.15 < frac < 0.85 else random.randint(24, 55)
    x, y = locate(arc, distance)
    if not rows or math.hypot(rows[-1]["x"] - x, rows[-1]["y"] - y) >= 3:
        rows.append({"x": x, "y": y, "t": cursor})
    else:
        rows[-1]["x"], rows[-1]["y"], rows[-1]["t"] = x, y, cursor
    return rows


def encode(points: list) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def choose(index: int, angle: int) -> int:
    lo = max(1, math.ceil(index / 99 * MAX_DRAG - 1e-9))
    hi = min(int(MAX_DRAG), math.floor((index + 1) / 99 * MAX_DRAG - 1e-9))
    if hi < lo:
        hi = lo
    return min(range(lo, hi + 1), key=lambda item: abs(item - angle / 360 * MAX_DRAG))


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for attempt in range(3):
            response = client.get("/captcha/api/cap7_challenge/captcha_image/")
            cap = response.json()
            fetched = int(time.time() * 1000)
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            value, angle, x, y = best_pose(bg, piece)
            found = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
            index = int(np.argmin(np.hypot(*(arc - found).T)))
            gap = float(np.hypot(*(arc[index] - found)))
            distance = choose(index, angle)
            rows = track(arc, distance, fetched + 40)
            delta = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, len(rows))]
            wait = rows[-1]["t"] + 70 - int(time.time() * 1000)
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
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(
                "try",
                attempt,
                "score",
                round(value, 3),
                "dy",
                int(y - cap["slider_y"]),
                "gap",
                round(gap, 2),
                "angle",
                angle,
                "arc",
                index,
                "dist",
                distance,
                "n",
                len(rows),
                "std",
                round(statistics.pstdev(delta), 2) if len(delta) > 1 else 0,
                "span",
                rows[-1]["t"] - rows[0]["t"],
                "ok",
                payload.get("success"),
                "error",
                payload.get("error"),
                "msg",
                payload.get("message"),
            )
            if payload.get("success") or (payload.get("error") and "重新操作" not in str(payload.get("error")) and "正常拖动" not in str(payload.get("error"))):
                if payload.get("success"):
                    print("unlocked", len(payload.get("page_data") or []))
                break


if __name__ == "__main__":
    main()
