"""Compare page endpoint bodies. Print only status and public error text."""

from __future__ import annotations

import hashlib
import time

from modules.runtime import SpiderSession

CHALLENGE = "wlzshield_captcha_challenge"
SALT = "wlz_shield_magic_2024"


def magic_sign(timestamp: int, page_num: int) -> str:
    raw = f"{timestamp}|{page_num}|{SALT}"
    first = hashlib.md5(raw.encode()).hexdigest()
    second = hashlib.md5(first[::-1].encode()).hexdigest()
    mixed = second[8:16] + second[24:32] + second[0:8] + second[16:24]
    return hashlib.md5((mixed + SALT).encode()).hexdigest()


def show(label: str, response) -> None:
    try:
        body = response.json()
    except Exception:
        print(label, response.status_code, "nonjson", len(response.content))
        return
    if isinstance(body, dict):
        kept = {key: body.get(key) for key in ("success", "error", "message", "need_verify", "page_num") if key in body}
        if "page_data" in body:
            kept["page_len"] = len(body["page_data"]) if isinstance(body["page_data"], list) else type(body["page_data"]).__name__
        print(label, response.status_code, kept, "keys", sorted(body))
    else:
        print(label, response.status_code, type(body).__name__)


def main() -> None:
    session = SpiderSession()
    stamp = int(time.time() * 1000)
    sign = magic_sign(stamp, 2)
    with session.client() as client:
        cases = [
            ("plain", {"page_num": 2, "challenge_type": CHALLENGE}, None),
            ("signed-query", {"page_num": 2, "challenge_type": CHALLENGE}, {"page_num": 2, "timestamp": stamp, "sign": sign}),
            ("token-body", {"wlz_token": "probe", "page_num": 2, "challenge_type": CHALLENGE}, {"page_num": 2, "timestamp": stamp, "sign": sign}),
            ("empty", {}, None),
            ("page-only", {"page": 2}, None),
        ]
        for label, payload, params in cases:
            response = client.post(f"/captcha/api/{CHALLENGE}/page/", params=params, json=payload)
            show(label, response)


if __name__ == "__main__":
    main()
