"""Print structural bounds of the obfuscated script."""

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
for needle in ("function _0x56d8(", "function _0x592d(", "_0x56d8=", "const _0x56d8"):
    start = 0
    hits = []
    while True:
        idx = text.find(needle, start)
        if idx < 0:
            break
        hits.append(idx)
        start = idx + 1
    print(needle, hits)

print("--- around 12000 ---")
print(text[12000:12800])
print("--- around decoder end guess ---")
print(text[127000:127200])
