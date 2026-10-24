from pathlib import Path

js = (Path(__file__).resolve().parent / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8")
needles = ["})(", "}) ([", "](", "])(", "],["]
for needle in ["})(", "](", "])("]:
    start = 0
    hits = []
    while True:
        pos = js.find(needle, start)
        if pos < 0:
            break
        hits.append(pos)
        start = pos + 1
    print(needle, len(hits))
    for pos in hits[:30]:
        print(pos, js[max(0, pos - 40): pos + 80].replace("\n", "\\n"))
    if len(hits) > 30:
        print("...")
        for pos in hits[-5:]:
            print(pos, js[max(0, pos - 40): pos + 120].replace("\n", "\\n"))
