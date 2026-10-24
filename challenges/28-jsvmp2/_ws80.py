"""Check plain HTTP websocket upgrade status. No cookies printed."""

import socket

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"


def upgrade(host: str, port: int, path: str, cookie: str, tls: bool) -> None:
    sock = socket.create_connection((host, port), 12)
    if tls:
        import ssl
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(sock, server_hostname=host)
    lines = [
        f"GET {path} HTTP/1.1",
        f"Host: {host}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
        "Sec-WebSocket-Version: 13",
        "Origin: https://www.spiderdemo.cn",
        "User-Agent: Mozilla/5.0",
        "Referer: " + REFERER,
    ]
    if cookie:
        lines.append("Cookie: " + cookie)
    sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
    data = sock.recv(300).decode("utf-8", "replace")
    print(port, path, data.split("\r\n", 1)[0])
    sock.close()


def main() -> None:
    session = SpiderSession()
    cookie = "; ".join(f"{item.name}={item.value}" for item in session.cookies.jar)
    upgrade("www.spiderdemo.cn", 80, "/ws/", cookie, False)
    upgrade("www.spiderdemo.cn", 80, "/ws", cookie, False)


if __name__ == "__main__":
    main()
