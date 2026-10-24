import hashlib
import re
from pathlib import Path

from modules.runtime import SpiderSession

root = Path(r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp")
session = SpiderSession()
with session.client() as client:
    page = client.get("/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge")
    html = page.text
    (root / "page.html").write_text(html, encoding="utf-8")
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
    hrefs = re.findall(r'<link[^>]+href="([^"]+)"', html)
    print("scripts", srcs)
    print("links", hrefs)
    for src in srcs:
        if not src.startswith("/static/"):
            continue
        body = client.get(src).content
        name = src.rsplit("/", 1)[-1]
        target = root / "assets" / name
        old = target.read_bytes() if target.exists() else b""
        digest = hashlib.sha256(body).hexdigest()[:12]
        print(name, len(body), digest, "changed" if body != old else "same")
        if body != old:
            target.write_bytes(body)
