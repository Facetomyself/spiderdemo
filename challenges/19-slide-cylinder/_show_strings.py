from pathlib import Path

text = Path(__file__).with_name("_strings.txt").read_bytes().decode("utf-8", errors="replace")
lines = text.splitlines()
kept = []
for line in lines:
    if not line:
        continue
    printable = sum(32 <= ord(ch) < 127 for ch in line) / len(line)
    if printable > 0.85 and len(line) >= 2:
        kept.append(line)
Path(__file__).with_name("_strings_ascii.txt").write_text("\n".join(kept), encoding="utf-8")
print("kept", len(kept), "of", len(lines))
