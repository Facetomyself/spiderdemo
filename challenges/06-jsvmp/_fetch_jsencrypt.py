from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).resolve().parent / "assets" / "jsencrypt1.js"


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get("/static/js/jsencrypt1.js")
        response.raise_for_status()
        OUT.write_bytes(response.content)
    print("bytes", len(response.content))


if __name__ == "__main__":
    main()
