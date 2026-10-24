"""Print redacted JSON shapes for the newest init/attest/page bodies."""

from __future__ import annotations

import json
import re
from pathlib import Path

ZW = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"]
INDEX = {char: pos for pos, char in enumerate(ZW)}
TRACE = Path(__file__).with_name("_trace")
HEX = re.compile(r"^[0-9a-fA-F]+$")


def decode(text: str):
    raw = bytearray()
    for offset in range(0, len(text), 3):
        raw.append((INDEX[text[offset]] << 6) | (INDEX[text[offset + 1]] << 3) | INDEX[text[offset + 2]])
    return json.loads(raw.decode("utf-8"))


def redact(value, depth: int = 0):
    if isinstance(value, dict):
        return {key: redact(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        if len(value) > 8:
            return [redact(item, depth + 1) for item in value[:3]] + [f"...{len(value)}"]
        return [redact(item, depth + 1) for item in value]
    if isinstance(value, str):
        if HEX.fullmatch(value) and len(value) >= 8:
            return f"H{len(value)}"
        if len(value) > 48:
            return f"S{len(value)}"
        return value
    return value


def main() -> None:
    groups = {
        "init": "1_200_res__authentication_api_spiderking_challenge_init_.bin",
    }
    names = sorted(path.name for path in TRACE.glob("*.bin"))
    picked = []
    for token in ("attest_main", "attest_worker", "page"):
        reqs = [name for name in names if name.startswith("4_") is False and "POST_req" in name and token in name]
        # page files start with 4_
        if token == "page":
            reqs = [name for name in names if "POST_req" in name and "_page_" in name]
        if reqs:
            picked.append(reqs[-1])
            res = reqs[-1].replace("POST_req", "200_res")
            if res in names:
                picked.append(res)
    if groups["init"] in names:
        picked.insert(0, groups["init"])
    for name in picked:
        value = decode((TRACE / name).read_text(encoding="utf-8"))
        print("\n==", name, "==")
        print(json.dumps(redact(value), ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()
