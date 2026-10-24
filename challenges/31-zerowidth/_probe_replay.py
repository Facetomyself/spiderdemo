"""Mint three page bodies and replay them on the same login."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages

HERE = Path(__file__).resolve().parent
NODE = Path(r"D:\reverse_ENV\tools\node\node.exe")
MINT = HERE / "_mint"
REFERER = "https://www.spiderdemo.cn/authentication/spiderking_challenge/"
ZW = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"]
INDEX = {char: pos for pos, char in enumerate(ZW)}


def decode(text: str):
    raw = bytearray()
    for offset in range(0, len(text), 3):
        raw.append((INDEX[text[offset]] << 6) | (INDEX[text[offset + 1]] << 3) | INDEX[text[offset + 2]])
    return json.loads(raw.decode("utf-8"))


def summarize(status: int, payload) -> str:
    if not isinstance(payload, dict):
        return f"http {status} type {type(payload).__name__}"
    values = payload.get("values")
    if isinstance(values, list):
        numbers = [int(item) for item in values]
        return (
            f"http {status} success {payload.get('success')} "
            f"n {len(numbers)} sum {sum(numbers)} page {payload.get('page')}"
        )
    detail = payload.get("error") or payload.get("message") or payload.get("msg") or ""
    keys = ",".join(list(payload)[:8])
    return f"http {status} keys {keys} detail {str(detail)[:120]}"


async def post_with_backoff(client, path: str, body: str):
    delay = 0.4
    response = None
    for _ in range(6):
        response = await client.post(
            path,
            content=body.encode("utf-8"),
            headers={"Content-Type": "application/json", "Referer": REFERER},
        )
        if response.status_code != 429:
            return response
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    return response


async def main() -> None:
    session = SpiderSession()
    env = os.environ.copy()
    env["SPIDER_COOKIE"] = "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies.jar)
    env["MINT"] = "1"
    env["MINT_LIMIT"] = "3"
    env.pop("PYTHONPATH", None)
    MINT.mkdir(exist_ok=True)
    for child in MINT.iterdir():
        child.unlink()
    completed = subprocess.run(
        [str(NODE), str(HERE / "_run_vm.js")],
        cwd=str(HERE),
        env=env,
        check=False,
        timeout=90,
    )
    manifest = json.loads((MINT / "manifest.json").read_text(encoding="utf-8"))
    print("mint_exit", completed.returncode, "count", len(manifest))

    async with session.async_client({"Referer": REFERER}) as client:
        async def fetch_page(page: int) -> str:
            item = next(entry for entry in manifest if entry["page"] == page)
            body = (MINT / item["file"]).read_text(encoding="utf-8")
            response = await post_with_backoff(client, item["path"], body)
            text = response.text
            try:
                payload = decode(text) if text and text[0] in INDEX else response.json()
            except Exception:
                payload = {"error": "undecodable", "message": str(response.status_code)}
            return summarize(response.status_code, payload)

        pages = await collect_pages(fetch_page, [1, 2, 3], concurrency=3)
    for page in sorted(pages):
        print(f"replay {page} {pages[page]}")


if __name__ == "__main__":
    asyncio.run(main())
