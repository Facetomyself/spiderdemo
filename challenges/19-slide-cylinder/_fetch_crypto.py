"""Download the page's crypto-js build. No cookies printed."""

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("crypto-js.min.js")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get("/static/js/crypto-js.min.js")
        response.raise_for_status()
        OUT.write_bytes(response.content)
    print("bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
