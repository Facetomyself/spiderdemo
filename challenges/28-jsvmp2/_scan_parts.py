import json
from pathlib import Path

parts = json.loads(Path(__file__).parent.joinpath("assets", "strings.json").read_text(encoding="utf-8"))
needles = [
    "host", "docu", "sock", "wss", "http", "page", "sign", "cookie", "Web",
    "send", "open", "ajax", "fetch", "json", "answer", "submit", "Array",
    "Uint", "proto", "message", "ready", "challenge", "auth", "token", "sum",
    "number", "grid", "click", "mouse", "ws", "binary", "buffer", "encrypt",
    "decrypt", "hmac", "sha", "md5", "aes", "xor", "opcode", "init",
]
lines = [f"count {len(parts)}"]
for needle in needles:
    hits = [(i, p) for i, p in enumerate(parts) if needle.lower() in p.lower()]
    lines.append(f"## {needle} {len(hits)}")
    for i, p in hits[:40]:
        lines.append(f"{i}\t{p[:200]}")
Path(__file__).with_name("_scan_parts.txt").write_text("\n".join(lines), encoding="utf-8")
print("lines", len(lines))
