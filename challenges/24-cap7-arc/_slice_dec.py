from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
Path(__file__).with_name("_decoder_slice.js").write_text(text[127021:140000], encoding="utf-8")
print("ok", 140000 - 127021)
