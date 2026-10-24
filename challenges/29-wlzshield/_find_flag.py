from pathlib import Path

text = Path(__file__).with_name("wlzshield.min.js").read_text(encoding="utf-8", errors="replace")
needles = [
    "xhr_missing",
    "xhr_constructor_hooked",
    "websocket_missing",
    "webrtc_unimplemented",
    "fetch_missing",
]
for needle in needles:
    escaped = "".join("\\u%04x" % ord(ch) for ch in needle)
    print(needle, "plain", text.find(needle), "esc", text.find(escaped))
