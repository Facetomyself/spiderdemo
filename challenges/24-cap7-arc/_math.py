"""List Math calls and readable identifiers in cap7 script."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
maths = re.findall(r"Math\['([A-Za-z]+)'\]|Math\.([A-Za-z]+)", text)
names = [a or b for a, b in maths]
print("math", Counter(names))
idents = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]{3,})\b", text)
skip = {"function", "return", "const", "let", "var", "undefined", "continue", "break", "case", "switch", "while", "else", "true", "false", "null", "typeof", "instanceof", "new", "this", "try", "catch", "throw", "async", "await"}
counts = Counter(name for name in idents if not name.startswith("_0x") and name not in skip)
print("top idents")
for name, count in counts.most_common(80):
    print(f"{count:4} {name}")
