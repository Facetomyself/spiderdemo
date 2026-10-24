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


def rsa_b64(text: str) -> str:
    cipher = KEY.encrypt(text.encode(), padding.PKCS1v15())
    return base64.b64encode(cipher).decode()


def fingerprint(mode: str, ua_token: str) -> bytes:
    if mode == "thin":
        return bytes.fromhex("220232342820300140004800")
    parts = [
        field_bytes(1, ua_token.encode()),
        field_bytes(2, b"zh-CN"),
        field_bytes(3, b"1920x1080"),
        field_bytes(4, b"24"),
        field_varint(5, 32),
        field_varint(6, 1),
        field_bytes(7, b"PDF Viewer, Chrome PDF Viewer"),
        field_varint(8, 1),
        field_varint(9, 0),
    ]
    return b"".join(parts)


def frame_for(page: int, stamp: int, token: str, finger: bytes, prefix: str) -> bytes:
    message = b"".join(
        [
            field_varint(1, page),
            field_bytes(2, b"jsvmp_challenge"),
            field_bytes(3, token.encode()),
            field_varint(4, stamp),
            field_bytes(5, finger),
        ]
    )
    if prefix == "grpc":
        return b"\x00" + struct.pack(">I", len(message)) + message
    if prefix == "raw":
        return message
    if prefix == "fixed":
        return bytes([0, 0, 0, 1, 251]) + message
    raise ValueError(prefix)


def main() -> None:
    stamp = int(time.time())
    ua_token = rsa_b64(UA)
    cases = []
    for year in ("2023", "2024", "2025", "2026"):
        raw = f"{stamp}_{year and 'jsvmp_secret_key_' + year}"
        wrapped = base64.b64encode(raw.encode()).decode()
        cases.append((f"b64-{year}-thin-grpc", rsa_b64(wrapped), "thin", "grpc"))
        cases.append((f"raw-{year}-thin-grpc", rsa_b64(raw), "thin", "grpc"))
    wrapped = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    cases.append(("b64-2023-full-grpc", rsa_b64(wrapped), "full", "grpc"))
    cases.append(("b64-2024-full-grpc", rsa_b64(base64.b64encode(f"{stamp}_jsvmp_secret_key_2024".encode()).decode()), "full", "grpc"))
    cases.append(("b64-2023-thin-raw", rsa_b64(wrapped), "thin", "raw"))
    cases.append(("b64-2024-full-raw", rsa_b64(base64.b64encode(f"{stamp}_jsvmp_secret_key_2024".encode()).decode()), "full", "raw"))
    session = SpiderSession()
    headers = {
        "Accept": "application/grpc-web+proto, application/json, */*",
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "User-Agent": UA,
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        for label, token, finger_mode, prefix in cases:
            body = frame_for(1, stamp, token, fingerprint(finger_mode, ua_token), prefix)
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=body,
            )
            text = response.content[:180].decode("utf-8", "replace").replace("\n", " ")
            print(label, response.status_code, response.headers.get("content-type"), len(response.content), text)


if __name__ == "__main__":
    main()
