"""Insert newlines so a function can be read."""

from pathlib import Path

src = Path(__file__).with_name("_fns")
for name in ("apiInitChallenge", "initializePage", "getPositionOnArc", "refreshCaptcha"):
    text = (src / f"{name}.js").read_text(encoding="utf-8")
    out = []
    quote = ""
    for ch in text:
        out.append(ch)
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch in (";", "{"):
            out.append("\n")
    (src / f"{name}.pretty.js").write_text("".join(out), encoding="utf-8")
    print(name, "lines", "".join(out).count("\n"))
