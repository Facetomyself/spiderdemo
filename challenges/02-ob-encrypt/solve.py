"""Solve ob_challenge1 by recovering the salted MD5 page sign locally."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "ob_challenge1"
PAGE = "/ob/ob_challenge1?challenge_type=ob_challenge1"
SALT = bytes((0xA3, 0xAC, 0xA1, 0xA3)) + b"fdjf,jkgfkl"
HERE = Path(__file__).resolve().parent
TOTAL_EXPECTED = 100
NUMBERS_PER_PAGE = 10


def page_sign(timestamp: str, page: int) -> str:
    """hex_md5(timestamp + page): append the fixed salt, then standard MD5."""
    raw = f"{timestamp}{page}".encode("ascii") + SALT
    return hashlib.md5(raw).hexdigest()


async def _fetch_page(client, page: int) -> list[int]:
    delay = 0.5
    last_error = "unknown"
    for _ in range(8):
        timestamp = str(int(time.time() * 1000))
        url = (
            f"/ob/api/ob_challenge1/page/{page}/"
            f"?challenge_type={CHALLENGE}&sign={page_sign(timestamp, page)}&timestamp={timestamp}"
        )
        response = await client.get(url)
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            last_error = "429"
            continue
        payload = response.json()
        if response.status_code == 200 and payload.get("success") is True:
            numbers = payload.get("page_data")
            if not isinstance(numbers, list) or len(numbers) != NUMBERS_PER_PAGE:
                raise RuntimeError(f"page {page} did not return {NUMBERS_PER_PAGE} numbers")
            return [int(item) for item in numbers]
        last_error = str(payload.get("error") or response.status_code)
        if response.status_code >= 500 or "频繁" in last_error:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        break
    raise RuntimeError(f"page {page} failed: {last_error}")


async def solve() -> dict:
    session = SpiderSession()
    headers = {
        "Accept": "application/json",
        "Referer": "https://www.spiderdemo.cn" + PAGE,
    }
    async with session.async_client(headers) as client:
        init_response = await client.get(f"/ob/api/challenge/init/?challenge_type={CHALLENGE}")
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            raise RuntimeError("init was not accepted")
        total_pages = int(init_payload.get("total_pages") or TOTAL_EXPECTED)
        if total_pages != TOTAL_EXPECTED:
            raise RuntimeError(f"unexpected total_pages {total_pages}")

        pages = await collect_pages(
            lambda page: _fetch_page(client, page),
            range(1, total_pages + 1),
            concurrency=4,
        )
        if set(pages) != set(range(1, total_pages + 1)):
            raise RuntimeError("missing pages")
        answer = sum(sum(pages[page]) for page in range(1, total_pages + 1))

        submit_response = await client.post(
            "/ob/api/challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        submit_payload = submit_response.json()
        kept = public_result(submit_payload)
        (HERE / "result.json").write_text(
            json.dumps(kept, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if submit_payload.get("is_correct") is not True:
            raise RuntimeError("submit was not accepted as correct")
        return kept


def main() -> None:
    result = asyncio.run(solve())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
