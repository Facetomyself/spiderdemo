"""See whether the jsvmp route accepts the T3 signature inside a grpc-web frame."""

import importlib.util
import time

from modules.runtime import SpiderSession

spec = importlib.util.spec_from_file_location(
    "pb", r"D:\reverse_ENV\workspace\spiderdemo\challenges\03-protobuf\solve.py"
)
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)

URL = "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"


def frame(message: bytes) -> bytes:
    return b"\x00" + len(message).to_bytes(4, "big") + message


def show(label: str, response) -> None:
    text = response.content[:180].decode("utf-8", "replace").replace("\n", " ")
    print(label, response.status_code, text)


def main() -> None:
    stamp = int(time.time())
    milli = stamp * 1000
    cases = {
        "t3-caesar-ms": frame(pb.encode_page_request(1, "jsvmp_challenge", milli)),
        "t3-caesar-sec": frame(pb.encode_page_request(1, "jsvmp_challenge", stamp)),
        "t3-raw-ms": frame(pb.encode_page_request(1, "jsvmp_challenge", milli).replace(
            pb.encrypt_type("jsvmp_challenge").encode(),
            b"jsvmp_challenge",
            1,
        )),
    }
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
    }
    with session.client(headers) as client:
        for label, body in cases.items():
            show(label, client.post(URL, content=body))


if __name__ == "__main__":
    main()
