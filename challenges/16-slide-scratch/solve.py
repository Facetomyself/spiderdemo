"""Solve the slide-scratch challenge locally and submit the page sum.

Captcha offsets come from masked template matching. No captcha image,
cookie, or token is written.
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

from modules.runtime import SpiderSession, collect_pages, public_result

ROOT = Path(__file__).parent
TEMPLATES = ROOT / "templates"
REFERER = "https://www.spiderdemo.cn/captcha/slide_scratch_challenge/"
CHALLENGE = "slide_scratch_challenge"
DISPLAY_WIDTH = 350
PAGE_COUNT = 100
QUESTION_RE = re.compile(r"(\d+)个(.+)")
NAMES = {
    "飞机": "t00.png",
    "篮球": "t01.png",
    "轮船": "t02.png",
    "火箭": "t03.png",
    "月亮": "t04.png",
    "手机": "t05.png",
    "奶瓶": "t06.png",
    "草莓": "t07.png",
    "书包": "t08.png",
    "羽毛球": "t09.png",
    "芒果": "t10.png",
    "太阳": "t11.png",
    "葡萄": "t12.png",
    "风扇": "t13.png",
    "菠萝": "t14.png",
    "足球": "t15.png",
}


def load_templates() -> dict[str, tuple[np.ndarray, np.ndarray, int]]:
    loaded = {}
    for kind, filename in NAMES.items():
        bgra = cv2.imdecode(np.fromfile(TEMPLATES / filename, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        alpha = bgra[:, :, 3]
        cols = np.nonzero((alpha > 0).any(axis=0))[0]
        loaded[kind] = (bgra[:, :, :3], alpha, int(cols.max()) + 1)
    return loaded


TEMPL = load_templates()


def scratch_edge(image: np.ndarray, kind: str, count: int) -> int:
    """Image-pixel x where `count` icons of `kind` are fully uncovered."""
    templ, alpha, width = TEMPL[kind]
    result = cv2.matchTemplate(image, templ, cv2.TM_CCORR_NORMED, mask=alpha)
    work = result.copy()
    found: list[int] = []
    th, tw = templ.shape[:2]
    for _ in range(16):
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(work)
        if float(max_val) < 0.96:
            break
        found.append(int(max_loc[0]) + width)
        y0, x0 = max(0, max_loc[1] - th // 2), max(0, max_loc[0] - tw // 2)
        y1 = min(work.shape[0], max_loc[1] + th // 2)
        x1 = min(work.shape[1], max_loc[0] + tw // 2)
        work[y0:y1, x0:x1] = 0
    if len(found) < count:
        raise LookupError(f"need {count} {kind}, saw {len(found)}")
    found.sort()
    return found[count - 1]


def decode_image(data_url: str) -> np.ndarray:
    _header, encoded = data_url.split(",", 1)
    image = cv2.imdecode(np.frombuffer(base64.b64decode(encoded), np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("captcha image could not be decoded")
    return image


async def request_json(client, method: str, url: str, **kwargs):
    delay = 1.0
    last = None
    for _ in range(7):
        response = await client.request(method, url, **kwargs)
        last = response
        if response.status_code != 429:
            return response
        await asyncio.sleep(delay)
        delay = min(delay * 2, 16)
    return last


async def fetch_protected_page(client, page: int) -> list[int]:
    last_error = "no attempt"
    for _attempt in range(8):
        captcha_response = await request_json(client, "GET", f"/captcha/api/{CHALLENGE}/captcha")
        captcha = captcha_response.json()
        data = captcha.get("data") or {}
        question = data.get("question") or ""
        matched = QUESTION_RE.fullmatch(question)
        if captcha_response.status_code != 200 or not matched or not data.get("bg"):
            last_error = f"captcha http {captcha_response.status_code}"
            await asyncio.sleep(0.4)
            continue
        count_s, kind = matched.groups()
        if kind not in TEMPL:
            raise RuntimeError(f"unknown icon {kind}")
        image = decode_image(data["bg"])
        try:
            edge = scratch_edge(image, kind, int(count_s))
        except LookupError as exc:
            last_error = str(exc)
            await asyncio.sleep(0.2)
            continue
        distance = edge * DISPLAY_WIDTH / image.shape[1]
        verified = await request_json(
            client,
            "POST",
            f"/captcha/api/{CHALLENGE}/verify",
            json={"distance": distance, "captchaId": data["captchaId"]},
        )
        verdict = verified.json()
        if verified.status_code == 429 or not verdict.get("success"):
            last_error = str(verdict.get("message") or verdict.get("error") or verified.status_code)
            await asyncio.sleep(0.3)
            continue
        token = (verdict.get("data") or {}).get("token")
        if not token:
            last_error = "verify missing token"
            continue
        page_response = await request_json(
            client,
            "GET",
            f"/captcha/api/{CHALLENGE}/page/{page}/",
            params={"challenge_type": CHALLENGE, "token": token},
        )
        payload = page_response.json()
        numbers = payload.get("page_data")
        if payload.get("success") and isinstance(numbers, list) and numbers:
            print(f"page {page} {question} edge {edge} n {len(numbers)}", flush=True)
            return [int(value) for value in numbers]
        last_error = str(payload.get("error") or payload.get("message") or page_response.status_code)
        await asyncio.sleep(0.3)
    raise RuntimeError(f"page {page} failed: {last_error}")


async def run(start: int, end: int, submit: bool) -> None:
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await request_json(
            client,
            "GET",
            f"/captcha/api/{CHALLENGE}/init/",
            params={"challenge_type": CHALLENGE},
        )
        init_payload = init_response.json()
        if not init_payload.get("success"):
            raise RuntimeError(init_payload.get("error") or "init failed")
        numbers = {1: [int(value) for value in init_payload["page_data"]]}
        print(f"init pages {init_payload.get('total_pages')} page1 {len(numbers[1])}", flush=True)
        if end >= 2:
            fetched = await collect_pages(
                lambda page: fetch_protected_page(client, page),
                range(max(2, start), end + 1),
                concurrency=4,
            )
            numbers.update(fetched)
        if not submit:
            ordered = [numbers[page] for page in range(1, end + 1) if page in numbers]
            print("partial_pages", len(ordered), "partial_sum", sum(sum(page) for page in ordered))
            return
        missing = [page for page in range(1, PAGE_COUNT + 1) if page not in numbers]
        if missing:
            raise RuntimeError(f"missing pages {missing[:8]}")
        answer = sum(sum(numbers[page]) for page in range(1, PAGE_COUNT + 1))
        print("answer", answer, flush=True)
        submitted = await request_json(
            client,
            "POST",
            f"/captcha/api/{CHALLENGE}/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        payload = submitted.json()
        result = public_result(payload)
        (ROOT / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("submit", submitted.status_code, json.dumps(result, ensure_ascii=False), flush=True)
        if result.get("is_correct") is not True and "正确" not in str(result.get("message", "")):
            raise RuntimeError("submit was not accepted")


def main() -> None:
    if len(sys.argv) == 3:
        asyncio.run(run(int(sys.argv[1]), int(sys.argv[2]), submit=False))
        return
    asyncio.run(run(2, PAGE_COUNT, submit=True))


if __name__ == "__main__":
    main()
