from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
for label, a, b in (
    ("before_dec", 126880, 127080),
    ("array_end", 22780, 23020),
    ("after_iife", 1850, 2100),
):
    print("\n====", label)
    print(text[a:b])
