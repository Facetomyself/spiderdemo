from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
idx = 0
while True:
    at = text.find("recordTrajectoryPoint(", idx)
    if at < 0:
        break
    print(text[at - 200: at + 80])
    print("---")
    idx = at + 20
