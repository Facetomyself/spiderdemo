"""Solve ob1_challenge by rebuilding the local signature and summing every page."""

from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "ob1_challenge"
PAGE = "/authentication/ob1_challenge?challenge_type=ob1_challenge"
INIT_URL = "/authentication/api/ob1_challenge/init/"
SUBMIT_URL = "/authentication/api/ob1_challenge/submit/"
MAGIC = 1661224081041
SYNC_OFFSET = 1530
SORTED_PARAMS = "5000downiphoneonepaid"
URL_PART = "/authentication/api/ob1_challenge/page"
KEY = "xyz517cda96efgh0"
OUT = Path(__file__).resolve().parent / "result.json"
PAGE_HEADERS = {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.spiderdemo.cn" + PAGE,
}


def xor_text(text: str, key: str) -> str:
    return "".join(
        chr(ord(char) ^ ord(key[(index + 10) % len(key)])) for index, char in enumerate(text)
    )


def sign() -> str:
    """Match O0o0O0O0: base64 the sorted params, then XOR, then base64 twice."""
    now = int(time.time() * 1000)
    adjusted = now - SYNC_OFFSET - MAGIC
    joined = base64.b64encode(SORTED_PARAMS.encode("ascii")).decode("ascii")
    payload = f"{joined}@#{URL_PART}@#{adjusted}@#3"
    inner = base64.b64encode(xor_text(payload, KEY).encode("utf-8")).decode("ascii")
    return base64.b64encode(f"{inner}{now}".encode("ascii")).decode("ascii")


def as_numbers(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) != 10:
        raise RuntimeError("page data did not contain 10 numbers")
    return [int(item) for item in value]


async def fetch_page(client, page: int) -> list[int]:
    last_error = "page request failed"
    for attempt in range(6):
        response = await client.get(
            f"/authentication/api/ob1_challenge/page/{page}/",
            params={"challenge_type": CHALLENGE, "signature": sign()},
            headers=PAGE_HEADERS,
        )
        if response.status_code == 429:
            await asyncio.sleep(min(2**attempt, 8))
            last_error = "429"
            continue
        payload = response.json()
        if payload.get("success") is True:
            return as_numbers(payload.get("page_data"))
        last_error = str(payload.get("error") or payload.get("message") or response.status_code)
        await asyncio.sleep(0.25 * (attempt + 1))
    raise RuntimeError(f"page {page}: {last_error}")


async def collect(session: SpiderSession, total_pages: int) -> dict[int, list[int]]:
    async with session.async_client(PAGE_HEADERS) as client:

        async def fetch(page: int) -> list[int]:
            return await fetch_page(client, page)

        return await collect_pages(fetch, range(2, total_pages + 1), concurrency=4)


def main() -> None:
    session = SpiderSession()
    with session.client(PAGE_HEADERS) as client:
        init = client.get(INIT_URL, params={"challenge_type": CHALLENGE})
        init.raise_for_status()
        init_payload = init.json()
        if init_payload.get("success") is not True:
            raise RuntimeError("init was not accepted")
        total_pages = int(init_payload["total_pages"])
        numbers = {1: as_numbers(init_payload.get("page_data"))}
    numbers.update(asyncio.run(collect(session, total_pages)))
    if len(numbers) != total_pages:
        raise RuntimeError("not every page was collected")
    answer = sum(sum(page) for page in numbers.values())
    with session.client(PAGE_HEADERS) as client:
        submitted = client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        submitted.raise_for_status()
        body = submitted.json()
    result = public_result(body)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    correct = body.get("is_correct") is True or "答案正确" in str(body.get("message") or "")
    print("pages", total_pages)
    print("answer", answer)
    print("public", json.dumps(result, ensure_ascii=False))
    if not correct:
        raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    main()
