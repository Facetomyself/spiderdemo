"""Build a runtime that only shuffles and decodes the string table."""

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
iife_end = text.find("}(_0x56d8,0x331*-0x83d+0x968a8+0x1f97ca));")
if iife_end < 0:
    raise SystemExit("iife end missing")
iife_end += len("}(_0x56d8,0x331*-0x83d+0x968a8+0x1f97ca));")
array_start = text.find("function _0x56d8(")
array_end = text.find("return _0x56d8();}", array_start)
if array_end < 0:
    raise SystemExit("array end missing")
array_end += len("return _0x56d8();}")
dec_start = text.find("function _0x592d(")
dec_end = text.find("function showLoading()", dec_start)
if dec_end < 0:
    raise SystemExit("decoder end missing")
chunk = text[array_start:array_end] + "\n" + text[dec_start:dec_end] + "\n" + text[:iife_end]
chunk += r"""
const arr = _0x56d8();
const lines = [];
for (let i = 0; i < arr.length; i++) {
  let value = '';
  try {
    value = String(_0x592d(i + 163, ''));
  } catch (err) {
    value = 'ERR ' + err.message;
  }
  lines.push(i + '\t' + value.replace(/\r|\n/g, ' '));
}
require('fs').writeFileSync('decoded_strings.txt', lines.join('\n'), 'utf8');
console.log('count', arr.length, 'sample', lines.slice(0, 8).join(' | '));
"""
Path(__file__).with_name("_decoder_runtime.js").write_text(chunk, encoding="utf-8")
print("iife", iife_end, "array", array_start, array_end, "dec", dec_start, dec_end, "bytes", len(chunk))
