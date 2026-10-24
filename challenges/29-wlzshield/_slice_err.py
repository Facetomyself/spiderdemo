from pathlib import Path

lines = Path(__file__).with_name("wlzshield.min.js").read_text(encoding="utf-8", errors="replace").splitlines()
for line_no, col in ((35, 9541), (35, 8625), (35, 6988), (33, 2221), (11, 6930)):
    line = lines[line_no - 1]
    start = max(0, col - 220)
    end = min(len(line), col + 220)
    print(f"\n--- L{line_no}:{col} len {len(line)} ---")
    print(line[start:end])
