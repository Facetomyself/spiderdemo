"""Same timing seed, three coordinate spaces."""

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
    coarse = max(((score_at(small_bg, small_piece, angle)[0], angle) for angle in range(0, 360, 6)))
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse[1] - 6, coarse[1] + 7):
        value, x, y = score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def gaps(n: int, rng: random.Random) -> list[int]:
    values = []
    for i in range(n - 1):
        frac = i / (n - 2)
        if frac < 0.12 or frac > 0.86:
            values.append(rng.randint(24, 36))
        elif rng.random() < 0.12:
            values.append(rng.randint(42, 68))
        else:
            values.append(rng.randint(11, 18))
    return values


def stamps(n: int, rng: random.Random) -> list[int]:
    step = gaps(n, rng)
    end = int(time.time() * 1000) - 50
    start = end - sum(step)
    rows = [start]
    for item in step:
        rows.append(rows[-1] + item)
    return rows


def encode(points: list[dict]) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for name in ("plus2", "shifted", "image"):
            rng = random.Random(7)
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            value, angle, x, y = best_pose(bg, piece)
            found = np.array([x + piece.shape[1] / 2.0, y + piece.shape[0] / 2.0])
            index = int(np.argmin(np.hypot(*(arc - found).T)))
            lo = math.ceil(index / 99 * MAX_DRAG - 1e-9)
            hi = math.floor((index + 1) / 99 * MAX_DRAG - 1e-9)
            distance = int(min(range(max(1, lo), max(lo, hi) + 1), key=lambda item: abs(item - angle / 360 * MAX_DRAG)))
            rotation = distance / MAX_DRAG * 360.0
            n = 36
            chosen = [min(99, round(i * index / (n - 1))) for i in range(n)]
            clock = stamps(n, rng)
            rows = []
            for point_index, stamp in zip(chosen, clock):
                if name == "image":
                    px, py = float(arc[point_index, 0]), float(arc[point_index, 1])
                else:
                    px = float(arc[point_index, 0]) * SCALE + (2 if name == "plus2" else 0)
                    py = OFFSET_Y + float(arc[point_index, 1]) * SCALE + (2 if name == "plus2" else 0)
                    if name == "shifted":
                        py += 22
                rows.append({"x": px, "y": py, "t": stamp})
            delta = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, n)]
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
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(
                name,
                "match",
                round(value, 3),
                "arc",
                index,
                "dist",
                distance,
                "rot",
                round(rotation, 2),
                "std",
                round(statistics.pstdev(delta), 2),
                "span",
                rows[-1]["t"] - rows[0]["t"],
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
