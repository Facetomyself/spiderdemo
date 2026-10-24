from pathlib import Path

text = Path(__file__).parent.joinpath("_fns", "updateSliderPosition.js").read_text(encoding="utf-8")
for name in ("_0x57598d", "_0x1bc5b8", "_0x4431c0"):
    at = text.find(name + "=")
    if at < 0:
        at = text.find(name + "={")
    print("\n====", name, at)
    print(text[at: at + 700] if at >= 0 else "missing")
