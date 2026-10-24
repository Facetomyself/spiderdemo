import re
from pathlib import Path

text = Path(__file__).with_name("wlzshield.min.js").read_text(encoding="utf-8", errors="replace")
for name in ("mo", "ht", "HI", "Wn", "mV"):
    hits = []
    for match in re.finditer(r"(?:function\s+%s\b|%s\s*=\s*function)" % (name, name), text):
        hits.append(match.start())
        if len(hits) >= 8:
            break
    print(name, hits[:8], "count_cap", len(hits))

# decode a few unicode-escaped identifier blobs near 'function mo'
idx = text.find("function mo(")
print("function mo(", idx)
if idx < 0:
    idx = text.find("mo=function")
    print("mo=function", idx)
if idx >= 0:
    print(text[idx:idx + 400])
