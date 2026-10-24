"""Locate the JSVMP string decoder and the call-site argument arrays."""

from __future__ import annotations

from pathlib import Path

js = Path(__file__).with_name("static__js__check_devtools_jsvmp.js").read_text(encoding="utf-8")
print("len", len(js))
print("HEAD")
print(js[:1500])
print("---TAIL---")
print(js[-1500:])
pos = js.find("66666")
print("---66666", pos)
print(js[max(0, pos - 250) : pos + 700])
print("---counts---")
for token in ("function em", "console", "debugger", "devtools", "RegExp", "toString", "outerWidth", "innerWidth"):
    print(token, js.find(token), js.count(token))
