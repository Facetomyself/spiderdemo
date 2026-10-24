from pathlib import Path

text = Path(__file__).parent.joinpath("_fns", "updateSliderPosition.js").read_text(encoding="utf-8")
idx = 0
n = 0
while True:
    at = text.find("_0x21792c", idx)
    if at < 0:
        break
    n += 1
    print("\n---", n, at)
    print(text[at - 80: at + 220])
    idx = at + 8
print("count", n)
