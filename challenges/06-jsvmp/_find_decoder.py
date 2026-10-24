from pathlib import Path

js = (Path(__file__).resolve().parent / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8")
marker = "function "
# find decoder by the 66666 constant
pos = js.find("66666")
print("pos", pos)
print(js[pos - 180: pos + 420])
print("---codepoints around return---")
snippet = js[pos: pos + 500]
ret = snippet.find("return")
print(repr(snippet[ret: ret + 80]))
