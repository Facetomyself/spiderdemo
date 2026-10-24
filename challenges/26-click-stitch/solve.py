"""Solve the click-stitch captcha locally and submit the 30-page sum."""

from __future__ import annotations

import asyncio
import base64
import io
import itertools
import json
from pathlib import Path

from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "click_stitch_challenge"
PAGE_COUNT = 30
OUT = Path(__file__).with_name("result.json")
REFERER = (
    "https://www.spiderdemo.cn/captcha/click_stitch_challenge/"
    "?challenge_type=click_stitch_challenge"
)


def load_background(value: str) -> Image.Image:
    payload = value.split(",", 1)[1] if value.startswith("data:") else value
    raw = base64.b64decode(payload)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def split_tiles(image: Image.Image) -> list[Image.Image]:
    width, height = image.size
    half_w, half_h = width // 2, height // 2
    boxes = (
        (0, 0, half_w, half_h),
        (half_w, 0, width, half_h),
        (0, half_h, half_w, height),
        (half_w, half_h, width, height),
    )
    return [image.crop(box) for box in boxes]


def clockwise(tile: Image.Image, turns: int) -> Image.Image:
    # CSS rotate() is clockwise. PIL's rotate() is counter-clockwise.
    return tile.rotate(-90 * (turns % 4), expand=True)


def band_cost(left: Image.Image, right: Image.Image, axis: str, depth: int = 4) -> int:
    pixels_a = left.load()
    pixels_b = right.load()
    width, height = left.size
    total = 0
    if axis == "h":
        for y in range(height):
            for step in range(depth):
                right_px = pixels_a[width - 1 - step, y]
                left_px = pixels_b[step, y]
                total += (
                    abs(right_px[0] - left_px[0])
                    + abs(right_px[1] - left_px[1])
                    + abs(right_px[2] - left_px[2])
                )
        return total
    for x in range(width):
        for step in range(depth):
            top_px = pixels_a[x, height - 1 - step]
            bottom_px = pixels_b[x, step]
            total += (
                abs(top_px[0] - bottom_px[0])
                + abs(top_px[1] - bottom_px[1])
                + abs(top_px[2] - bottom_px[2])
            )
    return total


def best_clicks(image: Image.Image) -> list[int]:
    """Clicks that rotate each quadrant clockwise onto the continuous picture."""
    tiles = split_tiles(image)
    best_cost: int | None = None
    best: tuple[int, int, int, int] | None = None
    for clicks in itertools.product(range(4), repeat=4):
        oriented = [clockwise(tiles[index], turns) for index, turns in enumerate(clicks)]
        cost = (
            band_cost(oriented[0], oriented[1], "h")
            + band_cost(oriented[2], oriented[3], "h")
            + band_cost(oriented[0], oriented[2], "v")
            + band_cost(oriented[1], oriented[3], "v")
        )
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best = clicks
    if best is None:
        raise RuntimeError("no stitch orientation")
    return list(best)


async def request_json(client, method: str, path: str, **kwargs):
    delay = 0.5
    last = None
    for _ in range(8):
        if method == "GET":
            last = await client.get(path, **kwargs)
        else:
            last = await client.post(path, **kwargs)
        if last.status_code != 429:
            return last
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    return last


def page_numbers(payload: dict) -> list[int]:
    numbers = payload.get("page_data")
    if not isinstance(numbers, list) or len(numbers) != 10:
        raise RuntimeError("unexpected page_data")
    return [int(item) for item in numbers]


async def main() -> None:
    session = SpiderSession()
    token_box: dict[str, str | None] = {"token": None}
    token_lock = asyncio.Lock()

    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await request_json(
            client,
            "GET",
            f"/captcha/api/{CHALLENGE}/init/?challenge_type={CHALLENGE}",
        )
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            detail = init_payload.get("error") or init_payload.get("message") or init_response.status_code
            raise SystemExit(f"init failed: {detail}")
        page_count = int(init_payload.get("total_pages") or PAGE_COUNT)

        async def refresh_token() -> str:
            async with token_lock:
                last_detail = "verify failed"
                for _ in range(5):
                    captcha_response = await request_json(
                        client,
                        "GET",
                        f"/captcha/api/{CHALLENGE}/captcha",
                    )
                    captcha_payload = captcha_response.json()
                    data = captcha_payload.get("data") if isinstance(captcha_payload, dict) else None
                    if (
                        captcha_response.status_code != 200
                        or not isinstance(data, dict)
                        or not data.get("bg")
                        or not data.get("captchaId")
                    ):
                        last_detail = "captcha payload missing image"
                        continue
                    clicks = await asyncio.to_thread(best_clicks, load_background(data["bg"]))
                    verify_response = await request_json(
                        client,
                        "POST",
                        f"/captcha/api/{CHALLENGE}/verify",
                        json={"clickCounts": clicks, "captchaId": data["captchaId"]},
                    )
                    verify_payload = verify_response.json()
                    issued = verify_payload.get("data") if isinstance(verify_payload, dict) else None
                    token = issued.get("token") if isinstance(issued, dict) else None
                    if verify_payload.get("success") is True and token:
                        token_box["token"] = token
                        return token
                    last_detail = str(
                        verify_payload.get("error") or verify_payload.get("message") or "verify rejected"
                    )
                raise RuntimeError(last_detail)

        await refresh_token()

        async def fetch_page(page: int) -> list[int]:
            last_detail = "page failed"
            for _ in range(6):
                token = token_box["token"]
                response = await request_json(
                    client,
                    "GET",
                    (
                        f"/captcha/api/{CHALLENGE}/page/{page}/"
                        f"?challenge_type={CHALLENGE}&token={token}"
                    ),
                )
                payload = response.json()
                if response.status_code == 200 and payload.get("success") is True:
                    return page_numbers(payload)
                detail = str(payload.get("error") or payload.get("message") or response.status_code)
                last_detail = detail
                if "token" in detail or "验证" in detail:
                    await refresh_token()
                    continue
                break
            raise RuntimeError(f"page {page}: {last_detail}")

        pages = await collect_pages(fetch_page, range(1, page_count + 1), concurrency=4)
        total = sum(sum(pages[page]) for page in range(1, page_count + 1))
        submit = await request_json(
            client,
            "POST",
            f"/captcha/api/{CHALLENGE}/submit/",
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        body = submit.json()
        result = public_result(body if isinstance(body, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        accepted = body.get("is_correct") is True or "答案正确" in str(body.get("message") or "")
        print(
            "pages",
            len(pages),
            "sum",
            total,
            "http",
            submit.status_code,
            "accepted",
            accepted,
        )
        print("message", body.get("message"))
        if not accepted:
            raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    asyncio.run(main())
