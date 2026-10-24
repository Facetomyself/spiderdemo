"""Extract the JSVMP string table and brute-force printable decodings."""

from __future__ import annotations

import json
from pathlib import Path

js = Path(__file__).with_name("static__js__check_devtools_jsvmp.js").read_text(encoding="utf-8")


def matching(text: str, open_at: int) -> int:
    depth = 0
    in_str = None
    escape = False
    for index in range(open_at, len(text)):
        char = text[index]
        if in_str:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_str:
                in_str = None
            continue
        if char in ("'", '"', "`"):
            in_str = char
            continue
        if char in "[{(":
            depth += 1
        elif char in "]})":
            depth -= 1
            if depth == 0:
                return index
    raise RuntimeError(f"unbalanced at {open_at}")


# The IIFE parameter list ends at the first "){" after "function em".
header_end = js.find("){")
print("header_end", header_end)
# Body starts after that. Find the call by scanning from the end: last "])" is not enough.
# The function body is one function expression. Find its closing brace by brace match
# starting at the "{" of "){".
body_open = header_end + 1
body_close = matching(js, body_open)
print("body", body_open, body_close, "call_head", js[body_close : body_close + 40])

call_open = js.find("(", body_close)
call_close = matching(js, call_open)
print("call", call_open, call_close, "after", repr(js[call_close + 1 : call_close + 80]))

# Split top-level arguments.
args_src = js[call_open + 1 : call_close]
args: list[str] = []
depth = 0
in_str = None
escape = False
start = 0
for index, char in enumerate(args_src):
    if in_str:
        if escape:
            escape = False
        elif char == "\\":
            escape = True
        elif char == in_str:
            in_str = None
        continue
    if char in ("'", '"', "`"):
        in_str = char
        continue
    if char in "[{(":
        depth += 1
    elif char in "]})":
        depth -= 1
    elif char == "," and depth == 0:
        args.append(args_src[start:index])
        start = index + 1
args.append(args_src[start:])
print("argc", len(args))
for index, arg in enumerate(args):
    snippet = arg.strip().replace("\n", " ")
    print(f"arg{index} len={len(snippet)} head={snippet[:80]!r}")

# Second argument is the string table.
table = json.loads(args[1].strip())
print("table", len(table), "types", {type(item).__name__ for item in table})


def decode(values: list[int], key: int) -> str | None:
    chars = []
    for index, value in enumerate(values):
        code = value - index - key
        if code < 9 or code > 0xFFFF:
            return None
        chars.append(chr(code))
    return "".join(chars)


decoded = []
for index, item in enumerate(table):
    if not isinstance(item, list) or not item or not all(isinstance(value, int) for value in item):
        decoded.append({"i": index, "raw": item if not isinstance(item, list) else f"list{len(item)}"})
        continue
    found = None
    base = item[0]
    for key in range(base - 0xFF, base - 8):
        text = decode(item, key)
        if text is None:
            continue
        if all(32 <= ord(ch) < 127 or "\u4e00" <= ch <= "\u9fff" for ch in text):
            found = {"i": index, "key": key, "text": text}
            break
    if found is None:
        # keep the most printable candidate
        best = None
        best_score = -1
        for key in range(base - 0xFF, base - 8):
            text = decode(item, key)
            if text is None:
                continue
            score = sum(32 <= ord(ch) < 127 or "\u4e00" <= ch <= "\u9fff" for ch in text)
            if score > best_score:
                best_score = score
                best = {"i": index, "key": key, "text": text, "score": score, "n": len(text)}
        decoded.append(best or {"i": index, "fail": item[:4], "n": len(item)})
    else:
        decoded.append(found)

out = Path(__file__).with_name("vm-strings.json")
out.write_text(json.dumps(decoded, ensure_ascii=False, indent=2), encoding="utf-8")
ok = [item for item in decoded if item and "text" in item and "score" not in item]
print("clean", len(ok), "of", len(table))
for item in ok:
    print(f"{item['i']:4} {item['text']}")
