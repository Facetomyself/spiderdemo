"""Summarize anti_automation.js without dumping large blobs."""

import re
from pathlib import Path

text = Path(__file__).parent.joinpath("assets", "anti_automation.js").read_text(
    encoding="utf-8", errors="replace"
)
lines: list[str] = []


def emit(msg: str) -> None:
    lines.append(msg)


emit(f"len {len(text)} lines {text.count(chr(10)) + 1}")
emit("HEAD " + text[:800].replace("\n", "\\n"))
emit("TAIL " + text[-500:].replace("\n", "\\n"))
for needle in (
    "Function",
    "WebSocket",
    "websocket",
    "Proxy",
    "navigator",
    "webdriver",
    "eval",
    "toString",
    "jsvmp",
    "challenge",
    "XMLHttpRequest",
    "fetch",
):
    emit(f"count {needle} {text.count(needle)}")
strings = re.findall(r"""['"]([^'"\\]{6,100})['"]""", text)
seen: list[str] = []
for item in strings:
    if item not in seen:
        seen.append(item)
emit(f"unique_strings {len(seen)}")
for item in seen[:200]:
    emit("STR " + item)
Path(__file__).with_name("_anti_scan.txt").write_text("\n".join(lines), encoding="utf-8")
