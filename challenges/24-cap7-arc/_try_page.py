"""Submit one page with the recovered arc angle. Print only the verdict."""

from __future__ import annotations

import base64
import json
import time

import cv2
import numpy as np
from PIL import Image
import io

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
CONTAINER_W = 400
CONTAINER_H = 240


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


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int, float]:
    best = (-1.0, 0, 0, 0)
    for angle in range(0, 360, 5):
        turned = rotate(piece, angle)
        mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
        score = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
        _, value, _, loc = cv2.minMaxLoc(score)
        if value > best[0]:
            best = (float(value), angle, int(loc[0]), int(loc[1]))
    coarse = best[1]
    for angle in range(coarse - 4, coarse + 5):
        turned = rotate(piece, angle % 360)
        mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
        score = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
        _, value, _, loc = cv2.minMaxLoc(score)
        if value > best[0]:
            best = (float(value), angle % 360, int(loc[0]), int(loc[1]))
    return best


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER, "Accept": "application/json"}) as client:
        init = client.get("/captcha/api/cap7_challenge/init/?challenge_type=cap7_challenge")
        print("init", init.status_code, init.json().get("success"), init.json().get("total_pages"))
        cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
        piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
        points = np.array(cap["arc_path"]["points"], dtype=np.float64)
        info = cap["image_info"]
        started = time.time()
        value, angle, x, y = best_pose(bg, piece)
        height, width = piece.shape[:2]
        center = np.array([x + width / 2, y + height / 2])
        dist = np.hypot(*(points - center).T)
        index = int(np.argmin(dist))
        print(
            "match",
            round(value, 3),
            "visual_angle",
            angle,
            "arc",
            index,
            "arc_dist",
            round(float(dist[index]), 2),
            "elapsed",
            round(time.time() - started, 2),
        )
        scale = max(CONTAINER_W / info["bg_width"], CONTAINER_H / info["bg_height"])
        offset_x = (CONTAINER_W - info["bg_width"] * scale) / 2
        offset_y = (CONTAINER_H - info["bg_height"] * scale) / 2
        max_drag = info["bg_width"] * scale - info["mask_width"] * scale
        progress = index / (len(points) - 1)
        distance = progress * max_drag
        rotation = progress * 360.0
        now = int(time.time() * 1000)
        trajectory = []
        for step, point_index in enumerate(range(0, index + 1, max(1, index // 16))):
            px, py = points[point_index]
            trajectory.append(
                {
                    "x": round(offset_x + px * scale, 2),
                    "y": round(offset_y + py * scale, 2),
                    "t": now + step * 45,
                }
            )
        if trajectory[-1]["x"] != round(offset_x + points[index][0] * scale, 2):
            trajectory.append(
                {
                    "x": round(offset_x + points[index][0] * scale, 2),
                    "y": round(offset_y + points[index][1] * scale, 2),
                    "t": now + len(trajectory) * 45,
                }
            )
        encoded = base64.b64encode(json.dumps(trajectory, separators=(",", ":")).encode("utf-8")).decode("ascii")
        body = {
            "distance": distance,
            "trajectory_encoded": encoded,
            "rotation_angle": rotation,
            "page_num": 1,
            "challenge_type": "cap7_challenge",
            "captcha_id": cap["captcha_id"],
            "container_width": CONTAINER_W,
            "container_height": CONTAINER_H,
        }
        print("progress", round(progress, 4), "distance", round(distance, 3), "rotation", round(rotation, 3), "traj", len(trajectory))
        response = client.post("/captcha/api/cap7_challenge/page/", json=body)
        payload = response.json()
        safe = {
            "status": response.status_code,
            "keys": sorted(payload.keys()),
            "success": payload.get("success"),
            "error": payload.get("error"),
            "message": payload.get("message"),
        }
        data = payload.get("page_data") or payload.get("data") or payload.get("numbers")
        if isinstance(data, list):
            safe["n"] = len(data)
            safe["sum"] = sum(item for item in data if isinstance(item, (int, float)))
        print(json.dumps(safe, ensure_ascii=False))


if __name__ == "__main__":
    main()
