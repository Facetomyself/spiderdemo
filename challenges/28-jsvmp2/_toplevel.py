from pathlib import Path

text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
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
lines = [f"statements {len(parts)} depth_end {depth}"]
for idx, part in enumerate(parts):
    preview = part.strip().replace("\n", " ")[:180]
    lines.append(f"{idx}\t{len(part)}\t{preview}")
Path(__file__).with_name("_toplevel.txt").write_text("\n".join(lines), encoding="utf-8")
print("statements", len(parts))
