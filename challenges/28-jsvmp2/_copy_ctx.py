from pathlib import Path
text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
needle = "_0x37FDF1C(77)"
i = 0
n = 0
chunks = []
while n < 8:
    i = text.find(needle, i)
    if i < 0:
        break
    chunks.append(f"\n--- {i} ---\n" + text[max(0, i - 200): i + 500])
    i += len(needle)
    n += 1
print("count", text.count(needle))
Path(__file__).with_name("_copy_ctx.txt").write_text("\n".join(chunks), encoding="utf-8")
