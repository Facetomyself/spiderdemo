"""Solve cap1_challenge: sum 100 pages, local captcha only.

Run with PYTHONPATH=D:\\reverse_ENV\\workspace\\spiderdemo.
"""

from __future__ import annotations

import asyncio
import contextlib
import itertools
import json
from io import BytesIO
from pathlib import Path

import ddddocr
from PIL import Image, ImageDraw, ImageFont

from modules.runtime import SpiderSession, collect_pages, public_result

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CHALLENGE = "cap1_challenge"
ORIGIN_PAGE = "https://www.spiderdemo.cn/captcha/cap1_challenge?challenge_type=cap1_challenge"
INIT_URL = "/captcha/api/cap1_challenge/init/?challenge_type=cap1_challenge"
PAGE_URL = "/captcha/api/cap1_challenge/page/"
IMAGE_URL = "/captcha/api/cap1_challenge/captcha_image/"
SUBMIT_URL = "/captcha/api/cap1_challenge/submit/"
HEADERS = {"Referer": ORIGIN_PAGE, "Content-Type": "application/json"}
HERE = Path(__file__).resolve().parent


def bitmap(image: Image.Image) -> tuple[tuple[int, ...], ...]:
    src = image.load()
    return tuple(
        tuple(1 if src[x, y] < 128 else 0 for x in range(image.size[0]))
        for y in range(image.size[1])
    )


def crop_ink(image: Image.Image) -> Image.Image:
    box = image.point(lambda p: 255 if p < 128 else 0).getbbox()
    if box is None:
        return image
    return image.crop(box)


def templates() -> dict[str, tuple[tuple[int, ...], ...]]:
    font = ImageFont.load_default()
    found = {}
    for char in ALPHABET:
        image = Image.new("L", (32, 32), 255)
        ImageDraw.Draw(image).text((2, 2), char, font=font, fill=0)
        found[char] = bitmap(crop_ink(image))
    return found


def binarize(raw: bytes) -> Image.Image:
    image = Image.open(BytesIO(raw)).convert("RGB")
    width, height = image.size
    mask = Image.new("L", (width, height), 255)
    src = image.load()
    dst = mask.load()
    for y in range(height):
        for x in range(width):
            red, green, blue = src[x, y]
            level = max(red, green, blue)
            if level < 130 and level - min(red, green, blue) < 45:
                dst[x, y] = 0
    return mask


def _drop_isolated(image: Image.Image) -> Image.Image:
    width, height = image.size
    src = image.load()
    kept = Image.new("L", (width, height), 255)
    dst = kept.load()
    for y in range(height):
        for x in range(width):
            if src[x, y] >= 128:
                continue
            neighbors = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and src[nx, ny] < 128:
                        neighbors += 1
            if neighbors:
                dst[x, y] = 0
    return kept


def text_band(image: Image.Image) -> Image.Image:
    """Capitals occupy 8 rows; descenders add 2 more."""
    width, height = image.size
    src = image.load()
    counts = [sum(src[x, y] < 128 for x in range(width)) for y in range(height)]
    window = 10
    best_top, best_score = 0, -1
    for top in range(0, max(1, height - window + 1)):
        score = sum(counts[top : top + window])
        if score > best_score:
            best_top, best_score = top, score
    band = image.crop((0, best_top, width, min(height, best_top + window)))
    return _drop_isolated(band)


def _column_groups(image: Image.Image) -> list[list[int]]:
    width, height = image.size
    src = image.load()
    cols = [sum(src[x, y] < 128 for y in range(height)) for x in range(width)]
    groups: list[list[int]] = []
    start = None
    for x, count in enumerate(cols + [0]):
        if count > 0 and start is None:
            start = x
        elif count == 0 and start is not None:
            groups.append([start, x])
            start = None
    changed = True
    while changed:
        changed = False
        rebuilt: list[list[int]] = []
        for left, right in groups:
            if right - left <= 8:
                rebuilt.append([left, right])
                continue
            interior = list(range(left + 2, right - 2))
            if not interior:
                rebuilt.append([left, right])
                continue
            split = min(interior, key=lambda col: cols[col])
            if cols[split] <= 2 and left + 2 < split < right - 2:
                rebuilt.append([left, split])
                rebuilt.append([split + 1, right])
                changed = True
            else:
                rebuilt.append([left, right])
        groups = rebuilt
    return groups


def glyphs(image: Image.Image) -> list[Image.Image]:
    band = text_band(image)
    width, height = band.size
    src = band.load()
    ranked: list[tuple[int, int, int]] = []
    for left, right in _column_groups(band):
        ys = [y for y in range(height) for x in range(left, right) if src[x, y] < 128]
        if not ys:
            continue
        if max(ys) - min(ys) + 1 >= 6:
            ranked.append((len(ys), left, right))
    ranked.sort(key=lambda item: item[1])
    while len(ranked) > 4:
        glued = False
        for index in range(len(ranked) - 1):
            area, left, right = ranked[index]
            next_area, next_left, next_right = ranked[index + 1]
            if next_left - right == 1 and next_right - left <= 8:
                ranked = (
                    ranked[:index]
                    + [(area + next_area, left, next_right)]
                    + ranked[index + 2 :]
                )
                glued = True
                break
        if not glued:
            break
    if len(ranked) > 4:
        ranked = sorted(ranked, reverse=True)[:4]
        ranked.sort(key=lambda item: item[1])
    out = []
    for _, left, right in ranked:
        glyph = crop_ink(band.crop((left, 0, right, height)))
        if glyph.size[0] >= 1 and glyph.size[1] >= 4:
            out.append(glyph)
    return out


def score(obs: tuple[tuple[int, ...], ...], tmpl: tuple[tuple[int, ...], ...]) -> int:
    oh, ow = len(obs), len(obs[0]) if obs else 0
    th, tw = len(tmpl), len(tmpl[0])
    best = 10**9
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            miss = 0
            for y in range(th):
                for x in range(tw):
                    oy, ox = y + dy, x + dx
                    seen = obs[oy][ox] if 0 <= oy < oh and 0 <= ox < ow else 0
                    if seen != tmpl[y][x]:
                        miss += 1
            for y in range(oh):
                for x in range(ow):
                    ty, tx = y - dy, x - dx
                    if obs[y][x] and not (0 <= ty < th and 0 <= tx < tw):
                        miss += 1
            best = min(best, miss)
    return best


def candidate_strings(raw: bytes, bank: dict[str, tuple[tuple[int, ...], ...]]) -> list[tuple[str, int]]:
    parts = glyphs(binarize(raw))
    if len(parts) != 4:
        return []
    options = []
    for glyph in parts:
        ranked = sorted((score(bitmap(glyph), tmpl), char) for char, tmpl in bank.items())
        best = ranked[0][0]
        chosen = [(char, item_score) for item_score, char in ranked if item_score <= best + 1][:3]
        names = {char for char, _item in chosen}
        if "I" in names or "l" in names:
            extra = "l" if "I" in names else "I"
            if extra not in names:
                chosen.append((extra, best))
        options.append(chosen)
    guesses = []
    for combo in itertools.product(*options):
        text = "".join(char for char, _item in combo)
        total = sum(item_score for _char, item_score in combo)
        guesses.append((text, total))
    guesses.sort(key=lambda item: item[1])
    unique = []
    seen = set()
    for text, total in guesses:
        if text in seen:
            continue
        seen.add(text)
        unique.append((text, total))
        if len(unique) >= 12:
            break
    return unique


def ocr_text(raw: bytes, engine: ddddocr.DdddOcr) -> str:
    band = text_band(binarize(raw))
    scaled = band.resize((max(1, band.size[0] * 4), band.size[1] * 4), Image.Resampling.NEAREST)
    text = engine.classification(scaled)
    if not isinstance(text, str):
        return ""
    chars = "".join(char for char in text if char in ALPHABET)
    return chars if len(chars) == 4 else ""


def as_json(response) -> dict:
    try:
        data = response.json()
    except Exception:
        return {"success": False, "error": f"HTTP {response.status_code}"}
    if not isinstance(data, dict):
        return {"success": False, "error": f"HTTP {response.status_code}"}
    return data


def numbers_of(page_data) -> list[int]:
    if not isinstance(page_data, list) or len(page_data) != 10:
        raise RuntimeError("page payload is not 10 numbers")
    return [int(item) for item in page_data]


def accepted(payload: dict) -> bool:
    if payload.get("is_correct") is True or payload.get("correct") is True:
        return True
    if payload.get("completed") is True and payload.get("is_correct") is not False:
        return True
    for key in ("message", "msg"):
        text = payload.get(key)
        if isinstance(text, str) and "正确" in text:
            return True
    return False


async def backoff(response, delay: float) -> float:
    if response.status_code != 429:
        return delay
    await asyncio.sleep(delay)
    return min(delay * 2, 8.0)


async def load_page(client, page: int, bank, engine, ocr_lock: asyncio.Lock) -> list[int]:
    delay = 1.0
    last = "unsolved"
    for attempt in range(10):
        image = await client.get(IMAGE_URL, params={"t": f"{page}-{attempt}"})
        if image.status_code == 429:
            delay = await backoff(image, delay)
            last = "429"
            continue
        try:
            guesses = candidate_strings(image.content, bank)
        except Exception:
            last = "bad-image"
            continue
        need_ocr = not guesses or guesses[0][1] > 0
        if need_ocr:
            async with ocr_lock:
                try:
                    alt = await asyncio.to_thread(ocr_text, image.content, engine)
                except Exception:
                    alt = ""
            if alt and alt not in {text for text, _score in guesses}:
                guesses.append((alt, 50))
        if not guesses:
            last = "no-guess"
            continue
        for code, _score in guesses:
            resp = await client.post(
                PAGE_URL,
                json={"captcha_input": code, "page_num": page, "challenge_type": CHALLENGE},
            )
            if resp.status_code == 429:
                delay = await backoff(resp, delay)
                resp = await client.post(
                    PAGE_URL,
                    json={"captcha_input": code, "page_num": page, "challenge_type": CHALLENGE},
                )
            data = as_json(resp)
            if data.get("success") is True:
                return numbers_of(data.get("page_data"))
            last = str(data.get("error") or resp.status_code)
    raise RuntimeError(f"page {page} {last}")


async def solve_all(bank, engine) -> dict:
    sessions = [SpiderSession() for _ in range(4)]
    async with contextlib.AsyncExitStack() as stack:
        clients = []
        for session in sessions:
            client = await stack.enter_async_context(session.async_client(headers=HEADERS))
            clients.append(client)
        init_resp = await clients[0].get(INIT_URL)
        if init_resp.status_code == 429:
            await asyncio.sleep(2)
            init_resp = await clients[0].get(INIT_URL)
        init_payload = as_json(init_resp)
        if init_payload.get("success") is not True:
            raise RuntimeError(init_payload.get("error") or "init failed")
        page1 = numbers_of(init_payload.get("page_data"))
        total_pages = int(init_payload.get("total_pages") or 100)
        print(f"init ok pages {total_pages}", flush=True)
        pool: asyncio.Queue = asyncio.Queue()
        for client in clients:
            pool.put_nowait(client)
        ocr_lock = asyncio.Lock()
        done = 0

        async def fetch_page(page: int) -> list[int]:
            nonlocal done
            client = await pool.get()
            try:
                values = await load_page(client, page, bank, engine, ocr_lock)
            finally:
                pool.put_nowait(client)
            done += 1
            if done % 10 == 0 or done == total_pages - 1:
                print(f"collected {done}", flush=True)
            return values

        fetched = await collect_pages(fetch_page, range(2, total_pages + 1), concurrency=4)
        ordered = [page1]
        for page in range(2, total_pages + 1):
            ordered.append(fetched[page])
        answer = sum(sum(values) for values in ordered)
        delay = 1.0
        submit_resp = None
        for _ in range(5):
            submit_resp = await clients[0].post(
                SUBMIT_URL,
                json={"challenge_type": CHALLENGE, "answer": answer},
            )
            if submit_resp.status_code != 429:
                break
            delay = await backoff(submit_resp, delay)
        payload = as_json(submit_resp)
        print(
            "submit",
            submit_resp.status_code,
            payload.get("is_correct"),
            payload.get("message") or payload.get("error"),
            flush=True,
        )
        return payload


def main() -> None:
    bank = templates()
    engine = ddddocr.DdddOcr(show_ad=False, beta=True)
    payload = asyncio.run(solve_all(bank, engine))
    public = public_result(payload)
    (HERE / "result.json").write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not accepted(payload):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
