from pathlib import Path
import re

root = Path(__file__).resolve().parent
js = (root / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8", errors="replace")
css = (root / "assets" / "jsvmp_challenge.css").read_text(encoding="utf-8", errors="replace")
print("js_len", len(js), "lines", js.count("\n") + 1)
print("head", js[:400])
print("---tail---")
print(js[-400:])
print("---urls---")
for match in re.findall(r"/[A-Za-z0-9_./?-]{4,80}", js):
    if any(token in match.lower() for token in ("api", "page", "proto", "auth", "jsvmp", "static", "submit", "challenge")):
        print(match)
print("---ascii strings >= 6---")
strings = re.findall(r"[A-Za-z0-9_./:?=&-]{8,}", js)
print("count", len(strings))
interesting = [item for item in strings if re.search(r"api|page|proto|submit|fetch|xml|http|sign|token|css|number|challenge|wasm", item, re.I)]
print("interesting", len(interesting))
for item in interesting[:200]:
    print(item)
print("---css selectors with content or before---")
for match in re.finditer(r"[^{}]+\{[^}]*content\s*:[^}]+\}", css):
    text = match.group(0).replace("\n", " ")
    print(text[:300])
print("css classes", re.findall(r"\.([A-Za-z0-9_-]+)", css)[:80])
