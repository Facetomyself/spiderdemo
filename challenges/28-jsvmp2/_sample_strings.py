from pathlib import Path

parts = Path(__file__).parent.joinpath("assets", "strings.txt").read_text(encoding="utf-8").split("|")
lines = []
lines.append("count " + str(len(parts)))
lengths = sorted((len(p), i, p[:80]) for i, p in enumerate(parts))
lines.append("--- longest ---")
for length, i, preview in lengths[-30:]:
    lines.append(f"{i}\t{length}\t{preview}")
lines.append("--- first 80 ---")
for i, p in enumerate(parts[:80]):
    lines.append(f"{i}\t{p[:120]}")
lines.append("--- alpha samples ---")
shown = 0
for i, p in enumerate(parts):
    if p.isidentifier() and len(p) > 3:
        lines.append(f"{i}\t{p}")
        shown += 1
        if shown >= 150:
            break
Path(__file__).with_name("_strings_sample.txt").write_text("\n".join(lines), encoding="utf-8")
