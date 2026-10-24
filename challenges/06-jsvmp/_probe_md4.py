import importlib.util
import struct
import time

from modules.runtime import SpiderSession

spec = importlib.util.spec_from_file_location(
    "pb", r"D:\reverse_ENV\workspace\spiderdemo\challenges\03-protobuf\solve.py"
)
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)


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
    milli = stamp * 1000
    finger = bytes.fromhex("220232342820300140004800")
    digests = {
        "md4-sec": pb.modified_md4(str(stamp)),
        "md4-ms": pb.modified_md4(str(milli)),
        "md4-secret": pb.modified_md4(f"{stamp}_jsvmp_secret_key_2023"),
        "md4-type": pb.modified_md4("jsvmp_challenge" + str(stamp)),
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
    }
    with session.client(headers=headers) as client:
        for label, digest in digests.items():
            message = fv(1, 1) + fb(2, b"jsvmp_challenge") + fb(3, digest.encode()) + fv(4, stamp) + fb(5, finger)
            response = client.post(
                "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge",
                content=frame(message),
            )
            print(label, response.status_code, response.content[:120].decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
