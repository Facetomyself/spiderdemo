"""Mint ZeroWidth page seals, then collect all 100 pages asynchronously."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

HERE = Path(__file__).resolve().parent
NODE = Path(r"D:\reverse_ENV\tools\node\node.exe")
MINT = HERE / "_mint"
OUT = HERE / "result.json"
REFERER = "https://www.spiderdemo.cn/authentication/spiderking_challenge/"
PAGE_COUNT = 100
ZW = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"]
INDEX = {char: pos for pos, char in enumerate(ZW)}


def decode(text: str):
    if len(text) % 3:
        raise ValueError("zero-width length is not a multiple of 3")
    raw = bytearray()
    for offset in range(0, len(text), 3):
        raw.append((INDEX[text[offset]] << 6) | (INDEX[text[offset + 1]] << 3) | INDEX[text[offset + 2]])
    return json.loads(raw.decode("utf-8"))


def wait_pages(proc: subprocess.Popen[bytes], timeout: float) -> list[dict]:
    deadline = time.time() + timeout
    last = 0
    while time.time() < deadline:
        manifest_path = MINT / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.1)
                continue
            pages: dict[int, dict] = {}
            for item in manifest:
                if item.get("kind") == "page":
                    pages[int(item["page"])] = item
            if len(pages) != last:
                last = len(pages)
                print("minted", last, flush=True)
            if set(pages) == set(range(1, PAGE_COUNT + 1)):
                return [pages[number] for number in range(1, PAGE_COUNT + 1)]
        if proc.poll() is not None:
            raise SystemExit(f"vm exited {proc.returncode} before all pages were minted")
        time.sleep(0.2)
    raise SystemExit(f"mint timed out at {last}")


async def post_page(client, item: dict) -> list[int]:
    body = (MINT / item["file"]).read_bytes()
    delay = 0.5
    detail = "no response"
    for _ in range(8):
        response = await client.post(
            item["path"],
            content=body,
            headers={"Content-Type": "text/plain;charset=utf-8", "Referer": REFERER},
        )
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            detail = "429"
            continue
        payload = {}
        try:
            payload = decode(response.text)
        except Exception:
            payload = {}
        values = payload.get("values") if isinstance(payload, dict) else None
        if (
            response.status_code == 200
            and isinstance(payload, dict)
            and payload.get("success") is True
            and isinstance(values, list)
            and len(values) == 10
        ):
            return [int(number) for number in values]
        detail = str(payload.get("error") or payload.get("message") or response.status_code)[:160]
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    raise RuntimeError(f"page {item['page']}: {detail}")


def site_accepted(payload: dict) -> bool:
    if payload.get("is_correct") is True or payload.get("correct") is True or payload.get("completed") is True:
        return True
    return "答案正确" in str(payload.get("message") or payload.get("msg") or "")


async def collect_sum(session: SpiderSession, manifest: list[dict]) -> int:
    headers = {"Referer": REFERER, "Accept": "application/json, text/plain, */*"}
    async with session.async_client(headers) as client:

        async def fetch_page(page: int) -> list[int]:
            return await post_page(client, manifest[page - 1])

        pages = await collect_pages(fetch_page, range(1, PAGE_COUNT + 1), concurrency=4)
    return sum(sum(pages[page]) for page in range(1, PAGE_COUNT + 1))


def stop(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> None:
    session = SpiderSession()
    MINT.mkdir(exist_ok=True)
    for child in MINT.iterdir():
        if child.is_file():
            child.unlink()
    env = os.environ.copy()
    env["SPIDER_COOKIE"] = "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies.jar)
    env["MINT"] = "1"
    env["MINT_LIMIT"] = str(PAGE_COUNT)
    env["WAIT_ANSWER"] = "1"
    env.pop("PYTHONPATH", None)
    proc = subprocess.Popen([str(NODE), str(HERE / "_run_vm.js")], cwd=str(HERE), env=env)
    try:
        manifest = wait_pages(proc, 720)
        total = asyncio.run(collect_sum(session, manifest))
        print("collected", PAGE_COUNT, "answer_len", len(str(total)), flush=True)
        (MINT / "answer.txt").write_text(str(total), encoding="utf-8")
        public_path = MINT / "submit_public.json"
        deadline = time.time() + 90
        while time.time() < deadline and not public_path.exists():
            if proc.poll() is not None:
                break
            time.sleep(0.2)
        if not public_path.exists():
            status_path = MINT / "status.log"
            if status_path.exists():
                tail = status_path.read_text(encoding="utf-8").splitlines()[-15:]
                print("status_tail", " || ".join(tail), flush=True)
            raise SystemExit("submit response missing")
        payload = json.loads(public_path.read_text(encoding="utf-8"))
        result = public_result(payload if isinstance(payload, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("accepted", site_accepted(result), flush=True)
        print("message", result.get("message") or result.get("msg") or result.get("error"), flush=True)
        if not site_accepted(result):
            raise SystemExit("submit was not accepted")
    finally:
        stop(proc)


if __name__ == "__main__":
    main()
