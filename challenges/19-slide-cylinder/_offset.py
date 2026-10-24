from pathlib import Path

text = Path(__file__).with_name("restore.js").read_text(encoding="utf-8")
text = text.replace("new _0x42d47f(_0x5bea)['FTHhhD']()", "0")
Path(__file__).with_name("_offset.txt").write_text(text[71800:74200], encoding="utf-8")
print("around", text[72400:72900])
