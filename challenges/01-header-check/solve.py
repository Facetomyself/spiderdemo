"""Solve the header_check number challenge.

Header order is part of the check. httpx prepends its own defaults and
moves Host, so the client is built from an explicit header list that
includes those defaults. Cookie is appended by the session and is never
printed.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from modules.login.client import ORIGIN
from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE_TYPE = "header_check"
PAGE_URL = "/sec1/header_check"
TOTAL_PAGES = 100
CONCURRENCY = 4
HERE = Path(__file__).parent

# Order after the Host line that HTTP/1.1 writes first. Defaults that
# httpx would otherwise inject are included so update() cannot reshuffle them.
HEADER_ORDER: list[tuple[str, str]] = [
    ("Connection", "keep-alive"),
    ("Accept", "application/json, text/javascript, */*; q=0.01"),
    ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8"),
    ("Accept-Encoding", "gzip, deflate, br"),
    ("User-Agent", (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )),
    ("X-Requested-With", "XMLHttpRequest"),
    ("Origin", ORIGIN),
    ("Referer", ORIGIN + PAGE_URL),
    ("Sec-Fetch-Site", "same-origin"),
    ("Sec-Fetch-Mode", "cors"),
    ("Sec-Fetch-Dest", "empty"),
]


class PageError(RuntimeError):
    """A page response did not contain numbers."""


def _numbers(payload: object) -> list[int]:
    if not isinstance(payload, dict) or payload.get("success") is not True:
        message = ""
        if isinstance(payload, dict):
            message = str(payload.get("error") or payload.get("message") or "")
        raise PageError(message or "page payload was rejected")
    raw = payload.get("page_data")
    if not isinstance(raw, list) or not raw:
        raise PageError("page_data missing")
    numbers: list[int] = []
    for item in raw:
        if isinstance(item, bool) or not isinstance(item, int):
            raise PageError("page_data item was not an int")
        numbers.append(item)
    return numbers


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, str] | None = None,
) -> dict[str, object]:
    delay = 0.5
    last = ""
    for _ in range(8):
        response = await client.get(url, params=params)
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            last = "429"
            continue
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise PageError(f"non-json status {response.status_code}") from exc
        if not isinstance(payload, dict):
            raise PageError("json was not an object")
        return payload
    raise PageError(last or "retries exhausted")


async def _fetch_all(client: httpx.AsyncClient) -> dict[int, list[int]]:
    init_payload = await _get_json(
        client,
        "/sec1/api/challenge/init/",
        {"challenge_type": CHALLENGE_TYPE},
    )
    if init_payload.get("success") is not True:
        raise PageError(str(init_payload.get("error") or init_payload.get("message") or "init failed"))

    async def fetch_page(page: int) -> list[int]:
        payload = await _get_json(
            client,
            f"/sec1/api/challenge/page/{page}/",
            {"challenge_type": CHALLENGE_TYPE},
        )
        return _numbers(payload)

    return await collect_pages(fetch_page, range(1, TOTAL_PAGES + 1), concurrency=CONCURRENCY)


async def _submit(client: httpx.AsyncClient, answer: int) -> dict[str, object]:
    delay = 0.5
    body = json.dumps(
        {"challenge_type": CHALLENGE_TYPE, "answer": answer},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    for _ in range(8):
        response = await client.post(
            "/sec1/api/challenge/submit/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        payload = response.json()
        if not isinstance(payload, dict):
            raise PageError("submit json was not an object")
        return payload
    raise PageError("submit retries exhausted")


def _accepted(payload: dict[str, object]) -> bool:
    if payload.get("is_correct") is True or payload.get("correct") is True:
        return True
    for key in ("message", "msg"):
        text = payload.get(key)
        if isinstance(text, str) and "正确" in text and "不正确" not in text and "错误" not in text:
            return True
    return False


async def main() -> None:
    session = SpiderSession()
    async with session.async_client() as client:
        # Replace the merged client headers with the required order.
        client.headers = httpx.Headers(HEADER_ORDER)
        pages = await _fetch_all(client)
        if len(pages) != TOTAL_PAGES:
            raise PageError(f"collected {len(pages)} pages")
        answer = sum(sum(numbers) for numbers in pages.values())
        submitted = await _submit(client, answer)
    result = public_result(submitted)
    (HERE / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("pages", len(pages), "accepted", _accepted(submitted))
    if not _accepted(submitted):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
