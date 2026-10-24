from pathlib import Path

inner = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
start = 13226
# find end of that literal
j = start + 1
while j < len(inner):
    if inner[j] == "\\":
        j += 2
        continue
    if inner[j] == '"':
        break
    j += 1
print("lit", start, j, "len", j - start - 1)
Path(__file__).parent.joinpath("assets", "after_lit.txt").write_text(inner[j:j + 2500], encoding="utf-8")
Path(__file__).parent.joinpath("assets", "before_lit.txt").write_text(inner[max(0, start - 800):start], encoding="utf-8")
