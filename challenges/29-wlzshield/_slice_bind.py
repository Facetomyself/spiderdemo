from pathlib import Path

text = Path(__file__).with_name("wlzshield.min.js").read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()
print("lines", len(lines), "lens", [len(line) for line in lines[:12]])
for line_no, col in ((3, 5548), (3, 9551), (2, 8433)):
    if line_no > len(lines):
        print("missing", line_no)
        continue
    line = lines[line_no - 1]
    start = max(0, col - 180)
    end = min(len(line), col + 180)
    snippet = line[start:end]
    print(f"\n--- L{line_no}:{col} len {len(line)} ---")
    print(snippet)
