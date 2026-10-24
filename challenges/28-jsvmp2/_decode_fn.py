from pathlib import Path
text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
start = 406343
Path(__file__).with_name("_decode_fn.txt").write_text(text[start:start + 6500], encoding="utf-8")
