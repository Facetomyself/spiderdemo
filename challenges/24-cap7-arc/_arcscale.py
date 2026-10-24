from pathlib import Path

text = Path(__file__).parent.joinpath("_fns", "drawArcPath.js").read_text(encoding="utf-8")
at = text.find("_0x332c27")
print("count", text.count("_0x332c27"), "first", at)
print(text[max(0, at - 1800): at + 400])
