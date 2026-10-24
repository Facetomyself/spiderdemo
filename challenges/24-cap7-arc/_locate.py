"""Locate decoder and string-array bounds in the obfuscated script."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
print("len", len(text))
for name in ("function _0x592d", "function _0x536a18", "atob", "fromCharCode", "arcPath", "getPositionOnArc", "rotation"):
    print(name, text.find(name))

funcs = [(m.start(), m.group(1)) for m in re.finditer(r"function (_0x[0-9a-f]+)\(", text)]
print("func_count", len(funcs))
print("first_funcs", funcs[:25])
print("last_funcs", funcs[-8:])
