"""Probe init and a signed verify without printing secrets."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from modules.runtime import SpiderSession

CHALLENGE = "wlzshield_captcha_challenge"
SALT = "wlz_shield_magic_2024"


def magic_sign(timestamp: int, page_num: int) -> str:
    raw = f"{timestamp}|{page_num}|{SALT}"
    first = hashlib.md5(raw.encode()).hexdigest()
    second = hashlib.md5(first[::-1].encode()).hexdigest()
    mixed = second[8:16] + second[24:32] + second[0:8] + second[16:24]
    return hashlib.md5((mixed + SALT).encode()).hexdigest()


def shape(value: Any, depth: int = 0) -> Any:
    if isinstance(value, dict):
        if depth >= 2:
            return sorted(value)
        return {key: shape(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        if not value:
            return ["empty"]
        return [shape(value[0], depth + 1), "len", len(value)]
    if isinstance(value, str):
        return f"str:{len(value)}"
    return type(value).__name__


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        init = client.get(
            f"/captcha/api/{CHALLENGE}/init/",
            params={"challenge_type": CHALLENGE},
        )
        payload = init.json()
        print("init", init.status_code, json.dumps(shape(payload), ensure_ascii=False))
        keys = sorted(payload) if isinstance(payload, dict) else []
        print("init_keys", keys)
        page = payload.get("page_data") if isinstance(payload, dict) else None
        if isinstance(page, list):
            print("page1_len", len(page), "sum", sum(page) if all(isinstance(n, int) for n in page) else "na")
        stamp = int(time.time() * 1000)
        sign = magic_sign(stamp, 2)
        verify = client.post(
            f"/captcha/api/{CHALLENGE}/verify/",
            params={"page_num": 2, "timestamp": stamp, "sign": sign},
            json={"wlz_token": "probe", "page_num": 2, "challenge_type": CHALLENGE},
        )
        body = verify.json()
        print("verify", verify.status_code, json.dumps(shape(body), ensure_ascii=False))
        print("verify_keys", sorted(body) if isinstance(body, dict) else type(body).__name__)


if __name__ == "__main__":
    main()
