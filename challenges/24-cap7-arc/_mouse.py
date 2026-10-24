"""Show the function that records the drag trajectory."""

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
at = text.find("recordTrajectoryPoint(")
start = text.rfind("function ", 0, at)
print("function at", start)
print(text[start: start + 180])
print("--- slice before call ---")
print(text[at - 2500: at + 40])
