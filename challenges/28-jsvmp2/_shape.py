"""Locate the outer Function wrapper and decoder anchors."""

from pathlib import Path

text = Path(__file__).parent.joinpath("assets", "jsvmp2.js").read_text(encoding="utf-8")
# drop the two comment/version lines
body = text.split("\n", 2)[-1]
print("body_len", len(body))
print("starts", body[:80])
print("ends", body[-200:])

idx = 0
while True:
    pos = body.find("Function(", idx)
    if pos < 0:
        break
    print("Function at", pos, "ctx", body[max(0, pos - 40): pos + 80].replace("\n", " "))
    idx = pos + 9

for needle in ("return ", "switch", "while(", "bytecode", "opcode", "WebSocket", "new ", "apply(", "call("):
    print(needle, body.count(needle))
