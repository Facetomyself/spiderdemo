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


def token_for(text: str) -> str:
    return base64.b64encode(KEY.encrypt(text.encode(), padding.PKCS1v15())).decode()


def send(client, label: str, parts: list[bytes]) -> None:
    message = b"".join(parts)
    body = b"\x00" + struct.pack(">I", len(message)) + message
    response = client.post(
        "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
        content=body,
    )
    print(label, response.status_code, response.content.decode("utf-8", "replace"), "date", response.headers.get("date"))


def main() -> None:
    stamp = int(time.time())
    print("local", stamp)
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    token = token_for(plain)
    finger = bytes.fromhex("220232342820300140004800")
    base = [
        field_varint(1, 1),
        field_bytes(2, b"jsvmp_challenge"),
        field_bytes(3, token.encode()),
        field_varint(4, stamp),
        field_bytes(5, finger),
    ]
    session = SpiderSession()
    headers = {
        "Accept": "application/grpc-web+proto, application/json, */*",
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        send(client, "full", base)
        send(client, "no3", [base[0], base[1], base[3], base[4]])
        send(client, "no4", [base[0], base[1], base[2], base[4]])
        send(client, "no5", base[:4])
        send(client, "ts0", [base[0], base[1], base[2], field_varint(4, 0), base[4]])
        send(client, "tsms", [base[0], base[1], base[2], field_varint(4, stamp * 1000), base[4]])
        milli = base64.b64encode(f"{stamp * 1000}_jsvmp_secret_key_2023".encode()).decode()
        send(
            client,
            "bothms",
            [base[0], base[1], field_bytes(3, token_for(milli).encode()), field_varint(4, stamp * 1000), base[4]],
        )
        send(client, "junk", [base[0], base[1], field_bytes(3, b"abc"), base[3], base[4]])


if __name__ == "__main__":
    main()
