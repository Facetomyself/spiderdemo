"""17 equally spaced arc points and the fixed interval sample."""

from __future__ import annotations

import base64
import io
import json
import math
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
DELTAS = [78, 51, 1, 156, 59, 29, 42, 36, 32, 39, 49, 84, 56, 29, 97, 825]


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
    coarse = max(range(0, 360, 6), key=lambda angle: score_at(small_bg, small_piece, angle)[0])
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse - 8, coarse + 9):
        value, x, y = score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def samples(arc: np.ndarray, index: int) -> np.ndarray:
    segment = arc[: index + 1]
    step = np.hypot(np.diff(segment[:, 0]), np.diff(segment[:, 1]))
    length = np.concatenate([[0.0], np.cumsum(step)])
    if length[-1] <= 0:
        return np.repeat(segment[:1], 17, axis=0)
    targets = np.linspace(0, length[-1], 17)
    cols = []
    for target in targets:
        pos = int(np.searchsorted(length, target, side="right") - 1)
        pos = min(max(pos, 0), len(segment) - 2)
        span = length[pos + 1] - length[pos]
        frac = 0 if span <= 0 else (target - length[pos]) / span
        cols.append(segment[pos] * (1 - frac) + segment[pos + 1] * frac)
    return np.vstack(cols)


def track(kind: str, arc: np.ndarray, index: int, start: int) -> list[dict]:
    pts = samples(arc, index)
    rows = []
    cursor = start
    for nth, point in enumerate(pts):
        px, py = float(point[0]), float(point[1])
        if kind == "image":
            x, y = px, py
        elif kind == "display":
            x, y = px * SCALE, OFFSET_Y + py * SCALE
        else:
            x, y = 2 + px * SCALE, 2 + OFFSET_Y + py * SCALE
        rows.append({"x": x, "y": y, "t": cursor})
        if nth < len(DELTAS):
            cursor += DELTAS[nth]
    return rows


def encode(points: list) -> str:
    return base64.b64encode(json.dumps(points, separators=(",", ":")).encode()).decode()


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for kind in ("plus2", "display", "image"):
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            value, angle, x, y = best_pose(bg, piece)
            found = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
            index = int(np.argmin(np.hypot(*(arc - found).T)))
            gap = float(np.hypot(*(arc[index] - found)))
            if value < 0.8 or gap > 3 or not 8 <= index <= 91:
                print("skip", kind, "score", round(value, 3), "gap", round(gap, 2), "idx", index)
                continue
            ratio = index / 99
            rows = track(kind, arc, index, int(time.time() * 1000) + 40)
            if kind == "image":
                distance = rows[-1]["x"] - rows[0]["x"]
                tangent = arc[min(index + 1, 99)] - arc[max(index - 1, 0)]
                rotation = math.degrees(math.atan2(float(tangent[1]), float(tangent[0])))
            else:
                distance = ratio * MAX_DRAG
                rotation = ratio * 360
            wait = rows[-1]["t"] + 80 - int(time.time() * 1000)
            if wait > 0:
                time.sleep(wait / 1000)
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
                kind,
                "score",
                round(value, 3),
                "idx",
                index,
                "gap",
                round(gap, 2),
                "dist",
                round(distance, 2),
                "rot",
                round(rotation, 2),
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
