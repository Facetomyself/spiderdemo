from pathlib import Path

inner = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
out = Path(__file__).parent / "assets"
out.joinpath("inner_head.txt").write_text(inner[:3500], encoding="utf-8")
# Find the string-array function: large array of quoted strings
idx = inner.find("=[\"")
idx2 = inner.find("=['")
print("dq", idx, "sq", idx2)
# count encoded-looking strings
print("inner_len", len(inner))
