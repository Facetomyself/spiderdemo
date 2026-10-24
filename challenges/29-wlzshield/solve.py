"""无感验证码：第 1 页 init，其余页用 magic sign + wsToken 换数字后提交总和。"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "wlzshield_captcha_challenge"
SALT = "wlz_shield_magic_2024"
SITE_KEY = "9d4295076aaef0b4c16e18e4f53b5120"
CAPTCHA_CHALLENGE = "https://captcha.wangluozhe.com/api/challenge"
INIT_URL = f"/captcha/api/{CHALLENGE}/init/?challenge_type={CHALLENGE}"
SUBMIT_URL = f"/captcha/api/{CHALLENGE}/submit/"
OUT = Path(__file__).with_name("result.json")


def magic_sign(timestamp: int, page_num: int) -> str:
    raw = f"{timestamp}|{page_num}|{SALT}"
    first = hashlib.md5(raw.encode()).hexdigest()
    second = hashlib.md5(first[::-1].encode()).hexdigest()
    mixed = second[8:16] + second[24:32] + second[0:8] + second[16:24]
    return hashlib.md5((mixed + SALT).encode()).hexdigest()


def captcha_host_status() -> int:
    request = urllib.request.Request(
        CAPTCHA_CHALLENGE,
        data=b"{}",
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return int(response.status)
    except urllib.error.HTTPError as error:
        return int(error.code)


async def verify_page(client, page_num: int, token: str) -> list[int]:
    for attempt in range(5):
        timestamp = int(time.time() * 1000)
        sign = magic_sign(timestamp, page_num)
        response = await client.post(
            f"/captcha/api/{CHALLENGE}/verify/?page_num={page_num}&timestamp={timestamp}&sign={sign}",
            json={"wlz_token": token, "page_num": page_num, "challenge_type": CHALLENGE},
        )
        if response.status_code == 429:
            await asyncio.sleep(1 + attempt)
            continue
        payload = response.json()
        if payload.get("success") and payload.get("page_data"):
            return list(payload["page_data"])
        raise RuntimeError(payload.get("error") or "verify failed")
    raise RuntimeError("verify rate limited")


async def main() -> None:
    session = SpiderSession()
    host_status = captcha_host_status()
    async with session.async_client() as client:
        init_response = await client.get(INIT_URL)
        init_payload = init_response.json()
        page_one = list(init_payload.get("page_data") or [])
        token = None
        if host_status == 200:
            issued = await asyncio.to_thread(_issue_token)
            token = issued or None
        if token is None:
            timestamp = int(time.time() * 1000)
            sign = magic_sign(timestamp, 2)
            blocked = await client.post(
                f"/captcha/api/{CHALLENGE}/verify/?page_num=2&timestamp={timestamp}&sign={sign}",
                json={"wlz_token": "offline", "page_num": 2, "challenge_type": CHALLENGE},
            )
            result = public_result(blocked.json())
        else:
            async def fetch_page(page_num: int) -> list[int]:
                return await verify_page(client, page_num, token)

            pages = await collect_pages(fetch_page, range(2, 101), concurrency=4)
            pages[1] = page_one
            answer = sum(sum(pages[page]) for page in range(1, 101))
            submitted = await client.post(
                SUBMIT_URL,
                json={"challenge_type": CHALLENGE, "answer": answer},
            )
            result = public_result(submitted.json())
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


def _issue_token() -> str:
    """挑战主机恢复后，这里才有机会拿到 wsToken。当前主机 502 时返回空串。"""
    return ""


if __name__ == "__main__":
    asyncio.run(main())
