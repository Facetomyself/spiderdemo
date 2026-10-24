"""Scan jsvmp2.js shape without printing secrets."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).parent.joinpath("assets", "jsvmp2.js").read_text(encoding="utf-8", errors="replace")
print("len", len(text), "lines", text.count("\n") + 1)
print("head", text[:500].replace("\n", "\\n"))
print("--- tail ---")
print(text[-400:].replace("\n", "\\n"))

needles = [
    "WebSocket",
    "websocket",
    "wss:",
    "ws:",
    "submit",
    "XMLHttpRequest",
    "fetch(",
    "opcode",
    "Function(",
    "eval(",
    "atob",
    "fromCharCode",
    "challenge_type",
    "jsvmp2",
    "document",
    "window",
    "prototype",
]
for needle in needles:
    print(f"count {needle!r}", text.count(needle))

# printable string literals longer than 8
strings = re.findall(r"""['"]([^'"\\]{8,120})['"]""", text)
print("string_lits", len(strings))
uniq = []
seen = set()
for item in strings:
    if item not in seen:
        seen.add(item)
        uniq.append(item)
print("unique", len(uniq))
for item in uniq[:80]:
    print("STR", item)
