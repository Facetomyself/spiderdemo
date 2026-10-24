"""Extract readable API-like strings from the WlzShield bundle."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
text = (ROOT / "wlzshield.min.js").read_text(encoding="utf-8", errors="replace")
print("bytes", len(text), "lines", text.count("\n") + 1)

needles = (
    "CheckboxCaptcha",
    "ScratchCaptcha",
    "wsToken",
    "siteKey",
    "wangluozhe",
    "captcha",
    "/api/",
    "fingerprint",
    "WlzShield",
)
for needle in needles:
    print(needle, text.lower().count(needle.lower()) if needle != "WlzShield" else text.count(needle))

urls = sorted(set(re.findall(r"https?://[^\"'\s]{8,180}", text)))
print("urls", len(urls))
for url in urls[:80]:
    print(url)

paths = sorted(set(re.findall(r"/[A-Za-z0-9_./-]{6,80}", text)))
interesting = [p for p in paths if any(k in p.lower() for k in ("api", "captcha", "token", "verify", "check", "config"))]
print("interesting_paths", len(interesting))
for path in interesting[:120]:
    print(path)
