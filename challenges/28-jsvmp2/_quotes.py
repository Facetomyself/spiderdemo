from pathlib import Path

text = Path(__file__).parent.joinpath("assets", "jsvmp2.js").read_text(encoding="utf-8")
expr = text.splitlines()[-1]
# Find ")( and "); sequences
needles = ['")(', '");', '") ', "')(", '");']
lines = []
for needle in ['")(', '");', "')(", "\\n"]:
    positions = []
    start = 0
    while True:
        i = expr.find(needle, start)
        if i < 0:
            break
        positions.append(i)
        start = i + len(needle)
        if len(positions) > 30:
            break
    lines.append(f"{needle!r} count_shown {len(positions)} first {positions[:15]}")

lines.append("TAIL2 " + expr[-1500:])
Path(__file__).with_name("_quotes.txt").write_text("\n".join(lines), encoding="utf-8")
