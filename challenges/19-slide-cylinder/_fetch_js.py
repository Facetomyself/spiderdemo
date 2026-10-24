"""Download challenge scripts. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).parent
PATHS = [
    "/static/js/captcha/slide_cylinder.js",
    "/static/js/captcha/restore.js",
    "/static/js/anti_automation.js",
]


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        for path in PATHS:
            response = client.get(path)
            name = path.rsplit("/", 1)[-1]
            dest = OUT / name
            dest.write_bytes(response.content)
            print(name, response.status_code, len(response.content))


if __name__ == "__main__":
    main()
