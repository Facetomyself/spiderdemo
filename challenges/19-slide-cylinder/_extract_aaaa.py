from pathlib import Path

text = Path(__file__).with_name("restore.js").read_text(encoding="utf-8")
start = text.find("function aaaa")
index = text.find("{", start)
depth = 0
end = None
for pos in range(index, len(text)):
    char = text[pos]
    if char == "{":
        depth += 1
    elif char == "}":
        depth -= 1
        if depth == 0:
            end = pos + 1
            break
body = text[start:end]
out = Path(__file__).with_name("_aaaa.js")
out.write_text(body, encoding="utf-8")
print("len", len(body))
print("tail", body[-600:])
