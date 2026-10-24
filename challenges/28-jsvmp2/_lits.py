import re
from pathlib import Path

inner = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
# string literals
lits = []
i = 0
n = len(inner)
while i < n:
    if inner[i] in "\"'":
        q = inner[i]
        j = i + 1
        while j < n:
            if inner[j] == "\\":
                j += 2
                continue
            if inner[j] == q:
                break
            j += 1
        raw = inner[i + 1:j]
        if len(raw) >= 40:
            lits.append((i, q, len(raw), raw[:80]))
        i = j + 1
    else:
        i += 1
print("long_lits", len(lits))
for pos, q, length, preview in lits[:40]:
    print(pos, q, length, preview.replace("\n", "\\n"))
print("--- longest ---")
for pos, q, length, preview in sorted(lits, key=lambda item: -item[2])[:15]:
    print(pos, length, preview[:60].replace("\n", "\\n"))
