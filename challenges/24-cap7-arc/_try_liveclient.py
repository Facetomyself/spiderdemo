"""Replay the page drag functions and post that trajectory."""

from __future__ import annotations

import base64
import io
import json
import math
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from modules.runtime import SpiderSession

ROOT = Path(__file__).resolve().parent
NODE = Path(r"D:\reverse_ENV\tools\node\node.exe")
REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
HEADERS = {
    "Referer": REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}
SCALE = 400 / 840
OFFSET_Y = (240 - 540 * SCALE) / 2
MAX_DRAG = 400 - 120 * SCALE


def rotate(piece: np.ndarray, angle: float) -> np.ndarray:
    height, width = piece.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        piece, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )


def score_at(bg: np.ndarray, piece: np.ndarray, angle: int) -> tuple[float, int, int]:
    turned = rotate(piece, angle)
    mask = (turned[:, :, 3] > 128).astype(np.uint8) * 255
    if int(mask.sum()) < 40:
        return -1.0, 0, 0
    scored = cv2.matchTemplate(bg, turned[:, :, :3], cv2.TM_CCOEFF_NORMED, mask=mask)
    _, value, _, loc = cv2.minMaxLoc(scored)
    return float(value), int(loc[0]), int(loc[1])


def best_pose(bg: np.ndarray, piece: np.ndarray) -> tuple[float, int, int, int]:
    small_bg = cv2.resize(bg, (420, 270), interpolation=cv2.INTER_AREA)
    small_piece = cv2.resize(piece, (60, 50), interpolation=cv2.INTER_AREA)
    coarse_angle = max(range(0, 360, 6), key=lambda angle: score_at(small_bg, small_piece, angle)[0])
    best = (-1.0, 0, 0, 0)
    for angle in range(coarse_angle - 8, coarse_angle + 9):
        value, x, y = score_at(bg, piece, angle % 360)
        if value > best[0]:
            best = (value, angle % 360, x, y)
    return best


def choose(index: int, angle: int) -> int:
    lo = max(51, math.ceil(index / 99 * MAX_DRAG - 1e-9))
    hi = min(int(MAX_DRAG), math.floor((index + 1) / 99 * MAX_DRAG - 1e-9))
    if hi < lo:
        hi = lo
    return min(range(lo, hi + 1), key=lambda item: abs(item - angle / 360 * MAX_DRAG))


def client_track(points: list, distance: int, start_ms: int, events: list[list[float]] | None = None) -> dict:
    runtime = (ROOT / "_decoder_runtime.js").read_text(encoding="utf-8")
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
        parts.append((ROOT / "_fns" / name).read_text(encoding="utf-8"))
        parts.append("\n")
    parts.append(
        r"""
const listeners = {};
function listen(target, type, fn) {
  const key = target + ':' + type;
  listeners[key] = listeners[key] || [];
  listeners[key].push(fn);
}
const ctx = new Proxy({}, { get: () => () => ctx, set: (t, p, v) => { t[p] = v; return true; } });
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
      const originY = name === 'slider-btn' ? 290 : 102;
      return { left: originX + left, top: originY + top, width, height, x: originX + left, y: originY + top };
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
  querySelector(sel) { console.log('SEL', sel); return elements[sel] || element(sel); },
  addEventListener(type, fn) { listen('document', type, fn); }
};
global.window = {
  captchaImageInfo: { bg_width: 840, bg_height: 540, mask_width: 120, mask_height: 100 },
  addEventListener(type, fn) { listen('window', type, fn); }
};
const arcPoints = __ARC__;
window.arcPathData = { points: arcPoints };
global.console = console;
global.setTimeout = (fn) => { try { fn(); } catch (err) { console.log('TIMEOUT_ERR', err.message); } return 0; };
global.challengeType = 'cap7_challenge';
global.pendingPageNum = 2;
global.showLoading = () => {};
global.hideLoading = () => {};
global.showCaptchaMessage = () => {};
global.hideCaptchaMessage = () => {};
global.clearTrajectory = () => { window.userTrajectory = []; };
global.resetSlider = () => {};
global.verifyCaptchaAndGetData = () => {};
let virtualNow = __START__;
Date.now = () => virtualNow;
try {
  setupSliderDynamic(elements['slider-piece'], window.captchaImageInfo, elements['.slider-container']);
  drawArcPath({ points: arcPoints, image_info: window.captchaImageInfo, arc_path: { points: arcPoints } });
  window.arcPathData = { points: arcPoints };
  initSliderEvents();
} catch (err) {
  console.log('INIT_ERR', String(err && err.stack || err).split('\n')[0]);
}
const startX = 120;
const target = __DISTANCE__;
function fire(name, type, clientX) {
  const list = listeners[name + ':' + type] || [];
  for (const fn of list) {
    try { fn({ clientX, clientY: 300, preventDefault() {}, touches: [{ clientX, clientY: 300 }] }); }
    catch (err) { console.log('FIRE_ERR', type, err.message); }
  }
}
fire('slider-btn', 'mousedown', startX);
const events = __EVENTS__;
if (events && events.length) {
  for (const ev of events) {
    virtualNow += ev[0];
    fire('document', 'mousemove', startX + Math.min(target, ev[1]));
  }
} else {
  const steps = 48;
  for (let i = 1; i <= steps; i++) {
    virtualNow += 9 + ((i * 5) % 11);
    const frac = i / steps;
    const eased = frac * frac * (3 - 2 * frac);
    fire('document', 'mousemove', startX + eased * target);
  }
}
virtualNow += 16;
fire('document', 'mouseup', startX + target);
const traj = window.userTrajectory || [];
const expectX = 2 + arcPoints[0][0] * (400 / 840);
const expectY = 2 + ((240 - 540 * 400 / 840) / 2) + arcPoints[0][1] * (400 / 840);
if (traj.length) {
  console.log('DELTA', (traj[0].x - expectX).toFixed(4), (traj[0].y - expectY).toFixed(4));
}
const dts = [];
for (let i = 1; i < traj.length; i++) dts.push(traj[i].t - traj[i - 1].t);
const mean = dts.reduce((sum, item) => sum + item, 0) / Math.max(1, dts.length);
const variance = dts.reduce((sum, item) => sum + (item - mean) ** 2, 0) / Math.max(1, dts.length);
console.log('STAT', traj.length, Math.round(Math.sqrt(variance) * 100) / 100, traj.length ? traj[traj.length - 1].t - traj[0].t : 0);
console.log('META', window.sliderDistance, window.currentRotation, traj.length, virtualNow);
console.log('B64', Buffer.from(JSON.stringify(traj)).toString('base64'));
""".replace("__ARC__", json.dumps(points))
        .replace("__START__", str(start_ms))
        .replace("__DISTANCE__", str(distance))
        .replace("__EVENTS__", json.dumps(events or []))
    )
    script = ROOT / "_sim_live.js"
    script.write_text("".join(parts), encoding="utf-8")
    proc = subprocess.run([str(NODE), str(script)], cwd=ROOT, capture_output=True, text=True)
    info = {"returncode": proc.returncode, "stderr": proc.stderr[-500:]}
    for line in proc.stdout.splitlines():
        if line.startswith("SEL "):
            info["selector"] = line[4:]
        elif line.startswith("DELTA "):
            info["delta"] = line[6:]
        elif line.startswith("STAT "):
            info["stat"] = line[5:]
        elif line.startswith("META "):
            info["meta"] = line[5:]
        elif line.startswith("B64 "):
            info["b64"] = line[4:]
        elif line.startswith("INIT_ERR") or line.startswith("FIRE_ERR"):
            info["jserr"] = line
    return info


def main() -> None:
    session = SpiderSession()
    with session.client(headers=HEADERS) as client:
        for attempt in range(3):
            cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
            bg = np.array(Image.open(io.BytesIO(base64.b64decode(cap["overlay"]))).convert("RGB"))
            piece = np.array(Image.open(io.BytesIO(base64.b64decode(cap["masked"]))).convert("RGBA"))
            points = cap["arc_path"]["points"]
            arc = np.array(points, dtype=np.float64)
            value, angle, x, y = best_pose(bg, piece)
            found = np.array([x + piece.shape[1] / 2, y + piece.shape[0] / 2])
            index = int(np.argmin(np.hypot(*(arc - found).T)))
            gap = float(np.hypot(*(arc[index] - found)))
            if value < 0.8 or gap > 3 or int(y - cap["slider_y"]) != 0:
                print("skip", attempt, "score", round(value, 3), "gap", round(gap, 2), "dy", int(y - cap["slider_y"]))
                continue
            distance = choose(index, angle)
            start_ms = int(time.time() * 1000) + 30
            info = client_track(points, distance, start_ms)
            encoded = info.get("b64")
            if not encoded:
                print("nosim", attempt, info.get("jserr"), info.get("stderr"))
                continue
            raw = json.loads(base64.b64decode(encoded))
            wait = int(raw[-1]["t"]) + 360 - int(time.time() * 1000)
            if wait > 0:
                time.sleep(wait / 1000)
            body = {
                "distance": distance,
                "trajectory_encoded": encoded,
                "rotation_angle": distance / MAX_DRAG * 360.0,
                "page_num": 2,
                "challenge_type": "cap7_challenge",
                "captcha_id": cap["captcha_id"],
                "container_width": 400,
                "container_height": 240,
            }
            payload = client.post("/captcha/api/cap7_challenge/page/", json=body).json()
            print(
                "try",
                attempt,
                "score",
                round(value, 3),
                "gap",
                round(gap, 2),
                "angle",
                angle,
                "arc",
                index,
                "dist",
                distance,
                "sel",
                info.get("selector"),
                "delta",
                info.get("delta"),
                "meta",
                info.get("meta"),
                "ok",
                payload.get("success"),
                "error",
                payload.get("error"),
                "msg",
                payload.get("message"),
            )
            if payload.get("success"):
                print("unlocked", len(payload.get("page_data") or []))
                break
            if payload.get("error") and "重新操作" not in str(payload.get("error")) and "正常拖动" not in str(payload.get("error")):
                break


if __name__ == "__main__":
    main()
