"""Scan anti_automation.js for protocol strings. No secrets printed."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).with_name("static__js__anti_automation.js").read_text(
    encoding="utf-8", errors="replace"
)
print("len", len(text))
for key in (
    "validatePageNavigation",
    "debugger",
    "fsymmetry",
    "X-Auth",
    "XMLHttpRequest",
    "fetch",
    "axios",
):
    print(key, text.lower().count(key.lower()))

strs = re.findall(r"[\x20-\x7e]{6,}", text)
print("ascii_strs", len(strs))
needles = (
    "page",
    "sign",
    "auth",
    "debug",
    "valid",
    "header",
    "token",
    "rsa",
    "dsa",
    "fetch",
    "xhr",
    "init",
    "submit",
    "function",
)
interesting = [s for s in strs if any(k in s.lower() for k in needles)]
print("interesting", len(interesting))
for item in interesting[:120]:
    print(item[:240])
