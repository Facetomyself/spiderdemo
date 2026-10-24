"""Download WlzShield guide pages for the local protocol notes."""

from __future__ import annotations

from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent / "_docs"
PAGES = [
    "/guide/getting-started.html",
    "/guide/checkbox-captcha.html",
    "/guide/scratch-captcha.html",
    "/guide/changelog.html",
    "/guide/community.html",
]


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for page in PAGES:
            response = client.get("https://captcha.wangluozhe.com" + page)
            name = page.strip("/").replace("/", "_") + ".html"
            (ROOT / name).write_text(response.text, encoding="utf-8")
            print(response.status_code, len(response.text), name)


if __name__ == "__main__":
    main()
