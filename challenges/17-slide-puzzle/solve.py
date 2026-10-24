"""Solve slide_puzzle_challenge: align the strip, sum 100 pages, submit."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import sys
from pathlib import Path

import ddddocr
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.runtime import SpiderSession, collect_pages, public_result

TYPE = "slide_puzzle_challenge"
REFERER = f"https://www.spiderdemo.cn/captcha/{TYPE}?challenge_type={TYPE}"
RESULT = Path(__file__).with_name("result.json")
SLIDE = ddddocr.DdddOcr(ocr=False, show_ad=False)


def _sad(top: list[tuple[int, int, int]], bottom: list[tuple[int, int, int]], width: int, band: int, shift: int) -> int:
    total = 0
    for row in range(band):
        base = row * width
        for col in range(width):
            src = top[base + (col - shift) % width]
            dst = bottom[base + col]
            total += abs(src[0] - dst[0]) + abs(src[1] - dst[1]) + abs(src[2] - dst[2])
    return total


def match_distance(image: Image.Image, split_y: int) -> int:
    """Offset that realigns the top strip with the rows below the cut.

    Slider CSS sets background-position to ``{distance}px 0``, so column
    ``col`` shows source column ``(col - distance) mod width``. ddddocr
    slide_match locates a crop of that strip; it is kept only when its
    offset is at least as good as the seam score.
    """
    rgb = image.convert("RGB")
    width, height = rgb.size
    if split_y <= 0 or split_y >= height:
        raise ValueError("split is outside the image")
    band = min(8, split_y, height - split_y)
    top = list(rgb.crop((0, split_y - band, width, split_y)).getdata())
    bottom = list(rgb.crop((0, split_y, width, split_y + band)).getdata())
    seam = min(range(width), key=lambda shift: _sad(top, bottom, width, band, shift))
    slide = _slide_match_offset(rgb, split_y)
    if slide is None:
        return seam
    slide %= width
    if _sad(top, bottom, width, band, slide) <= _sad(top, bottom, width, band, seam):
        return slide
    return seam


def _slide_match_offset(image: Image.Image, split_y: int) -> int | None:
    piece_w = 40
    band = 12
    if split_y < band or image.height - split_y < band or image.width <= piece_w:
        return None
    piece = image.crop((0, split_y - band, piece_w, split_y))
    background = image.crop((0, split_y, image.width, split_y + band))
    piece_buf = io.BytesIO()
    bg_buf = io.BytesIO()
    piece.save(piece_buf, format="PNG")
    background.save(bg_buf, format="PNG")
    try:
        found = SLIDE.slide_match(piece_buf.getvalue(), bg_buf.getvalue(), simple_target=True)
    except Exception:
        return None
    return int(round(found["target_x"] - piece_w / 2))


def _json_body(response: object) -> dict:
    try:
        body = response.json()
    except Exception:
        return {}
    return body if isinstance(body, dict) else {}


async def _request_json(client: object, method: str, url: str, **kwargs: object) -> tuple[int, dict]:
    delay = 0.4
    last_status = 0
    for _ in range(6):
        response = await client.request(method, url, **kwargs)
        last_status = response.status_code
        if response.status_code == 429 or response.status_code >= 500:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        return response.status_code, _json_body(response)
    raise RuntimeError(f"HTTP {last_status}")


async def _unlock(client: object) -> str:
    for _ in range(4):
        status, body = await _request_json(client, "GET", f"/captcha/api/{TYPE}/captcha")
        data = body.get("data")
        if status != 200 or not isinstance(data, dict):
            continue
        encoded = str(data.get("bg") or "")
        payload = encoded.split(",", 1)[1] if "," in encoded else encoded
        image = Image.open(io.BytesIO(base64.b64decode(payload)))
        try:
            distance = match_distance(image, int(data["y"]))
        finally:
            image.close()
        verify_status, verified = await _request_json(
            client,
            "POST",
            f"/captcha/api/{TYPE}/verify",
            json={"distance": distance, "captchaId": data["captchaId"]},
        )
        token = verified.get("data", {}).get("token") if isinstance(verified.get("data"), dict) else None
        if verify_status == 200 and verified.get("success") is True and isinstance(token, str) and token:
            return token
    raise RuntimeError("captcha was not accepted")


async def _submit(client: object, answer: int) -> dict:
    candidates = (
        "/captcha/api/challenge/submit/",
        f"/captcha/api/{TYPE}/submit/",
    )
    last: dict = {}
    for url in candidates:
        _status, body = await _request_json(
            client,
            "POST",
            url,
            json={"challenge_type": TYPE, "answer": answer},
        )
        last = body
        if "is_correct" in body or "correct" in body:
            return body
    return last


async def solve() -> dict:
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        _status, init_body = await _request_json(
            client,
            "GET",
            "/captcha/api/challenge/init/",
            params={"challenge_type": TYPE},
        )
        if init_body.get("success") is not True:
            raise RuntimeError("init was not accepted")
        total_pages = int(init_body["total_pages"])
        token_box = {"token": await _unlock(client)}
        lock = asyncio.Lock()

        async def fetch_page(page: int) -> list[int]:
            delay = 0.4
            for _ in range(6):
                used = token_box["token"]
                status, body = await _request_json(
                    client,
                    "GET",
                    f"/captcha/api/{TYPE}/page/{page}/",
                    params={"challenge_type": TYPE, "token": used},
                )
                nums = body.get("page_data")
                if body.get("success") is True and isinstance(nums, list) and len(nums) == 10:
                    return [int(num) for num in nums]
                error = str(body.get("error") or "")
                if status == 400 or "token" in error or "验证" in error:
                    async with lock:
                        if token_box["token"] == used:
                            token_box["token"] = await _unlock(client)
                    continue
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8.0)
            raise RuntimeError(f"page {page} was not accepted")

        pages = await collect_pages(fetch_page, range(1, total_pages + 1), concurrency=4)
        if len(pages) != total_pages:
            raise RuntimeError("missing pages")
        answer = sum(sum(nums) for nums in pages.values())
        print("pages", total_pages, "answer", answer)
        return await _submit(client, answer)


def main() -> None:
    body = asyncio.run(solve())
    kept = public_result(body)
    RESULT.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("is_correct", kept.get("is_correct"))
    print("success", kept.get("success"))
    print("message", kept.get("message"))
    if kept.get("is_correct") is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
