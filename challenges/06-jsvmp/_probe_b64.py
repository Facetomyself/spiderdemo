"""See whether token decode errors leak the server exception."""

import base64
import time

from modules.runtime import SpiderSession

URL = "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        out.append(piece | (0x80 if value else 0))
        if not value:
            return bytes(out)


def fb(field: int, data: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(data)) + data


def fv(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def frame(token: bytes, stamp: int) -> bytes:
    message = b"".join([fv(1, 1), fb(2, b"jsvmp_challenge"), fb(3, token), fv(4, stamp)])
    return b"\x00" + len(message).to_bytes(4, "big") + message


def main() -> None:
    stamp = int(time.time())
    samples = {
        "bang": b"!!!!",
        "short-b64": base64.b64encode(b"hello"),
        "empty": b"",
        "words": b"not-a-token",
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
    }
    with session.client(headers) as client:
        for label, token in samples.items():
            response = client.post(URL, content=frame(token, stamp))
            print(label, response.status_code, response.content.decode("utf-8", "replace")[:240])


if __name__ == "__main__":
    main()
