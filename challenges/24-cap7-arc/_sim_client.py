"""Run the captcha client functions and print scale, pose, and submit URL."""

from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
runtime = (root / "_decoder_runtime.js").read_text(encoding="utf-8")
cut = runtime.index("const arr = _0x56d8();")
parts = [
    runtime[:cut],
    "function _0x530b6a(a,b,c,d){return _0x592d(b-0x2d8, c);}\n",
    "function _0xa33d87(a,b,c,d){return _0x592d(c-0x2e, b);}\n",
    (root / "_fns" / "setupSliderDynamic.js").read_text(encoding="utf-8"),
    "\n",
    (root / "_fns" / "drawArcPath.js").read_text(encoding="utf-8"),
    "\n",
    (root / "_fns" / "getPositionOnArc.js").read_text(encoding="utf-8"),
    "\n",
    (root / "_fns" / "updateSliderPosition.js").read_text(encoding="utf-8"),
    "\n",
    (root / "_fns" / "recordTrajectoryPoint.js").read_text(encoding="utf-8"),
    "\n",
    (root / "_fns" / "apiSubmitAnswer.js").read_text(encoding="utf-8").replace(
        "function apiSubmitAnswer", "async function apiSubmitAnswer", 1
    ),
    "\n",
]
tail = r"""
const calls = [];
const ctx = new Proxy({}, {
  get(target, prop) {
    if (prop in target) return target[prop];
    if (prop === Symbol.toPrimitive) return undefined;
    return () => ctx;
  },
  set(target, prop, value) {
    target[prop] = value;
    return true;
  }
});
function element(name) {
  const el = {
    name,
    style: {},
    width: 400,
    height: 240,
    getContext() { return ctx; },
    getBoundingClientRect() {
      if (name === '.slider-container' || name === 'container') {
        return { x: 80, y: 100, left: 80, top: 100, width: 400, height: 240, right: 480, bottom: 340 };
      }
      const left = parseFloat(el.style.left || '0') || 0;
      const top = parseFloat(el.style.top || '0') || 0;
      const width = parseFloat(el.style.width) || 57.14285714285714;
      const height = parseFloat(el.style.height) || 47.61904761904761;
      const originX = 80 + 2;
      const originY = 100 + 2;
      return {
        left: originX + left,
        top: originY + top,
        width,
        height,
        right: originX + left + width,
        bottom: originY + top + height
      };
    }
  };
  return el;
}
const elements = {
  'slider-piece': element('slider-piece'),
  'slider-btn': element('slider-btn'),
  'arc-path-canvas': element('arc-path-canvas'),
  '.slider-container': element('.slider-container')
};
global.document = {
  getElementById(id) { calls.push('id:' + id); return elements[id] || element(id); },
  querySelector(sel) { calls.push('qs:' + sel); return elements[sel] || element(sel); }
};
const windowState = {};
global.window = new Proxy(windowState, {
  get(target, prop) {
    if (typeof prop === 'string' && !(prop in target)) console.log('MISS', prop);
    return target[prop];
  },
  set(target, prop, value) {
    target[prop] = value;
    return true;
  }
});
global.console = console;
global.setTimeout = (fn) => { try { fn(); } catch (err) {} return 0; };
global.requestAnimationFrame = (fn) => { try { fn(0); } catch (err) {} return 0; };
global.challengeType = 'cap7_challenge';
global.fetch = async (url, opts) => {
  console.log('FETCH', url);
  console.log('METHOD', opts && opts.method);
  console.log('CTYPE', opts && opts.headers && opts.headers['Content-Type']);
  console.log('BODY', opts && opts.body);
  return { ok: true, json: async () => ({ success: true }) };
};
const info = { bg_width: 840, bg_height: 540, mask_width: 120, mask_height: 100 };
const points = [];
for (let i = 0; i < 100; i++) points.push([176 + i * 4.888, 250 + Math.sin(i / 12) * 20]);
try {
  setupSliderDynamic(elements['slider-piece'], info, elements['.slider-container']);
  console.log('SCALE', JSON.stringify(window.sliderScaleInfo));
} catch (err) {
  console.log('SCALE_ERR', err.stack.split('\n').slice(0, 3).join(' | '));
}
window.captchaImageInfo = info;
window.imageInfo = info;
try {
  drawArcPath({ points, image_info: info, arc_path: { points } });
  console.log('AFTER_DRAW', Object.keys(window).join(','));
  if (window.arcPathScale) console.log('ARCSCALE', JSON.stringify(window.arcPathScale));
  if (window.arcPathData) console.log('ARCDATA', JSON.stringify(window.arcPathData).slice(0, 180));
} catch (err) {
  console.log('DRAW_ERR', err.stack.split('\n').slice(0, 4).join(' | '));
}
if (!window.arcPathData) window.arcPathData = { points };
if (!window.arcPathScale && window.sliderScaleInfo) {
  window.arcPathScale = {
    scale: window.sliderScaleInfo.scale,
    offsetX: window.sliderScaleInfo.offsetX,
    offsetY: window.sliderScaleInfo.offsetY
  };
}
try {
  const pos = getPositionOnArc(120);
  console.log('POS120', JSON.stringify(pos));
  updateSliderPosition(120);
  const piece = elements['slider-piece'];
  const box = elements['.slider-container'].getBoundingClientRect();
  const rect = piece.getBoundingClientRect();
  const x = rect.left + rect.width / 2 - box.left;
  const y = rect.top + rect.height / 2 - box.top;
  console.log('STYLE', piece.style.left, piece.style.top, piece.style.transform);
  console.log('CENTER', x, y);
  console.log('ROT', window.currentRotation);
  console.log('BTN', elements['slider-btn'].style.left);
} catch (err) {
  console.log('MOVE_ERR', err.stack.split('\n').slice(0, 4).join(' | '));
}
console.log('CALLS', calls.slice(0, 30).join(' ; '));
apiSubmitAnswer(42).catch((err) => console.log('SUBMIT_ERR', err && err.message));
"""
script = "".join(parts) + tail
out = root / "_sim_client.js"
out.write_text(script, encoding="utf-8")
node = Path(r"D:\reverse_ENV\tools\node\node.exe")
proc = subprocess.run([str(node), str(out)], cwd=root, capture_output=True, text=True)
print(proc.stdout[-5000:])
print(proc.stderr[-2000:])
print("exit", proc.returncode)
