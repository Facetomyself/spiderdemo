"""Solve the cylinder slider challenge locally and submit the page sum."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import itertools
import json
import math
import time
from pathlib import Path

from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890+/="
CHALLENGE = "slide_cylinder_challenge"
REFERER = (
    "https://www.spiderdemo.cn/captcha/slide_cylinder_challenge"
    "?challenge_type=slide_cylinder_challenge"
)
TILE_W = 255
TILE_H = 185
CONTAINER_W = 400
CONTAINER_H = 240
HERE = Path(__file__).parent


def code_at(text: str, index: int) -> int:
    if index < 0 or index >= len(text):
        return 0
    return ord(text[index])


def custom_btoa(text: str) -> str:
    """Match slide_cylinder.js btoa. Caller keeps len(text) % 3 == 0."""
    out: list[str] = []
    pad = (0, 2, 1)[len(text) % 3]
    index = 0
    while index < len(text) - pad:
        chunk = (
            (code_at(text, index) << 16)
            | (code_at(text, index + 1) << 8)
            | code_at(text, index + 2)
        )
        out.append(ALPHABET[(chunk >> 18) & 63])
        out.append(ALPHABET[(chunk >> 12) & 63])
        out.append(ALPHABET[(chunk >> 6) & 63])
        out.append(ALPHABET[chunk & 63])
        index += 3
    if pad == 2:
        chunk = code_at(text, index)
        out.append(ALPHABET[(chunk >> 2) & 63])
        out.append(ALPHABET[(chunk << 4) & 63])
        out.append("==")
    elif pad == 1:
        chunk = (code_at(text, index) << 8) | code_at(text, index + 1)
        out.append(ALPHABET[(chunk >> 10) & 63])
        out.append(ALPHABET[(chunk >> 4) & 63])
        out.append(ALPHABET[(chunk << 2) & 63])
        out.append("=")
    return "".join(out)


def js_number(value: float) -> str:
    nearest = round(value)
    if abs(value - nearest) < 1e-9:
        return str(int(nearest))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def encode_track(fraction: float) -> str:
    final_x = (fraction % 1.0) * 350.0
    points: list[tuple[float, int, int]] = []
    for step in range(1, 25):
        progress = step / 24
        eased = 1 - (1 - progress) ** 2
        points.append((final_x * eased, 480 + (step % 3) - 1, 16 + (step % 5)))
    points[-1] = (final_x, 480, 18)
    body = "[" + ",".join(
        '{"x":%s,"y":%s,"timestamp":%s}' % (js_number(x), js_number(y), js_number(ts))
        for x, y, ts in points
    ) + "]"
    while len(body) % 3:
        body += " "
    return custom_btoa(body)


def permutation(order: str, server_time: str) -> list[int]:
    for perm in itertools.permutations(range(8)):
        text = json.dumps(list(perm), separators=(",", ":")) + server_time
        if hashlib.md5(text.encode()).hexdigest() == order:
            return list(perm)
    raise RuntimeError("permutation not found")


def restore(image: Image.Image, perm: list[int]) -> Image.Image:
    canvas = Image.new("RGB", image.size)
    for source, dest in enumerate(perm):
        sx = (source % 4) * TILE_W
        sy = (source // 4) * TILE_H
        dx = (dest % 4) * TILE_W
        dy = (dest // 4) * TILE_H
        canvas.paste(image.crop((sx, sy, sx + TILE_W, sy + TILE_H)), (dx, dy))
    return canvas


def ink_center(image: Image.Image) -> float:
    pixels = image.load()
    width, height = image.size
    bg = pixels[width // 2, 2]
    sin_sum = 0.0
    cos_sum = 0.0
    total = 0.0
    for x in range(width):
        weight = 0
        for y in range(0, height, 2):
            red, green, blue = pixels[x, y]
            if abs(red - bg[0]) + abs(green - bg[1]) + abs(blue - bg[2]) > 40:
                weight += 1
        if weight < 4:
            continue
        angle = math.tau * x / width
        sin_sum += math.sin(angle) * weight
        cos_sum += math.cos(angle) * weight
        total += weight
    if total <= 0:
        raise RuntimeError("empty foreground")
    angle = math.atan2(sin_sum, cos_sum)
    return (angle / math.tau) % 1.0


def slide_fraction(bg_b64: str, order: str, server_time: str, offset: float) -> float:
    picture = Image.open(io.BytesIO(base64.b64decode(bg_b64))).convert("RGB")
    if picture.size != (TILE_W * 4, TILE_H * 2):
        raise RuntimeError(f"unexpected image size {picture.size}")
    restored = restore(picture, permutation(order, server_time))
    center = ink_center(restored)
    return (offset - center) % 1.0


def as_numbers(value: object) -> list[int] | None:
    if not isinstance(value, list) or len(value) != 10:
        return None
    if not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        return None
    return [int(item) for item in value]


def server_time_from(response) -> str:
    value = response.cookies.get("server_time")
    if value:
        return value
    for header in response.headers.get_list("set-cookie"):
        for part in header.split(";"):
            name, sep, cookie = part.strip().partition("=")
            if sep and name == "server_time" and cookie:
                return cookie
    return ""


async def request_with_backoff(client, method: str, url: str, **kwargs):
    delay = 0.8
    response = None
    for _ in range(6):
        response = await client.request(method, url, **kwargs)
        if response.status_code != 429:
            return response
        await asyncio.sleep(delay)
        delay = min(delay * 2, 16)
    return response


async def load_page(client, page: int) -> list[int]:
    last_error = "no attempt"
    for _ in range(5):
        image = await request_with_backoff(
            client,
            "GET",
            "/captcha/api/slide_cylinder_challenge/captcha_image/",
            params={"t": time.time_ns()},
        )
        if image.status_code != 200:
            last_error = f"image http {image.status_code}"
            await asyncio.sleep(0.6)
            continue
        payload = image.json()
        stamp = server_time_from(image)
        if not stamp or "bg" not in payload or "order" not in payload:
            last_error = "captcha payload incomplete"
            continue
        try:
            fraction = await asyncio.to_thread(
                slide_fraction,
                payload["bg"],
                payload["order"],
                stamp,
                float(payload["offset"]),
            )
        except RuntimeError as exc:
            last_error = str(exc)
            continue
        response = await request_with_backoff(
            client,
            "POST",
            "/captcha/api/slide_cylinder_challenge/page/",
            json={
                "captcha_id": payload["captchaId"],
                "page_num": page,
                "challenge_type": CHALLENGE,
                "track": encode_track(fraction),
                "container_width": CONTAINER_W,
                "container_height": CONTAINER_H,
            },
        )
        if response.status_code != 200:
            last_error = f"page http {response.status_code}"
            await asyncio.sleep(0.6)
            continue
        body = response.json()
        numbers = as_numbers(body.get("page_data")) if isinstance(body, dict) else None
        if isinstance(body, dict) and body.get("success") is True and numbers is not None:
            return numbers
        last_error = str(body.get("error") or body.get("message") or "rejected") if isinstance(body, dict) else "rejected"
    raise RuntimeError(f"page {page}: {last_error}")


async def run() -> dict:
    session = SpiderSession()
    async with session.async_client(headers={"Referer": REFERER}) as client:
        init_response = await request_with_backoff(
            client,
            "GET",
            "/captcha/api/slide_cylinder_challenge/init/",
            params={"challenge_type": CHALLENGE},
        )
        init_response.raise_for_status()
        init_body = init_response.json()
        first = as_numbers(init_body.get("page_data"))
        if init_body.get("success") is not True or first is None:
            raise RuntimeError("init did not return page 1")
        total_pages = int(init_body.get("total_pages") or 100)
        fetched = await collect_pages(lambda page: load_page(client, page), range(2, total_pages + 1), concurrency=4)
        numbers = {1: first}
        numbers.update(fetched)
        if len(numbers) != total_pages:
            raise RuntimeError(f"missing pages: {len(numbers)}/{total_pages}")
        answer = sum(sum(page_numbers) for page_numbers in numbers.values())
        submit_response = await request_with_backoff(
            client,
            "POST",
            "/captcha/api/slide_cylinder_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        submit_response.raise_for_status()
        submit_body = submit_response.json()
    result = public_result(submit_body if isinstance(submit_body, dict) else {})
    (HERE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("pages", total_pages, "answer", answer)
    print("result", json.dumps(result, ensure_ascii=False))
    return result


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
