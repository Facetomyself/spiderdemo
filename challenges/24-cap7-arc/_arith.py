import re
from pathlib import Path

text = Path(__file__).parent.joinpath("_fns", "updateSliderPosition.js").read_text(encoding="utf-8")
for m in re.finditer(r"'(?P<k>[A-Za-z0-9]+)':function\([^)]*\)\{return [^;]+;\}", text):
    print(m.group(0)[:180])
print("--- dynamic keys near multiply ---")
for m in re.finditer(r"return _0x[0-9a-f]+[*][_0-9a-fx]", text):
    print("mul", m.start(), text[m.start() - 120: m.end() + 20])
