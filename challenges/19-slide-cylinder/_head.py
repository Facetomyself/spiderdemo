from pathlib import Path

text = Path(__file__).with_name("crypto-js.min.js").read_text(encoding="utf-8", errors="replace")
Path(__file__).with_name("_crypto_head.txt").write_text(text[:500], encoding="utf-8")
print(len(text))
