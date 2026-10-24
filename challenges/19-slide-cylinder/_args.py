from pathlib import Path

text = Path(__file__).with_name("restore.js").read_text(encoding="utf-8")
start = text.find("function _0x5c0d1c")
index = text.find("{", start)
depth = 0
end = None
for pos in range(index, len(text)):
    if text[pos] == "{":
        depth += 1
    elif text[pos] == "}":
        depth -= 1
        if depth == 0:
            end = pos + 1
            break
body = text[start:end]
Path(__file__).with_name("_order_fn.js").write_text(body, encoding="utf-8")
print("len", len(body))
print(body[:1500])
print("---TAIL---")
print(body[-800:])
