from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
print(text[12585:13200])
print("\n---- LEN CHECK ----")
print("next function after 12585")
idx = text.find("function ", 12590)
print(idx, text[idx:idx+60])
