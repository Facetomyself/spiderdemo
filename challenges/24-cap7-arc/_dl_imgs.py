"""Download public writeup figures."""

import urllib.request
from pathlib import Path

urls = Path(__file__).with_name("_note_imgs.txt").read_text(encoding="utf-8").splitlines()
out = Path(__file__).with_name("_note_img")
out.mkdir(exist_ok=True)
for url in urls:
    if "ax1x.com" not in url and "cnblogs.com/blog" not in url:
        continue
    name = url.rstrip("/").split("/")[-1].split("?")[0]
    dest = out / name
    if dest.exists() and dest.stat().st_size > 1000:
        print("have", name, dest.stat().st_size)
        continue
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.cnblogs.com/"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
    except Exception as exc:
        print("fail", name, type(exc).__name__)
        continue
    dest.write_bytes(data)
    print("saved", name, len(data))
