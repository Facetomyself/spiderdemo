from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
idx = text.find("function _0x592d(")
print("idx", idx)
print(repr(text[idx - 20: idx + 30]))
print("space find", text.find("function ", 120000))
print("array return", text.find("return _0x314a9a"))
print(repr(text[22820:22920]))
