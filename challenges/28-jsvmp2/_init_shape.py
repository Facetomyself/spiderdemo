"""Print the init response shape. Values that look like secrets are lengths only."""

from __future__ import annotations

import json
import re

from modules.runtime import SpiderSession

URL = "/authentication/api/jsvmp2_challenge/init/?challenge_type=jsvmp2_challenge"
REFERER = "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"
SECRET = re.compile(r"(token|cookie|session|password|sign|key|auth)", re.I)


def shape(value, key=""):
    if isinstance(value, dict):
        return {k: shape(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [shape(item, key) for item in value[:3]] + (["...%d" % len(value)] if len(value) > 3 else [])
    if isinstance(value, str):
        if SECRET.search(key) or len(value) > 80:
            return "str:%d" % len(value)
        return value
    return value


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": REFERER, "Accept": "application/json"}) as client:
        response = client.get(URL)
        print("status", response.status_code)
        print("ctype", response.headers.get("content-type", ""))
        try:
            payload = response.json()
        except json.JSONDecodeError:
            print("not-json", len(response.content))
            return
        print(json.dumps(shape(payload), ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()
