"""Solve the spiderdemo font anti-crawl challenge.

Page text is ASCII digits. The woff2 cmap draws a different digit for each
code point. The ten outlines are stable; only the cmap permutation changes.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "font_anti_challenge"
PAGE_URL = "/font_anti/api/font_anti_challenge/page/{page}/?challenge_type=" + CHALLENGE
INIT_URL = "/font_anti/api/challenge/init/?challenge_type=" + CHALLENGE
SUBMIT_URL = "/font_anti/api/challenge/submit/"
OUT = Path(__file__).resolve().parent / "result.json"

# Outline hash -> digit the glyph actually draws. Confirmed by rasterizing
# one woff2; later pages reuse the same ten outlines.
DIGIT_BY_OUTLINE = {
    "ed8737ab5853": "0",
    "4faf287c6bcb": "1",
    "1f63a36f8fbb": "2",
    "fd445e48e44f": "3",
    "fb8718f1345f": "4",
    "8912139f833a": "5",
    "23445c031d4d": "6",
    "cc495172731f": "7",
    "7b931fce424d": "8",
    "39ad34f6fe79": "9",
}


def outline_hash(font: TTFont, glyph_name: str) -> str:
    pen = RecordingPen()
    font.getGlyphSet()[glyph_name].draw(pen)
    return hashlib.sha256(repr(pen.value).encode("utf-8")).hexdigest()[:12]


def digit_table(font_b64: str) -> dict[str, str]:
    font = TTFont(io.BytesIO(base64.b64decode(font_b64)))
    table: dict[str, str] = {}
    for code, name in (font.getBestCmap() or {}).items():
        digest = outline_hash(font, name)
        digit = DIGIT_BY_OUTLINE.get(digest)
        if digit is None:
            raise RuntimeError("unknown glyph outline")
        table[chr(code)] = digit
    if len(table) < 10:
        raise RuntimeError("font cmap is incomplete")
    return table


def decode_page(page_data: list, font_b64: str) -> list[int]:
    table = digit_table(font_b64)
    numbers: list[int] = []
    for raw in page_data:
        shown = "".join(table[char] for char in str(raw))
        if not shown.isdigit():
            raise RuntimeError("decoded value is not a number")
        numbers.append(int(shown))
    if len(numbers) != 10:
        raise RuntimeError("page did not contain 10 numbers")
    return numbers


async def fetch_page(client, page: int) -> list[int]:
    delay = 1.0
    for _ in range(8):
        response = await client.get(PAGE_URL.format(page=page))
        if response.status_code == 429 or response.status_code >= 500:
            retry_after = response.headers.get("Retry-After", "")
            wait = float(retry_after) if retry_after.isdigit() else delay
            await asyncio.sleep(wait)
            delay = min(delay * 2, 10.0)
            continue
        payload = response.json()
        if payload.get("success") and payload.get("b64Font"):
            return decode_page(payload["page_data"], payload["b64Font"])
        await asyncio.sleep(delay)
        delay = min(delay * 2, 10.0)
    raise RuntimeError(f"page {page} was not accepted")


async def main() -> None:
    session = SpiderSession()
    async with session.async_client() as client:
        init_response = await client.get(INIT_URL)
        init_payload = init_response.json()
        if init_payload.get("success") is not True:
            raise RuntimeError("challenge init was not accepted")
        init_page = [int(value) for value in init_payload["page_data"]]

        pages = await collect_pages(
            lambda page: fetch_page(client, page),
            range(1, 101),
            concurrency=4,
        )
        if pages[1] != init_page:
            raise RuntimeError("page 1 font decode does not match init")
        total = sum(number for values in pages.values() for number in values)
        submit = await client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        body = submit.json()
        result = public_result(body)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("pages", len(pages), "sum", total, "status", submit.status_code)
        print(json.dumps(result, ensure_ascii=False))
        if result.get("is_correct") is not True:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
