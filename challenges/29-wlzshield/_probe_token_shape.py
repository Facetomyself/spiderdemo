"""Record only status and public error text for verify/page variants."""

import hashlib
import json
import time
import urllib.request

from modules.runtime import SpiderSession

SALT = "wlz_shield_magic_2024"
ORIGIN = "https://www.spiderdemo.cn"


def magic_sign(timestamp: int, page_num: int) -> str:
    raw = f"{timestamp}|{page_num}|{SALT}"
    first = hashlib.md5(raw.encode()).hexdigest()
    second = hashlib.md5(first[::-1].encode()).hexdigest()
    mixed = second[8:16] + second[24:32] + second[0:8] + second[16:24]
    return hashlib.md5((mixed + SALT).encode()).hexdigest()


def host_status(url: str, method: str = "GET", body: bytes | None = None) -> str:
    request = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        request.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(180)
            return f"{response.status} len {len(raw)}"
    except urllib.error.HTTPError as error:
        raw = error.read(180)
        text = raw.decode("utf-8", "replace").lower()
        kind = "gateway" if "bad gateway" in text or "502" in text else "http"
        return f"{error.code} {kind} len {len(raw)}"


def main() -> None:
    print("challenge", host_status("https://captcha.wangluozhe.com/api/challenge", "POST", b"{}"))
    print("verify-host", host_status("https://captcha.wangluozhe.com/api/verify", "POST", b"{}"))
    session = SpiderSession()
    timestamp = int(time.time() * 1000)
    sign = magic_sign(timestamp, 2)
    path = f"/captcha/api/wlzshield_captcha_challenge/verify/?page_num=2&timestamp={timestamp}&sign={sign}"
    samples = {
        "omit": {"page_num": 2, "challenge_type": "wlzshield_captcha_challenge"},
        "empty": {"wlz_token": "", "page_num": 2, "challenge_type": "wlzshield_captcha_challenge"},
        "short": {"wlz_token": "x", "page_num": 2, "challenge_type": "wlzshield_captcha_challenge"},
        "dot3": {"wlz_token": "aaa.bbb.ccc", "page_num": 2, "challenge_type": "wlzshield_captcha_challenge"},
    }
    with session.client() as client:
        init = client.get("/captcha/api/wlzshield_captcha_challenge/init/?challenge_type=wlzshield_captcha_challenge")
        payload = init.json()
        print("init", init.status_code, "keys", ",".join(sorted(payload)))
        for name, body in samples.items():
            response = client.post(path, json=body)
            data = response.json()
            print(name, response.status_code, "success", data.get("success"), "error", data.get("error"), "keys", ",".join(sorted(data)))
        page = client.post(
            "/captcha/api/wlzshield_captcha_challenge/page/",
            json={"challenge_type": "wlzshield_captcha_challenge", "page_num": 2},
        )
        page_data = page.json()
        print("page", page.status_code, "success", page_data.get("success"), "error", page_data.get("error"), "need", page_data.get("need_verify"))


if __name__ == "__main__":
    main()
