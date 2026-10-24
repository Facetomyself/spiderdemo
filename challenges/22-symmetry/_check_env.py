"""Check local crypto libraries and whether anti_automation defines navigation hooks."""

from __future__ import annotations

import importlib
from pathlib import Path

for name in ("Crypto", "Crypto.Cipher.AES", "Crypto.Cipher.DES", "cryptography"):
    try:
        importlib.import_module(name)
        print("ok", name)
    except Exception as exc:
        print("no", name, type(exc).__name__)

text = Path(__file__).with_name("anti_automation.js").read_text(encoding="utf-8")
print("anti_len", len(text))
for needle in (
    "validatePageNavigation",
    "XMLHttpRequest",
    "fetch",
    "symmetry",
    "X-Token",
    "setRequestHeader",
):
    print(needle, text.find(needle))
