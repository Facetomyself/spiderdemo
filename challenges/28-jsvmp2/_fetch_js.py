"""Download scripts referenced by the jsvmp2 page."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).parent / "assets"
PATHS = [
    "/static/js/jsvmp2.js",
    "/static/js/anti_automation.js",
    "/static/js/login-alert.js",
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    session = SpiderSession()
    with session.client() as client:
        for path in PATHS:
            response = client.get(path)
            name = path.rsplit("/", 1)[-1]
            target = OUT / name
            target.write_bytes(response.content)
            print(name, response.status_code, len(response.content), response.headers.get("content-type", ""))


if __name__ == "__main__":
    main()
