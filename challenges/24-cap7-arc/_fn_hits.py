from pathlib import Path

root = Path(__file__).with_name("_fns")
needles = ["Math['PI']", "Math['atan", "Math['sin", "Math['cos", "rotation", "rotate", "transform", "trajectory", "distance", "sliderDist", "userTrajec", "toFixed", "deg", "rad"]
for path in sorted(root.glob("*.js")):
    if path.name.endswith(".pretty.js"):
        continue
    text = path.read_text(encoding="utf-8")
    hits = [n for n in needles if n in text]
    if hits:
        print(path.name, hits)
