from pathlib import Path

text = Path(__file__).with_name("restore.js").read_text(encoding="utf-8")
needles = [
    "FTHhhD",
    "Math['random']",
    "Math['round']",
    "while(!![])",
    "debugger",
    "setInterval",
    "setTimeout",
]
for needle in needles:
    print(needle, text.count(needle))
target = "new _0x42d47f(_0x5bea)['FTHhhD']()"
print("exact", text.count(target))
index = text.find("FTHhhD")
print(repr(text[index - 40 : index + 80]))
