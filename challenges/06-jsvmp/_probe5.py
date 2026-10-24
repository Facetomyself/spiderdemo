from pathlib import Path

js = (Path(__file__).resolve().parent / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8")
start = js.find("})([193,6261")
print("start", start)
array_start = js.find("[", start)
depth = 0
in_str = None
escape = False
end = None
for index in range(array_start, len(js)):
    char = js[index]
    if in_str:
        if escape:
            escape = False
        elif char == "\\":
            escape = True
        elif char == in_str:
            in_str = None
        continue
    if char in ("'", '"'):
        in_str = char
        continue
    if char == "[":
        depth += 1
    elif char == "]":
        depth -= 1
        if depth == 0:
            end = index
            break
print("array_end", end, "array_len", end - array_start)
print("AFTER")
print(js[end: end + 3000])
print("---BEFORE CALL 200---")
print(js[start - 200: start + 30])
