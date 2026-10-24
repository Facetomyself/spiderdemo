"""Simulate a drag and print the trajectory the client would record."""

from pathlib import Path
import json
import subprocess

root = Path(__file__).resolve().parent
runtime = (root / "_decoder_runtime.js").read_text(encoding="utf-8")
cut = runtime.index("const arr = _0x56d8();")
files = [
    "setupSliderDynamic.js",
    "drawArcPath.js",
    "getPositionOnArc.js",
    "updateSliderPosition.js",
    "recordTrajectoryPoint.js",
    "mouseHandler.js",
]
parts = [
    runtime[:cut],
    "function _0x530b6a(a,b,c,d){return _0x592d(b-0x2d8, c);}\n",
    "function _0xa33d87(a,b,c,d){return _0x592d(c-0x2e, b);}\n",
]
for name in files:
    parts.append((root / "_fns" / name).read_text(encoding="utf-8"))
    parts.append("\n")
parts.append(r"""
const listeners = {};
function listen(target, type, fn) {
  const key = target + ':' + type;
  listeners[key] = listeners[key] || [];
  listeners[key].push(fn);
  console.log('ON', key);
}
const ctx = new Proxy({}, {
  get(target, prop) {
    if (prop in target) return target[prop];
    return () => ctx;
  },
  set(target, prop, value) { target[prop] = value; return true; }
});
function element(name) {
  const el = {
    name,
    style: {},
    classList: { add() {}, remove() {}, contains() { return false; } },
    addEventListener(type, fn) { listen(name, type, fn); },
    getContext() { return ctx; },
    getBoundingClientRect() {
      if (name === '.slider-container') {
        return { x: 80, y: 100, left: 80, top: 100, width: 400, height: 240, right: 480, bottom: 340 };
      }
      const left = parseFloat(el.style.left || '0') || 0;
      const top = parseFloat(el.style.top || '0') || 0;
      const width = parseFloat(el.style.width) || (name === 'slider-btn' ? 50 : 57.14285714285714);
      const height = parseFloat(el.style.height) || (name === 'slider-btn' ? 50 : 47.61904761904761);
      const originX = name === 'slider-btn' ? 80 : 82;
      const originY = name === 'slider-btn' ? 360 : 102;
      return { left: originX + left, top: originY + top, width, height };
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
  getElementById(id) { return elements[id] || element(id); },
  querySelector(sel) { return elements[sel] || element(sel); },
  addEventListener(type, fn) { listen('document', type, fn); }
};
global.window = {
  captchaImageInfo: { bg_width: 840, bg_height: 540, mask_width: 120, mask_height: 100 },
  addEventListener(type, fn) { listen('window', type, fn); }
};
const points = [];
for (let i = 0; i < 100; i++) points.push([176 + i * (484 / 99), 250 - Math.sin(i / 99 * Math.PI) * 30]);
window.arcPathData = { points };
global.console = console;
global.setTimeout = (fn, ms) => { console.log('TIMEOUT', ms); try { fn(); } catch (err) { console.log('TIMEOUT_ERR', err.message); } return 0; };
global.challengeType = 'cap7_challenge';
global.pendingPageNum = 2;
global.apiGetPageData = (page, type, distance, trajectory, rotation) => {
  console.log('PAGE', page, type, distance, rotation, trajectory.length);
  console.log('FIRST', JSON.stringify(trajectory[0]));
  console.log('MID', JSON.stringify(trajectory[Math.floor(trajectory.length / 2)]));
  console.log('LAST', JSON.stringify(trajectory[trajectory.length - 1]));
  return Promise.resolve({ success: false });
};
global.showLoading = () => {};
global.hideLoading = () => {};
global.showCaptchaMessage = () => {};
global.hideCaptchaMessage = () => {};
global.clearTrajectory = () => { window.userTrajectory = []; };
global.resetSlider = () => {};
global.verifyCaptchaAndGetData = () => {
  const traj = window.userTrajectory || [];
  console.log('VERIFY', 'dist', window.sliderDistance, 'rot', window.currentRotation, 'n', traj.length);
  if (traj.length) {
    console.log('VFIRST', JSON.stringify(traj[0]));
    console.log('VMID', JSON.stringify(traj[Math.floor(traj.length / 2)]));
    console.log('VLAST', JSON.stringify(traj[traj.length - 1]));
  }
};
try {
  setupSliderDynamic(elements['slider-piece'], window.captchaImageInfo, elements['.slider-container']);
  drawArcPath({ points, image_info: window.captchaImageInfo, arc_path: { points } });
  console.log('ARC', JSON.stringify(window.arcPathScale));
  initSliderEvents();
} catch (err) {
  console.log('INIT_ERR', err.stack.split('\n').slice(0, 5).join(' | '));
}
const startX = 400;
function fire(name, type, clientX) {
  const list = listeners[name + ':' + type] || [];
  for (const fn of list) {
    try { fn({ clientX, clientY: 380, preventDefault() {}, touches: [{ clientX, clientY: 380 }] }); }
    catch (err) { console.log('FIRE_ERR', type, err.message); }
  }
}
fire('slider-btn', 'mousedown', startX);
for (let dx = 0; dx <= 180; dx += 4) fire('document', 'mousemove', startX + dx);
fire('slider-btn', 'mousemove', startX + 180);
fire('document', 'mouseup', startX + 180);
fire('slider-btn', 'mouseup', startX + 180);
console.log('TRAJ', (window.userTrajectory || []).length, 'SLIDER', window.sliderDistance, 'ROT', window.currentRotation);
console.log('WKEYS', Object.keys(window).join(','));
console.log('KEYS', Object.keys(listeners).join(','));
""")
out = root / "_sim_drag.js"
out.write_text("".join(parts), encoding="utf-8")
node = Path(r"D:\reverse_ENV\tools\node\node.exe")
proc = subprocess.run([str(node), str(out)], cwd=root, capture_output=True, text=True)
print(proc.stdout[-4000:])
print(proc.stderr[-1500:])
print("exit", proc.returncode)
