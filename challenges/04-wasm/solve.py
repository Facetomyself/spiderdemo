"""WASM challenge solver. AES is local; pages are fetched concurrently."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "wasm_challenge"
PAGE_URL = "https://www.spiderdemo.cn/sec1/wasm_challenge?challenge_type=wasm_challenge"
KEY = b"0123456789abcdef"
IV = b"abcdef9876543210"
TOTAL_PAGES = 100
CONCURRENCY = 4
HERE = Path(__file__).resolve().parent


def encrypt_simple(verify_string: str, timestamp: str) -> str:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    plain = pad((verify_string + timestamp).encode(), 16)
    return cipher.encrypt(plain).hex()


def page_path(page: int, timestamp: str) -> str:
    token = encrypt_simple(f"{CHALLENGE}_page_{page}", timestamp)
    return (
        f"/sec1/api/wasm_challenge/page/{page}/"
        f"?challenge_type={CHALLENGE}&wasm_auth={token}"
    )


async def fetch_page(client, page: int) -> list[int]:
    delay = 0.5
    last_error = "page request failed"
    for _ in range(6):
        timestamp = str(int(time.time()))
        response = await client.get(
            page_path(page, timestamp),
            headers={
                "Accept": "application/json",
                "Referer": PAGE_URL,
                "X-WASM-Timestamp": timestamp,
                "X-WASM-Page": str(page),
            },
        )
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            last_error = "429"
            continue
        payload = response.json()
        if response.status_code == 200 and payload.get("success") is True:
            return [int(item) for item in payload["page_data"]]
        last_error = str(payload.get("error") or response.status_code)
        if payload.get("need_init"):
            break
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    raise RuntimeError(f"page {page}: {last_error}")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        init = client.get(
            f"/sec1/api/challenge/init/?challenge_type={CHALLENGE}",
            headers={"Accept": "application/json", "Referer": PAGE_URL},
        )
        init_payload = init.json()
        if init.status_code != 200 or init_payload.get("success") is not True:
            raise RuntimeError(str(init_payload.get("error") or init.status_code))

    async def run() -> dict[int, list[int]]:
        async with session.async_client() as client:

            async def one(page: int) -> list[int]:
                return await fetch_page(client, page)

            return await collect_pages(one, range(1, TOTAL_PAGES + 1), CONCURRENCY)

    pages = asyncio.run(run())
    if len(pages) != TOTAL_PAGES:
        raise RuntimeError(f"collected {len(pages)} pages")
    answer = sum(sum(pages[page]) for page in range(1, TOTAL_PAGES + 1))

    with session.client() as client:
        submitted = client.post(
            "/sec1/api/challenge/submit/",
            headers={"Accept": "application/json", "Referer": PAGE_URL},
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        payload = submitted.json()

    result = public_result(payload)
    (HERE / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    message = str(result.get("message") or "")
    if result.get("is_correct") is not True and "答案正确" not in message:
        raise RuntimeError(message or "answer was not accepted")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
