"""Print captcha API shapes only. No cookies, no image bytes."""

from __future__ import annotations

import json
from typing import Any

from modules.runtime import SpiderSession


def shape(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: shape(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        if not value:
            return ["empty"]
        if all(isinstance(item, (int, float)) for item in value):
            return [f"num*{len(value)}", value[:8]]
        return [shape(value[0], depth + 1), f"len={len(value)}"]
    if isinstance(value, str):
        if len(value) > 80:
            return f"str len={len(value)} prefix={value[:24]!r}"
        return value
    return value


def main() -> None:
    session = SpiderSession()
    with session.client(
        headers={"Referer": "https://www.spiderdemo.cn/captcha/slide_cylinder_challenge?challenge_type=slide_cylinder_challenge"}
    ) as client:
        init = client.get(
            "/captcha/api/slide_cylinder_challenge/init/",
            params={"challenge_type": "slide_cylinder_challenge"},
        )
        print("init", init.status_code)
        body = init.json()
        print(json.dumps(shape(body), ensure_ascii=False, indent=2))
        image = client.get("/captcha/api/slide_cylinder_challenge/captcha_image/")
        print("image", image.status_code, image.headers.get("content-type"), "bytes", len(image.content))
        payload = image.json()
        print("image_keys", sorted(payload.keys()))
        print(json.dumps(shape(payload), ensure_ascii=False, indent=2))
        css = client.get("/static/css/captcha/slide_cylinder_challenge.css")
        print("css", css.status_code, len(css.content))
        (image and None)
        path = __import__("pathlib").Path(__file__).with_name("slide_cylinder.css")
        path.write_text(css.text, encoding="utf-8")


if __name__ == "__main__":
    main()
