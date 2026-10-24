"""List public captcha-host response shapes. No credentials."""

from __future__ import annotations

import httpx

URLS = [
    "https://captcha.wangluozhe.com/",
    "https://captcha.wangluozhe.com/api/v1/config?siteKey=9d4295076aaef0b4c16e18e4f53b5120",
    "https://captcha.wangluozhe.com/api/config?siteKey=9d4295076aaef0b4c16e18e4f53b5120",
]


def main() -> None:
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for url in URLS:
            try:
                response = client.get(url)
            except Exception as exc:
                print("fail", url, type(exc).__name__)
                continue
            text = response.text[:180].replace("\n", " ")
            print(response.status_code, response.headers.get("content-type"), len(response.content), url)
            print(text)


if __name__ == "__main__":
    main()
