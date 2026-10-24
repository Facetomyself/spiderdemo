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


def fv(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def fb(field: int, data: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(data)) + data


def finger(ua: bytes) -> bytes:
    return b"".join(
        [
            fb(1, ua),
            fb(2, b"zh-CN"),
            fb(3, b"1920x1080"),
            fb(4, b"24"),
            fv(5, 32),
            fv(6, 1),
            fb(7, b"PDF Viewer"),
            fv(8, 1),
            fv(9, 0),
        ]
    )


def main() -> None:
    stamp = int(time.time())
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    token = base64.b64encode(KEY.encrypt(plain.encode(), padding.PKCS1v15())).decode()
    ua_rsa = base64.b64encode(KEY.encrypt(UA.encode(), padding.PKCS1v15())).decode()
    cases = {
        "ua-plain": finger(UA.encode()),
        "ua-rsa": finger(ua_rsa.encode()),
        "ua-empty": bytes.fromhex("220232342820300140004800"),
    }
    session = SpiderSession()
    with session.client() as client:
        for label, fp in cases.items():
            message = fv(1, 1) + fb(2, b"jsvmp_challenge") + fb(3, token.encode()) + fv(4, stamp) + fb(5, fp)
            body = b"\x00" + struct.pack(">I", len(message)) + message
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=body,
                headers={
                    "Content-Type": "application/grpc-web+proto",
                    "X-Protobuf-Request": "1",
                    "User-Agent": UA,
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
                },
            )
            print(label, response.status_code, response.content[:100].decode())


if __name__ == "__main__":
    main()
