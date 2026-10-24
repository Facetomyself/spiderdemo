"""Print only the websocket handshake status. No cookie or body."""

import asyncio
import socket
import ssl

import websockets

from modules.runtime import SpiderSession

URL = "wss://www.spiderdemo.cn/ws/"
ORIGIN = "https://www.spiderdemo.cn"
REFERER = ORIGIN + "/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"


def cookie_header(session: SpiderSession) -> str:
    return "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies.jar)


def preview(body: bytes) -> str:
    text = body.decode("utf-8", "replace")
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    return text[:180]


async def attempt(label: str, headers: dict, origin: str | None = ORIGIN) -> None:
    try:
        ws = await websockets.connect(
            URL,
            origin=origin,
            compression=None,
            additional_headers=headers,
            open_timeout=12,
            ping_interval=None,
        )
        print(label, "open")
        await ws.close()
    except Exception as exc:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        body = getattr(response, "body", b"") or b""
        print(label, type(exc).__name__, status, "body", len(body), preview(body))


def raw_status(path: str, cookie: str, upgrade: bool) -> None:
    ctx = ssl.create_default_context()
    with socket.create_connection(("www.spiderdemo.cn", 443), 12) as sock:
        with ctx.wrap_socket(sock, server_hostname="www.spiderdemo.cn") as secure:
            lines = [
                f"GET {path} HTTP/1.1",
                "Host: www.spiderdemo.cn",
                "User-Agent: Mozilla/5.0",
                "Origin: https://www.spiderdemo.cn",
            ]
            if upgrade:
                lines.extend([
                    "Upgrade: websocket",
                    "Connection: Upgrade",
                    "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version: 13",
                ])
            if cookie:
                lines.append("Cookie: " + cookie)
            secure.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
            data = secure.recv(800)
    text = data.decode("utf-8", "replace")
    lines = text.split("\r\n")
    status = lines[0]
    location = next((line for line in lines if line.lower().startswith("location:")), "")
    print(("up" if upgrade else "get"), path, status, location[:120])


def raw_upgrade(cookie: str) -> None:
    ctx = ssl.create_default_context()
    with socket.create_connection(("www.spiderdemo.cn", 443), 12) as sock:
        with ctx.wrap_socket(sock, server_hostname="www.spiderdemo.cn") as secure:
            lines = [
                "GET /ws/ HTTP/1.1",
                "Host: www.spiderdemo.cn",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version: 13",
                "Origin: https://www.spiderdemo.cn",
                "User-Agent: Mozilla/5.0",
            ]
            if cookie:
                lines.append("Cookie: " + cookie)
            secure.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
            data = secure.recv(1500)
    text = data.decode("utf-8", "replace")
    head = text.split("\r\n\r\n", 1)[0]
    safe = []
    for line in head.split("\r\n"):
        if line.lower().startswith("set-cookie:"):
            safe.append("set-cookie: <redacted>")
        else:
            safe.append(line[:160])
    print("raw", "cookie" if cookie else "bare")
    print("\n".join(safe[:16]))


async def main() -> None:
    session = SpiderSession()
    cookie = cookie_header(session)
    with session.client({"Referer": REFERER, "Accept": "application/json"}) as client:
        response = client.get("/authentication/api/jsvmp2_challenge/init/?challenge_type=jsvmp2_challenge")
    print("init", response.status_code)
    set_cookie = response.headers.get_list("set-cookie") if hasattr(response.headers, "get_list") else []
    print("set-cookie-names", ",".join(item.split("=", 1)[0] for item in set_cookie))
    print("jar", ",".join(sorted({cookie.name for cookie in session.cookies.jar})))
    fresh = cookie_header(session)
    chrome = {
        "Cookie": fresh,
        "Referer": REFERER,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "websocket",
        "Sec-Fetch-Mode": "websocket",
        "Sec-Fetch-Site": "same-origin",
    }
    await attempt("chrome-fetch", chrome)
    with session.client({"Referer": REFERER}) as client:
        plain = client.get("/ws/")
        print("httpx-get", plain.status_code, plain.headers.get("server", ""), len(plain.content))


if __name__ == "__main__":
    asyncio.run(main())
