from pathlib import Path
import re

js = (Path(__file__).resolve().parent / "assets" / "jsvmp_challenge.js").read_text(encoding="utf-8")
lines = js.splitlines()
print("nlines", len(lines))
for index, line in enumerate(lines):
    print("LINE", index, "len", len(line), "head", line[:180].replace("\n", ""))

needles = [
    "apiInitChallenge",
    "apiGetPageData",
    "apiSubmitAnswer",
    "ProtobufAuth",
    "CSSAntiCrawler",
    "ChallengePageRequest",
    "fetch(",
    "XMLHttpRequest",
    "application/x-protobuf",
    "protobuf",
    "/authentication/",
    "jsvmp",
    "function ",
]
for needle in needles:
    positions = [match.start() for match in re.finditer(re.escape(needle), js)]
    print("NEEDLE", needle, len(positions), positions[:12])

# dump a window around the first real challenge function name after the header
anchor = js.find("function apiInitChallenge")
print("anchor function apiInitChallenge", anchor)
anchor2 = js.find("apiInitChallenge=")
print("anchor assign", anchor2)
anchor3 = js.find("apiInitChallenge ")
print("anchor space", anchor3)
# show a slice around protobuf
for needle in ("ProtobufAuth", "CSSAntiCrawlerDecryptor", "ChallengePageRequest"):
    pos = js.find(needle)
    print("\n====", needle, pos)
    print(js[max(0, pos - 120): pos + 400])
