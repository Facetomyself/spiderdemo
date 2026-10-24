"""Retry the client schema through a Chrome TLS fingerprint."""

import base64
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from curl_cffi import requests as curl

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
URL = "https://www.spiderdemo.cn/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"


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


def page_body() -> bytes:
    stamp = int(time.time())
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2025".encode()).decode()
    token = base64.b64encode(KEY.encrypt(plain.encode(), padding.PKCS1v15())).decode()
    ua = base64.b64encode(KEY.encrypt(UA[:80].encode(), padding.PKCS1v15())).decode()
    plugins = "PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer".encode()
    nested = b"".join([
        fb(1, ua.encode()),
        fb(2, b"zh-CN"),
        fb(3, b"1920x1080"),
        fb(4, b"24"),
        fv(5, 32),
        fv(6, 1),
        fb(7, plugins),
        fv(8, 1),
        fv(9, 0),
    ])
    message = b"".join([
        fv(1, 1),
        fb(2, b"jsvmp_challenge"),
        fb(3, token.encode()),
        fv(4, stamp),
        fb(5, nested),
    ])
    return b"\x00" + len(message).to_bytes(4, "big") + message


def show(label: str, response) -> None:
    text = response.content[:140].decode("utf-8", "replace").replace("\n", " ")
    cost = response.headers.get("req-cost-time")
    print(label, response.status_code, len(response.content), "cost", cost, text)


def main() -> None:
    session = SpiderSession()
    cookies = {cookie.name: cookie.value for cookie in session.cookies.jar}
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Origin": "https://www.spiderdemo.cn",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    for name in ("chrome120", "chrome131"):
        response = curl.post(
            URL,
            data=page_body(),
            headers=headers,
            cookies=cookies,
            impersonate=name,
            timeout=30,
        )
        show(name, response)
        time.sleep(0.4)


if __name__ == "__main__":
    main()
