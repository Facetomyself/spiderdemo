from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
at = text.find("lientX")
print("count", text.count("lientX"))
print(text[at - 900: at + 200])
