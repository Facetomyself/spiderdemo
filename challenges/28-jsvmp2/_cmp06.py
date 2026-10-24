from pathlib import Path

p = Path(r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp\assets\jsvmp_challenge.js")
text = p.read_text(encoding="utf-8", errors="replace")
out = Path(__file__).with_name("_cmp06.txt")
lines = [
    f"len {len(text)} lines {text.count(chr(10))+1}",
    "HEAD " + text[:300].replace("\n", "\\n"),
    "TAIL " + text[-250:].replace("\n", "\\n"),
    f"Function {text.count('Function')}",
    f"WebSocket {text.count('WebSocket')}",
    f"version {text[:200]}",
]
out.write_text("\n".join(lines), encoding="utf-8")
