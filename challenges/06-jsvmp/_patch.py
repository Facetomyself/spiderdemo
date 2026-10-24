from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8")
old = "return \u18de\u1d52[\u18de\u3147]=\u3147\u3007(\u1424\u039f);"
new = "var __s=\u3147\u3007(\u1424\u039f);globalThis.__STRS.push(__s);return \u18de\u1d52[\u18de\u3147]=__s;"
count = source.count(old)
if count != 1:
    raise SystemExit(f"marker count {count}")
(root / "assets" / "jsvmp_patched.js").write_text(source.replace(old, new, 1), encoding="utf-8")
print("patched", count)
