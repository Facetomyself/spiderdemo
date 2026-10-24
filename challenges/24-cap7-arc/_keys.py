import re
from pathlib import Path

text = Path(__file__).parent.joinpath("_fns", "updateSliderPosition.js").read_text(encoding="utf-8")
for key in ("_0x21792c", "_0x5489eb", "_0xda51a2", "_0x5ea7f5", "_0x538bf4", "_0x264179", "_0x111da0", "_0x2030b3", "_0x4e5449", "_0x2d8231", "_0x14cbf7"):
    m = re.search(re.escape(key) + r":(0x[0-9a-f]+)", text)
    print(key, m.group(1) if m else "MISSING")
