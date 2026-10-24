"""See whether a real init changes the protobuf page response."""

import base64
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCHshK1NixnImx08tq3V6Vjvfwk
ARCOJbnPMZr4Ogh16ORkC45CFUB+2gu+IN2vjH3oJaY2e/6y0shD2fURMB3urxKE
3gewRZMm5/T7noAXs4DJTOxJGwAJFHFfd9Zp73vXEcac4DKrvItOkjLx9P5JkA39
47brgsMObYGdG3HOdwIDAQAB
-----END PUBLIC KEY-----"""
KEY = serialization.load_pem_public_key(PUBLIC_KEY.encode())
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
PLUGINS = "PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer"


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        out.append(piece | (0x80 if value else 0))
        if not value:
            return bytes(out)


def fv(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def fb(field: int, data: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(data)) + data


def rsa(text: str) -> str:
    return base64.b64encode(KEY.encrypt(text.encode(), padding.PKCS1v15())).decode()


def body(page: int, stamp: int) -> bytes:
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2025".encode()).decode()
    token = rsa(plain)
    ua = rsa(UA[:80])
    nested = b"".join(
        [
            fb(1, ua.encode()),
            fb(2, b"zh-CN"),
            fb(3, b"1920x1080"),
            fb(4, b"24"),
            fv(5, 32),
            fv(6, 1),
            fb(7, PLUGINS.encode()),
            fv(8, 1),
            fv(9, 0),
        ]
    )
    message = b"".join(
        [
            fv(1, page),
            fb(2, b"jsvmp_challenge"),
            fb(3, token.encode()),
            fv(4, stamp),
            fb(5, nested),
        ]
    )
    return b"\x00" + len(message).to_bytes(4, "big") + message


def show(label: str, response) -> None:
    text = response.content[:160].decode("utf-8", "replace").replace("\n", " ")
    interesting = {
        key: value
        for key, value in response.headers.items()
        if key.lower() in {"content-type", "req-cost-time", "x-envoy-upstream-service-time"}
    }
    print(label, response.status_code, len(response.content), interesting, text)


def main() -> None:
    session = SpiderSession()
    headers = {
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
    }
    with session.client(headers) as client:
        init = client.get("/authentication/api/jsvmp_challenge/init/?challenge_type=jsvmp_challenge")
        payload = init.json()
        print("init", init.status_code, sorted(payload.keys()), "pages", payload.get("total_pages"), "n", len(payload.get("page_data") or []))
        stamp = int(time.time())
        page_headers = {
            "Content-Type": "application/grpc-web+proto",
            "X-Protobuf-Request": "1",
            "Accept": "application/grpc-web+proto, application/json, */*",
        }
        show("after-init", client.post(
            "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
            content=body(1, stamp),
            headers=page_headers,
        ))
        millis = int(time.time() * 1000)
        plain = base64.b64encode(f"{millis}_jsvmp_secret_key_2025".encode()).decode()
        token = rsa(plain)
        message = b"".join([
            varint((1 << 3) | 0) + varint(1),
            fb(2, b"jsvmp_challenge"),
            fb(3, token.encode()),
            fv(4, millis),
        ])
        framed = b"\x00" + len(message).to_bytes(4, "big") + message
        show("ms-no-fp", client.post(
            "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
            content=framed,
            headers=page_headers,
        ))
        garbage = b"\x00" + (20).to_bytes(4, "big") + b"A" * 20
        show("garbage", client.post(
            "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
            content=garbage,
            headers=page_headers,
        ))


if __name__ == "__main__":
    main()
