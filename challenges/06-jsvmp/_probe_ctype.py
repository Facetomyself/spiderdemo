import base64
import struct
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
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        out.append(piece | (0x80 if value else 0))
        if not value:
            return bytes(out)


def field_varint(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def field_bytes(field: int, data: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(data)) + data


def message(stamp: int, token: str) -> bytes:
    finger = b"".join(
        [
            field_bytes(1, base64.b64encode(KEY.encrypt(UA.encode(), padding.PKCS1v15()))),
            field_bytes(2, b"zh-CN"),
            field_bytes(3, b"1920x1080"),
            field_bytes(4, b"24"),
            field_varint(5, 32),
            field_varint(6, 1),
            field_bytes(7, b"PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer, Microsoft Edge PDF Viewer, WebKit built-in PDF"),
            field_varint(8, 1),
            field_varint(9, 0),
        ]
    )
    return b"".join(
        [
            field_varint(1, 1),
            field_bytes(2, b"jsvmp_challenge"),
            field_bytes(3, token.encode()),
            field_varint(4, stamp),
            field_bytes(5, finger),
        ]
    )


def main() -> None:
    stamp = int(time.time())
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    token = base64.b64encode(KEY.encrypt(plain.encode(), padding.PKCS1v15())).decode()
    raw = message(stamp, token)
    framed = b"\x00" + struct.pack(">I", len(raw)) + raw
    session = SpiderSession()
    types = [
        "application/grpc-web+proto",
        "application/x-protobuf",
        "application/octet-stream",
        "application/grpc-web-text",
    ]
    with session.client() as client:
        for ctype in types:
            for label, body in (("raw", raw), ("framed", framed)):
                response = client.post(
                    "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                    content=body,
                    headers={
                        "Accept": "*/*",
                        "Content-Type": ctype,
                        "X-Protobuf-Request": "1",
                        "User-Agent": UA,
                        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
                    },
                )
                text = response.content[:160].decode("utf-8", "replace")
                print(ctype.split("/")[-1], label, response.status_code, len(response.content), text)


if __name__ == "__main__":
    main()
