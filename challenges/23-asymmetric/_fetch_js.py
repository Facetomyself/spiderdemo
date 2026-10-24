"""Download challenge scripts. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).parent
PATHS = [
    "/static/js/obfuscation/fsymmetry_challenge.js",
    "/static/js/anti_automation.js",
    "/static/js/login-alert.js",
]


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        for path in PATHS:
            response = client.get(path)
            name = path.strip("/").replace("/", "__")
            target = OUT / name
            target.write_bytes(response.content)
            print(response.status_code, path, len(response.content), "->", target.name)


if __name__ == "__main__":
    main()
