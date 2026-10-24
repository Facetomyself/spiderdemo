import base64
import struct
import time

from modules.runtime import SpiderSession


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


def frame(message: bytes) -> bytes:
    return b"\x00" + struct.pack(">I", len(message)) + message


def main() -> None:
    stamp = int(time.time())
    secret = f"{stamp}_jsvmp_secret_key_2023"
    wrapped = base64.b64encode(secret.encode()).decode()
    finger = bytes.fromhex("220232342820300140004800")
    cases = {
        "client-b64": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fb(3, wrapped.encode()) + fv(4, stamp) + fb(5, finger)),
        "client-raw": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fb(3, secret.encode()) + fv(4, stamp) + fb(5, finger)),
        "pub-b64": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fv(3, stamp) + fb(4, wrapped.encode())),
        "pub-raw": frame(fv(1, 1) + fb(2, b"jsvmp_challenge") + fv(3, stamp) + fb(4, secret.encode())),
        "pub-b64-caesar": frame(fv(1, 1) + fb(2, b"mvypsbfkdoohqjh") + fv(3, stamp) + fb(4, wrapped.encode())),
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
            print(label, response.status_code, response.content[:180].decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
