"""Map which request shapes change the protobuf error text."""

from modules.runtime import SpiderSession

URL = "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def show(label: str, response) -> None:
    text = response.content[:180].decode("utf-8", "replace").replace("\n", " ")
    print(label, response.status_code, response.headers.get("content-type"), text)


def main() -> None:
    session = SpiderSession()
    headers = {
        "User-Agent": UA,
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
    }
    message = b"\x08\x01"
    framed = b"\x00\x00\x00\x00\x02" + message
    cases = [
        ("json", {"Content-Type": "application/json", "X-Protobuf-Request": "1"}, b'{"page":1}'),
        ("no-flag", {"Content-Type": "application/grpc-web+proto", "X-Protobuf-Request": "1"}, message),
        ("bad-len", {"Content-Type": "application/grpc-web+proto", "X-Protobuf-Request": "1"}, b"\x00\x00\x00\x00\x09" + message),
        ("framed", {"Content-Type": "application/grpc-web+proto", "X-Protobuf-Request": "1"}, framed),
        ("xproto", {"Content-Type": "application/x-protobuf", "X-Protobuf-Request": "1"}, message),
        ("xproto-frame", {"Content-Type": "application/x-protobuf", "X-Protobuf-Request": "1"}, framed),
        ("no-x", {"Content-Type": "application/grpc-web+proto"}, framed),
        ("empty", {"Content-Type": "application/grpc-web+proto", "X-Protobuf-Request": "1"}, b""),
        ("get", None, None),
    ]
    with session.client(headers) as client:
        for label, extra, body in cases:
            if label == "get":
                response = client.get(URL)
            else:
                response = client.post(URL, content=body, headers=extra)
            show(label, response)


if __name__ == "__main__":
    main()
