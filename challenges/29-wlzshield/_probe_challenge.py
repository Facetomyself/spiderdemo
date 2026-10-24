"""Check whether the captcha challenge route is up."""

from __future__ import annotations

import httpx

URLS = [
    "https://captcha.wangluozhe.com/api/challenge",
    "https://captcha.wangluozhe.com/api/captcha/challenge",
    "https://captcha.wangluozhe.com/static/js/wlzshield.min.js",
]


def main() -> None:
    body = {"siteKey": "9d4295076aaef0b4c16e18e4f53b5120"}
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for url in URLS:
            for method in ("GET", "POST"):
                response = client.request(method, url, json=body if method == "POST" else None)
                print(method, response.status_code, len(response.content), url, response.text[:80].replace("\n", " "))


if __name__ == "__main__":
    main()
