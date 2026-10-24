"""Try trajectory coordinate systems until the site accepts one page."""

from __future__ import annotations

import base64
import io
import json
import random
import time

import cv2
import numpy as np
from PIL import Image

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"


def rotate(piece: np.ndarray, angle: float) -> np.ndarray:
    height, width = piece.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(piece, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int]:
    best = (-1.0, 0, (0, 0))
    for angle in range(0, 360, 5):
        turned = rotate(piece, angle)
        mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
        score = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
        _, value, _, loc = cv2.minMaxLoc(score)
        if value > best[0]:
            best = (float(value), angle, (int(loc[0]), int(loc[1])))
    coarse = best[1]
    for angle in range(coarse - 4, coarse + 5):
        turned = rotate(piece, angle % 360)
        mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
        score = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
        _, value, _, loc = cv2.minMaxLoc(score)
        if value > best[0]:
            best = (float(value), angle % 360, (int(loc[0]), int(loc[1])))
    return best[0], best[1], best[2][0], best[2][1]


def encode(points: list[dict]) -> str:
    raw = json.dumps(points, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def build(kind: str, arc: np.ndarray, index: int, info: dict, distance: float) -> list[dict]:
    indexes = list(range(0, index + 1, max(1, index // 18)))
    if indexes[-1] != index:
        indexes.append(index)
    now = int(time.time() * 1000)
    rows = []
    if kind == "image":
        coords = [(float(arc[i][0]), float(arc[i][1])) for i in indexes]
    elif kind == "container400":
        coords = _container(arc, indexes, info, 400, 240, 0)
    elif kind == "container396":
        coords = _container(arc, indexes, info, 396, 236, 0)
    elif kind == "border":
        coords = _container(arc, indexes, info, 396, 236, 2)
    elif kind == "button":
        coords = []
        for step, i in enumerate(indexes):
            progress = i / (len(arc) - 1)
            coords.append((25 + progress / (index / (len(arc) - 1)) * distance, 280))
    else:
        raise ValueError(kind)
    span = 2600
    for step, (x, y) in enumerate(coords):
        frac = step / max(1, len(coords) - 1)
        # Ease-in-out timing, still monotonic.
        eased = frac * frac * (3 - 2 * frac)
        rows.append({"x": round(x, 2), "y": round(y, 2), "t": now + int(eased * span)})
    return rows


def _container(arc, indexes, info, width, height, border):
    scale = max(width / info["bg_width"], height / info["bg_height"])
    offset_x = (width - info["bg_width"] * scale) / 2 + border
    offset_y = (height - info["bg_height"] * scale) / 2 + border
    return [(offset_x + float(arc[i][0]) * scale, offset_y + float(arc[i][1]) * scale) for i in indexes]


def main() -> None:
    random.seed(1)
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER, "Accept": "application/json"}) as client:
        print("init", client.get("/captcha/api/cap7_challenge/init/?challenge_type=cap7_challenge").status_code)
        for kind in ("image", "container400", "container396", "border", "button"):
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            arc = np.array(cap["arc_path"]["points"], dtype=np.float64)
            info = cap["image_info"]
            value, angle, x, y = best_pose(bg, piece)
            height, width = piece.shape[:2]
            center = np.array([x + width / 2, y + height / 2])
            dist = np.hypot(*(arc - center).T)
            index = int(np.argmin(dist))
            scale = max(400 / info["bg_width"], 240 / info["bg_height"])
            max_drag = (info["bg_width"] - info["mask_width"]) * scale
            progress = index / (len(arc) - 1)
            distance = progress * max_drag
            rotation = progress * 360.0
            rows = build(kind, arc, index, info, distance)
            body = {
                "distance": distance,
                "trajectory_encoded": encode(rows),
                "rotation_angle": rotation,
                "page_num": 1,
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
                "arc",
                index,
                "gap",
                round(float(dist[index]), 2),
                "rot",
                round(rotation, 2),
                "status",
                response.status_code,
                "success",
                payload.get("success"),
                "error",
                payload.get("error"),
                "keys",
                sorted(payload.keys()),
            )
            if payload.get("success") is True:
                data = payload.get("page_data")
                print("page_data", type(data).__name__, len(data) if isinstance(data, list) else "")
                break


if __name__ == "__main__":
    main()
