"""Show how the page VM calls its host hooks."""

from pathlib import Path

text = Path(__file__).with_name("spiderking_challenge.js").read_text(encoding="utf-8")
plain = text.translate({
    0x200B: None,
    0x200C: None,
    0x200D: None,
    0x2060: None,
    0x2061: None,
    0x2062: None,
    0x2063: None,
    0x2064: None,
})
for needle in ("__vmpHostGet", "__vmpHostSet", "__vmpHostTypeof", "function __vmp", "vmpHost"):
    print("\n==", needle, plain.count(needle), "==")
    start = 0
    for _ in range(4):
        at = plain.find(needle, start)
        if at < 0:
            break
        print(plain[max(0, at - 80): at + 180].replace("\n", " "))
        print("---")
        start = at + len(needle)
