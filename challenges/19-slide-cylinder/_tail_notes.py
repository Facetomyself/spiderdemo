from pathlib import Path

lines = Path(__file__).with_name("_aaaa_notes.txt").read_text(encoding="utf-8").splitlines()
print("count", len(lines))
print("---tail---")
print("\n".join(lines[-25:]))
