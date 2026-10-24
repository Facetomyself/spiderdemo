"""Probe cap7 init and captcha endpoints. Do not print images or cookies."""

from __future__ import annotations

import json

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
PATHS = [
    "/captcha/api/cap7_challenge/init/?challenge_type=cap7_challenge",
    "/captcha/api/cap7_challenge/captcha/",
    "/captcha/api/cap7_challenge/captcha_image/",
    "/captcha/api/cap7_challenge/image/",
    "/captcha/api/cap7_challenge/get_captcha/",
]


def brief(value, depth=0):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if any(token in key.lower() for token in ("image", "img", "bg", "piece", "base64", "data")):
                if isinstance(item, str):
                    out[key] = {"type": "str", "len": len(item), "prefix": item[:24]}
                else:
                    out[key] = {"type": type(item).__name__}
            else:
                out[key] = brief(item, depth + 1) if depth < 2 else type(item).__name__
        return out
    if isinstance(value, list):
        return {"type": "list", "len": len(value), "first": brief(value[0], depth + 1) if value else None}
    if isinstance(value, str):
        if len(value) > 180:
            return {"type": "str", "len": len(value), "prefix": value[:40]}
        return value
    return value


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER, "Accept": "application/json"}) as client:
        for path in PATHS:
            response = client.get(path)
            ctype = response.headers.get("content-type", "")
            print("GET", path, response.status_code, ctype.split(";")[0], len(response.content))
            if "json" in ctype:
                try:
                    payload = response.json()
                except Exception as exc:  # noqa: BLE001
                    print("  json_error", type(exc).__name__)
                    continue
                print(json.dumps(brief(payload), ensure_ascii=False)[:2000])


if __name__ == "__main__":
    main()
