"""Execute drawArcPath and print anything it stores on window."""

from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
runtime = (root / "_decoder_runtime.js").read_text(encoding="utf-8")
cut = runtime.index("const arr = _0x56d8();")
fn = (root / "_fns" / "drawArcPath.js").read_text(encoding="utf-8")
script = runtime[:cut] + """
function _0xa33d87(a,b,c,d){return _0x592d(c-0x2e, b);}
""" + fn + """
const ctx = {
  set width(v) { this._w = v; },
  set height(v) { this._h = v; },
  get width() { return this._w || 400; },
  get height() { return this._h || 240; },
  clearRect() {},
  beginPath() {},
  moveTo() {},
  lineTo() {},
  stroke() {},
  arc() {},
  fill() {},
  save() {},
  restore() {},
  translate() {},
  rotate() {},
  scale() {},
  quadraticCurveTo() {},
  bezierCurveTo() {},
  closePath() {},
  setLineDash() {},
  fillText() {},
  strokeText() {},
  measureText() { return { width: 10 }; },
  drawImage() {},
  createLinearGradient() { return { addColorStop() {} }; },
};
const canvas = {
  style: {},
  width: 400,
  height: 240,
  getContext() { return ctx; },
  getBoundingClientRect() { return { width: 400, height: 240, left: 0, top: 0 }; }
};
global.document = {
  getElementById() { return canvas; },
  querySelector() { return canvas; }
};
global.window = {
  sliderScaleInfo: {
    scale: 400/840,
    displayWidth: 400,
    displayHeight: 540*400/840,
    offsetX: 0,
    offsetY: (240 - 540*400/840)/2,
    sliderWidth: 120*400/840,
    sliderHeight: 100*400/840,
    maxDragDistance: 400 - 120*400/840
  },
  arcPathData: { points: [[200,250],[300,260],[400,250]] }
};
global.console = console;
const points = [];
for (let i = 0; i < 100; i++) points.push([200 + i * 4, 250 + Math.sin(i / 10) * 20]);
try {
  drawArcPath({ points });
} catch (err) {
  console.log('ERR', err.stack.split('\\n').slice(0, 4).join('\\n'));
}
const keys = Object.keys(window);
console.log('keys', keys.join(','));
for (const key of keys) {
  const value = window[key];
  if (value && typeof value === 'object') console.log(key, JSON.stringify(value).slice(0, 500));
  else console.log(key, value);
}
"""
node = Path(r"D:\reverse_ENV\tools\node\node.exe")
proc = subprocess.run([str(node), "-e", script], cwd=root, capture_output=True, text=True)
print(proc.stdout[-3000:])
print(proc.stderr[-1500:])
