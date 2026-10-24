import base64
import struct
import subprocess
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


def main() -> None:
    key = serialization.load_pem_public_key(PUBLIC_KEY.encode())
    numbers = key.public_numbers()
    modulus = format(numbers.n, "x")
    print("py", modulus[:8], modulus[-8:], "elen", numbers.e)
    stamp = str(int(time.time()))
    token = subprocess.check_output(
        [
            r"D:\reverse_ENV\tools\node\node.exe",
            r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp\_jsencrypt_round.js",
            stamp,
        ],
        text=True,
    ).strip()
    print("token_len", len(token))
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    py_token = base64.b64encode(key.encrypt(plain.encode(), padding.PKCS1v15())).decode()
    finger = bytes.fromhex("220232342820300140004800")
    session = SpiderSession()
    headers = {
        "Accept": "application/grpc-web+proto, application/json, */*",
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        for label, value in (("js", token), ("py", py_token)):
            message = b"".join(
                [
                    field_varint(1, 1),
                    field_bytes(2, b"jsvmp_challenge"),
                    field_bytes(3, value.encode()),
                    field_varint(4, int(stamp)),
                    field_bytes(5, finger),
                ]
            )
            body = b"\x00" + struct.pack(">I", len(message)) + message
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=body,
            )
            print(label, response.status_code, len(response.content), response.content[:120].decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
