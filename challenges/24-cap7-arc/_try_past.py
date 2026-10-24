"""Client arc centers with timestamps entirely before the POST."""

from __future__ import annotations

import base64
import io
import json
import math
import random
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
    if int(mask.sum()) < 50:
        return -1.0, 0, 0
    scored = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
    _, value, _, loc = cv2.minMaxLoc(scored)
    return float(value), int(loc[0]), int(loc[1])


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int, int]:
    small_bg = cv2.resize(bg, (420, 270), interpolation=cv2.INTER_AREA)
    small_piece = cv2.resize(piece, (60, 50), interpolation=cv2.INTER_AREA)
    coarse_value, coarse_angle = -1.0, 0
    for angle in range(0, 360, 6):
        value, _, _ = score_at(small_bg, small_piece, angle)
        if value > coarse_value:
            coarse_value, coarse_angle = value, angle
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse_angle - 6, coarse_angle + 7):
        value, x, y = score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def choose_distance(index: int) -> int:
    lo = max(1, math.ceil(index / 99 * MAX_DRAG - 1e-9))
    hi = min(int(MAX_DRAG), math.floor((index + 1) / 99 * MAX_DRAG - 1e-9))
    if hi < lo:
        hi = lo
    return (lo + hi) // 2


def center(arc: np.ndarray, drag: float, border: float) -> tuple[float, float]:
    progress = min(1.0, drag / MAX_DRAG)
    index = min(99, int(math.floor(progress * 99)))
    return (
        border + float(arc[index, 0]) * SCALE,
        border + OFFSET_Y + float(arc[index, 1]) * SCALE,
    )


def track(arc: np.ndarray, distance: int, border: float) -> list[dict]:
    duration = random.randint(900, 1500)
    end = int(time.time() * 1000) - random.randint(40, 120)
    start = end - duration
    rows: list[dict] = []
    previous = None
    cursor = start
    drag = 0.0
    guard = 0
    while drag < distance and guard < 400:
        guard += 1
        frac = drag / distance
        pace = 0.45 + 2.2 * math.sin(frac * math.pi) ** 1.3
        drag = min(distance, drag + max(1.4, pace * random.uniform(1.5, 3.2)))
        x, y = center(arc, drag, border)
        if previous is not None and math.hypot(x - previous[0], y - previous[1]) < 3.05:
            continue
        if frac < 0.1 or frac > 0.88:
            gap = random.randint(18, 42)
        elif random.random() < 0.1:
            gap = random.randint(50, 120)
        else:
            gap = random.randint(8, 20)
        cursor = min(end - 15, cursor + gap)
        rows.append({"x": x, "y": y, "t": cursor})
        previous = (x, y)
    final = center(arc, distance, border)
    if not rows or math.hypot(rows[-1]["x"] - final[0], rows[-1]["y"] - final[1]) >= 3:
        rows.append({"x": final[0], "y": final[1], "t": end})
    else:
        rows[-1]["x"], rows[-1]["y"], rows[-1]["t"] = final[0], final[1], end
    return rows


def encode(points: list[dict]) -> str:
    raw = json.dumps(points, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for border in (2.0, 0.0):
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            value, angle, x, y = best_pose(bg, piece)
            found = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
            index = int(np.argmin(np.hypot(*(arc - found).T)))
            gap = float(np.hypot(*(arc[index] - found)))
            distance = choose_distance(index)
            rotation = distance / MAX_DRAG * 360.0
            rows = track(arc, distance, border)
            ahead = rows[-1]["t"] - int(time.time() * 1000)
            body = {
                "distance": distance,
                "trajectory_encoded": encode(rows),
                "rotation_angle": rotation,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": cap["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            response = client.post("/captcha/api/cap7_challenge/page/", json=body)
            payload = response.json()
            print(
                "border",
                border,
                "match",
                round(value, 3),
                "angle",
                angle,
                "arc",
                index,
                "gap",
                round(gap, 2),
                "dy",
                abs(int(cap["slider_y"]) - y),
                "dist",
                distance,
                "rot",
                round(rotation, 2),
                "n",
                len(rows),
                "span",
                rows[-1]["t"] - rows[0]["t"],
                "ahead",
                ahead,
                "ok",
                payload.get("success"),
                "error",
                payload.get("error"),
            )
            if payload.get("success"):
                print("unlocked", len(payload.get("page_data") or []))
                break


if __name__ == "__main__":
    main()
