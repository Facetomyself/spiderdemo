import base64
import hashlib
import struct
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCHshK1NixnImx08tq3V6Vjvfwk
ARCOJbnPMZr4Ogh16ORkC45CFUB+2gu+IN2vjH3oJaY2e/6y0shD2fURMB3urxKE
3gewRZMm5/T7noAXs4DJTOxJGwAJFHFfd9Zp73vXEcac4DKrvItOkjLx9P5JkA39
47brgsMObYGdG3HOdwIDAQAB
-----END PUBLIC KEY-----"""
KEY = serialization.load_pem_public_key(PUBLIC_KEY.encode())


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


def frame(stamp: int, token: str) -> bytes:
    finger = bytes.fromhex("220232342820300140004800")
    message = b"".join(
        [
            field_varint(1, 1),
            field_bytes(2, b"jsvmp_challenge"),
            field_bytes(3, token.encode()),
            field_varint(4, stamp),
            field_bytes(5, finger),
        ]
    )
    return b"\x00" + struct.pack(">I", len(message)) + message


def main() -> None:
    stamp = int(time.time())
    raw = f"{stamp}_jsvmp_secret_key_2023".encode()
    wrapped = base64.b64encode(raw)
    variants = {
        "pkcs1-b64": base64.b64encode(KEY.encrypt(wrapped, padding.PKCS1v15())).decode(),
        "oaep1-b64": base64.b64encode(KEY.encrypt(wrapped, padding.OAEP(mgf=padding.MGF1(hashes.SHA1()), algorithm=hashes.SHA1(), label=None))).decode(),
        "oaep256-raw": base64.b64encode(KEY.encrypt(raw, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))).decode(),
        "hex-pkcs1": KEY.encrypt(wrapped, padding.PKCS1v15()).hex(),
        "md5": base64.b64encode(KEY.encrypt(hashlib.md5(raw).hexdigest().encode(), padding.PKCS1v15())).decode(),
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        for label, token in variants.items():
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=frame(stamp, token),
            )
            print(label, len(token), response.status_code, response.content.decode()[:80])


if __name__ == "__main__":
    main()
