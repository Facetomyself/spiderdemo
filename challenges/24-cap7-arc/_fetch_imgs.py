"""List image URLs in the public writeup."""

import re
import urllib.request
from pathlib import Path

url = "https://www.cnblogs.com/ikdl/p/22183586"
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    html = response.read().decode("utf-8", "replace")
srcs = re.findall(r'<img[^>]+src="([^"]+)"', html, flags=re.I)
out = Path(__file__).with_name("_note_imgs.txt")
out.write_text("\n".join(srcs), encoding="utf-8")
print("imgs", len(srcs))
for src in srcs:
    print(src[:180])
