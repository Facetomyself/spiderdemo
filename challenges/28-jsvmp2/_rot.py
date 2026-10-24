from pathlib import Path
text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
i = text.find("new Function(")
Path(__file__).with_name("_rot.txt").write_text(text[i - 2500:i + 400], encoding="utf-8")
print("at", i)
