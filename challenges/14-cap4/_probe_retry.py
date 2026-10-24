"""See whether one captcha id accepts a second distance. No ids printed."""

from __future__ import annotations

import base64
import json

import ddddocr

from modules.runtime import SpiderSession

TYPE = "cap4_challenge"
CONTAINER_W = 400
CONTAINER_H = 240


def brief(payload: dict) -> dict:
    return {
        key: payload.get(key)
        for key in ("success", "error", "message", "current_page", "data_type")
        if key in payload
    }


def distance_of(data: dict, ocr: ddddocr.DdddOcr) -> int:
    info = data["image_info"]
    scale = max(CONTAINER_W / info["bg_width"], CONTAINER_H / info["bg_height"])
    match = ocr.slide_match(base64.b64decode(data["masked"]), base64.b64decode(data["overlay"]))
    gap_x = match["target_x"] - info["mask_width"] / 2
    return int(round(gap_x * scale))


def main() -> None:
    session = SpiderSession()
    ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    with session.client() as client:
        data = client.get(f"/captcha/api/{TYPE}/captcha_image/").json()
        distance = distance_of(data, ocr)
        body = {
            "distance": distance + 40,
            "page_num": 3,
            "challenge_type": TYPE,
            "captcha_id": data["captcha_id"],
            "container_width": CONTAINER_W,
            "container_height": CONTAINER_H,
        }
        first = client.post(f"/captcha/api/{TYPE}/page/", json=body)
        print("wrong", first.status_code, json.dumps(brief(first.json()), ensure_ascii=False), "distance", distance)
        body["distance"] = distance
        second = client.post(f"/captcha/api/{TYPE}/page/", json=body)
        print("retry", second.status_code, json.dumps(brief(second.json()), ensure_ascii=False))


if __name__ == "__main__":
    main()
