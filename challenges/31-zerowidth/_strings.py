"""Pull readable protocol strings out of the page VM source."""

from __future__ import annotations

import re
from pathlib import Path

text = Path(__file__).with_name("spiderking_challenge.js").read_text(encoding="utf-8")
plain = text.translate({0x200B: None, 0x200C: None, 0x200D: None, 0x2060: None, 0xFEFF: None})
needles = (
    "TextEncoder",
    "digest",
    "mainSeal",
    "workerSeal",
    "pulseSeal",
    "attest",
    "spiderdemo",
    "submit",
    "SharedWorker",
    "changePage",
    "encode",
    "subtle",
    "crypto",
    "baidu",
    "ticket",
    "salts",
    "proof",
    "gate",
)
for needle in needles:
    print(needle, plain.count(needle))

found = sorted(set(re.findall(r"[A-Za-z0-9_./:?=&-]{8,80}", plain)))
interesting = [
    item
    for item in found
    if any(
        token in item.lower()
        for token in (
            "seal",
            "attest",
            "page",
            "submit",
            "spider",
            "worker",
            "digest",
            "ticket",
            "salt",
            "proof",
            "gate",
            "pulse",
            "api",
            "auth",
            "zero",
            "width",
            "baidu",
            "shared",
            "crypto",
            "encode",
        )
    )
]
print("interesting", len(interesting))
for item in interesting[:200]:
    print(item)
