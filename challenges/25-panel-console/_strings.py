"""Extract readable strings from the panel scripts. No secrets printed."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent
FILES = [
    "static__js__check_devtools_jsvmp.js",
    "static__js__anti_automation.js",
]


def strings(data: str) -> list[str]:
    found = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_./:?=&%#-]{4,}", data)
    unique: list[str] = []
    seen: set[str] = set()
    for item in found:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def main() -> None:
    for name in FILES:
        text = (ROOT / name).read_text(encoding="utf-8", errors="replace")
        print("===", name, "len", len(text), "head", text[:180].replace("\n", " "))
        items = strings(text)
        interesting = [
            item
            for item in items
            if any(
                key in item.lower()
                for key in (
                    "console",
                    "devtool",
                    "debug",
                    "panel",
                    "answer",
                    "token",
                    "fetch",
                    "page",
                    "init",
                    "submit",
                    "hook",
                    "open",
                    "print",
                    "log",
                    "detector",
                    "outer",
                    "inner",
                    "toString",
                )
            )
            or any("\u4e00" <= ch <= "\u9fff" for ch in item)
        ]
        print("interesting", len(interesting), "of", len(items))
        for item in interesting[:250]:
            print(item)


if __name__ == "__main__":
    main()
