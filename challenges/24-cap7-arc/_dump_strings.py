"""Run the shuffled string table and dump base64-decoded entries."""

from __future__ import annotations

from pathlib import Path

text = Path(__file__).with_name("static__js__captcha__cap7_challenge.js").read_text(encoding="utf-8")
end = text.find("function showLoading()")
if end < 0:
    raise SystemExit("showLoading not found")
chunk = text[:end]
out = Path(__file__).with_name("_decoder_runtime.js")
out.write_text(
    chunk
    + r"""
const arr = _0x56d8();
const lines = [];
for (let i = 0; i < arr.length; i++) {
  let value = '';
  try {
    value = _0x592d(i + 163, '');
  } catch (err) {
    value = 'ERR ' + err.message;
  }
  lines.push(i + '\t' + value);
}
require('fs').writeFileSync('decoded_strings.txt', lines.join('\n'), 'utf8');
console.log('count', arr.length);
""",
    encoding="utf-8",
)
print("runtime_bytes", out.stat().st_size, "end", end)
