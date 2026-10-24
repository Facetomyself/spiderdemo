"""Slice the bundle tail and print the verify error text."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from modules.runtime import SpiderSession

ROOT = Path(__file__).resolve().parent
text = (ROOT / "wlzshield.min.js").read_text(encoding="utf-8", errors="replace")
(ROOT / "_tail.js").write_text(text[-12000:], encoding="utf-8")
print("tail_written", len(text))

CHALLENGE = "wlzshield_captcha_challenge"
SALT = "wlz_shield_magic_2024"
stamp = int(time.time() * 1000)
raw = f"{stamp}|2|{SALT}"
first = hashlib.md5(raw.encode()).hexdigest()
second = hashlib.md5(first[::-1].encode()).hexdigest()
mixed = second[8:16] + second[24:32] + second[0:8] + second[16:24]
sign = hashlib.md5((mixed + SALT).encode()).hexdigest()
session = SpiderSession()
with session.client() as client:
    verify = client.post(
        f"/captcha/api/{CHALLENGE}/verify/",
        params={"page_num": 2, "timestamp": stamp, "sign": sign},
        json={"wlz_token": "probe", "page_num": 2, "challenge_type": CHALLENGE},
    )
    body = verify.json()
    print("verify_success", body.get("success"))
    print("verify_error", body.get("error"))
    bad = client.post(
        f"/captcha/api/{CHALLENGE}/verify/",
        params={"page_num": 2, "timestamp": stamp, "sign": "0" * 32},
        json={"wlz_token": "probe", "page_num": 2, "challenge_type": CHALLENGE},
    )
    bad_body = bad.json()
    print("bad_sign", bad.status_code, bad_body.get("success"), bad_body.get("error"))
