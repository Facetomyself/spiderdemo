"""Solve the cap6 dual-slider sum locally. Do not log cookies or captcha bytes."""

from __future__ import annotations

import asyncio
import base64
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "cap6_challenge"
CONTAINER_W = 400
CONTAINER_H = 240
CONCURRENCY = 4
OUT = Path(__file__).with_name("result.json")


def display_scale(info: dict) -> float:
    # Desktop .slider-container is 400x240. Raw image pixels are rejected.
    return max(CONTAINER_W / info["bg_width"], CONTAINER_H / info["bg_height"])


def piece_x(bg: np.ndarray, rgba: np.ndarray, y: int) -> int:
    alpha = rgba[:, :, 3] > 128
    height, width = alpha.shape
    if y < 0 or y + height > bg.shape[0] or width > bg.shape[1]:
        raise ValueError("piece does not fit the background")
    band = bg[y : y + height]
    mask = np.where(alpha, 255, 0).astype(np.uint8)
    result = cv2.matchTemplate(band, rgba[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return int(max_loc[0])


def page_body(payload: dict, page: int) -> dict:
    info = payload["image_info"]
    scale = display_scale(info)
    bg = np.array(Image.open(io.BytesIO(base64.b64decode(payload["overlay"]))).convert("RGB"))
    body = {
        "page_num": page,
        "challenge_type": CHALLENGE,
        "captcha_id": payload["captcha_id"],
        "container_width": CONTAINER_W,
        "container_height": CONTAINER_H,
    }
    if payload.get("mode") == "dual":
        distances = {}
        for index, slider in enumerate(payload["sliders"], start=1):
            rgba = np.array(Image.open(io.BytesIO(base64.b64decode(slider["masked"]))).convert("RGBA"))
            raw_x = piece_x(bg, rgba, int(slider["y"]))
            distances[f"slider{index}"] = int(round(raw_x * scale))
        body["distances"] = distances
        return body
    rgba = np.array(Image.open(io.BytesIO(base64.b64decode(payload["masked"]))).convert("RGBA"))
    raw_x = piece_x(bg, rgba, int(payload["slider_y"]))
    body["distance"] = int(round(raw_x * scale))
    return body


async def fetch_verified_page(client, page: int) -> list[int]:
    delay = 0.5
    last_error = "no response"
    for _ in range(8):
        image = await client.get(f"/captcha/api/{CHALLENGE}/captcha_image/")
        if image.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            last_error = "429"
            continue
        payload = image.json()
        response = await client.post(f"/captcha/api/{CHALLENGE}/page/", json=page_body(payload, page))
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            last_error = "429"
            continue
        data = response.json()
        numbers = data.get("page_data")
        if data.get("success") and isinstance(numbers, list) and numbers:
            return [int(item) for item in numbers]
        last_error = str(data.get("error") or data.get("message") or response.status_code)[:80]
        await asyncio.sleep(delay)
        delay = min(delay * 2, 4.0)
    raise RuntimeError(f"page {page} failed: {last_error}")


async def solve() -> dict:
    session = SpiderSession()
    async with session.async_client() as client:
        init_response = await client.get(f"/captcha/api/{CHALLENGE}/init/?challenge_type={CHALLENGE}")
        init_payload = init_response.json()
        if not init_payload.get("success"):
            raise RuntimeError("init was not accepted")
        page_one = [int(item) for item in init_payload["page_data"]]
        total_pages = int(init_payload["total_pages"])
        fetched = await collect_pages(
            lambda page: fetch_verified_page(client, page),
            range(2, total_pages + 1),
            concurrency=CONCURRENCY,
        )
        numbers = list(page_one)
        for page in range(2, total_pages + 1):
            numbers.extend(fetched[page])
        answer = sum(numbers)
        submit = await client.post(
            f"/captcha/api/{CHALLENGE}/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        result = public_result(submit.json())
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("pages", total_pages, "numbers", len(numbers), "status", submit.status_code)
        print("is_correct", result.get("is_correct"), "success", result.get("success"))
        return result


def main() -> None:
    asyncio.run(solve())


if __name__ == "__main__":
    main()
