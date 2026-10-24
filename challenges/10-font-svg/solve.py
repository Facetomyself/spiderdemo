"""Solve font_svg_challenge by reading SVG glyph paths locally."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "font_svg_challenge"
ORIGIN_PAGE = (
    "https://www.spiderdemo.cn/font_anti/font_svg_challenge"
    "?challenge_type=font_svg_challenge"
)
INIT_URL = f"/font_anti/api/{CHALLENGE}/init/?challenge_type={CHALLENGE}"
PAGE_URL = "/font_anti/api/" + CHALLENGE + "/page/{page}/?challenge_type=" + CHALLENGE
SUBMIT_URL = f"/font_anti/api/{CHALLENGE}/submit/"
HERE = Path(__file__).resolve().parent
TOKEN = re.compile(r"[MmLlHhVvQqCcZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
ALIAS = {
    "O": "0",
    "o": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "l": "1",
    "|": "1",
    "Z": "2",
    "z": "2",
    "S": "5",
    "s": "5",
    "B": "8",
    "g": "9",
    "q": "9",
    "b": "6",
}

_OCR = None


def tokenize(path_d: str) -> list[str]:
    return TOKEN.findall(path_d)


def parse_subpaths(path_d: str) -> list[list[tuple[float, float]]]:
    tokens = tokenize(path_d)
    index = 0
    cx = cy = sx = sy = 0.0
    command = ""
    current: list[tuple[float, float]] = []
    subpaths: list[list[tuple[float, float]]] = []

    def read_num() -> float:
        nonlocal index
        value = float(tokens[index])
        index += 1
        return value

    def close_current() -> None:
        nonlocal current
        if len(current) >= 3:
            subpaths.append(current)
        current = []

    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command in "Zz":
            if current:
                current.append(current[0])
            close_current()
            cx, cy = sx, sy
            continue
        if command in "Mm":
            if current:
                close_current()
            x, y = read_num(), read_num()
            if command == "m":
                x += cx
                y += cy
            cx, cy = sx, sy = x, y
            current = [(cx, cy)]
            command = "L" if command == "M" else "l"
            continue
        if command in "Ll":
            x, y = read_num(), read_num()
            if command == "l":
                x += cx
                y += cy
            cx, cy = x, y
            current.append((cx, cy))
            continue
        if command in "Hh":
            x = read_num()
            if command == "h":
                x += cx
            cx = x
            current.append((cx, cy))
            continue
        if command in "Vv":
            y = read_num()
            if command == "v":
                y += cy
            cy = y
            current.append((cx, cy))
            continue
        if command in "Qq":
            x1, y1 = read_num(), read_num()
            x, y = read_num(), read_num()
            if command == "q":
                x1 += cx
                y1 += cy
                x += cx
                y += cy
            for step in range(1, 9):
                t = step / 8
                u = 1 - t
                current.append(
                    (
                        u * u * cx + 2 * u * t * x1 + t * t * x,
                        u * u * cy + 2 * u * t * y1 + t * t * y,
                    )
                )
            cx, cy = x, y
            continue
        raise ValueError(f"unsupported path command {command}")
    close_current()
    return subpaths


def apply_transform(points: list[tuple[float, float]], transform: str) -> list[tuple[float, float]]:
    match = re.search(
        r"translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*scale\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)",
        transform,
    )
    if not match:
        raise ValueError("unexpected glyph transform")
    tx, ty, sx, sy = (float(part) for part in match.groups())
    return [(x * sx + tx, y * sy + ty) for x, y in points]


def raster(subpaths: list[list[tuple[float, float]]], scale: float = 8.0) -> np.ndarray:
    mapped = [[(x * scale, y * scale) for x, y in sub] for sub in subpaths]
    xs = [x for sub in mapped for x, _ in sub]
    ys = [y for sub in mapped for _, y in sub]
    pad = 8
    min_x, min_y = min(xs), min(ys)
    width = int(np.ceil(max(xs) - min_x)) + pad * 2 + 2
    height = int(np.ceil(max(ys) - min_y)) + pad * 2 + 2
    mask = np.zeros((height, width), dtype=np.uint8)
    for sub in mapped:
        polygon = np.array(
            [[int(round(x - min_x + pad)), int(round(y - min_y + pad))] for x, y in sub],
            dtype=np.int32,
        )
        layer = np.zeros_like(mask)
        cv2.fillPoly(layer, [polygon], 255)
        mask = np.bitwise_xor(mask, layer)
    return 255 - mask


def normalize(image: np.ndarray) -> np.ndarray:
    ink = np.where(image < 128)
    if len(ink[0]) == 0:
        return np.full((48, 32), 255, dtype=np.uint8)
    y0, y1 = int(ink[0].min()), int(ink[0].max())
    x0, x1 = int(ink[1].min()), int(ink[1].max())
    crop = image[y0 : y1 + 1, x0 : x1 + 1]
    return cv2.resize(crop, (32, 48), interpolation=cv2.INTER_AREA)


def features(image: np.ndarray, parts: int) -> dict[str, float]:
    ink = image < 128
    ys, xs = np.where(ink)
    if len(ys) == 0:
        raise ValueError("empty glyph")
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    crop = ink[y0 : y1 + 1, x0 : x1 + 1]
    height, width = crop.shape
    return {
        "parts": float(parts),
        "aspect": width / height,
        "top": float(crop[: height // 2].mean()),
        "bot": float(crop[height // 2 :].mean()),
        "left": float(crop[:, : width // 2].mean()),
        "right": float(crop[:, width // 2 :].mean()),
    }


def rule_digit(feat: dict[str, float]) -> str:
    parts = int(feat["parts"])
    aspect = feat["aspect"]
    top, bot = feat["top"], feat["bot"]
    left, right = feat["left"], feat["right"]
    if parts >= 3:
        return "8"
    if parts == 2:
        if top + 0.04 < bot:
            return "6"
        if bot + 0.03 < top:
            return "9"
        return "0"
    if aspect < 0.65:
        return "1"
    if bot < 0.28 and top > bot + 0.15:
        return "7"
    if aspect > 0.82 and top + 0.1 < bot:
        return "4"
    if right > left + 0.05:
        return "3"
    if left > right + 0.04:
        return "5"
    return "2"


def get_ocr():
    global _OCR
    if _OCR is None:
        import ddddocr

        _OCR = ddddocr.DdddOcr(show_ad=False)
    return _OCR


def ocr_digit(image: np.ndarray, allowed: set[str]) -> str | None:
    text = str(get_ocr().classification(Image.fromarray(image)))
    chars = []
    for char in text:
        mapped = ALIAS.get(char, char)
        if mapped in allowed:
            chars.append(mapped)
    if len(chars) == 1:
        return chars[0]
    return None


def glyphs_from_svg(svg: str) -> list[dict]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(svg)
    glyphs = []
    for element in root:
        if not str(element.tag).endswith("path"):
            continue
        subpaths = [
            apply_transform(sub, element.attrib.get("transform", ""))
            for sub in parse_subpaths(element.attrib["d"])
        ]
        xs = [x for sub in subpaths for x, _ in sub]
        glyphs.append(
            {
                "x": min(xs),
                "parts": len(subpaths),
                "image": raster(subpaths),
            }
        )
    glyphs.sort(key=lambda item: item["x"])
    return glyphs


def split_numbers(glyphs: list[dict]) -> list[list[dict]]:
    if len(glyphs) < 2:
        return [glyphs]
    diffs = [glyphs[index + 1]["x"] - glyphs[index]["x"] for index in range(len(glyphs) - 1)]
    ordered = sorted(diffs)
    # Ten numbers leave nine larger gaps. Split at the midpoint of that knee.
    if len(ordered) < 10:
        threshold = 24.0
    else:
        threshold = (ordered[-10] + ordered[-9]) / 2
    groups: list[list[dict]] = [[glyphs[0]]]
    for index, diff in enumerate(diffs):
        if diff > threshold:
            groups.append([])
        groups[-1].append(glyphs[index + 1])
    return groups


def glyph_vector(image: np.ndarray) -> np.ndarray:
    sample = (normalize(image) < 128).astype(np.float32).ravel()
    return sample / (float(np.linalg.norm(sample)) + 1e-6)


def assign_digits(page_glyphs: dict[int, list[dict]]) -> dict[int, list[int]]:
    """Cluster every glyph, then name each cluster from the local OCR majority."""
    rows: list[np.ndarray] = []
    owners: list[dict] = []
    for page in sorted(page_glyphs):
        for glyph in page_glyphs[page]:
            rows.append(glyph_vector(glyph["image"]))
            owners.append(glyph)
    data = np.stack(rows).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.05)
    _compact, found, _centers = cv2.kmeans(
        data, 10, None, criteria, 6, cv2.KMEANS_PP_CENTERS
    )
    buckets: dict[int, list[dict]] = {}
    for glyph, cluster in zip(owners, found.ravel().tolist()):
        buckets.setdefault(int(cluster), []).append(glyph)
    mapping: dict[int, str] = {}
    report = []
    for cluster, glyphs in sorted(buckets.items()):
        step = max(1, len(glyphs) // 24)
        sample = glyphs[::step][:24]
        ocr_votes: Counter[str] = Counter()
        rule_votes: Counter[str] = Counter()
        for glyph in sample:
            feat = features(glyph["image"], glyph["parts"])
            rule_votes[rule_digit(feat)] += 1
            predicted = ocr_digit(glyph["image"], set("0123456789"))
            if predicted:
                ocr_votes[predicted] += 1
        if not ocr_votes:
            raise RuntimeError(f"cluster {cluster} has no OCR label")
        ocr_top, ocr_n = ocr_votes.most_common(1)[0]
        rule_top, _rule_n = rule_votes.most_common(1)[0]
        purity = ocr_n / sum(ocr_votes.values())
        if purity < 0.85:
            raise RuntimeError(f"cluster {cluster} impure {dict(ocr_votes)}")
        if ocr_top != rule_top and purity < 0.95:
            raise RuntimeError(
                f"cluster {cluster} ocr {dict(ocr_votes)} rule {dict(rule_votes)}"
            )
        mapping[cluster] = ocr_top
        report.append({"digit": ocr_top, "size": len(glyphs), "purity": round(purity, 3)})
    if set(mapping.values()) != set("0123456789"):
        raise RuntimeError(f"cluster labels {sorted(mapping.values())}")
    for glyph, cluster in zip(owners, found.ravel().tolist()):
        glyph["digit"] = mapping[int(cluster)]
    numbers: dict[int, list[int]] = {}
    for page, glyphs in page_glyphs.items():
        groups = split_numbers(glyphs)
        page_numbers = [int("".join(item["digit"] for item in group)) for group in groups]
        if len(page_numbers) != 10:
            raise RuntimeError(f"page {page} has {len(page_numbers)} numbers")
        numbers[page] = page_numbers
    print(json.dumps({"clusters": report}, ensure_ascii=False))
    return numbers


async def fetch_text(client, url: str) -> dict:
    delay = 0.5
    last = "request failed"
    for _ in range(6):
        response = await client.get(url)
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            last = "429"
            continue
        data = response.json()
        if response.status_code >= 400 or data.get("success") is False:
            last = str(data.get("error") or data.get("message") or response.status_code)
            if data.get("need_init"):
                raise RuntimeError(last)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        return data
    raise RuntimeError(last)


async def run(limit: int, submit: bool) -> None:
    session = SpiderSession()
    headers = {
        "Referer": ORIGIN_PAGE,
        "Accept": "application/json, text/plain, */*",
    }
    async with session.async_client(headers) as client:
        init = await fetch_text(client, INIT_URL)
        total = int(init.get("total_pages") or 100)
        last_page = min(total, limit)

        async def fetch_page(page: int) -> str:
            payload = await fetch_text(client, PAGE_URL.format(page=page))
            svg = payload.get("svg_content")
            if not isinstance(svg, str):
                raise RuntimeError(f"page {page} missing svg")
            return svg

        pages = await collect_pages(fetch_page, range(1, last_page + 1), concurrency=4)
        parsed = {page: glyphs_from_svg(pages[page]) for page in range(1, last_page + 1)}
        collected = assign_digits(parsed)
        answer = sum(value for page in collected.values() for value in page)
        summary = {
            "pages": last_page,
            "numbers": sum(len(item) for item in collected.values()),
            "answer": answer,
        }
        print(json.dumps(summary, ensure_ascii=False))
        if not submit:
            return
        if last_page != total:
            raise RuntimeError("refusing to submit a partial sum")
        response = await client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        payload = response.json()
        kept = public_result(payload)
        (HERE / "result.json").write_text(
            json.dumps(kept, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        message = str(payload.get("message") or "")
        correct = payload.get("is_correct") is True or ("正确" in message and "不正确" not in message and "错误" not in message)
        print(json.dumps({"http": response.status_code, "correct": correct, **kept}, ensure_ascii=False))
        if not correct:
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--no-submit", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.limit, submit=not args.no_submit))


if __name__ == "__main__":
    main()
