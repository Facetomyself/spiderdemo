"""List readable string literals from the stripped page VM."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).with_name("spiderking_challenge.js").read_text(encoding="utf-8")
plain = text.translate({
    0x200B: None,
    0x200C: None,
    0x200D: None,
    0x2060: None,
    0x2061: None,
    0x2062: None,
    0x2063: None,
    0x2064: None,
})
found = re.findall(r'"((?:\\.|[^"\\]){2,120})"', plain)
cleaned = []
for item in found:
    try:
        value = bytes(item, "utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        value = item
    if all(32 <= ord(ch) < 127 or ch in "\u4e00-\u9fff" for ch in value):
        cleaned.append(value)
unique = []
seen = set()
for item in cleaned:
    if item not in seen:
        seen.add(item)
        unique.append(item)
print("literals", len(unique))
for item in unique:
    if re.search(r"[A-Za-z]{3,}", item):
        print(item)
