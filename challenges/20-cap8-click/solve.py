"""Solve the cap8 click-captcha number sum without a browser or remote OCR."""

from __future__ import annotations

import asyncio
import base64
import io
import itertools
import json
import threading
from pathlib import Path

import cv2
import ddddocr
import numpy as np
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

HERE = Path(__file__).resolve().parent
CHALLENGE = "cap8_challenge"
HEADER_Y = 48
GLYPH = 40
PAGE_ATTEMPTS = 8
CALIBRATION_FRAMES = 8
CONCURRENCY = 4

_DETECTOR = ddddocr.DdddOcr(det=True, ocr=False, show_ad=False)
_DETECT_LOCK = threading.Lock()


def _encode_points(points: list[list[int]]) -> str:
    raw = json.dumps(points, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def _content_norm(mask: np.ndarray, size: int = GLYPH) -> np.ndarray:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return np.zeros((size, size), np.float32)
    x1, x2 = int(xs.min()), int(xs.max())
    y1, y2 = int(ys.min()), int(ys.max())
    sub = mask[y1 : y2 + 1, x1 : x2 + 1]
    height, width = sub.shape
    side = max(height, width, 1)
    canvas = np.zeros((side, side), np.uint8)
    y0 = (side - height) // 2
    x0 = (side - width) // 2
    canvas[y0 : y0 + height, x0 : x0 + width] = sub
    resized = cv2.resize(canvas, (size, size), interpolation=cv2.INTER_AREA)
    out = (resized > 40).astype(np.float32)
    norm = float(np.linalg.norm(out))
    if norm < 1e-6:
        return out
    return out / norm


def _prompt_mask(crop: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return mask


def _rotate(mask: np.ndarray, angle: float) -> np.ndarray:
    height, width = mask.shape
    matrix = cv2.getRotationMatrix2D((width / 2.0, height / 2.0), angle, 1.0)
    return cv2.warpAffine(mask, matrix, (width, height), flags=cv2.INTER_NEAREST, borderValue=0)


def _best_score(body: np.ndarray, template: np.ndarray) -> float:
    best = -1.0
    height, width = body.shape
    center = (width / 2.0, height / 2.0)
    for angle in range(0, 360, 12):
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(body, matrix, (width, height), flags=cv2.INTER_NEAREST, borderValue=0)
        score = float(np.dot(_content_norm(rotated).ravel(), template.ravel()))
        if score > best:
            best = score
    return best


def _components(diff: np.ndarray, threshold: int, kernel: int) -> list[tuple[list[int], tuple[int, int], np.ndarray]]:
    raw = (diff > threshold).astype(np.uint8)
    raw[:HEADER_Y, :] = 0
    dilated = cv2.dilate(raw, np.ones((kernel, kernel), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(dilated, 8)
    found = []
    for index in range(1, count):
        x, y, width, height, area = [int(value) for value in stats[index]]
        if area < 100 or width < 14 or height < 14 or width > 80 or height > 80:
            continue
        stroke = (labels[y : y + height, x : x + width] == index) & (raw[y : y + height, x : x + width] > 0)
        ys, xs = np.where(stroke)
        if len(xs) < 15:
            continue
        cx = int(round(float(xs.mean()) + x))
        cy = int(round(float(ys.mean()) + y))
        found.append(([x, y, x + width, y + height], (cx, cy), (stroke.astype(np.uint8) * 255)))
    return found


def _body_glyphs(image: np.ndarray, background: np.ndarray) -> list[tuple[tuple[int, int], np.ndarray, list[int]]]:
    diff = np.abs(image.astype(np.int16) - background.astype(np.int16)).max(axis=2)
    for threshold, kernel in ((30, 9), (36, 7), (24, 7), (30, 5), (42, 9)):
        found = _components(diff, threshold, kernel)
        if len(found) == 4:
            return [(point, mask, box) for box, point, mask in found]
    return []


def _header_targets(image: np.ndarray, raw: bytes) -> list[np.ndarray]:
    with _DETECT_LOCK:
        boxes = _DETECTOR.detection(raw)
    header = []
    detected_body = []
    for box in boxes:
        x1, y1, x2, y2 = [int(value) for value in box]
        if x2 - x1 < 8 or y2 - y1 < 8:
            continue
        if (y1 + y2) / 2 < HEADER_Y:
            header.append((x1, y1, x2, y2))
        else:
            detected_body.append((x1, y1, x2, y2))
    header.sort(key=lambda box: box[0])
    if len(header) < 4:
        return [], detected_body
    templates = []
    for x1, y1, x2, y2 in header[-4:]:
        templates.append(_content_norm(_prompt_mask(image[y1:y2, x1:x2])))
    return templates, detected_body


def locate_clicks(raw: bytes, background: np.ndarray) -> list[list[int]] | None:
    image = np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
    if image.shape[:2] != background.shape[:2]:
        return None
    templates, detected_body = _header_targets(image, raw)
    glyphs = _body_glyphs(image, background)
    if len(templates) != 4 or len(glyphs) != 4:
        return None
    scores = np.zeros((4, 4), np.float32)
    for i, template in enumerate(templates):
        for j, (_, mask, _) in enumerate(glyphs):
            scores[i, j] = _best_score(mask, template)
    best_total = -1e9
    best_perm = None
    for perm in itertools.permutations(range(4)):
        total = float(sum(scores[i, perm[i]] for i in range(4)))
        if total > best_total:
            best_total = total
            best_perm = perm
    if best_perm is None:
        return None
    points = []
    for index in best_perm:
        (cx, cy), _, box = glyphs[index]
        x1, y1, x2, y2 = box
        for dx1, dy1, dx2, dy2 in detected_body:
            det_x = (dx1 + dx2) // 2
            det_y = (dy1 + dy2) // 2
            if x1 <= det_x <= x2 and y1 <= det_y <= y2:
                cx, cy = det_x, det_y
                break
        points.append([int(cx), int(cy)])
    return points


async def _request_json(client, method: str, url: str, payload: dict | None = None) -> dict:
    delay = 0.5
    for _ in range(10):
        if method == "GET":
            response = await client.get(url)
        else:
            response = await client.post(url, json=payload)
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 12)
            continue
        try:
            data = response.json()
        except Exception:
            response.raise_for_status()
            raise
        if isinstance(data, dict):
            return data
        raise RuntimeError("unexpected response")
    raise RuntimeError("rate limited")


def _decode_image(payload: dict) -> bytes | None:
    picture = payload.get("background_pic")
    if not isinstance(picture, str) or not picture:
        return None
    try:
        return base64.b64decode(picture)
    except Exception:
        return None


async def _calibrate(client) -> np.ndarray:
    frames = []
    for index in range(CALIBRATION_FRAMES):
        payload = await _request_json(
            client,
            "GET",
            f"/captcha/api/{CHALLENGE}/click_captcha_image/?t=cal-{index}",
        )
        raw = _decode_image(payload)
        if raw is None:
            raise RuntimeError("calibration image missing")
        frames.append(np.array(Image.open(io.BytesIO(raw)).convert("RGB")))
    return np.median(np.stack(frames, axis=0), axis=0).astype(np.uint8)


async def _fetch_page(client, background: np.ndarray, page: int) -> list[int]:
    for attempt in range(PAGE_ATTEMPTS):
        payload = await _request_json(
            client,
            "GET",
            f"/captcha/api/{CHALLENGE}/click_captcha_image/?t={page}-{attempt}",
        )
        raw = _decode_image(payload)
        captcha_id = payload.get("captcha_id")
        if raw is None or not isinstance(captcha_id, str):
            await asyncio.sleep(0.3 * (attempt + 1))
            continue
        points = await asyncio.to_thread(locate_clicks, raw, background)
        if not points or len(points) != 4:
            continue
        body = await _request_json(
            client,
            "POST",
            f"/captcha/api/{CHALLENGE}/click_page/",
            {
                "click_positions_encoded": _encode_points(points),
                "page_num": page,
                "challenge_type": CHALLENGE,
                "captcha_id": captcha_id,
            },
        )
        numbers = body.get("page_data")
        if body.get("success") is True and isinstance(numbers, list) and len(numbers) == 10:
            print(f"page {page} ok", flush=True)
            return [int(number) for number in numbers]
        await asyncio.sleep(0.25 * (attempt + 1))
    raise RuntimeError(f"page {page} captcha was not accepted")


async def _run() -> dict:
    session = SpiderSession()
    async with session.async_client() as client:
        init = await _request_json(
            client,
            "GET",
            f"/captcha/api/{CHALLENGE}/init/?challenge_type={CHALLENGE}",
        )
        if init.get("success") is not True:
            raise RuntimeError("init was not accepted")
        page_one = init.get("page_data")
        total_pages = int(init.get("total_pages") or 0)
        if not isinstance(page_one, list) or len(page_one) != 10 or total_pages < 2:
            raise RuntimeError("init payload missing page data")
        background = await _calibrate(client)
        fetched = await collect_pages(
            lambda page: _fetch_page(client, background, page),
            range(2, total_pages + 1),
            concurrency=CONCURRENCY,
        )
        pages = {1: [int(number) for number in page_one]}
        pages.update(fetched)
        if len(pages) != total_pages:
            raise RuntimeError("missing pages")
        answer = sum(sum(pages[page]) for page in range(1, total_pages + 1))
        submitted = await _request_json(
            client,
            "POST",
            f"/captcha/api/{CHALLENGE}/submit/",
            {"challenge_type": CHALLENGE, "answer": answer},
        )
    result = public_result(submitted)
    (HERE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
