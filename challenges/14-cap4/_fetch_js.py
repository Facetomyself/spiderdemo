"""Download cap4 page scripts. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).parent
SCRIPTS = [
    "/static/js/captcha/cap4_challenge.js",
    "/static/js/anti_automation.js",
]


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        for src in SCRIPTS:
            response = client.get(src)
            name = src.strip("/").replace("/", "__")
            path = OUT / name
            path.write_bytes(response.content)
            print(response.status_code, len(response.content), name)


if __name__ == "__main__":
    main()
