"""Fetch cap7 page and list scripts. No cookies printed."""

from __future__ import annotations

import re
from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("page.html")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get("/captcha/cap7_challenge?challenge_type=cap7_challenge")
        text = response.text
        OUT.write_text(text, encoding="utf-8")
        print("status", response.status_code, "len", len(text))
        print("ctype", response.headers.get("content-type"))
        print("final_path", response.url.path)
    srcs = re.findall(r"""<(?:script|link)[^>]+(?:src|href)=["']([^"']+)["']""", text, re.I)
    print("asset_count", len(srcs))
    for src in srcs:
        print(src)
    inlines = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.I | re.S)
    print("inline_count", len(inlines))
    for index, block in enumerate(inlines):
        print("--- inline", index, "len", len(block))
        print(block[:8000])


if __name__ == "__main__":
    main()
