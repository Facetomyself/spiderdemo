"""Print local decoder wrappers inside slider functions."""

from pathlib import Path

root = Path(__file__).with_name("_fns")
for name in ("updateSliderPosition.js", "setupSliderDynamic.js", "verifyCaptchaAndGetData.js", "drawArcPath.js"):
    text = (root / name).read_text(encoding="utf-8")
    print("\n====", name, "len", len(text))
    start = 0
    while True:
        at = text.find("function _0x", start)
        if at < 0 or at > 8000 and name != "setupSliderDynamic.js":
            break
        print(text[at: at + 180])
        print("---")
        start = at + 12
