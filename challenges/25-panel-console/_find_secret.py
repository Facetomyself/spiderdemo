"""Find the string-table entry that decodes to the console secret."""

from __future__ import annotations

import json
from pathlib import Path

js = Path(__file__).with_name("static__js__check_devtools_jsvmp.js").read_text(encoding="utf-8")
marker = ",[["
pos = js.find(marker, js.find("})(function(em,eB"))
# The table is the second call argument. Locate the first "[[" after the bytecode call.
start = js.find("[[", js.find("})(function(em,eB"))
depth = 0
end = None
for index, char in enumerate(js[start:], start):
    if char == "[":
        depth += 1
    elif char == "]":
        depth -= 1
        if depth == 0:
            end = index
            break
table = json.loads(js[start : end + 1])
print("entries", len(table))
target = "SecretKey: "
hits = []
for index, item in enumerate(table):
    if not isinstance(item, list) or not item or not all(isinstance(value, int) for value in item):
        continue
    if len(item) < 20:
        continue
    base = item[0]
    for key in range(base - 126, base - 31):
        chars = []
        ok = True
        for offset, value in enumerate(item):
            code = value - offset - key
            if code < 32 or code > 126:
                ok = False
                break
            chars.append(chr(code))
        if not ok:
            continue
        text = "".join(chars)
        if "Secret" in text or "key-" in text or "wlz" in text:
            hits.append((index, key, text))
print("hits", len(hits))
for index, key, text in hits:
    print(index, key, text)
