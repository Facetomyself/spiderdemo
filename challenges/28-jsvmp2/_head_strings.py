import json
from pathlib import Path
parts = json.loads(Path(__file__).parent.joinpath("assets", "strings.json").read_text(encoding="utf-8"))
lines = []
for i, p in enumerate(parts[:250]):
    lines.append(f"{i}\t{p[:300]}")
Path(__file__).with_name("_head_strings.txt").write_text("\n".join(lines), encoding="utf-8")
print(len(parts))
