from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).resolve().parent / "assets"
PATHS = [
    "/static/js/jsvmp_challenge.js",
    "/static/css/jsvmp_challenge.css",
    "/static/js/anti_automation.js",
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    session = SpiderSession()
    with session.client() as client:
        for path in PATHS:
            resp = client.get(path)
            name = path.rsplit("/", 1)[-1]
            target = OUT / name
            target.write_bytes(resp.content)
            print(name, resp.status_code, len(resp.content), resp.headers.get("content-type"))


if __name__ == "__main__":
    main()
