"""Solve the font-sprites challenge by matching sprite glyphs locally."""

from __future__ import annotations

import asyncio
import base64
import json
import re
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

HERE = Path(__file__).resolve().parent
TYPE = "font_sprites_challenge"
INIT_URL = "/font_anti/api/font_sprites_challenge/init/"
PAGE_URL = "/font_anti/api/font_sprites_challenge/page/{page}/"
SUBMIT_URL = "/font_anti/api/font_sprites_challenge/submit/"
POS_RE = re.compile(r"\.(class\d+)\{background-position:\s*(-?\d+)px")
CLASS_RE = re.compile(r"sprite (class\d+)")
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.spiderdemo.cn/font_anti/font_sprites_challenge/?challenge_type=font_sprites_challenge",
    "X-Requested-With": "XMLHttpRequest",
}


def load_sprite(payload: dict) -> Image.Image:
    return Image.open(BytesIO(base64.b64decode(payload["sprite"]))).convert("RGBA")


def class_positions(css: str) -> dict[str, int]:
    found: dict[str, int] = {}
    for name, raw_x in POS_RE.findall(css or ""):
        value = int(raw_x)
        previous = found.get(name)
        if previous is not None and previous != value:
            raise ValueError(f"conflicting position for {name}")
        found[name] = value
    if not found:
        raise ValueError("css has no sprite positions")
    return found


def cell_index(position: int, cell_w: int) -> int:
    # The sheet is 10 cells of cell_w. The first glyph is inset by 8px,
    # so -8//50 == 0 and -58//50 == 1. Do not derive the origin from the
    # smallest position on the page: an unused first cell would shift every index.
    index = (-position) // cell_w
    if not 0 <= index <= 9:
        raise ValueError(f"position {position} is outside the sprite")
    return index


def glyph_bytes(image: Image.Image, index: int, cell_w: int) -> bytes:
    cell = image.crop((index * cell_w, 0, (index + 1) * cell_w, image.height)).convert("L")
    mask = cell.point(lambda pixel: 255 if pixel < 180 else 0)
    box = mask.getbbox()
    if box is None:
        raise ValueError(f"empty glyph at {index}")
    ink = cell.crop(box).point(lambda pixel: 0 if pixel < 180 else 255)
    return ink.size[0].to_bytes(2, "big") + ink.size[1].to_bytes(2, "big") + ink.tobytes()


def numbers_from_glyphs(
    payload: dict,
    image: Image.Image,
    templates: dict[bytes, str],
) -> list[int]:
    positions = class_positions(payload.get("css_code") or "")
    cell_w = image.width // 10
    sheet = [glyph_bytes(image, index, cell_w) for index in range(10)]
    if len({templates[signature] for signature in sheet}) != 10:
        raise ValueError("sprite is not a permutation of 0-9")
    numbers: list[int] = []
    for html in payload["page_data"]:
        classes = CLASS_RE.findall(html)
        if len(classes) != 4:
            raise ValueError(f"expected 4 glyphs, got {len(classes)}")
        digits = []
        for name in classes:
            index = cell_index(positions[name], cell_w)
            signature = sheet[index]
            try:
                digits.append(templates[signature])
            except KeyError as exc:
                raise KeyError(f"unknown glyph at offset {positions[name]}") from exc
        numbers.append(int("".join(digits)))
    return numbers


def templates_from_page1(plain: list[int], payload: dict) -> dict[bytes, str]:
    image = load_sprite(payload)
    positions = class_positions(payload.get("css_code") or "")
    cell_w = image.width // 10
    templates: dict[bytes, str] = {}
    for number, html in zip(plain, payload["page_data"], strict=True):
        classes = CLASS_RE.findall(html)
        rendered = f"{int(number):0{len(classes)}d}"
        if len(rendered) != len(classes):
            raise ValueError(f"digit width mismatch for {number}")
        for digit, name in zip(rendered, classes, strict=True):
            signature = glyph_bytes(image, cell_index(positions[name], cell_w), cell_w)
            previous = templates.get(signature)
            if previous is not None and previous != digit:
                raise ValueError("one glyph image maps to two digits")
            templates[signature] = digit
    if len(templates) != 10:
        raise ValueError(f"expected 10 glyph templates, got {len(templates)}")
    return templates


def plain_numbers(payload: dict) -> list[int] | None:
    page_data = payload.get("page_data") or []
    if len(page_data) != 10:
        return None
    if all(isinstance(item, int) for item in page_data):
        return [int(item) for item in page_data]
    if all(isinstance(item, str) and item.isdigit() for item in page_data):
        return [int(item) for item in page_data]
    return None


async def fetch_page(client: httpx.AsyncClient, page: int) -> dict:
    delay = 0.4
    last = "empty"
    for _attempt in range(8):
        try:
            response = await client.get(PAGE_URL.format(page=page), params={"challenge_type": TYPE})
        except httpx.TransportError as exc:
            last = type(exc).__name__
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8)
            continue
        if response.status_code == 429:
            last = "429"
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8)
            continue
        response.raise_for_status()
        data = response.json()
        if data.get("success") and data.get("page_data") and data.get("sprite"):
            return data
        last = str(data.get("error") or data.get("message") or data.get("success"))
        if data.get("need_init"):
            raise RuntimeError("need_init")
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8)
    raise RuntimeError(f"page {page} failed: {last}")


async def solve() -> dict:
    session = SpiderSession()
    async with session.async_client(HEADERS) as client:
        init_response = await client.get(INIT_URL, params={"challenge_type": TYPE})
        init_response.raise_for_status()
        init_payload = init_response.json()
        if not init_payload.get("success"):
            raise RuntimeError(init_payload.get("error") or "init failed")
        plain = plain_numbers(init_payload)
        if plain is None:
            raise RuntimeError("init did not return page 1 plaintext")
        total_pages = int(init_payload.get("total_pages") or 100)
        page1 = await fetch_page(client, 1)
        templates = templates_from_page1(plain, page1)
        checked = numbers_from_glyphs(page1, load_sprite(page1), templates)
        if checked != plain:
            raise RuntimeError("page 1 template round-trip failed")

        async def fetch(page: int) -> list[int]:
            last = "empty"
            for _attempt in range(4):
                payload = await fetch_page(client, page)
                if int(payload.get("current_page") or 0) != page:
                    last = "current_page"
                    continue
                try:
                    return numbers_from_glyphs(payload, load_sprite(payload), templates)
                except (KeyError, ValueError) as exc:
                    last = str(exc)
            raise RuntimeError(f"page {page} decode failed: {last}")

        decoded = await collect_pages(fetch, range(1, total_pages + 1), concurrency=4)
        if decoded[1] != plain:
            raise RuntimeError("page 1 changed while collecting")
        answer = sum(sum(numbers) for numbers in decoded.values())
        submit = await client.post(SUBMIT_URL, json={"challenge_type": TYPE, "answer": answer})
        submit.raise_for_status()
        body = submit.json()
    result = public_result(body)
    (HERE / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("pages", total_pages, "templates", len(templates), "answer", answer)
    print("submit_keys", sorted(body))
    print("result", json.dumps(result, ensure_ascii=False))
    return result


def main() -> None:
    asyncio.run(solve())


if __name__ == "__main__":
    main()
