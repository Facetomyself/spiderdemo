"""Pull quoted literals out of anti_automation.js."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).with_name("static__js__anti_automation.js").read_text(encoding="utf-8")
literals = re.findall(r"""(['"])(?:\\.|(?!\1).){3,200}\1""", text)
print("quoted", len(literals))
seen = []
for item in literals:
    value = item[1:-1]
    if value not in seen:
        seen.append(value)
print("unique", len(seen))
for item in seen:
    if any(token in item.lower() for token in ("key", "console", "page", "panel", "dev", "answer", "http", "api", "sign")) or any("\u4e00" <= ch <= "\u9fff" for ch in item):
        print(item[:240])
