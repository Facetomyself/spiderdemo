"""GET the challenge HTML, then post the client schema with the same session."""

import base64
import re
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
PAGE = "/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge"
URL = "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        out.append(piece | (0x80 if value else 0))
        if not value:
            return bytes(out)


def fb(field: int, data: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(data)) + data


def fv(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def main() -> None:
    session = SpiderSession()
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://www.spiderdemo.cn/",
    }
    with session.client(headers) as client:
        page = client.get(PAGE)
        text = page.text
        scripts = re.findall(r"<script[^>]+src=\"([^\"]+)\"", text)
        hiddens = re.findall(r"<input[^>]+>", text)
        print("page", page.status_code, len(text), "scripts", len(scripts))
        for src in scripts:
            print(" script", src)
        print(" inputs", len(hiddens))
        for tag in hiddens:
            print(" input", tag[:240])
        stamp = int(time.time())
        plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2025".encode()).decode()
        token = base64.b64encode(KEY.encrypt(plain.encode(), padding.PKCS1v15())).decode()
        ua = base64.b64encode(KEY.encrypt(UA[:80].encode(), padding.PKCS1v15())).decode()
        plugins = "PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer".encode()
        nested = b"".join([
            fb(1, ua.encode()), fb(2, b"zh-CN"), fb(3, b"1920x1080"), fb(4, b"24"),
            fv(5, 32), fv(6, 1), fb(7, plugins), fv(8, 1), fv(9, 0),
        ])
        message = b"".join([
            fv(1, 1), fb(2, b"jsvmp_challenge"), fb(3, token.encode()), fv(4, stamp), fb(5, nested),
        ])
        body = b"\x00" + len(message).to_bytes(4, "big") + message
        response = client.post(URL, content=body, headers={
            "Content-Type": "application/grpc-web+proto",
            "X-Protobuf-Request": "1",
            "Origin": "https://www.spiderdemo.cn",
            "Referer": "https://www.spiderdemo.cn" + PAGE,
            "Accept": "*/*",
        })
        print("post", response.status_code, response.content[:120].decode())


if __name__ == "__main__":
    main()
