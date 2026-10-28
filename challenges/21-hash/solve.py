"""Reimplement the hash_challenge page digest and submit the page sum."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "hash_challenge"
SHA_SALT = "spiderdemo_sha_salt_2025"
MD5_SALT = "spiderdemo_md5_salt_2025"
HMAC_KEY = b"spiderdemo_hmac_secret_2025"
PAGE_COUNT = 100
OUT = Path(__file__).with_name("result.json")
REFERER = "https://www.spiderdemo.cn/authentication/hash_challenge/?challenge_type=hash_challenge"


def digests(page: int, ts: int) -> dict[str, str]:
    material = f"{page}_{CHALLENGE}_{ts}"
    return {
        "token": hmac.new(HMAC_KEY, material.encode(), hashlib.sha256).hexdigest(),
        "verify": hashlib.md5((material + MD5_SALT).encode()).hexdigest(),
        "sign": hashlib.sha256((material + SHA_SALT).encode()).hexdigest(),
        "code": hashlib.sha3_256((material + SHA_SALT).encode()).hexdigest(),
    }


async def get_with_backoff(client, path: str, headers: dict[str, str] | None = None):
    delay = 0.5
    last = None
    for _ in range(8):
        last = await client.get(path, headers=headers)
        if last.status_code != 429:
            return last
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    return last


async def main() -> None:
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await get_with_backoff(
            client,
            f"/authentication/api/hash_challenge/init/?challenge_type={CHALLENGE}",
        )
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            detail = init_payload.get("error") or init_payload.get("message") or init_response.status_code
            raise SystemExit(f"init failed: {detail}")

        async def fetch_page(page: int) -> list[int]:
            stamp = int(time.time() * 1000)
            signed = digests(page, stamp)
            path = (
                f"/authentication/api/hash_challenge/page/{page}/"
                f"?challenge_type={CHALLENGE}&sign={signed['sign']}"
                f"&code={signed['code']}&t={stamp}"
            )
            response = await get_with_backoff(
                client,
                path,
                {
                    "X-Request-Token": signed["token"],
                    "X-Verify-Code": signed["verify"],
                },
            )
            payload = response.json()
            if response.status_code != 200 or payload.get("success") is not True:
                detail = payload.get("error") or payload.get("message") or response.status_code
                raise RuntimeError(f"page {page}: {detail}")
            numbers = payload.get("page_data")
            if not isinstance(numbers, list) or len(numbers) != 10:
                raise RuntimeError(f"page {page}: unexpected page_data")
            return [int(item) for item in numbers]

        pages = await collect_pages(fetch_page, range(1, PAGE_COUNT + 1), concurrency=4)
        total = sum(sum(pages[page]) for page in range(1, PAGE_COUNT + 1))
        submit = await client.post(
            "/authentication/api/hash_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        body = submit.json()
        result = public_result(body if isinstance(body, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        accepted = body.get("is_correct") is True or "答案正确" in str(body.get("message") or "")
        print("pages", len(pages), "sum", total, "http", submit.status_code, "accepted", accepted)
        print("message", body.get("message"))
        if not accepted:
            raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    asyncio.run(main())
