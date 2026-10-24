from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
idx = text.find("function _0x530b6a(")
print("idx", idx)
print(text[idx: idx + 500])
print("--- a33 ---")
idx2 = text.find("function _0xa33d87(")
print(text[idx2: idx2 + 250])
