import base64
import struct
import time

from cryptography.hazmat.primitives import serialization

from modules.runtime import SpiderSession

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCHshK1NixnImx08tq3V6Vjvfwk
ARCOJbnPMZr4Ogh16ORkC45CFUB+2gu+IN2vjH3oJaY2e/6y0shD2fURMB3urxKE
3gewRZMm5/T7noAXs4DJTOxJGwAJFHFfd9Zp73vXEcac4DKrvItOkjLx9P5JkA39
47brgsMObYGdG3HOdwIDAQAB
-----END PUBLIC KEY-----"""
KEY = serialization.load_pem_public_key(PUBLIC_KEY.encode())
NUMBERS = KEY.public_numbers()


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


def textbook(data: bytes) -> bytes:
    block = int.from_bytes(data, "big")
    cipher = pow(block, NUMBERS.e, NUMBERS.n)
    return cipher.to_bytes(128, "big")


def frame(token: bytes, stamp: int) -> bytes:
    finger = bytes.fromhex("220232342820300140004800")
    message = fv(1, 1) + fb(2, b"jsvmp_challenge") + fb(3, token) + fv(4, stamp) + fb(5, finger)
    return b"\x00" + struct.pack(">I", len(message)) + message


def main() -> None:
    stamp = int(time.time())
    secret = f"{stamp}_jsvmp_secret_key_2023".encode()
    wrapped = base64.b64encode(secret)
    cases = {
        "tb-raw-b64": base64.b64encode(textbook(secret)),
        "tb-wrap-b64": base64.b64encode(textbook(wrapped)),
        "tb-raw-bytes": textbook(secret),
        "tb-wrap-hex": textbook(wrapped).hex().encode(),
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        for label, token in cases.items():
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=frame(token, stamp),
            )
            print(label, response.status_code, response.content[:160].decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
