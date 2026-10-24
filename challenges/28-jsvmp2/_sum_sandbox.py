from pathlib import Path
from collections import Counter
text = Path(__file__).with_name("_sandbox.txt").read_text(encoding="utf-8")
lines = text.splitlines()
print("events", len(lines))
kinds = Counter(line.split(" ", 1)[0] for line in lines)
print(dict(kinds))
for line in lines:
    if not line.startswith("byId ") and not line.startswith("create "):
        print(line[:300])
print("--- byId ---")
ids = [line[5:] for line in lines if line.startswith("byId ")]
print("unique", sorted(set(ids))[:80], "count", len(ids))
