"""Collect jsvmp2 pages over one websocket and submit the sum.

Node only calls the SDK cipher. Python owns the socket and the page schedule.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import websockets
from websockets.extensions.permessage_deflate import ClientPerMessageDeflateFactory
from curl_cffi import CurlWsFlag
from curl_cffi.requests import AsyncSession

from modules.runtime import SpiderSession, collect_pages, public_result

ROOT = Path(__file__).resolve().parent
NODE = r"D:\reverse_ENV\tools\node\node.exe"
BRIDGE = ROOT / "_sandbox.js"
ORIGIN = "https://www.spiderdemo.cn"
PAGE = "/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"
INIT = "/authentication/api/jsvmp2_challenge/init/?challenge_type=jsvmp2_challenge"
SUBMIT = "/authentication/api/jsvmp2_challenge/submit/"
CHALLENGE = "jsvmp2_challenge"
REFERER = ORIGIN + PAGE
OUT = ROOT / "result.json"
PAGE_CONCURRENCY = 4


def worker_count() -> int:
    raw = os.environ.get("SPIDER_WORKERS", "")
    if raw.isdigit():
        count = int(raw)
        if 1 <= count <= 8:
            return count
    return PAGE_CONCURRENCY
FIREFOX_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) "
    "Gecko/20100101 Firefox/155.0"
)
BROWSER_UPGRADE = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "websocket",
    "Sec-Fetch-Site": "same-origin",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _upgrade_error(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    code = getattr(response, "status_code", None)
    if code is None:
        code = getattr(exc, "status_code", None)
    body = getattr(response, "body", b"") or getattr(response, "content", b"") or b""
    if isinstance(body, str):
        body = body.encode("utf-8", "replace")
    if code:
        return f"status {code} bodyLen {len(body)}"
    return type(exc).__name__


class _CurlSocket:
    def __init__(self, http: AsyncSession, ws: object) -> None:
        self.http = http
        self.ws = ws

    async def send_text(self, text: str) -> None:
        await self.ws.send_str(text)

    async def send_bin(self, data: bytes) -> None:
        await self.ws.send_binary(data)

    async def recv(self) -> tuple[bytes, bool]:
        payload, flags = await self.ws.recv()
        return payload, not bool(flags & int(CurlWsFlag.TEXT))

    async def close(self) -> None:
        await self.ws.close()
        await self.http.close()


class _LibSocket:
    def __init__(self, ws: object) -> None:
        self.ws = ws

    async def send_text(self, text: str) -> None:
        await self.ws.send(text)

    async def send_bin(self, data: bytes) -> None:
        await self.ws.send(data)

    async def recv(self) -> tuple[bytes, bool]:
        incoming = await self.ws.recv()
        if isinstance(incoming, bytes):
            return incoming, True
        return str(incoming).encode("utf-8"), False

    async def close(self) -> None:
        await self.ws.close()


def cookie_header(session: SpiderSession) -> str:
    return "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies.jar)


def load_init(session: SpiderSession) -> dict:
    with session.client({"Referer": REFERER, "Accept": "application/json"}) as client:
        delay = 1.0
        for _ in range(5):
            response = client.get(INIT)
            if response.status_code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 16)
                continue
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("init payload was not an object")
            return payload
    raise RuntimeError("init was rate limited")


async def submit_answer(session: SpiderSession, total: int) -> dict:
    body = {"challenge_type": CHALLENGE, "answer": str(total)}
    async with session.async_client({"Referer": REFERER, "Accept": "application/json"}) as client:
        delay = 1.0
        for _ in range(5):
            response = await client.post(SUBMIT, json=body)
            if response.status_code == 429:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 16)
                continue
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {"success": False, "error": "submit was not json", "message": str(response.status_code)}
            if isinstance(payload, dict):
                return payload
            return {"success": False, "error": "submit payload was not an object"}
    return {"success": False, "error": "submit was rate limited"}


FP = [1] * 22 + [28, 0, 5, 24, 1920, 1080, 100, 1313108922, -1708469978, 1, -1, 0, 0, 1, 0, 1]
WS_URL = "wss://www.spiderdemo.cn/ws/"


class _Codec:
    def __init__(self) -> None:
        self.proc: asyncio.subprocess.Process | None = None
        self.lock = asyncio.Lock()

    async def start(self) -> None:
        self.proc = await asyncio.create_subprocess_exec(
            NODE,
            str(ROOT / "_sdk_codec.js"),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        ready = await self._read()
        if ready.get("op") != "ready":
            raise RuntimeError("codec did not start")

    async def _read(self) -> dict:
        assert self.proc and self.proc.stdout
        line = await self.proc.stdout.readline()
        if not line:
            raise RuntimeError("codec closed")
        payload = json.loads(line)
        if payload.get("op") == "error":
            raise RuntimeError("codec " + str(payload.get("name") or "error"))
        return payload

    async def call(self, message: dict) -> dict:
        assert self.proc and self.proc.stdin
        async with self.lock:
            self.proc.stdin.write((json.dumps(message, separators=(",", ":")) + "\n").encode())
            await self.proc.stdin.drain()
            return await self._read()

    async def close(self) -> None:
        if self.proc and self.proc.returncode is None:
            self.proc.kill()
            await self.proc.wait()


def _nested(init: dict, key: str):
    value = init.get(key)
    if value is not None:
        return value
    data = init.get("data")
    if isinstance(data, dict):
        return data.get(key)
    return None


def seed_of(init: dict) -> str:
    for key in ("token_seed", "seed"):
        value = _nested(init, key)
        if isinstance(value, str) and value:
            return value
    raise RuntimeError("init has no seed")


def page_one_numbers(init: dict) -> list[int]:
    raw = _nested(init, "page_data") or []
    if not isinstance(raw, list):
        return []
    numbers = []
    for item in raw:
        if isinstance(item, str) and item.isdigit():
            numbers.append(int(item))
        elif isinstance(item, int) and not isinstance(item, bool):
            numbers.append(item)
    return numbers if len(numbers) == 10 else []


def extract_numbers(obj: object) -> list[int]:
    found: list[int] = []

    def walk(node: object) -> None:
        if isinstance(node, list):
            if len(node) == 3 and node[0] == 16:
                value = node[2]
                if isinstance(value, str) and value.lstrip("-").isdigit():
                    found.append(int(value))
                elif isinstance(value, int) and not isinstance(value, bool):
                    found.append(value)
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)

    walk(obj)
    return found


def page_id_of(obj: object) -> int | None:
    found: list[int] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            ident = node.get("id")
            if isinstance(ident, str) and ident.startswith("page-") and ident[5:].isdigit():
                found.append(int(ident[5:]))
            for item in node.values():
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(obj)
    return found[0] if found else None


def _frame_text(payload: bytes) -> str:
    return payload.decode("utf-8", "replace")


async def _connect(cookie: str, use_ads: bool, token: str):
    headers = dict(BROWSER_UPGRADE)
    jar = cookie
    if use_ads:
        jar = jar + "; ads-baidu=" + token
    if jar:
        headers["Cookie"] = jar
    kwargs = {
        "origin": ORIGIN,
        "additional_headers": headers,
        "user_agent_header": FIREFOX_UA,
        "proxy": None,
        "open_timeout": 12,
        "ping_interval": None,
        "compression": None,
        "extensions": [
            ClientPerMessageDeflateFactory(
                client_max_window_bits=None,
                compress_settings={"memLevel": 5},
            )
        ],
    }
    try:
        raw = await websockets.connect(WS_URL, **kwargs)
        return _LibSocket(raw), ""
    except Exception as exc:
        return None, "deflate " + _upgrade_error(exc)


class _PageSocket:
    def __init__(self, ws, codec: _Codec, seed: str) -> None:
        self.ws = ws
        self.codec = codec
        self.seed = seed
        self.waiters: list[tuple[int, asyncio.Future]] = []
        self.lock = asyncio.Lock()
        self.failed = asyncio.Event()
        self.error = ""
        self.reader: asyncio.Task | None = None

    async def start(self) -> None:
        self.reader = asyncio.create_task(self._read())

    async def _read(self) -> None:
        try:
            while True:
                payload, _binary = await self.ws.recv()
                text = _frame_text(payload).strip()
                if not text:
                    continue
                opened = await self.codec.call({"op": "open", "key": self.seed, "text": text})
                value = opened.get("value")
                if isinstance(value, list) and value and value[0] == 99:
                    detail = value[1] if len(value) > 1 else ""
                    self.error = "server " + str(detail)[:120]
                    self.failed.set()
                    return
                page = page_id_of(value)
                numbers = extract_numbers(value)
                async with self.lock:
                    index = 0
                    if page is not None:
                        for pos, (waiting, _future) in enumerate(self.waiters):
                            if waiting == page:
                                index = pos
                                break
                    if not self.waiters:
                        self.error = "unexpected page frame"
                        self.failed.set()
                        return
                    _page, future = self.waiters.pop(index)
                    if not future.done():
                        future.set_result(numbers)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            received = getattr(exc, "rcvd", None)
            code = getattr(received, "code", None)
            self.error = f"recv closed {code}" if code else type(exc).__name__
            self.failed.set()

    async def fetch(self, page: int) -> list[int]:
        if self.failed.is_set():
            raise RuntimeError(self.error or "socket failed")
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        async with self.lock:
            self.waiters.append((page, future))
        sealed = await self.codec.call({
            "op": "seal",
            "key": self.seed,
            "value": {"cmd": 4, "page": page, "ts": time.time_ns() // 1_000_000},
        })
        try:
            await self.ws.send_text(str(sealed["text"]))
        except Exception as exc:
            received = getattr(exc, "rcvd", None)
            code = getattr(received, "code", None)
            raise RuntimeError(f"send closed {code}" if code else type(exc).__name__) from exc
        done, _pending = await asyncio.wait({future, asyncio.create_task(self.failed.wait())}, return_when=asyncio.FIRST_COMPLETED, timeout=20)
        if future in done:
            return future.result()
        raise RuntimeError(self.error or "page timeout")

    async def close(self) -> None:
        if self.reader:
            self.reader.cancel()
        await self.ws.close()


async def _handshake(codec: _Codec, cookie: str, seed: str):
    last = "no socket"
    for use_ads in (True, False):
        issued = await codec.call({"op": "token", "seed": seed, "ts": time.time_ns() // 1_000_000})
        token = str(issued["token"])
        frame = base64.b64decode(str(issued["frame"]))
        ws, error = await _connect(cookie, use_ads, token)
        if ws is None:
            last = error
            if "status 403" not in error and use_ads:
                continue
            if use_ads:
                continue
            break
        try:
            await ws.send_bin(frame)
            payload, _binary = await asyncio.wait_for(ws.recv(), timeout=8)
        except Exception as exc:
            received = getattr(exc, "rcvd", None)
            code = getattr(received, "code", None)
            last = f"send closed {code}" if code else type(exc).__name__
            await ws.close()
            continue
        text = _frame_text(payload).strip()
        opened = await codec.call({"op": "open", "key": seed, "text": text})
        sealed = await codec.call({"op": "seal", "key": seed, "value": {"cmd": 99, "fp": FP}})
        await ws.send_text(str(sealed["text"]))
        print(json.dumps({
            "phase": "ready",
            "ads": use_ads,
            "tokenLen": issued.get("tokenLen"),
            "frameLen": issued.get("frameLen"),
            "challengeLen": len(text),
            "plainLen": opened.get("plainLen"),
            "fpLen": sealed.get("textLen"),
        }), flush=True)
        return ws
    raise RuntimeError("websocket upgrade rejected: " + last)


async def collect(session: SpiderSession, init: dict, only: list[int] | None = None) -> list[list[int]]:
    total_pages = int(_nested(init, "total_pages") or 100)
    first = page_one_numbers(init)
    current = _nested(init, "current_page")
    pages: dict[int, list[int]] = {}
    wanted = list(only) if only is not None else list(range(1, total_pages + 1))
    if only is None and first and current in (1, "1", None):
        pages[1] = first
        wanted = [page for page in wanted if page != 1]
    if not wanted:
        return [pages[page] for page in range(1, total_pages + 1)]
    codec = _Codec()
    socket: _PageSocket | None = None
    try:
        await codec.start()
        ws = await _handshake(codec, cookie_header(session), seed_of(init))
        socket = _PageSocket(ws, codec, seed_of(init))
        await socket.start()

        async def fetch_page(page: int) -> list[int]:
            return await socket.fetch(page)

        fetched = await collect_pages(fetch_page, wanted, worker_count())
        pages.update(fetched)
    finally:
        if socket is not None:
            await socket.close()
        await codec.close()
    if only is not None:
        return [pages[page] for page in wanted]
    return [pages[page] for page in range(1, total_pages + 1)]


def write_result(payload: dict) -> dict:
    result = public_result(payload)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


async def main() -> None:
    session = SpiderSession()
    if os.environ.get("SPIDER_SKIP_PY_INIT") == "1":
        init = {"total_pages": 100, "page_data": []}
    else:
        init = load_init(session)
    try:
        groups = await collect(session, init)
    except RuntimeError as exc:
        write_result({"success": False, "error": str(exc), "message": str(exc)})
        raise SystemExit(1) from exc
    total = sum(sum(group) for group in groups)
    payload = await submit_answer(session, total)
    result = write_result(payload if isinstance(payload, dict) else {})
    accepted = result.get("is_correct") is True or result.get("correct") is True or result.get("completed") is True
    if not accepted and "答案正确" not in str(result.get("message") or ""):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
