"""Extract readable strings from the obfuscated cap7 script."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).with_name("static__js__captcha__cap7_challenge.js")
OUT = Path(__file__).with_name("strings.txt")


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    strings = re.findall(r"""['"]([^'"\\]{4,})['"]""", text)
    uniq: list[str] = []
    seen: set[str] = set()
    for item in strings:
        if item in seen:
            continue
        seen.add(item)
        if re.search(r"[\u4e00-\u9fff]|/|api|angle|rotat|captcha|page|submit|init|arc|track|bezier|sin|cos", item, re.I):
            uniq.append(item)
    OUT.write_text("\n".join(uniq), encoding="utf-8")
    print("candidates", len(uniq), "file", OUT.name)
    for item in uniq:
        print(item[:240])


if __name__ == "__main__":
    main()
