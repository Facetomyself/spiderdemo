from pathlib import Path

parts = Path(__file__).parent.joinpath("assets", "strings.txt").read_text(encoding="utf-8").split("|")
print("parts", len(parts))
keys = (
    "socket", "Socket", "ws", "wss", "http", "submit", "page", "answer",
    "challenge", "token", "sign", "cookie", "Sec-", "binary", "ArrayBuffer",
    "onmessage", "send", "JSON", "parse", "fetch", "XML", "ajax", "api",
    "number", "sum", "page_data", "init", "auth", "jsvmp",
)
hits = []
for i, item in enumerate(parts):
    low = item.lower()
    if any(k.lower() in low for k in keys) or any(ch in item for ch in "/?&="):
        if len(item) <= 180:
            hits.append(f"{i}\t{item}")
out = Path(__file__).with_name("_strings_hits.txt")
out.write_text("\n".join(hits), encoding="utf-8")
print("hits", len(hits))
