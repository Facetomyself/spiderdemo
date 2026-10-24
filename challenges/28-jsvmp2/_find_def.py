from pathlib import Path
inner = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
needles = [
    "function _0xB94BD2",
    "_0xB94BD2=function",
    "var _0xB94BD2",
    "decompressFromUTF16",
    "_0x171F94=",
    "location",
    "hostname",
    "WebSocket",
    "websocket",
]
for needle in needles:
    positions = []
    start = 0
    while len(positions) < 8:
        i = inner.find(needle, start)
        if i < 0:
            break
        positions.append(i)
        start = i + len(needle)
    print(needle, positions)
