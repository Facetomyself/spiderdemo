from pathlib import Path

for name in ("setupSliderDynamic.js", "drawArcPath.js", "enableSliderDrag.js"):
    text = Path(__file__).parent.joinpath("_fns", name).read_text(encoding="utf-8")
    print("\n====", name, "window", text.count("window["))
    idx = 0
    shown = 0
    while shown < 12:
        at = text.find("window[", idx)
        if at < 0:
            break
        print(text[at: at + 160].replace("\n", " "))
        print("---")
        idx = at + 7
        shown += 1
