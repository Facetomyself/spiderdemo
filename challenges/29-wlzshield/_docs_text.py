"""Strip guide HTML down to visible text."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "_docs"


def visible(name: str) -> str:
    html = (ROOT / name).read_text(encoding="utf-8")
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", html)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def main() -> None:
    for name in ("guide_getting-started.html.html", "guide_checkbox-captcha.html.html"):
        text = visible(name)
        out = ROOT / (name + ".txt")
        out.write_text(text, encoding="utf-8")
        print(name, len(text))


if __name__ == "__main__":
    main()
