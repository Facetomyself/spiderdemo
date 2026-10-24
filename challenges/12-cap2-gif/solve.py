"""Solve the cap2 GIF captcha challenge and submit the page sum.

The session stores one captcha at a time. Page fetches stay on collect_pages,
and a lock keeps image, OCR, and page POST in one critical section.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import re
import time
from pathlib import Path

import ddddocr
from PIL import Image, ImageSequence

from modules.login.client import ORIGIN
from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "cap2_challenge"
HERE = Path(__file__).parent
RESULT_PATH = HERE / "result.json"
REFERER = ORIGIN + "/captcha/cap2_challenge?challenge_type=cap2_challenge"
CODE_RE = re.compile(r"^[a-z0-9]{4}$")
MAX_ATTEMPTS = 8


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def longest_frame(raw: bytes) -> Image.Image:
    """The real code is the GIF frame that stays on screen the longest."""
    image = Image.open(io.BytesIO(raw))
    chosen: Image.Image | None = None
    rank: tuple[int, int] | None = None
    for frame in ImageSequence.Iterator(image):
        duration = int(frame.info.get("duration") or 0)
        rgb = frame.convert("RGB")
        darkest = min(bound[0] for bound in rgb.getextrema())
        key = (duration, -darkest)
        if rank is None or key > rank:
            rank = key
            chosen = rgb
    if chosen is None:
        raise ValueError("gif had no frames")
    return chosen


def strip_lines(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    out = Image.new("RGB", rgb.size, (255, 255, 255))
    src = rgb.load()
    dst = out.load()
    width, height = rgb.size
    for y in range(height):
        for x in range(width):
            red, green, blue = src[x, y]
            span = max(red, green, blue) - min(red, green, blue)
            if span < 45 and red < 160:
                dst[x, y] = (0, 0, 0)
    return out


def recognize(raw: bytes, ocr: ddddocr.DdddOcr) -> str | None:
    frame = longest_frame(raw)
    views = (
        frame,
        frame.resize((frame.width * 2, frame.height * 2), Image.Resampling.LANCZOS),
        strip_lines(frame),
    )
    for view in views:
        text = re.sub(r"[^a-z0-9]", "", ocr.classification(png_bytes(view)).lower())
        if CODE_RE.fullmatch(text):
            return text
    return None


def too_many(response_status: int, payload: dict) -> bool:
    if response_status == 429:
        return True
    error = str(payload.get("error") or payload.get("message") or "")
    return "频繁" in error or "too many" in error.lower()


async def wait_backoff(delay: float) -> float:
    await asyncio.sleep(delay)
    return min(delay * 2, 20.0)


async def load_page(
    client,
    page: int,
    ocr: ddddocr.DdddOcr,
    slot: asyncio.Lock,
) -> list[int]:
    delay = 1.0
    async with slot:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            image_response = await client.get(
                f"/captcha/api/{CHALLENGE}/captcha_image/",
                params={"t": int(time.time() * 1000)},
            )
            image_payload = image_response.json() if image_response.status_code != 429 else {}
            if too_many(image_response.status_code, image_payload):
                print(f"page {page} image 429", flush=True)
                delay = await wait_backoff(delay)
                continue
            encoded = image_payload.get("T")
            if not isinstance(encoded, str):
                delay = await wait_backoff(delay)
                continue
            code = recognize(base64.b64decode(encoded), ocr)
            if code is None:
                print(f"page {page} ocr miss {attempt}", flush=True)
                continue
            page_response = await client.post(
                f"/captcha/api/{CHALLENGE}/page/",
                json={
                    "captcha_input": code,
                    "page_num": page,
                    "challenge_type": CHALLENGE,
                },
            )
            page_payload = page_response.json() if page_response.headers.get("content-type", "").startswith("application/json") else {}
            if too_many(page_response.status_code, page_payload):
                print(f"page {page} post 429", flush=True)
                delay = await wait_backoff(delay)
                continue
            numbers = page_payload.get("page_data")
            if page_payload.get("success") and isinstance(numbers, list) and numbers:
                print(f"page {page} ok {len(numbers)} attempt {attempt}", flush=True)
                return [int(number) for number in numbers]
            print(f"page {page} reject {attempt} {page_payload.get('error')}", flush=True)
            await asyncio.sleep(0.2)
    raise RuntimeError(f"page {page} was not accepted")


async def run() -> dict:
    ocr = ddddocr.DdddOcr(show_ad=False)
    session = SpiderSession()
    headers = {
        "Referer": REFERER,
        "Accept": "application/json, text/plain, */*",
    }
    async with session.async_client(headers) as client:
        init_response = await client.get(
            f"/captcha/api/{CHALLENGE}/init/",
            params={"challenge_type": CHALLENGE},
        )
        init_payload = init_response.json()
        if not init_payload.get("success"):
            raise RuntimeError(init_payload.get("error") or "init failed")
        page_one = [int(number) for number in init_payload["page_data"]]
        total_pages = int(init_payload["total_pages"])
        print(f"init pages {total_pages} first {len(page_one)}", flush=True)
        slot = asyncio.Lock()

        async def fetch_page(page: int) -> list[int]:
            return await load_page(client, page, ocr, slot)

        collected = await collect_pages(
            fetch_page,
            range(2, total_pages + 1),
            concurrency=4,
        )
        pages = {1: page_one, **collected}
        if sorted(pages) != list(range(1, total_pages + 1)):
            raise RuntimeError("page set is incomplete")
        answer = sum(number for values in pages.values() for number in values)
        submit_response = await client.post(
            f"/captcha/api/{CHALLENGE}/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        submit_payload = submit_response.json()
        print(
            "submit",
            submit_response.status_code,
            "correct",
            submit_payload.get("is_correct"),
            "message",
            submit_payload.get("message") or submit_payload.get("error"),
            flush=True,
        )
        return submit_payload


def main() -> None:
    payload = asyncio.run(run())
    result = public_result(payload)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    message = str(payload.get("message") or "")
    if payload.get("is_correct") is True or "答案正确" in message:
        return
    raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    main()
