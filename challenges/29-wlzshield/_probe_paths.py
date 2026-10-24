"""Probe likely page endpoints. Print status and public keys only."""

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


def brief(response) -> str:
    text = response.text.replace("\n", " ")[:120]
    return f"{response.status_code} {text}"


def main() -> None:
    stamp = int(time.time() * 1000)
    sign = magic_sign(stamp, 2)
    session = SpiderSession()
    paths = [
        ("GET", f"/captcha/api/{CHALLENGE}/page/?page_num=2", None),
        ("GET", f"/captcha/api/{CHALLENGE}/page/2/?challenge_type={CHALLENGE}", None),
        ("GET", f"/captcha/api/{CHALLENGE}/data/?page_num=2&challenge_type={CHALLENGE}", None),
        ("POST", f"/captcha/api/{CHALLENGE}/page/", {"page_num": 2, "challenge_type": CHALLENGE}),
        ("GET", f"/api/challenge?siteKey=9d4295076aaef0b4c16e18e4f53b5120", None),
        ("POST", "/api/challenge", {"siteKey": "9d4295076aaef0b4c16e18e4f53b5120"}),
        ("GET", f"/captcha/api/challenge?siteKey=9d4295076aaef0b4c16e18e4f53b5120", None),
    ]
    with session.client() as client:
        for method, path, body in paths:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json=body)
            print(method, path, brief(response))
        response = client.get(
            f"/captcha/api/{CHALLENGE}/verify/",
            params={"page_num": 2, "timestamp": stamp, "sign": sign},
        )
        print("GET verify", brief(response))


if __name__ == "__main__":
    main()
