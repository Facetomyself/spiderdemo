from pathlib import Path
import re

text = Path(__file__).parent.joinpath("assets", "sdk.min.js").read_text(encoding="utf-8", errors="replace")
print("len", len(text), "lines", text.count("\n") + 1)
print("HEAD", text[:200].replace("\n", "\\n"))
for needle in ["WebSocket", "websocket", "wss", "token_seed", "PAGE", "onmessage", "postMessage", "page_data", "challenge", "jsvmp2", "ArrayBuffer", "Uint8"]:
    print(needle, text.count(needle))
strings = re.findall(r"""['"]([^'"\\]{6,80})['"]""", text)
seen = []
for item in strings:
    if item not in seen:
        seen.append(item)
print("unique", len(seen))
Path(__file__).with_name("_sdk_strings.txt").write_text("\n".join(seen[:400]), encoding="utf-8")
