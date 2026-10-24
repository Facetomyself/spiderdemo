from pathlib import Path
text = Path(__file__).with_name("_fns").joinpath("drawArcPath.js").read_text(encoding="utf-8")
print(text[:400])
print("---")
print(text[9200:9800])
print("---")
print(text[13400:14200])
