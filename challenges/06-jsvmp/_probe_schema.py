import base64
import hashlib
import importlib.util
import struct
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession

spec = importlib.util.spec_from_file_location(
    "pb", r"D:\reverse_ENV\workspace\spiderdemo\challenges\03-protobuf\solve.py"
)
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)

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


def fv(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def fb(field: int, data: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(data)) + data


def rsa(text: str) -> str:
    return base64.b64encode(KEY.encrypt(text.encode(), padding.PKCS1v15())).decode()


def frame(message: bytes) -> bytes:
    return b"\x00" + struct.pack(">I", len(message)) + message


def main() -> None:
    stamp = int(time.time())
    milli = stamp * 1000
    secret = f"{stamp}_jsvmp_secret_key_2023"
    token = rsa(base64.b64encode(secret.encode()).decode())
    caesar = pb.encrypt_type("jsvmp_challenge")
    md4 = pb.modified_md4(str(stamp))
    md4ms = pb.modified_md4(str(milli))
    cases = {
        "swap-rsa": frame(fb(1, b"")[:0] + fv(1, 1) + fb(2, b"jsvmp_challenge") + fv(3, stamp) + fb(4, token.encode())),
        "swap-rsa-ms": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fv(3, milli) + fb(4, rsa(base64.b64encode(f"{milli}_jsvmp_secret_key_2023".encode()).decode()).encode())),
        "pub-md4": frame(fv(1, 1) + fb(2, caesar.encode()) + fv(3, milli) + fb(4, md4ms.encode())),
        "pub-md4-sec": frame(fv(1, 1) + fb(2, caesar.encode()) + fv(3, stamp) + fb(4, md4.encode())),
        "pub-md5": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fv(3, stamp) + fb(4, hashlib.md5(str(stamp).encode()).hexdigest().encode())),
        "client-plus-md4": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fb(3, token.encode()) + fv(4, stamp) + fb(6, md4.encode())),
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        for label, body in cases.items():
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=body,
            )
            print(label, response.status_code, response.content[:140].decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
