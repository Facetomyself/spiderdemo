"""Download the symmetry challenge scripts. No cookies printed."""

from __future__ import annotations

from pathlib import Path

from modules.runtime import SpiderSession

FILES = {
    "/static/js/obfuscation/symmetry_challenge.js": "symmetry_challenge.js",
    "/static/js/anti_automation.js": "anti_automation.js",
}


def main() -> None:
    session = SpiderSession()
    root = Path(__file__).parent
    with session.client() as client:
        for path, name in FILES.items():
            response = client.get(path)
            target = root / name
            target.write_bytes(response.content)
            print(name, response.status_code, len(response.content), response.headers.get("content-type"))


if __name__ == "__main__":
    main()
