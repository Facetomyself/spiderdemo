"""Solve cap4: sum 100 pages, each page after 1 gated by a local slider match."""

from __future__ import annotations

import asyncio
import base64
import json
import threading
from pathlib import Path

import ddddocr

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "cap4_challenge"
CONTAINER_W = 400
CONTAINER_H = 240
CONCURRENCY = 4
OUT = Path(__file__).with_name("result.json")
_MATCH_LOCK = threading.Lock()


def display_distance(payload: dict, ocr: ddddocr.DdddOcr) -> int | None:
    """Map a ddddocr center hit back to the CSS drag distance.

    slide_match returns the piece center. The page posts style.left, which is
    the piece's left edge in the 400x240 cover-scaled container.
    """
    info = payload.get("image_info") or {}
    try:
        bg_w = float(info["bg_width"])
        bg_h = float(info["bg_height"])
        mask_w = float(info["mask_width"])
        mask_h = float(info["mask_height"])
        slider_y = float(payload["slider_y"])
        masked = base64.b64decode(payload["masked"])
        overlay = base64.b64decode(payload["overlay"])
    except (KeyError, TypeError, ValueError):
        return None
    if bg_w <= 0 or bg_h <= 0 or mask_w <= 0:
        return None
    scale = max(CONTAINER_W / bg_w, CONTAINER_H / bg_h)
    expect_y = slider_y + mask_h / 2

    def accept(match: dict) -> int | None:
        try:
            center_x = float(match["target_x"])
            center_y = float(match["target_y"])
        except (KeyError, TypeError, ValueError):
            return None
        if abs(center_y - expect_y) > 12:
            return None
        gap_x = center_x - mask_w / 2
        distance = int(round(gap_x * scale))
        max_drag = int(round((bg_w - mask_w) * scale))
        if distance < 0 or distance > max_drag:
            return None
        return distance

    with _MATCH_LOCK:
        edge = ocr.slide_match(masked, overlay, simple_target=False)
        chosen = accept(edge)
        if chosen is None:
            simple = ocr.slide_match(masked, overlay, simple_target=True)
            chosen = accept(simple)
    return chosen


async def _read_json(response) -> dict:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


async def _backoff(response, delay: float) -> float:
    if response.status_code != 429:
        return delay
    await asyncio.sleep(delay)
    return min(delay * 2, 16.0)


async def fetch_page(client, ocr: ddddocr.DdddOcr, page: int) -> list[int]:
    delay = 0.8
    for attempt in range(12):
        image = await client.get(
            f"/captcha/api/{CHALLENGE}/captcha_image/",
            params={"t": page * 1000 + attempt},
        )
        delay = await _backoff(image, delay)
        if image.status_code == 429:
            continue
        payload = await _read_json(image)
        if "captcha_id" not in payload:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 16.0)
            continue
        distance = await asyncio.to_thread(display_distance, payload, ocr)
        if distance is None:
            continue
        posted = await client.post(
            f"/captcha/api/{CHALLENGE}/page/",
            json={
                "distance": distance,
                "page_num": page,
                "challenge_type": CHALLENGE,
                "captcha_id": payload["captcha_id"],
                "container_width": CONTAINER_W,
                "container_height": CONTAINER_H,
            },
        )
        delay = await _backoff(posted, delay)
        if posted.status_code == 429:
            continue
        body = await _read_json(posted)
        numbers = body.get("page_data")
        if body.get("success") is True and body.get("current_page") == page and isinstance(numbers, list) and numbers:
            print(f"page {page} ok", flush=True)
            return [int(item) for item in numbers]
        print(f"page {page} retry {attempt + 1}", flush=True)
        await asyncio.sleep(0.2)
    raise RuntimeError(f"page {page} was not accepted")


async def init_challenge(client) -> dict:
    delay = 0.8
    for _ in range(6):
        response = await client.get(
            f"/captcha/api/{CHALLENGE}/init/",
            params={"challenge_type": CHALLENGE},
        )
        delay = await _backoff(response, delay)
        if response.status_code == 429:
            continue
        payload = await _read_json(response)
        if payload.get("success") is True and isinstance(payload.get("page_data"), list):
            return payload
        await asyncio.sleep(delay)
        delay = min(delay * 2, 16.0)
    raise RuntimeError("init was not accepted")


async def submit_answer(client, answer: int) -> dict:
    delay = 0.8
    last: dict = {}
    for _ in range(6):
        response = await client.post(
            f"/captcha/api/{CHALLENGE}/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        delay = await _backoff(response, delay)
        if response.status_code == 429:
            continue
        last = public_result(await _read_json(response))
        if last:
            return last
        await asyncio.sleep(delay)
        delay = min(delay * 2, 16.0)
    return last


async def main() -> None:
    session = SpiderSession()
    ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    async with session.async_client() as client:
        init = await init_challenge(client)
        total_pages = int(init.get("total_pages") or 100)
        pages: dict[int, list[int]] = {1: [int(item) for item in init["page_data"]]}
        print("page 1 ok", flush=True)

        async def load(page: int) -> list[int]:
            return await fetch_page(client, ocr, page)

        rest = await collect_pages(load, range(2, total_pages + 1), concurrency=CONCURRENCY)
        pages.update(rest)
        if sorted(pages) != list(range(1, total_pages + 1)):
            raise RuntimeError("page set is incomplete")
        answer = sum(sum(numbers) for numbers in pages.values())
        result = await submit_answer(client, answer)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
