"""Download the public writeup and keep only trajectory-related lines."""

import re
import urllib.request
from pathlib import Path

url = "https://www.cnblogs.com/ikdl/p/22183586"
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    html = response.read().decode("utf-8", "replace")
codes = re.findall(r"<pre[\s\S]*?</pre>|<code[\s\S]*?</code>", html, flags=re.I)
code_path = Path(__file__).resolve().parent / "_note_code.txt"
code_path.write_text("\n\n----- CODE -----\n\n".join(codes), encoding="utf-8")
print("codes", len(codes), "code_chars", code_path.stat().st_size)
text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
text = re.sub(r"<[^>]+>", "\n", text)
text = re.sub(r"\n+", "\n", text)
lines = [line.strip() for line in text.splitlines() if line.strip()]
keep = [line for line in lines if any(word in line for word in ("轨迹", "distance", "旋转", "base64", "偏离", "角度", "arc", "编码", "点"))]
out = Path(__file__).resolve().parent / "_note_text.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("lines", len(lines), "chars", out.stat().st_size)
