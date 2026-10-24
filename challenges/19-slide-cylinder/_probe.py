"""Fetch slide-cylinder page and list scripts. No cookies printed."""

from __future__ import annotations

import re
from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("page.html")


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get(
            "/captcha/slide_cylinder_challenge?challenge_type=slide_cylinder_challenge"
        )
        text = response.text
        OUT.write_text(text, encoding="utf-8")
        print("status", response.status_code, "len", len(text))
        print("ctype", response.headers.get("content-type"))
    srcs = re.findall(r"""<script[^>]+src=["']([^"']+)["']""", text, re.I)
    print("script_srcs", len(srcs))
    for src in srcs:
        print(src)
    links = re.findall(r"""<link[^>]+href=["']([^"']+)["']""", text, re.I)
    print("links", len(links))
    for href in links:
        print(href)
    inlines = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.I | re.S)
    print("inline_count", len(inlines))
    for index, block in enumerate(inlines):
        print("--- inline", index, "len", len(block))
        print(block[:8000])


if __name__ == "__main__":
    main()
