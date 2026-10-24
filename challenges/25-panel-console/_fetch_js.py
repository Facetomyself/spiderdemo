"""Download the panel challenge scripts. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).parent
PATHS = [
    "/static/js/check_devtools_jsvmp.js",
    "/static/js/anti_automation.js",
    "/static/js/login-alert.js",
    "/static/js/panel_challenge.js",
    "/static/css/panel.css",
]


def safe_name(path: str) -> str:
    return path.strip("/").replace("/", "__")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        for path in PATHS:
            response = client.get(path)
            name = safe_name(path)
            target = OUT / name
            target.write_bytes(response.content)
            print(response.status_code, len(response.content), name)


if __name__ == "__main__":
    main()
