"""Status lines for likely websocket paths. No cookies printed."""

import socket
import ssl

from modules.runtime import SpiderSession

PATHS = [
    "/ws/?EIO=4&transport=websocket",
    "/socket.io/?EIO=4&transport=websocket",
    "/ws/socket.io/?EIO=4&transport=websocket",
    "/authentication/ws/?challenge_type=jsvmp2_challenge",
]


def status(path: str, cookie: str) -> None:
    ctx = ssl.create_default_context()
    with socket.create_connection(("www.spiderdemo.cn", 443), 12) as sock:
        with ctx.wrap_socket(sock, server_hostname="www.spiderdemo.cn") as secure:
            head = "\r\n".join([
                f"GET {path} HTTP/1.1",
                "Host: www.spiderdemo.cn",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version: 13",
                "Origin: https://www.spiderdemo.cn",
                "Cookie: " + cookie,
                "",
                "",
            ])
            secure.sendall(head.encode())
            line = secure.recv(180).decode("utf-8", "replace").split("\r\n", 1)[0]
    print(line, path.split("?", 1)[0])


def main() -> None:
    session = SpiderSession()
    cookie = "; ".join(f"{item.name}={item.value}" for item in session.cookies.jar)
    for path in PATHS:
        status(path, cookie)


if __name__ == "__main__":
    main()
