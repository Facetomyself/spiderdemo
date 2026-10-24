"""Recover the console secret from the JSVMP string table and submit key-sum."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

ROOT = Path(__file__).resolve().parent
JS_PATH = ROOT / "static__js__check_devtools_jsvmp.js"
PAGE = "/authentication/panel_challenge/?challenge_type=panel_challenge"
REFERER = "https://www.spiderdemo.cn" + PAGE
CHALLENGE = "panel_challenge"
OUT = ROOT / "result.json"
PREFIX = "SecretKey: "


def _matching(text: str, open_at: int) -> int:
    depth = 0
    for index in range(open_at, len(text)):
        char = text[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
    raise RuntimeError("string table is not balanced")


def console_secret(source: str) -> str:
    """The printed line is a string-table constant, not a live DevTools side effect."""
    call = source.find("})(function(em,eB")
    start = source.find("[[", call)
    table = json.loads(source[start : _matching(source, start) + 1])
    for item in table:
        if not isinstance(item, list) or len(item) < len(PREFIX):
            continue
        if not all(isinstance(value, int) for value in item):
            continue
        key = item[0] - ord(PREFIX[0])
        chars = []
        for offset, value in enumerate(item):
            code = value - offset - key
            if code < 32 or code > 126:
                chars = []
                break
            chars.append(chr(code))
        text = "".join(chars)
        if text.startswith(PREFIX):
            secret = text[len(PREFIX) :].strip()
            if secret:
                return secret
    raise RuntimeError("console secret was not in the string table")


async def get_with_backoff(client, path: str):
    delay = 0.4
    last = None
    for _ in range(8):
        last = await client.get(path)
        if last.status_code != 429:
            return last
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    return last


async def main() -> None:
    secret = console_secret(JS_PATH.read_text(encoding="utf-8"))
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await get_with_backoff(
            client,
            f"/authentication/api/panel_challenge/init/?challenge_type={CHALLENGE}",
        )
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            detail = init_payload.get("error") or init_payload.get("message") or init_response.status_code
            raise SystemExit(f"init failed: {detail}")
        total_pages = int(init_payload["total_pages"])

        async def fetch_page(page: int) -> list[int]:
            response = await get_with_backoff(
                client,
                f"/authentication/api/panel_challenge/page/{page}/?challenge_type={CHALLENGE}",
            )
            payload = response.json()
            if response.status_code != 200 or payload.get("success") is not True:
                detail = payload.get("error") or payload.get("message") or response.status_code
                raise RuntimeError(f"page {page}: {detail}")
            numbers = payload.get("page_data")
            if not isinstance(numbers, list) or not numbers:
                raise RuntimeError(f"page {page}: unexpected page_data")
            return [int(item) for item in numbers]

        pages = await collect_pages(fetch_page, range(1, total_pages + 1), concurrency=4)
        total = sum(sum(pages[page]) for page in range(1, total_pages + 1))
        answer = f"{secret}-{total}"
        submit = await client.post(
            "/authentication/api/panel_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        body = submit.json()
        result = public_result(body if isinstance(body, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        accepted = body.get("is_correct") is True or "答案正确" in str(body.get("message") or "")
        print("pages", len(pages), "sum", total, "http", submit.status_code, "accepted", accepted)
        print("message", body.get("message") or body.get("error"))
        if not accepted:
            raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    asyncio.run(main())
