"""Extract named function bodies from the obfuscated script."""

from __future__ import annotations

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
names = [
    "getPositionOnArc",
    "updateSliderPosition",
    "verifyCaptchaAndGetData",
    "drawArcPath",
    "setupSliderDynamic",
    "refreshCaptcha",
    "apiInitChallenge",
    "recordTrajectoryPoint",
    "clearTrajectory",
    "enableSliderDrag",
    "resetSlider",
    "initializePage",
    "loadPageData",
    "apiSubmitAnswer",
    "submitAnswer",
]


def extract(name: str) -> str | None:
    token = f"function {name}("
    start = text.find(token)
    if start < 0:
        return None
    paren = text.find("(", start)
    depth = 0
    i = paren
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    brace = text.find("{", i)
    depth = 0
    j = brace
    while j < len(text):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : j + 1]
        elif ch in ("'", '"'):
            quote = ch
            j += 1
            while j < len(text) and text[j] != quote:
                if text[j] == "\\":
                    j += 1
                j += 1
        j += 1
    return None


out = Path(__file__).with_name("_fns")
out.mkdir(exist_ok=True)
for name in names:
    body = extract(name)
    if body is None:
        print(f"{name}: MISSING")
        continue
    (out / f"{name}.js").write_text(body, encoding="utf-8")
    print(f"{name}: {len(body)}")
