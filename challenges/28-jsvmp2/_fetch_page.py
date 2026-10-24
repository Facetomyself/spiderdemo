"""Download the jsvmp2 challenge page and list script/link URLs."""

from __future__ import annotations

import re
from pathlib import Path

from modules.runtime import SpiderSession

PAGE = "/authentication/jsvmp2_challenge?challenge_type=jsvmp2_challenge"
OUT = Path(__file__).with_name("page.html")


def main() -> None:
    session = SpiderSession()
    with session.client(
        {"Referer": "https://www.spiderdemo.cn/authentication/jsvmp2_challenge?challenge_type=jsvmp2_challenge"}
    ) as client:
        response = client.get(PAGE)
        OUT.write_bytes(response.content)
        text = response.text
        urls = re.findall(r"""(?:src|href)=["']([^"']+)["']""", text)
        print("status", response.status_code)
        print("bytes", len(response.content))
        print("final", response.url.path if hasattr(response.url, "path") else "")
        print("title", re.search(r"<title>(.*?)</title>", text, re.I | re.S).group(1).strip() if re.search(r"<title>", text, re.I) else "")
        for url in urls:
            print("url", url)


if __name__ == "__main__":
    main()
