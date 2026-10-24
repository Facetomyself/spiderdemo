"""Decode the jsfuck challenge locally and submit the 100-page sum."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import quote

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "jsfuck_challenge"
CAESAR_KEY = "spiderdemo_caesar_2025"
PAGE_COUNT = 100
OUT = Path(__file__).with_name("result.json")
REFERER = (
    "https://www.spiderdemo.cn/authentication/jsfuck_challenge/"
    f"?challenge_type={CHALLENGE}"
)


def dynamic_shift(page: int) -> int:
    digest = hashlib.md5(f"{CAESAR_KEY}_{page}".encode()).hexdigest()
    return int(digest[:2], 16) % 25 + 1


def caesar(text: str, shift: int) -> str:
    out: list[str] = []
    for char in text:
        if "a" <= char <= "z":
            out.append(chr((ord(char) - 97 + shift) % 26 + 97))
        elif "A" <= char <= "Z":
            out.append(chr((ord(char) - 65 + shift) % 26 + 65))
        elif char.isdigit():
            out.append(str((int(char) + shift) % 10))
        else:
            out.append(char)
    return "".join(out)


def decrypt_numbers(values: list, page: int) -> list[int]:
    shift = dynamic_shift(page)
    numbers: list[int] = []
    for value in values:
        plain = caesar(str(value), -shift)
        if not plain.lstrip("-").isdigit():
            raise RuntimeError(f"page {page}: undecryptable value")
        numbers.append(int(plain))
    return numbers


def sign_page(page: int, timestamp: int) -> dict[str, str]:
    shift = dynamic_shift(page)
    return {
        "p": caesar(str(page), shift),
        "t": caesar(CHALLENGE, shift),
        "token": caesar(f"{page}_{CHALLENGE}_{timestamp}", shift),
        "ts": str(timestamp),
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


def page_path(page: int, signed: dict[str, str]) -> str:
    return (
        f"/authentication/api/jsfuck_challenge/page/{page}/"
        f"?challenge_type={quote(CHALLENGE)}"
        f"&p={quote(signed['p'], safe='')}"
        f"&t={quote(signed['t'], safe='')}"
        f"&ts={signed['ts']}"
    )


async def main() -> None:
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await get_with_backoff(
            client,
            f"/authentication/api/jsfuck_challenge/init/?challenge_type={quote(CHALLENGE)}",
        )
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            detail = init_payload.get("error") or init_payload.get("message") or init_response.status_code
            raise SystemExit(f"init failed: {detail}")
        init_numbers = init_payload.get("page_data")
        if not isinstance(init_numbers, list) or len(init_numbers) != 10:
            raise SystemExit("init failed: unexpected page_data")

        async def fetch_page(page: int) -> list[int]:
            if page == 1:
                return decrypt_numbers(init_numbers, 1)
            stamp = int(time.time() * 1000)
            signed = sign_page(page, stamp)
            response = await get_with_backoff(
                client,
                page_path(page, signed),
                {"X-Caesar-Token": signed["token"]},
            )
            payload = response.json()
            if response.status_code != 200 or payload.get("success") is not True:
                detail = payload.get("error") or payload.get("message") or response.status_code
                raise RuntimeError(f"page {page}: {detail}")
            numbers = payload.get("page_data")
            if not isinstance(numbers, list) or len(numbers) != 10:
                raise RuntimeError(f"page {page}: unexpected page_data")
            return decrypt_numbers(numbers, page)

        pages = await collect_pages(fetch_page, range(1, PAGE_COUNT + 1), concurrency=4)
        total = sum(sum(pages[page]) for page in range(1, PAGE_COUNT + 1))
        submit = await client.post(
            "/authentication/api/jsfuck_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        body = submit.json()
        result = public_result(body if isinstance(body, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        message = str(body.get("message") or "")
        accepted = body.get("is_correct") is True or body.get("correct") is True or "答案正确" in message
        print("pages", len(pages), "sum", total, "http", submit.status_code, "accepted", accepted)
        print("message", message)
        if not accepted:
            raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    asyncio.run(main())
