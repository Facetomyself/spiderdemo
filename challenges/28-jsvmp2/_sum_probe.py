from pathlib import Path
from collections import Counter

text = Path(__file__).with_name("_probe_env.txt").read_text(encoding="utf-8")
lines = [line for line in text.splitlines() if line]
print("events", len(lines))
kinds = Counter(line.split(" ", 1)[0] for line in lines)
print("kinds", dict(kinds))
# unique get paths
gets = Counter()
for line in lines:
    if line.startswith("get "):
        gets[line[4:].split(".")[0] + "." + line[4:].split(".", 1)[-1].split("(")[0]] += 1
print("--- top gets ---")
for key, count in gets.most_common(80):
    print(count, key)
print("--- non-get ---")
for line in lines:
    if not line.startswith("get "):
        print(line[:300])
