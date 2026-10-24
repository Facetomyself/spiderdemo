"""Distinguish a decrypt exception from a plaintext mismatch."""

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
URL = "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"


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


def frame(token: str, stamp: int) -> bytes:
    message = b"".join([
        fv(1, 1),
        fb(2, b"jsvmp_challenge"),
        fb(3, token.encode()),
        fv(4, stamp),
    ])
    return b"\x00" + len(message).to_bytes(4, "big") + message


def main() -> None:
    stamp = int(time.time())
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2025".encode()).decode()
    good = base64.b64encode(KEY.encrypt(plain.encode(), padding.PKCS1v15())).decode()
    samples = {
        "ff": base64.b64encode(b"\xff" * 128).decode(),
        "zero": base64.b64encode(b"\x00" * 128).decode(),
        "short": base64.b64encode(b"\x02" * 32).decode(),
        "good": good,
        "rawplain": plain,
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
    }
    with session.client(headers) as client:
        for label, token in samples.items():
            response = client.post(URL, content=frame(token, stamp))
            print(label, response.status_code, response.headers.get("req-cost-time"), response.content[:120].decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
