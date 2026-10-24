"""Bridge the VM to one real websocket and print only message types."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess

import websockets

from modules.runtime import SpiderSession

NODE = r"D:\reverse_ENV\tools\node\node.exe"
BRIDGE = r"D:\reverse_ENV\workspace\spiderdemo\challenges\28-jsvmp2\_sandbox.js"
ORIGIN = "https://www.spiderdemo.cn"
REFERER = ORIGIN + "/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"
WS_URL = "wss://www.spiderdemo.cn/ws/"


def cookie_header(session: SpiderSession) -> str:
    return "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies.jar)


def brief(data):
    if isinstance(data, dict):
        kind = data.get("type")
        keys = [key for key in data.keys() if key != "type"]
        return kind, keys
    return type(data).__name__, []


async def main() -> None:
    session = SpiderSession()
    env = os.environ.copy()
    env["SPIDER_COOKIE"] = cookie_header(session)
    proc = await asyncio.create_subprocess_exec(
        NODE,
        BRIDGE,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.stdin and proc.stdout and proc.stderr

    async def send(message: dict) -> None:
        proc.stdin.write((json.dumps(message, separators=(",", ":")) + "\n").encode())
        await proc.stdin.drain()

    holder: dict = {"pending": [], "cookies": {}}

    async def pump_socket() -> None:
        ws = holder["ws"]
        try:
            async for incoming in ws:
                if isinstance(incoming, bytes):
                    print("recv-bin", len(incoming))
                    payload = base64.b64encode(incoming).decode("ascii")
                    await send({"op": "recv", "binary": True, "data": payload})
                else:
                    print("recv-text", len(incoming))
                    payload = base64.b64encode(incoming.encode("utf-8")).decode("ascii")
                    await send({"op": "recv", "binary": False, "data": payload})
        except asyncio.CancelledError:
            return

    async def pump_err() -> None:
        while True:
            line = await proc.stderr.readline()
            if not line:
                return
            text = line.decode("utf-8", "replace").strip()
            if text and "版权" not in text:
                print("stderr", text[:180])

    async def pump_bridge() -> None:
        while True:
            line = await proc.stdout.readline()
            if not line:
                print("bridge-eof")
                return
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            op = message.get("op")
            if op == "cookie":
                holder["cookies"][str(message.get("name") or "")] = str(message.get("value") or "")
                print("cookie-set", message.get("name"), len(str(message.get("value") or "")))
            elif op == "open":
                if "connect" not in holder:
                    async def connect_socket(url: str) -> None:
                        print("connecting", url.split("?")[0], "q", "?" in (url or ""))
                        pairs = [env["SPIDER_COOKIE"]]
                        for name, value in holder["cookies"].items():
                            if name:
                                pairs.append(f"{name}={value}")
                        token = next(iter(holder["cookies"].values()), "")
                        attempts = [("cookie", url, {"Cookie": "; ".join(pairs)})]
                        if token:
                            attempts.append(("query", url + "?ads-baidu=" + token, {"Cookie": env["SPIDER_COOKIE"]}))
                            attempts.append(("bearer", url, {"Cookie": env["SPIDER_COOKIE"], "Authorization": "Bearer " + token}))
                        chosen = None
                        for label, target, headers in attempts:
                            headers["Referer"] = REFERER
                            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            try:
                                chosen = await websockets.connect(
                                    target,
                                    origin=ORIGIN,
                                    compression=None,
                                    additional_headers=headers,
                                    open_timeout=12,
                                    ping_interval=None,
                                )
                                print("socket-open", label)
                                break
                            except Exception as exc:
                                response = getattr(exc, "response", None)
                                print("socket-error", label, getattr(response, "status_code", type(exc).__name__))
                        if chosen is None:
                            return
                        holder["ws"] = chosen
                        holder["socket"] = asyncio.create_task(pump_socket())
                        while holder["pending"]:
                            kind, raw = holder["pending"].pop(0)
                            await holder["ws"].send(raw if kind == "bin" else raw.decode("utf-8"))
                            print("sent", kind, len(raw))

                    holder["connect"] = asyncio.create_task(connect_socket(message.get("url") or WS_URL))
            elif op == "send":
                raw = base64.b64decode(message["data"])
                kind = "bin" if message.get("binary") else "text"
                ws = holder.get("ws")
                if ws is None:
                    holder["pending"].append((kind, raw))
                    print("buffer-send", kind, len(raw))
                    continue
                await ws.send(raw if kind == "bin" else raw.decode("utf-8"))
                print("sent", kind, len(raw))
            elif op == "msg":
                kind, keys = brief(message.get("data"))
                print("worker", kind, ",".join(keys))
            elif op == "grid":
                nums = message.get("numbers") or []
                print("grid", len(nums), sum(nums) if nums else 0)
            elif op == "fetch":
                print("fetch", message.get("method"), message.get("url"))
            elif op == "error":
                print("error", message.get("message"))
            else:
                shown = {key: value for key, value in message.items() if key not in {"op", "data"}}
                print("bridge", op, json.dumps(shown, ensure_ascii=False)[:400])

    tasks = [asyncio.create_task(pump_bridge()), asyncio.create_task(pump_err())]
    try:
        await asyncio.sleep(50)
        print("request-page", 2)
        await send({"op": "page", "page": 2})
        await asyncio.sleep(6)
    finally:
        for task in tasks:
            task.cancel()
        if holder.get("socket"):
            holder["socket"].cancel()
        if holder.get("ws"):
            await holder["ws"].close()
        proc.kill()
        await proc.wait()


if __name__ == "__main__":
    asyncio.run(main())
