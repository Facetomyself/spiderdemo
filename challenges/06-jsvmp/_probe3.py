from pathlib import Path

js = (Path(__file__).resolve().parent / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8")
print("TAIL 2500")
print(js[-2500:])
print("---LINE0---")
print(js.splitlines()[0])
