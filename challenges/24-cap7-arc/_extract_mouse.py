"""Extract the outermost function whose body contains the trajectory call."""

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
at = text.find("recordTrajectoryPoint(")


def matching_brace(source: str, open_at: int) -> int:
    i = open_at
    depth = 0
    quote = ""
    escape = False
    while i < len(source):
        ch = source[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'`":
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise RuntimeError("unclosed")


cursor = 0
chosen = None
while True:
    start = text.find("function ", cursor)
    if start < 0 or start > at:
        break
    paren = text.find("(", start)
    if paren < 0:
        break
    # skip parameter list
    depth = 0
    i = paren
    quote = ""
    escape = False
    while i < len(text):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    brace = text.find("{", i)
    if brace < 0 or brace > at:
        cursor = start + 9
        continue
    end = matching_brace(text, brace)
    if start <= at < end:
        chosen = (start, end, end - start)
    cursor = start + 9

print("chosen", chosen)
if chosen:
    start, end, _ = chosen
    out = Path(__file__).with_name("_fns").joinpath("mouseHandler.js")
    out.write_text(text[start:end], encoding="utf-8")
    print(text[start:start + 180])
