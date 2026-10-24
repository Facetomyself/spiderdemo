"""Solve the cap3 math-captcha number sum locally.

Page 1 comes from init. Later pages need the sliced expression image.
ddddocr reads the stitched image first. A local PIL font match is used
when that read is not a valid expression. No captcha image is stored.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import re
from pathlib import Path

import ddddocr
from PIL import Image, ImageDraw, ImageFont

from modules.runtime import SpiderSession, collect_pages, public_result

HERE = Path(__file__).resolve().parent
CHALLENGE = "cap3_challenge"
PAGE_URL = "/captcha/cap3_challenge/?challenge_type=cap3_challenge"
INIT_URL = f"/captcha/api/cap3_challenge/init/?challenge_type={CHALLENGE}"
IMAGE_URL = "/captcha/api/cap3_challenge/captcha_image/"
DATA_URL = "/captcha/api/cap3_challenge/page/"
SUBMIT_URL = "/captcha/api/cap3_challenge/submit/"
DIGITS = "0123456789"
OPERATORS = "+-*xX"
EXPR = re.compile(r"^(\d+)([+\-*/])(\d+)$")
HEADERS = {"Referer": "https://www.spiderdemo.cn" + PAGE_URL}


def stitch(parts: list[str]) -> Image.Image:
    images = [Image.open(io.BytesIO(base64.b64decode(part))).convert("RGB") for part in parts]
    width = sum(image.width for image in images)
    height = max(image.height for image in images)
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    offset = 0
    for image in images:
        canvas.paste(image, (offset, 0))
        offset += image.width
    return canvas


def binarize(image: Image.Image, limit: int = 145) -> Image.Image:
    raw = image.convert("RGB").load()
    canvas = Image.new("L", image.size, 255)
    pixels = canvas.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue = raw[x, y]
            spread = max(red, green, blue) - min(red, green, blue)
            lum = (red + green + blue) // 3
            if spread <= 30 and lum <= limit:
                pixels[x, y] = 0
    return canvas


def ink_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    raw = image.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(image.height):
        for x in range(image.width):
            if raw[x, y] < 128:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def text_band(image: Image.Image, band_height: int = 10) -> Image.Image:
    raw = image.load()
    rows = [sum(1 for x in range(image.width) if raw[x, y] < 128) for y in range(image.height)]
    best_top = 0
    best_score = -1
    last = max(1, image.height - band_height + 1)
    for top in range(last):
        score = sum(rows[top : top + band_height])
        if score > best_score:
            best_score = score
            best_top = top
    canvas = Image.new("L", image.size, 255)
    pixels = canvas.load()
    for y in range(best_top, min(image.height, best_top + band_height)):
        for x in range(image.width):
            pixels[x, y] = raw[x, y]
    return canvas


def glyphs(image: Image.Image) -> list[tuple[tuple[int, int, int, int], Image.Image]]:
    banded = text_band(image)
    outer = ink_bbox(banded)
    if not outer:
        return []
    cropped = banded.crop(outer)
    raw = cropped.load()
    found: list[tuple[tuple[int, int, int, int], Image.Image]] = []
    start = None
    for x in range(cropped.width + 1):
        count = 0 if x == cropped.width else sum(1 for y in range(cropped.height) if raw[x, y] < 128)
        if count and start is None:
            start = x
        elif not count and start is not None:
            piece = cropped.crop((start, 0, x, cropped.height))
            box = ink_bbox(piece)
            if box and box[2] - box[0] >= 2 and box[3] - box[1] >= 3:
                glyph = piece.crop(box)
                absolute = (
                    outer[0] + start + box[0],
                    outer[1] + box[1],
                    outer[0] + start + box[2],
                    outer[1] + box[3],
                )
                found.append((absolute, glyph))
            start = None
    return found


def _runs(mask: set[tuple[int, int]]) -> tuple[int, int]:
    by_row: dict[int, list[int]] = {}
    by_col: dict[int, list[int]] = {}
    for x, y in mask:
        by_row.setdefault(y, []).append(x)
        by_col.setdefault(x, []).append(y)

    def longest(groups: dict[int, list[int]]) -> int:
        best = 0
        for values in groups.values():
            ordered = sorted(values)
            run = 1
            for previous, current in zip(ordered, ordered[1:]):
                if current == previous + 1:
                    run += 1
                else:
                    best = max(best, run)
                    run = 1
            best = max(best, run)
        return best

    return longest(by_row), longest(by_col)


def operator_in_box(image: Image.Image, box: tuple[int, int, int, int]) -> str | None:
    raw = image.convert("RGB").load()
    left, top, right, bottom = box
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)
    ink: set[tuple[int, int]] = set()
    for y in range(top, bottom):
        for x in range(left, right):
            red, green, blue = raw[x, y]
            spread = max(red, green, blue) - min(red, green, blue)
            lum = (red + green + blue) // 3
            if spread <= 22 and lum <= 188 and not (red == green == blue and red >= 192):
                ink.add((x, y))
    if len(ink) < 3:
        return None
    horizontal, vertical = _runs(ink)
    if horizontal >= 3 and vertical >= 3:
        return "+"
    if horizontal >= 3 and vertical <= 2:
        return "-"
    return "*"


def _font_bank() -> list[tuple[str, Image.Image]]:
    bank: list[tuple[str, Image.Image]] = []
    for size in (10, 12, 14, 16, 18, 20):
        font = ImageFont.load_default(size)
        for char in DIGITS + OPERATORS:
            canvas = Image.new("L", (80, 80), 255)
            ImageDraw.Draw(canvas).text((4, 4), char, font=font, fill=0)
            box = ink_bbox(canvas)
            if box:
                bank.append((char, canvas.crop(box)))
    return bank


def _iou(left: Image.Image, right: Image.Image) -> float:
    if left.size != right.size:
        right = right.resize(left.size, Image.Resampling.NEAREST)
    paired = zip(left.getdata(), right.getdata())
    both = 0
    either = 0
    for left_value, right_value in paired:
        left_bit = left_value < 128
        right_bit = right_value < 128
        both += left_bit and right_bit
        either += left_bit or right_bit
    return both / either if either else 0.0


def _best(glyph: Image.Image, bank: list[tuple[str, Image.Image]], allowed: str) -> tuple[str, float]:
    ranked = [(_iou(glyph, image), char) for char, image in bank if char in allowed]
    ranked.sort(reverse=True)
    if not ranked:
        return "", 0.0
    return ranked[0][1], ranked[0][0]


def _normalize_operator(char: str) -> str:
    if char in {"x", "X", "*"}:
        return "*"
    return char


def _evaluate(expression: str) -> int | None:
    match = EXPR.fullmatch(expression.replace(" ", ""))
    if not match:
        return None
    left = int(match.group(1))
    operator = match.group(2)
    right = int(match.group(3))
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if right == 0:
        return None
    if left % right != 0:
        return None
    return left // right


def _from_glyphs(
    source: Image.Image,
    parts: list[tuple[tuple[int, int, int, int], Image.Image]],
    bank: list[tuple[str, Image.Image]],
) -> str | None:
    digits: list[tuple[tuple[int, int, int, int], str]] = []
    for box, glyph in parts:
        if glyph.height <= 5:
            continue
        char, score = _best(glyph, bank, DIGITS)
        if score < 0.55:
            return None
        digits.append((box, char))
    if not digits:
        return None
    chars = [digits[0][1]]
    operators = 0
    for previous, current in zip(digits, digits[1:]):
        gap = (
            previous[0][2],
            min(previous[0][1], current[0][1]) - 1,
            current[0][0],
            max(previous[0][3], current[0][3]) + 1,
        )
        if gap[2] - gap[0] >= 3:
            operator = operator_in_box(source, gap)
            if operator:
                chars.append(operator)
                operators += 1
        chars.append(current[1])
    if operators != 1:
        return None
    return "".join(chars)


def read_expression(image: Image.Image, reader: ddddocr.DdddOcr, bank: list[tuple[str, Image.Image]]) -> int | None:
    payload = io.BytesIO()
    image.save(payload, format="PNG")
    ocr_text = reader.classification(payload.getvalue())
    ocr_value = _evaluate(_normalize_expression(ocr_text))
    expression = _from_glyphs(image, glyphs(binarize(image)), bank)
    template_value = _evaluate(_normalize_expression(expression or ""))
    if template_value is not None:
        return template_value
    return ocr_value


def _normalize_expression(text: str) -> str:
    cleaned = text.strip().replace(" ", "")
    cleaned = cleaned.replace("×", "*").replace("✕", "*").replace("x", "*").replace("X", "*")
    cleaned = cleaned.replace("÷", "/")
    return cleaned


class Collector:
    def __init__(self, client, reader: ddddocr.DdddOcr, bank: list[tuple[str, Image.Image]]) -> None:
        self.client = client
        self.reader = reader
        self.bank = bank
        self.page_one: list[int] = []
        # The image endpoint keeps one answer in the session. A second fetch expires it.
        self.captcha_slot = asyncio.Lock()

    async def fetch_page(self, page: int) -> list[int]:
        if page == 1:
            return list(self.page_one)
        delay = 1.0
        last_error = "captcha not accepted"
        for _attempt in range(12):
            data_response = None
            async with self.captcha_slot:
                image_response = await self.client.get(IMAGE_URL, params={"t": page})
                if image_response.status_code == 429:
                    last_error = "429"
                else:
                    image_response.raise_for_status()
                    image = stitch(image_response.json()["data"])
                    answer = read_expression(image, self.reader, self.bank)
                    data_response = None
                    if answer is None:
                        last_error = "unreadable expression"
                    else:
                        data_response = await self.client.post(
                            DATA_URL,
                            json={
                                "captcha_input": str(answer),
                                "page_num": page,
                                "challenge_type": CHALLENGE,
                            },
                        )
            if image_response.status_code == 429 or (data_response is not None and data_response.status_code == 429):
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8.0)
                last_error = "429"
                continue
            if data_response is None:
                continue
            payload = data_response.json()
            if payload.get("success") and isinstance(payload.get("page_data"), list):
                print(f"page {page} ok", flush=True)
                return [int(value) for value in payload["page_data"]]
            last_error = str(payload.get("error") or payload.get("message") or data_response.status_code)
        raise RuntimeError(f"page {page} failed: {last_error}")


async def _run() -> dict:
    reader = ddddocr.DdddOcr(show_ad=False)
    reader.set_ranges(DIGITS + "+-*xX=")
    bank = _font_bank()
    session = SpiderSession()
    async with session.async_client(headers=HEADERS) as client:
        init_response = await client.get(INIT_URL)
        init_response.raise_for_status()
        init_payload = init_response.json()
        if not init_payload.get("success"):
            raise RuntimeError(str(init_payload.get("error") or init_payload.get("message") or "init failed"))
        total = int(init_payload.get("total_pages") or 100)
        collector = Collector(client, reader, bank)
        collector.page_one = [int(value) for value in init_payload["page_data"]]
        pages = await collect_pages(collector.fetch_page, range(1, total + 1), concurrency=4)
        missing = [page for page in range(1, total + 1) if page not in pages]
        if missing:
            raise RuntimeError(f"missing pages: {missing[:5]}")
        answer = sum(sum(pages[page]) for page in range(1, total + 1))
        submit_response = await client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        submit_response.raise_for_status()
        payload = submit_response.json()
    result = public_result(payload)
    (HERE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if result.get("is_correct") is not True and "正确" not in str(result.get("message") or ""):
        raise RuntimeError(str(result.get("message") or result.get("error") or "submit was not accepted"))
    return result


def main() -> None:
    result = asyncio.run(_run())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
