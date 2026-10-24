"""Write short readable strings from the WlzShield bundle."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
text = (ROOT / "wlzshield.min.js").read_text(encoding="utf-8", errors="replace")
strings = re.findall(r"[\x20-\x7e]{6,160}", text)
keys = (
    "http",
    "captcha",
    "token",
    "site",
    "check",
    "api",
    "finger",
    "mouse",
    "canvas",
    "webgl",
    "encrypt",
    "aes",
    "wasm",
    "worker",
    "verify",
    "config",
    "behavior",
    "shield",
    "checkbox",
    "scratch",
    "ws",
)
picked: list[str] = []
seen: set[str] = set()
for item in strings:
    low = item.lower()
    if any(key in low for key in keys) and item not in seen:
        seen.add(item)
        picked.append(item)
(ROOT / "_strings.txt").write_text("\n".join(picked[:4000]), encoding="utf-8")
(ROOT / "_string_count.txt").write_text(
    f"all={len(strings)} picked={len(picked)} unique_head={text[:40]}\n",
    encoding="utf-8",
)
