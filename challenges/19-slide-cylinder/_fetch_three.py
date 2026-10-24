"""Download three.min.js and locate cylinder UV writes."""

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("three.min.js")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get("/static/js/three.min.js")
        response.raise_for_status()
        OUT.write_bytes(response.content)
    text = OUT.read_text(encoding="utf-8", errors="replace")
    print("bytes", len(text))
    for needle in ["CylinderGeometry", "REVISION", "thetaLength"]:
        print(needle, text.find(needle))


if __name__ == "__main__":
    main()
