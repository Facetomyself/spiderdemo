from pathlib import Path
text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
for needle in ["_0x37FDF1C(134)", "_0x37FDF1C(135)", "Int32Array", "Uint8Array", "WebSocket", "debugger"]:
    print(needle, text.count(needle))
# contexts of (134)
idx = 0
n = 0
while n < 6:
    i = text.find("_0x37FDF1C(134)", idx)
    if i < 0:
        break
    print("\nCTX", i)
    print(text[i-120:i+200])
    idx = i + 10
    n += 1
