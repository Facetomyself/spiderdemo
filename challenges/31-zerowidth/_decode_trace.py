"""Decode saved zero-width bodies. Print JSON shape only."""

from __future__ import annotations

import json
from pathlib import Path

ZW = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"]
INDEX = {char: pos for pos, char in enumerate(ZW)}
TRACE = Path(__file__).with_name("_trace")


def decode(text: str):
    if len(text) % 3:
        raise ValueError(f"length {len(text)} is not a multiple of 3")
    raw = bytearray()
    for offset in range(0, len(text), 3):
        raw.append((INDEX[text[offset]] << 6) | (INDEX[text[offset + 1]] << 3) | INDEX[text[offset + 2]])
    payload = raw.decode("utf-8")
    return json.loads(payload)


def shape(value, depth: int = 0) -> object:
    if isinstance(value, dict):
        if depth > 2:
            return {"_keys": list(value)[:12]}
        return {key: shape(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return {"_list": len(value), "_sample": shape(value[0], depth + 1) if value else None}
    if isinstance(value, str):
        return {"_str": len(value)}
    return {"_t": type(value).__name__, "_v": value}


def main() -> None:
    for path in sorted(TRACE.glob("*.bin")):
        text = path.read_text(encoding="utf-8")
        print("FILE", path.name, "chars", len(text))
        try:
            value = decode(text)
        except Exception as exc:
            print("  fail", type(exc).__name__, str(exc)[:160])
            continue
        print(" ", json.dumps(shape(value), ensure_ascii=False)[:1200])


if __name__ == "__main__":
    main()
