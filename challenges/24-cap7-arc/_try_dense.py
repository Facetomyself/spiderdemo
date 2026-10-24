"""One-page probes: dense client centers versus a bad angle control."""

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


def rotate(piece: np.ndarray, angle: float) -> np.ndarray:
    height, width = piece.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        piece,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


def _score(bg: np.ndarray, piece: np.ndarray, angle: int) -> tuple[float, int, int]:
    turned = rotate(piece, angle)
    mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
    if int(mask.sum()) < 50:
        return -1.0, 0, 0
    score = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
    _, value, _, loc = cv2.minMaxLoc(score)
    return float(value), int(loc[0]), int(loc[1])


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int, int]:
    small_bg = cv2.resize(bg, (420, 270), interpolation=cv2.INTER_AREA)
    small_piece = cv2.resize(piece, (60, 50), interpolation=cv2.INTER_AREA)
    coarse = (-1.0, 0)
    for angle in range(0, 360, 6):
        value, _, _ = _score(small_bg, small_piece, angle)
        if value > coarse[0]:
            coarse = (value, angle)
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse[1] - 8, coarse[1] + 9):
        value, x, y = _score(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def encode(points: list[dict]) -> str:
    raw = json.dumps(points, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def scale_of(info: dict) -> tuple[float, float, float, float]:
    scale = max(400 / info["bg_width"], 240 / info["bg_height"])
    offset_x = (400 - info["bg_width"] * scale) / 2
    offset_y = (240 - info["bg_height"] * scale) / 2
    max_drag = 400 - info["mask_width"] * scale
    return scale, offset_x, offset_y, max_drag


def build(arc: np.ndarray, index: int, info: dict, kind: str) -> tuple[list[dict], float, float]:
    scale, offset_x, offset_y, max_drag = scale_of(info)
    progress = min(0.999, (index + 0.45) / (len(arc) - 1))
    distance = float(round(progress * max_drag))
    progress = min(1.0, distance / max_drag)
    snapped = min(len(arc) - 1, int(math.floor(progress * (len(arc) - 1))))
    rotation = progress * 360.0
    if kind == "badangle":
        rotation = (rotation + 140.0) % 360.0
    border = 2.0 if kind == "border" else 0.0
    centers = np.column_stack(
        (
            offset_x + border + arc[:, 0] * scale,
            offset_y + border + arc[:, 1] * scale,
        )
    )
    span = random.randint(980, 1460)
    now = int(time.time() * 1000)
    rows: list[dict] = []
    previous = None
    last_t = now - 30
    steps = list(range(0, int(distance) + 1, 2))
    if steps[-1] != int(distance):
        steps.append(int(distance))
    for step_i, drag in enumerate(steps):
        frac = drag / max(1, int(distance))
        # Inverse smoothstep so the middle of the drag is faster.
        time_frac = 0.5 - math.sin(math.asin(1 - 2 * frac) / 3)
        point_index = min(len(arc) - 1, int(math.floor(min(1.0, drag / max_drag) * (len(arc) - 1))))
        if kind == "button":
            x = 25.0 + drag
            y = 25.0
        else:
            x = float(centers[point_index, 0])
            y = float(centers[point_index, 1])
        if previous is not None and math.hypot(x - previous[0], y - previous[1]) < 3.4:
            continue
        stamp = now + int(time_frac * span) + random.randint(-3, 6)
        stamp = max(last_t + random.randint(11, 28), stamp)
        rows.append({"x": round(x, 4), "y": round(y, 4), "t": stamp})
        previous = (x, y)
        last_t = stamp
    if kind != "badangle":
        rotation = progress * 360.0
    _ = snapped
    return rows, distance, rotation


def main() -> None:
    random.seed()
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        init = client.get("/captcha/api/cap7_challenge/init/?challenge_type=cap7_challenge").json()
        print(
            "init",
            init.get("success"),
            "pages",
            init.get("total_pages"),
            "have",
            len(init.get("page_data") or []),
            "passed",
            init.get("has_passed_before"),
        )
        for kind in ("center", "border", "button", "badangle"):
            started = time.time()
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            info = cap["image_info"]
            value, angle, x, y = best_pose(bg, piece)
            center = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
            nearest = int(np.argmin(np.hypot(*(arc - center).T)))
            gap = float(np.hypot(*(arc[nearest] - center)))
            rows, distance, rotation = build(arc, nearest, info, kind)
            duration = rows[-1]["t"] - rows[0]["t"]
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
                kind,
                "match",
                round(value, 3),
                "angle",
                angle,
                "arc",
                nearest,
                "gap",
                round(gap, 2),
                "dy",
                abs(y - int(cap.get("slider_y") or 0)),
                "n",
                len(rows),
                "ms",
                duration,
                "dist",
                distance,
                "rot",
                round(rotation, 2),
                "http",
                response.status_code,
                "ok",
                payload.get("success"),
                "error",
                payload.get("error"),
                "keys",
                sorted(payload.keys()),
                "sec",
                round(time.time() - started, 1),
            )
            if payload.get("success") is True:
                data = payload.get("page_data")
                print("unlocked", type(data).__name__, len(data) if isinstance(data, list) else "")
                break


if __name__ == "__main__":
    main()
