"""Solve the arc slider and sum every page the site returns.

Page posts stay on the fixed 17-point track that the page endpoint accepts.
Scheduling goes through collect_pages with concurrency 4.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "cap7_challenge"
REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
HEADERS = {
    "Referer": REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}
SCALE = 400 / 840
OFFSET_Y = (240 - 540 * SCALE) / 2
MAX_DRAG = 400 - 120 * SCALE
DELTAS = [78, 51, 1, 156, 59, 29, 42, 36, 32, 39, 49, 84, 56, 29, 97, 825]
OUT = Path(__file__).with_name("result.json")


def _rotate(piece: np.ndarray, angle: float) -> np.ndarray:
    height, width = piece.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        piece,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


def _score_at(bg: np.ndarray, piece: np.ndarray, angle: int) -> tuple[float, int, int]:
    turned = _rotate(piece, angle)
    mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
    if int(mask.sum()) < 40:
        return -1.0, 0, 0
    scored = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
    _, value, _, loc = cv2.minMaxLoc(scored)
    return float(value), int(loc[0]), int(loc[1])


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int, int]:
    small_bg = cv2.resize(bg, (420, 270), interpolation=cv2.INTER_AREA)
    small_piece = cv2.resize(piece, (60, 50), interpolation=cv2.INTER_AREA)
    coarse = max(range(0, 360, 6), key=lambda angle: _score_at(small_bg, small_piece, angle)[0])
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse - 8, coarse + 9):
        value, x, y = _score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def _decode_images(overlay: str, masked: str) -> tuple[np.ndarray, np.ndarray]:
    bg = np.array(Image.open(io.BytesIO(base64.b64decode(overlay))).convert("RGB"))
    piece = np.array(Image.open(io.BytesIO(base64.b64decode(masked))).convert("RGBA"))
    return bg, piece


def _samples(arc: np.ndarray, index: int) -> np.ndarray:
    segment = arc[: index + 1]
    step = np.hypot(np.diff(segment[:, 0]), np.diff(segment[:, 1]))
    length = np.concatenate([[0.0], np.cumsum(step)])
    if length[-1] <= 0:
        return np.repeat(segment[:1], 17, axis=0)
    targets = np.linspace(0, length[-1], 17)
    cols = []
    for target in targets:
        pos = int(np.searchsorted(length, target, side="right") - 1)
        pos = min(max(pos, 0), len(segment) - 2)
        span = length[pos + 1] - length[pos]
        frac = 0.0 if span <= 0 else (target - length[pos]) / span
        cols.append(segment[pos] * (1 - frac) + segment[pos + 1] * frac)
    return np.vstack(cols)


def _track(arc: np.ndarray, index: int, start: int) -> list[dict]:
    rows = []
    cursor = start
    for nth, point in enumerate(_samples(arc, index)):
        rows.append(
            {
                "x": 2 + float(point[0]) * SCALE,
                "y": 2 + OFFSET_Y + float(point[1]) * SCALE,
                "t": cursor,
            }
        )
        if nth < len(DELTAS):
            cursor += DELTAS[nth]
    return rows


def _encode(points: list) -> str:
    raw = json.dumps(points, separators=(",", ":")).encode()
    return base64.b64encode(raw).decode()


def _json_body(response) -> dict:
    try:
        payload = response.json()
    except Exception as exc:
        raise RuntimeError(f"non-json response {response.status_code}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected response {response.status_code}")
    return payload


async def _backoff(response, attempt: int) -> bool:
    if response.status_code != 429:
        return False
    await asyncio.sleep(min(8.0, 1.5 * (attempt + 1)))
    return True


def _pose_index(bg: np.ndarray, piece: np.ndarray, arc: np.ndarray, slider_y: int) -> tuple[int, float, float] | None:
    value, _angle, x, y = best_pose(bg, piece)
    if abs(y - slider_y) > 1:
        return None
    found = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
    index = int(np.argmin(np.hypot(*(arc - found).T)))
    gap = float(np.hypot(*(arc[index] - found)))
    if value < 0.8 or gap > 3 or not 8 <= index <= 91:
        return None
    return index, value, gap


async def fetch_page_numbers(client, page: int) -> list[int]:
    last_error = "captcha was not accepted"
    for attempt in range(8):
        image_response = await client.get("/captcha/api/cap7_challenge/captcha_image/")
        if await _backoff(image_response, attempt):
            last_error = "captcha image was rate limited"
            continue
        captcha = _json_body(image_response)
        if "overlay" not in captcha or "masked" not in captcha or "arc_path" not in captcha:
            last_error = str(captcha.get("error") or captcha.get("message") or "captcha image missing")
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
        bg, piece = await asyncio.to_thread(_decode_images, captcha["overlay"], captcha["masked"])
        arc = np.array(captcha["arc_path"]["points"], dtype=np.float64)
        slider_y = int(captcha.get("slider_y", -999))
        posed = await asyncio.to_thread(_pose_index, bg, piece, arc, slider_y)
        if posed is None:
            last_error = "pose was below the accept gate"
            continue
        index, _value, _gap = posed
        ratio = index / 99
        rows = _track(arc, index, int(time.time() * 1000) + 40)
        wait = rows[-1]["t"] + 80 - int(time.time() * 1000)
        if wait > 0:
            await asyncio.sleep(wait / 1000)
        response = await client.post(
            "/captcha/api/cap7_challenge/page/",
            json={
                "distance": ratio * MAX_DRAG,
                "trajectory_encoded": _encode(rows),
                "rotation_angle": ratio * 360,
                "page_num": page,
                "challenge_type": CHALLENGE,
                "captcha_id": captcha["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            },
        )
        if await _backoff(response, attempt):
            last_error = "page post was rate limited"
            continue
        payload = _json_body(response)
        numbers = payload.get("page_data")
        if payload.get("success") is True and isinstance(numbers, list) and numbers:
            return [int(number) for number in numbers]
        last_error = str(payload.get("error") or payload.get("message") or "page request failed")
        await asyncio.sleep(0.3 * (attempt + 1))
    raise RuntimeError(f"page {page}: {last_error}")


async def solve() -> dict:
    session = SpiderSession()
    async with session.async_client(headers=HEADERS) as client:
        init_response = await client.get(f"/captcha/api/cap7_challenge/init/?challenge_type={CHALLENGE}")
        if init_response.status_code == 429:
            await asyncio.sleep(2)
            init_response = await client.get(f"/captcha/api/cap7_challenge/init/?challenge_type={CHALLENGE}")
        init_body = _json_body(init_response)
        if init_body.get("success") is not True:
            raise RuntimeError(str(init_body.get("error") or init_body.get("message") or "init failed"))
        first_page = [int(number) for number in init_body["page_data"]]
        total_pages = int(init_body["total_pages"])

        async def fetch_page(page: int) -> list[int]:
            numbers = await fetch_page_numbers(client, page)
            print("collected", page, "of", total_pages, flush=True)
            return numbers

        collected = await collect_pages(fetch_page, range(2, total_pages + 1), concurrency=4)
        pages = {1: first_page}
        pages.update(collected)
        missing = [page for page in range(1, total_pages + 1) if page not in pages]
        if missing:
            raise RuntimeError(f"missing pages: {missing[:8]}")
        answer = sum(sum(pages[page]) for page in range(1, total_pages + 1))
        print("pages", total_pages, "answer", answer, flush=True)
        submit = await client.post(
            "/captcha/api/cap7_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        payload = _json_body(submit)
        result = public_result(payload)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("submit", result.get("success"), result.get("is_correct"), result.get("correct"), result.get("message"), flush=True)
        return result


def main() -> None:
    result = asyncio.run(solve())
    accepted = result.get("is_correct") is True or result.get("correct") is True or result.get("completed") is True
    if result.get("success") is not True or not accepted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
