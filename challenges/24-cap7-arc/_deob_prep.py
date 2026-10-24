"""Split the obfuscated script enough to find the string decoder."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
markers = [
    "function _0x592d",
    "function _0x536a18",
    "getPositionOnArc",
    "drawArcPath",
    "verifyCaptchaAndGetData",
    "rotation_angle",
    "trajectory",
    "atob(",
    "fromCharCode",
]
for name in markers:
    idx = text.find(name)
    print("\n====", name, idx)
    if idx >= 0:
        print(text[max(0, idx - 120) : idx + 500])

print("\n==== function names")
names = re.findall(r"function (_0x[0-9a-f]{4,})\(", text)
print("count", len(names))
print(names[:30])
