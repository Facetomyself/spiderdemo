"""Describe captcha id shape without printing the id."""

import base64
import json
import re

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"


def describe(value: str) -> str:
    parts = value.split(".")
    kinds = []
    for part in parts:
        pad = "=" * ((4 - len(part) % 4) % 4)
        try:
            raw = base64.urlsafe_b64decode(part + pad)
        except Exception:
            kinds.append(f"raw{len(part)}")
            continue
        text = raw.decode("utf-8", "replace")
        if text.startswith("{") and text.endswith("}"):
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                kinds.append(f"b64text{len(text)}")
            else:
                kinds.append("json:" + ",".join(obj.keys()))
        else:
            kinds.append(f"b64:{len(raw)}:{'hex' if re.fullmatch(r'[0-9a-f]+', text) else 'bin'}")
    return f"len={len(value)} parts={len(parts)} " + "|".join(kinds)


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER, "Accept": "application/json"}) as client:
        cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        print(describe(str(cap["captcha_id"])))
        print("arc", len(cap["arc_path"]["points"]), "ytype", type(cap["slider_y"]).__name__)


if __name__ == "__main__":
    main()
