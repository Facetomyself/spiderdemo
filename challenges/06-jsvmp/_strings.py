import re
from pathlib import Path

text = Path(r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp\assets\anti_automation.js").read_text(encoding="utf-8", errors="replace")
found = sorted(set(re.findall(r"[A-Za-z0-9_./:-]{8,}", text)))
for item in found:
    if any(word in item.lower() for word in ("header", "proto", "token", "sign", "auth", "cookie", "page", "api", "fetch", "xhr")):
        print(item)
print("count", len(found))
