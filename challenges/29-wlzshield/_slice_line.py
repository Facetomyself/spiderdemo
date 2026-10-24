"""Show the constructor region named in the bind stack."""

from __future__ import annotations

from pathlib import Path

text = Path(__file__).with_name("wlzshield.min.js").read_text(encoding="utf-8")
lines = text.splitlines()
print("lines", len(lines), "lens", [len(line) for line in lines[:8]], "...", [len(line) for line in lines[-3:]])
line = lines[1]
print(line[2700:3400])
print("---")
print(line[8000:8600])
