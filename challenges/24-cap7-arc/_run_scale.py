"""Execute setupSliderDynamic against a 400x240 box and print sliderScaleInfo."""

from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
runtime = (root / "_decoder_runtime.js").read_text(encoding="utf-8")
cut = runtime.index("const arr = _0x56d8();")
fn = (root / "_fns" / "setupSliderDynamic.js").read_text(encoding="utf-8")
script = runtime[:cut] + """
function _0xa33d87(a,b,c,d){return _0x592d(c-0x2e, b);}
""" + fn + """
function element(width, height) {
  return {
    style: {},
    width,
    height,
    getBoundingClientRect() {
      return { x: 10, y: 20, left: 10, top: 20, width, height, right: 10 + width, bottom: 20 + height };
    }
  };
}
global.document = {
  querySelector() { return element(400, 240); },
  getElementById() { return element(120, 100); }
};
global.window = {};
global.console = console;
const info = { bg_width: 840, bg_height: 540, mask_width: 120, mask_height: 100 };
try {
  setupSliderDynamic(element(120, 100), info, element(400, 240));
  console.log(JSON.stringify(window.sliderScaleInfo, null, 2));
  console.log('arc', JSON.stringify(window.arcPathScale));
} catch (err) {
  console.log('ERR', err && err.stack ? err.stack : err);
}
"""
node = Path(r"D:\reverse_ENV\tools\node\node.exe")
proc = subprocess.run([str(node), "-e", script], cwd=root, capture_output=True, text=True)
print(proc.stdout[-4000:])
print(proc.stderr[-2000:])
print("code", proc.returncode)
