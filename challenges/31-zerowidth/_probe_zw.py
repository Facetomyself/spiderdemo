"""Save the init body and describe its zero-width alphabet. No secrets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("init_body.bin")
PAGE = Path(__file__).with_name("page_post_body.bin")


def describe(label: str, raw: bytes, status: int) -> None:
    text = raw.decode("utf-8", "replace")
    counts = Counter(ord(char) for char in text)
    print(label, "status", status, "bytes", len(raw), "chars", len(text), "unique", len(counts))
    for code, count in counts.most_common():
        print(f"  U+{code:04X} x{count}")
    visible = "".join(char for char in text if ord(char) > 0x20 and not (0x2000 <= ord(char) <= 0x206F))
    print("  visible", repr(visible[:200]))


def main() -> None:
    session = SpiderSession()
    headers = {
        "Referer": "https://www.spiderdemo.cn/authentication/spiderking_challenge/",
        "Accept": "application/json, text/plain, */*",
    }
    with session.client(headers) as client:
        init = client.get(
            "/authentication/api/spiderking_challenge/init/?challenge_type=spiderking_challenge"
        )
        OUT.write_bytes(init.content)
        describe("init", init.content, init.status_code)
        print("init ctype", init.headers.get("content-type"))
        for method, path, body in (
            ("POST", "/authentication/api/spiderking_challenge/init/?challenge_type=spiderking_challenge", None),
            ("POST", "/authentication/api/spiderking_challenge/page/1/?challenge_type=spiderking_challenge", {}),
            ("POST", "/authentication/api/spiderking_challenge/page/1/", {"challenge_type": "spiderking_challenge", "page": 1}),
            ("GET", "/authentication/api/spiderking_challenge/page/1/", None),
        ):
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json=body)
            print(method, path, response.status_code, len(response.content), response.headers.get("content-type"))
            if response.content and response.status_code != 404:
                describe(method + " " + path.split("?")[0], response.content[:4000], response.status_code)
                if "page/1" in path and method == "POST":
                    PAGE.write_bytes(response.content)


if __name__ == "__main__":
    main()
