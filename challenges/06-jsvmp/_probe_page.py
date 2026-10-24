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


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        out.append(piece | (0x80 if value else 0))
        if not value:
            return bytes(out)


def tag(field: int, wire: int) -> bytes:
    return varint((field << 3) | wire)


def field_varint(field: int, value: int) -> bytes:
    return tag(field, 0) + varint(value)


def field_string(field: int, text: str) -> bytes:
    data = text.encode()
    return tag(field, 2) + varint(len(data)) + data


def field_bytes(field: int, data: bytes) -> bytes:
    return tag(field, 2) + varint(len(data)) + data


def auth_token(stamp: int) -> str:
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    key = serialization.load_pem_public_key(PUBLIC_KEY.encode())
    cipher = key.encrypt(plain.encode(), padding.PKCS1v15())
    return base64.b64encode(cipher).decode()


def page_frame(page: int, stamp: int, token: str) -> bytes:
    fingerprint = bytes.fromhex("220232342820300040004800")
    message = b"".join(
        [
            field_varint(1, page),
            field_string(2, "jsvmp_challenge"),
            field_string(3, token),
            field_varint(4, stamp),
            field_bytes(5, fingerprint),
        ]
    )
    return b"\x00" + struct.pack(">I", len(message)) + message


def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        piece = data[offset]
        offset += 1
        value |= (piece & 0x7F) << shift
        if not piece & 0x80:
            return value, offset
        shift += 7


def summarize_protobuf(data: bytes) -> list[str]:
    offset = 0
    rows = []
    while offset < len(data):
        key, offset = read_varint(data, offset)
        field, wire = key >> 3, key & 7
        if wire == 0:
            value, offset = read_varint(data, offset)
            rows.append(f"f{field}/varint={value}")
        elif wire == 2:
            length, offset = read_varint(data, offset)
            chunk = data[offset : offset + length]
            offset += length
            text = chunk.decode("utf-8", "replace")
            if all(32 <= ord(char) < 127 or char in "\n\r\t" for char in text):
                rows.append(f"f{field}/str[{length}]={text[:180]}")
            else:
                rows.append(f"f{field}/bytes[{length}]={chunk[:24].hex()}")
        else:
            rows.append(f"f{field}/wire{wire} at {offset}")
            break
    return rows


def decode_varint(data: bytes) -> int:
    value, _ = read_varint(data, 0)
    return value


def main() -> None:
    sample = base64.b64decode("MTc5MTYzMDYxMF9qc3ZtcF9zZWNyZXRfa2V5XzIwMjM=")
    print("sample_plain", sample.decode())
    print("sample_varint", decode_varint(bytes.fromhex("92baa8d606")))
    stamp = int(time.time())
    plain = base64.b64encode(f"{stamp}_jsvmp_secret_key_2023".encode()).decode()
    key = serialization.load_pem_public_key(PUBLIC_KEY.encode())
    token = base64.b64encode(key.encrypt(plain.encode(), padding.PKCS1v15())).decode()
    print("token_len", len(token), "plain_len", len(plain))
    frame = page_frame(1, stamp, token)
    session = SpiderSession()
    with session.client(
        headers={
            "Accept": "application/grpc-web+proto, application/json, */*",
            "Content-Type": "application/grpc-web+proto",
            "X-Protobuf-Request": "1",
            "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        }
    ) as client:
        response = client.post(
            "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
            content=frame,
        )
    print("status", response.status_code, response.headers.get("content-type"), len(response.content))
    interesting = {key: response.headers.get(key) for key in response.headers if key.lower().startswith("grpc") or key.lower().startswith("x-")}
    print("headers", interesting)
    body = response.content
    print("head", body[:80].hex())
    if body[:1] == b"{":
        print(body[:400].decode("utf-8", "replace"))
        return
    offset = 0
    index = 0
    while offset + 5 <= len(body) and index < 4:
        flag = body[offset]
        length = struct.unpack(">I", body[offset + 1 : offset + 5])[0]
        chunk = body[offset + 5 : offset + 5 + length]
        print("frame", index, "flag", flag, "len", length)
        if flag == 0:
            for row in summarize_protobuf(chunk)[:30]:
                print(row)
        else:
            print(chunk[:300].decode("utf-8", "replace"))
        offset += 5 + length
        index += 1
    print("consumed", offset, "total", len(body))


if __name__ == "__main__":
    main()
