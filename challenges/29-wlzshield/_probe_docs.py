"""Save the WlzShield docs page and list script/API hints."""

from __future__ import annotations

import re
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parent / "_docs.html"


def main() -> None:
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        response = client.get("https://captcha.wangluozhe.com/")
        OUT.write_text(response.text, encoding="utf-8")
        print("status", response.status_code, "len", len(response.text))
        srcs = re.findall(r"""(?:src|href)=["']([^"']+)["']""", response.text)
        for src in srcs:
            print("asset", src)


if __name__ == "__main__":
    main()
