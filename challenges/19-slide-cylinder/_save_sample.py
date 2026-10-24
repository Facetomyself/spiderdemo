"""Save one captcha image and the server_time cookie for local restore."""

from __future__ import annotations

import json
from pathlib import Path

from modules.runtime import SpiderSession

FOLDER = Path(__file__).parent


def main() -> None:
    session = SpiderSession()
    with session.client(
        headers={
            "Referer": "https://www.spiderdemo.cn/captcha/slide_cylinder_challenge?challenge_type=slide_cylinder_challenge"
        }
    ) as client:
        response = client.get("/captcha/api/slide_cylinder_challenge/captcha_image/")
        response.raise_for_status()
        payload = response.json()
        server_time = ""
        for cookie in client.cookies.jar:
            if cookie.name == "server_time":
                server_time = cookie.value
    (FOLDER / "_sample.json").write_text(
        json.dumps(
            {
                "bg": payload.get("bg"),
                "offset": payload.get("offset"),
                "order": payload.get("order"),
            }
        ),
        encoding="utf-8",
    )
    (FOLDER / "_server_time.txt").write_text(server_time, encoding="utf-8")
    print("saved", "offset", payload.get("offset"), "time_len", len(server_time))


if __name__ == "__main__":
    main()
