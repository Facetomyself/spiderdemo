"""Fetch the panel challenge document and list its scripts. No cookies printed."""

from __future__ import annotations

import re
from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).with_name("page.html")
PAGE = "/authentication/panel_challenge?challenge_type=panel_challenge"


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get(PAGE)
        text = response.text
        OUT.write_text(text, encoding="utf-8")
        print("status", response.status_code, "len", len(text))
        print("ctype", response.headers.get("content-type"))
        print("final_path", response.url.path)
    srcs = re.findall(r"""<script[^>]+src=["']([^"']+)["']""", text, re.I)
    print("script_srcs", len(srcs))
    for src in srcs:
        print(src)
    links = re.findall(r"""<(?:link|img)[^>]+(?:href|src)=["']([^"']+)["']""", text, re.I)
    print("asset_count", len(links))
    for src in links:
        print(src)
    inlines = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.I | re.S)
    print("inline_count", len(inlines))
    for index, block in enumerate(inlines):
        snippet = block.strip()
        print("--- inline", index, "len", len(snippet))
        print(snippet[:4000])


if __name__ == "__main__":
    main()
