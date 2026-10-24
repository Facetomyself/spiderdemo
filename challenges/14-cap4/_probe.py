"""Probe cap4 init and one slider page. Do not print ids or image bytes."""

from __future__ import annotations

import base64
import io
import json

import ddddocr
from PIL import Image

from modules.runtime import SpiderSession

TYPE = "cap4_challenge"
CONTAINER_W = 400
CONTAINER_H = 240


def summarize(payload: dict) -> dict:
    out = {}
    for key, value in payload.items():
        if key in {"masked", "overlay", "captcha_id"}:
            out[key] = f"<{type(value).__name__} len={len(value) if hasattr(value, '__len__') else '?'}>"
        elif isinstance(value, list):
            out[key] = value[:12]
            out[key + "_len"] = len(value)
        else:
            out[key] = value
    return out


def scale_of(info: dict) -> float:
    bg_w = info["bg_width"]
    bg_h = info["bg_height"]
    return max(CONTAINER_W / bg_w, CONTAINER_H / bg_h)


def main() -> None:
    session = SpiderSession()
    ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    with session.client() as client:
        init = client.get(f"/captcha/api/{TYPE}/init/?challenge_type={TYPE}")
        body = init.json()
        print("init", init.status_code, json.dumps(summarize(body), ensure_ascii=False))
        cap = client.get(f"/captcha/api/{TYPE}/captcha_image/")
        data = cap.json()
        print("captcha", cap.status_code, json.dumps(summarize(data), ensure_ascii=False))
        masked = base64.b64decode(data["masked"])
        overlay = base64.b64decode(data["overlay"])
        piece = Image.open(io.BytesIO(masked))
        bg = Image.open(io.BytesIO(overlay))
        print("piece", piece.mode, piece.size, "bg", bg.mode, bg.size)
        if piece.mode == "RGBA":
            alpha = piece.getchannel("A")
            extrema = alpha.getextrema()
            print("alpha_extrema", extrema)
        match = ocr.slide_match(masked, overlay, simple_target=False)
        simple = ocr.slide_match(masked, overlay, simple_target=True)
        print("edge", {k: match[k] for k in match if k != "target"})
        print("simple", {k: simple[k] for k in simple if k != "target"})
        info = data["image_info"]
        scale = scale_of(info)
        mask_w = info["mask_width"]
        # ddddocr returns the center. Left edge is the drag origin.
        gap_x = match["target_x"] - mask_w / 2
        distance = gap_x * scale
        print("scale", round(scale, 4), "gap_x", round(gap_x, 2), "distance", round(distance, 2), "slider_y", data.get("slider_y"))
        page = client.post(
            f"/captcha/api/{TYPE}/page/",
            json={
                "distance": round(distance),
                "page_num": 2,
                "challenge_type": TYPE,
                "captcha_id": data["captcha_id"],
                "container_width": CONTAINER_W,
                "container_height": CONTAINER_H,
            },
        )
        page_body = page.json()
        print("page", page.status_code, json.dumps(summarize(page_body), ensure_ascii=False))


if __name__ == "__main__":
    main()
