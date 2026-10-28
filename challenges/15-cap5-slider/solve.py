"""Solve cap5 random-slider number collection with a local gap offset.

The captcha answer lives in the session, so image fetch and page post stay
atomic. Page scheduling still goes through collect_pages.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "cap5_challenge"
PAGE = "/captcha/cap5_challenge?challenge_type=cap5_challenge"
REFERER = "https://www.spiderdemo.cn" + PAGE
CONTAINER_WIDTH = 400
CONTAINER_HEIGHT = 240
OUT = Path(__file__).with_name("result.json")


def _decode_image(value: str) -> Image.Image:
    if "," in value:
        value = value.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(value))).convert("RGBA")


def gap_origin(piece: Image.Image, background: Image.Image) -> tuple[int, int]:
    """Return the mask canvas origin on the background, in source pixels."""
    piece_px = np.asarray(piece)
    background_px = np.asarray(background)
    piece_y, piece_x = np.where(piece_px[..., 3] == 255)
    hole_y, hole_x = np.where(background_px[..., 3] < 250)
    if piece_x.size == 0 or hole_x.size == 0:
        raise ValueError("captcha alpha masks were empty")
    origin_x = int(hole_x.min() - piece_x.min())
    origin_y = int(hole_y.min() - piece_y.min())
    shifted_x = piece_x + origin_x
    shifted_y = piece_y + origin_y
    if shifted_x.max() >= background_px.shape[1] or shifted_y.max() >= background_px.shape[0]:
        raise ValueError("captcha gap origin fell outside the background")
    hole = np.zeros(background_px.shape[:2], dtype=bool)
    guess = np.zeros(background_px.shape[:2], dtype=bool)
    hole[hole_y, hole_x] = True
    guess[shifted_y, shifted_x] = True
    if np.any(hole != guess):
        raise ValueError("captcha piece did not match the alpha gap")
    return origin_x, origin_y


def display_distance(origin_x: int, image_info: dict) -> int:
    """Match the page cover-scale used by a 400x240 slider container."""
    bg_width = int(image_info["bg_width"])
    bg_height = int(image_info["bg_height"])
    scale = max(CONTAINER_WIDTH / bg_width, CONTAINER_HEIGHT / bg_height)
    return int(origin_x * scale + 0.5)


def _json_body(response) -> dict:
    try:
        payload = response.json()
    except Exception as exc:
        raise RuntimeError(f"non-json response {response.status_code}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected response {response.status_code}")
    return payload


async def _backoff(response, attempt: int) -> bool:
    if response.status_code != 429:
        return False
    await asyncio.sleep(min(8.0, 1.5 * (attempt + 1)))
    return True


async def fetch_page_numbers(client, page: int) -> list[int]:
    last_error = "captcha was not accepted"
    for attempt in range(6):
        captcha_response = await client.get("/captcha/api/cap5_challenge/captcha_image/")
        if await _backoff(captcha_response, attempt):
            last_error = "captcha image was rate limited"
            continue
        captcha = _json_body(captcha_response)
        if "masked" not in captcha or "overlay" not in captcha:
            last_error = str(captcha.get("error") or captcha.get("message") or "captcha image missing")
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
        origin_x, origin_y = gap_origin(_decode_image(captcha["masked"]), _decode_image(captcha["overlay"]))
        if int(captcha.get("slider_y", origin_y)) != origin_y:
            last_error = "slider_y did not match the alpha gap"
            continue
        distance = display_distance(origin_x, captcha["image_info"])
        response = await client.post(
            "/captcha/api/cap5_challenge/page/",
            json={
                "distance": distance,
                "page_num": page,
                "challenge_type": CHALLENGE,
                "container_width": CONTAINER_WIDTH,
                "container_height": CONTAINER_HEIGHT,
            },
        )
        if await _backoff(response, attempt):
            last_error = "page post was rate limited"
            continue
        payload = _json_body(response)
        numbers = payload.get("page_data")
        if payload.get("success") is True and isinstance(numbers, list) and numbers:
            return [int(number) for number in numbers]
        last_error = str(payload.get("error") or payload.get("message") or "page request failed")
        await asyncio.sleep(0.25 * (attempt + 1))
    raise RuntimeError(f"page {page}: {last_error}")


async def solve() -> dict:
    session = SpiderSession()
    headers = {"Referer": REFERER, "Accept": "application/json"}
    async with session.async_client(headers=headers) as client:
        init_response = await client.get(
            f"/captcha/api/cap5_challenge/init/?challenge_type={CHALLENGE}"
        )
        if init_response.status_code == 429:
            await asyncio.sleep(2)
            init_response = await client.get(
                f"/captcha/api/cap5_challenge/init/?challenge_type={CHALLENGE}"
            )
        init_body = _json_body(init_response)
        if init_body.get("success") is not True:
            raise RuntimeError(str(init_body.get("error") or init_body.get("message") or "init failed"))
        first_page = [int(number) for number in init_body["page_data"]]
        total_pages = int(init_body["total_pages"])
        slot = asyncio.Lock()

        async def fetch_page(page: int) -> list[int]:
            async with slot:
                numbers = await fetch_page_numbers(client, page)
            if page % 10 == 0:
                print("collected", page, "of", total_pages, flush=True)
            return numbers

        collected = await collect_pages(fetch_page, range(2, total_pages + 1), concurrency=4)
        pages = {1: first_page}
        pages.update(collected)
        missing = [page for page in range(1, total_pages + 1) if page not in pages]
        if missing:
            raise RuntimeError(f"missing pages: {missing[:8]}")
        answer = sum(sum(pages[page]) for page in range(1, total_pages + 1))
        print("pages", total_pages, "answer", answer, flush=True)
        submit = await client.post(
            "/captcha/api/cap5_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        payload = _json_body(submit)
        result = public_result(payload)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("submit", result.get("success"), result.get("is_correct"), result.get("message"), flush=True)
        return result


def main() -> None:
    result = asyncio.run(solve())
    if result.get("is_correct") is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
