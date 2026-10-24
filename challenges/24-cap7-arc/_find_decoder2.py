from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
start = 0
while True:
    idx = text.find("function _0x592d(", start)
    if idx < 0:
        break
    print("hit", idx, "context", text[idx - 30: idx + 40].replace("\n", " "))
    start = idx + 1
print("--- return context ---")
ret = text.find("return _0x314a9a")
print(text[ret - 40: ret + 80])
print("--- showLoading hits ---")
start = 0
while True:
    idx = text.find("function showLoading(", start)
    if idx < 0:
        break
    print("show", idx)
    start = idx + 1
