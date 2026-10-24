"""Save the challenge script. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("hash_challenge.js")
SRC = "/static/js/obfuscation/hash_challenge.js"


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get(SRC)
        text = response.text
        OUT.write_text(text, encoding="utf-8")
        print("status", response.status_code, "len", len(text))
        print("ctype", response.headers.get("content-type"))
        print(text[:1500])


if __name__ == "__main__":
    main()
