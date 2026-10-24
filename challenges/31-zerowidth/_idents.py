"""Print identifier-like literals that sit in the page VM string table."""

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
items = re.findall(r'"((?:\\.|[^"\\])*)"', plain)
idents = []
for item in items:
    if len(item) > 80:
        continue
    if re.fullmatch(r"[A-Za-z_$][\w$.:/?-]{1,60}", item) or any(
        token in item.lower() for token in ("seal", "page", "submit", "worker", "digest", "ticket", "proof", "gate", "pulse", "spider", "auth", "zero", "baidu")
    ):
        idents.append(item)
print("count", len(idents))
for item in idents:
    print(item)
