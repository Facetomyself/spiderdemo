from pathlib import Path

root = Path(__file__).with_name("_fns")
for name, needle in (
    ("drawArcPath.js", "Math['PI']"),
    ("updateSliderPosition.js", "rotate"),
    ("recordTrajectoryPoint.js", "userTrajec"),
    ("verifyCaptchaAndGetData.js", "apiGetPageData"),
    ("verifyCaptchaAndGetData.js", "rotation"),
    ("verifyCaptchaAndGetData.js", "distance"),
    ("verifyCaptchaAndGetData.js", "trajectory"),
):
    text = (root / name).read_text(encoding="utf-8")
    idx = 0
    print("\n====", name, needle, text.count(needle))
    while True:
        at = text.find(needle, idx)
        if at < 0:
            break
        print(text[max(0, at - 220): at + 280])
        print("---")
        idx = at + len(needle)
