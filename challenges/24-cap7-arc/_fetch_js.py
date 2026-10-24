"""Download cap7 static assets. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

ASSETS = [
    "/static/js/captcha/cap7_challenge.js",
    "/static/css/captcha/cap7_challenge.css",
    "/static/js/anti_automation.js",
]


def safe_name(path: str) -> str:
    return path.strip("/").replace("/", "__")


def main() -> None:
    session = SpiderSession()
    out_dir = Path(__file__).parent
    with session.client() as client:
        for path in ASSETS:
            response = client.get(path)
            dest = out_dir / safe_name(path)
            dest.write_bytes(response.content)
            print(path, response.status_code, len(response.content), dest.name)


if __name__ == "__main__":
    main()
