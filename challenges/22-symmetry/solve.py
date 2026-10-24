"""Reimplement the symmetry_challenge AES/DES tokens and submit the page sum."""

from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path
from urllib.parse import urlencode

from Crypto.Cipher import AES, DES
from Crypto.Util.Padding import pad

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "symmetry_challenge"
PAGE_COUNT = 100
AES_IV = b"abcdefghijklmnop"
AES128_KEY = b"1234567890123456"
AES256_KEY = b"12345678901234567890123456789012"
DES_KEY = b"6f726c64"
DES_IV = b"01234567"
OUT = Path(__file__).with_name("result.json")
REFERER = (
    "https://www.spiderdemo.cn/authentication/symmetry_challenge/"
    "?challenge_type=symmetry_challenge"
)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def aes_ctr(plaintext: str) -> str:
    """CryptoJS AES-128-CTR, IV as the counter block, no padding."""
    cipher = AES.new(AES128_KEY, AES.MODE_CTR, nonce=AES_IV[:12], initial_value=AES_IV[12:])
    return _b64(cipher.encrypt(plaintext.encode("utf-8")))


def aes_ofb(plaintext: str) -> str:
    """CryptoJS AES-256-OFB, no padding."""
    cipher = AES.new(AES256_KEY, AES.MODE_OFB, iv=AES_IV)
    return _b64(cipher.encrypt(plaintext.encode("utf-8")))


def des_cbc(plaintext: str) -> str:
    """CryptoJS DES-CBC PKCS7. The ciphertext is raw base64, not OpenSSL salted."""
    cipher = DES.new(DES_KEY, DES.MODE_CBC, iv=DES_IV)
    encrypted = cipher.encrypt(pad(plaintext.encode("utf-8"), DES.block_size))
    return _b64(encrypted)


def page_tokens(page: int, stamp: int) -> dict[str, str]:
    material = f"{page}_{CHALLENGE}_{stamp}"
    return {
        "aes_token": aes_ctr(material),
        "des_token": des_cbc(material),
        "aes_sign": aes_ofb(material),
        "des_sign": des_cbc(material + "_param"),
        "t": str(stamp),
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


def _numbers(payload: dict, page: int) -> list[int]:
    numbers = payload.get("page_data")
    if not isinstance(numbers, list) or len(numbers) != 10:
        detail = payload.get("error") or payload.get("message") or "unexpected page_data"
        raise RuntimeError(f"page {page}: {detail}")
    return [int(item) for item in numbers]


async def main() -> None:
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await get_with_backoff(
            client,
            f"/authentication/api/symmetry_challenge/init/?challenge_type={CHALLENGE}",
        )
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            detail = init_payload.get("error") or init_payload.get("message") or init_response.status_code
            raise SystemExit(f"init failed: {detail}")
        page_one = _numbers(init_payload, 1)

        async def fetch_page(page: int) -> list[int]:
            stamp = int(time.time() * 1000)
            signed = page_tokens(page, stamp)
            query = urlencode(
                {
                    "challenge_type": CHALLENGE,
                    "aes_sign": signed["aes_sign"],
                    "des_sign": signed["des_sign"],
                    "t": signed["t"],
                }
            )
            path = f"/authentication/api/symmetry_challenge/page/{page}/?{query}"
            response = await get_with_backoff(
                client,
                path,
                {
                    "X-Aes-Token": signed["aes_token"],
                    "X-Des-Token": signed["des_token"],
                },
            )
            payload = response.json()
            if response.status_code != 200 or payload.get("success") is not True:
                detail = payload.get("error") or payload.get("message") or response.status_code
                raise RuntimeError(f"page {page}: {detail}")
            return _numbers(payload, page)

        pages = await collect_pages(fetch_page, range(2, PAGE_COUNT + 1), concurrency=4)
        pages[1] = page_one
        total = sum(sum(pages[page]) for page in range(1, PAGE_COUNT + 1))
        submit = await client.post(
            "/authentication/api/symmetry_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        body = submit.json()
        result = public_result(body if isinstance(body, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        message = "" if not isinstance(body, dict) else str(body.get("message") or "")
        accepted = (
            isinstance(body, dict)
            and (body.get("is_correct") is True or "答案正确" in message)
        )
        print("pages", len(pages), "http", submit.status_code, "accepted", accepted)
        if not accepted:
            detail = result.get("error") or result.get("message") or submit.status_code
            raise SystemExit(f"submit was not accepted: {detail}")


if __name__ == "__main__":
    asyncio.run(main())
