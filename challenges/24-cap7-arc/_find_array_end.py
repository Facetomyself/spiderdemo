from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
start = text.find("function _0x56d8(")
print("start", start)
for needle in ("return _0x314a9a", "];function", "}function _0x592d", "function _0x592d"):
    print(needle, text.find(needle, start))
print("iife_end_marker", text.find("}(_0x56d8,"))
print("after iife", text[text.find("}(_0x56d8,"): text.find("}(_0x56d8,") + 80])
# show 200 chars before decoder
dec = text.find("function _0x592d(")
print("before decoder", text[dec - 180: dec])
