from pathlib import Path

text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
# reuse the same splitter quickly by importing logic
depth = 0
start = 0
parts = []
i = 0
n = len(text)
in_str = None
esc = False
while i < n:
    ch = text[i]
    if in_str:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == in_str:
            in_str = None
        i += 1
        continue
    if ch in "\"'":
        in_str = ch
    elif ch in "([{":
        depth += 1
    elif ch in ")]}":
        depth -= 1
    elif ch == ";" and depth == 0:
        parts.append(text[start:i + 1])
        start = i + 1
    i += 1
if start < n:
    parts.append(text[start:])
out = Path(__file__).parent / "assets"
for idx in (1, 4, 6, 7, 9, 11):
    part = parts[idx]
    out.joinpath(f"stmt{idx}_head.txt").write_text(part[:2500], encoding="utf-8")
    out.joinpath(f"stmt{idx}_tail.txt").write_text(part[-2500:], encoding="utf-8")
print("ok", [len(parts[i]) for i in (1, 4, 6, 7, 9, 11)])
