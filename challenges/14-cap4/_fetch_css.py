"""Download cap4 stylesheet. No cookies printed."""

from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("cap4_challenge.css")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get("/static/css/captcha/cap4_challenge.css")
        OUT.write_bytes(response.content)
        print(response.status_code, len(response.content))


if __name__ == "__main__":
    main()
