"""Extract the string-array shuffle and decoder into decoder.js."""

from __future__ import annotations

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
dec_at = text.find("function _0x592d(")
arr_at = text.find("function _0x56d8(")
if dec_at < 0 or arr_at < 0:
    raise SystemExit(f"missing bounds dec={dec_at} arr={arr_at}")

# The shuffle IIFE is the prefix up to the decoder. The array function follows the decoder.
prefix = text[:dec_at]
decoder_and_array = text[dec_at:]
# Cut the array function at the next top-level function after _0x56d8.
rest = decoder_and_array
next_fn = rest.find("function _0x", len("function _0x56d8("))
# There may be nested functions inside _0x592d before _0x56d8.
arr_rel = rest.find("function _0x56d8(")
after_arr = rest.find("function _0x", arr_rel + 20)
if after_arr < 0:
    raise SystemExit("no function after array")
chunk = prefix + rest[:after_arr]
out = Path(__file__).with_name("decoder.js")
out.write_text(
    chunk
    + "\nmodule.exports = { decode: _0x592d, array: _0x56d8 };\n",
    encoding="utf-8",
)
print("wrote", out.name, "bytes", out.stat().st_size, "arr_at", arr_at, "next", after_arr)
