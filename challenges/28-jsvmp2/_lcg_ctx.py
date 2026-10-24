from pathlib import Path
text = Path(__file__).parent.joinpath("assets", "inner.js").read_text(encoding="utf-8")
needle = "1664525"
positions = []
start = 0
while True:
    i = text.find(needle, start)
    if i < 0:
        break
    positions.append(i)
    start = i + len(needle)
print("count", len(positions))
out = []
for i in positions:
    out.append("\n--- " + str(i) + " ---\n")
    out.append(text[max(0, i - 600): i + 900])
Path(__file__).with_name("_lcg_ctx.txt").write_text("\n".join(out), encoding="utf-8")
