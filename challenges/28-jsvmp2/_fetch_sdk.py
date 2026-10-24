from pathlib import Path

from modules.runtime import SpiderSession

PATHS = [
    "/static/js/authentication/sdk.min.js",
    "/static/js/authentication/sdk.js",
]
OUT = Path(__file__).parent / "assets"


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        for path in PATHS:
            response = client.get(path)
            name = path.rsplit("/", 1)[-1]
            target = OUT / name
            if response.status_code == 200:
                target.write_bytes(response.content)
            print(name, response.status_code, len(response.content), response.headers.get("content-type", ""))


if __name__ == "__main__":
    main()
