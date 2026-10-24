const fs = require("fs");
const path = require("path");
const vm = require("vm");

const dir = __dirname;
const sample = JSON.parse(fs.readFileSync(path.join(dir, "_sample.json"), "utf8"));
const notes = [];
function note(...parts) {
  notes.push(parts.map((part) => String(part).slice(0, 500)).join(" "));
}

let code = fs.readFileSync(path.join(dir, "restore.js"), "utf8");
code = code.replace("new _0x42d47f(_0x5bea)['FTHhhD']()", "0");
code = code.replace(
  "_0x9d1176=_0x5bea['FSkonq'](_0x9d1176,_0x332793),_0x207e1c[_0x2f6d7b]=_0x9d1176;",
  "_0x9d1176=_0x5bea['FSkonq'](_0x9d1176,_0x332793);if(global.__rec)global.__rec.push(_0x9d1176);_0x207e1c[_0x2f6d7b]=_0x9d1176;"
);
global.__rec = [];

class FakeCanvas {
  constructor() {
    this.width = 0;
    this.height = 0;
  }
  getContext() {
    note("getContext", this.width, this.height);
    const ctx = {
      canvas: this,
      drawImage: (...args) => note("drawImage", args.map((item) => (item && item.width ? item.width + "x" + item.height : item)).join("|")),
      getImageData: (x, y, w, h) => {
        note("getImageData", [x, y, w, h].join(","));
        return { data: new Uint8ClampedArray(Math.max(4, (w | 0) * (h | 0) * 4)), width: w, height: h };
      },
      putImageData: (data, x, y) => note("putImageData", [x, y, data && data.width, data && data.height].join(",")),
      fillRect: (...args) => note("fillRect", args.join(",")),
      clearRect(...args) { note("clearRect", args.join(",")); },
      save() { note("save"); },
      restore() { note("restore"); },
      beginPath() {},
      closePath() {},
      moveTo(...args) { note("moveTo", args.join(",")); },
      lineTo(...args) { note("lineTo", args.join(",")); },
      arc: (...args) => note("arc", args.join(",")),
      fill() { note("fill"); },
      stroke() { note("stroke"); },
      translate: (...args) => note("translate", args.join(",")),
      rotate: (value) => note("rotate", value),
      scale(...args) { note("scale", args.join(",")); },
      setTransform(...args) { note("setTransform", args.join(",")); },
      measureText: (text) => ({ width: String(text).length * 7 }),
      fillText: (...args) => note("fillText", args.join(",")),
      createLinearGradient: () => ({ addColorStop() {} }),
      createPattern: () => ({}),
    };
    return new Proxy(ctx, {
      get(target, prop) {
        if (!(prop in target) && typeof prop === "string") note("ctx.get", prop);
        return target[prop];
      },
      set(target, prop, value) {
        note("ctx.set", prop, value);
        target[prop] = value;
        return true;
      },
    });
  }
  toDataURL(type) {
    note("toDataURL", type, this.width, this.height);
    return "data:image/jpeg;base64,QUJD";
  }
}

global.window = global;
global.self = global;
const serverTime = fs.readFileSync(path.join(dir, "_server_time.txt"), "utf8").trim();
global.document = {
  cookie: "a=1; server_time=" + serverTime,
  createElement(tag) {
    note("createElement", tag);
    if (String(tag).toLowerCase() === "canvas") return new FakeCanvas();
    return { style: {}, appendChild() {}, setAttribute() {} };
  },
};
global.atob = (value) => Buffer.from(String(value), "base64").toString("binary");
global.btoa = (value) => Buffer.from(String(value), "binary").toString("base64");
global.Image = class Image {
  set src(value) {
    note("image.src", String(value).slice(0, 32), String(value).length);
    this._src = value;
    this.width = 1020;
    this.height = 370;
    setTimeout(() => {
      note("image.onload");
      try {
        if (this.onload) this.onload();
        note("onload returned");
      } catch (error) {
        note("onload error", error && error.message);
        finish();
      }
    }, 0);
  }
  get src() { return this._src; }
};

try {
  eval(code);
  note("loaded aaaa", typeof global.aaaa);
} catch (error) {
  note("eval failed", error && error.message);
  finish();
}

const sandbox = { exports: {}, module: { exports: {} }, window: {}, self: {}, console };
vm.runInNewContext(fs.readFileSync(path.join(dir, "crypto-js.min.js"), "utf8"), sandbox);
global.CryptoJS = sandbox.module.exports;
note("CryptoJS", typeof global.CryptoJS, global.CryptoJS && Object.keys(global.CryptoJS).slice(0, 12).join(","));

const orig = {};
for (const key of ["MD5", "SHA1", "SHA256", "HmacMD5", "HmacSHA256", "AES", "enc"]) {
  if (global.CryptoJS[key]) note("has", key);
}
const parse = JSON.parse;
JSON.parse = function (text, ...rest) {
  note("JSON.parse", String(text).slice(0, 180));
  return parse.call(this, text, ...rest);
};
const md5 = global.CryptoJS.MD5;
global.CryptoJS.MD5 = function (message, cfg) {
  const result = md5(message, cfg);
  const hex = result.toString();
  if (hex === sample.order || notes.length < 20) note("MD5", String(message).slice(0, 80), hex);
  if (hex === sample.order) note("MD5 HIT", String(message).slice(0, 80));
  return result;
};

function finish() {
  fs.writeFileSync(path.join(dir, "_aaaa_notes.txt"), notes.join("\n"), "utf8");
  const strings = [...new Set(global.__rec || [])];
  fs.writeFileSync(path.join(dir, "_strings.txt"), strings.join("\n"), "utf8");
  console.log("notes", notes.length, "strings", strings.length);
  process.exit(0);
}

try {
  const result = global.aaaa(sample.bg, sample.order);
  note("sync", typeof result, result && String(result).slice(0, 150));
  if (result && typeof result.then === "function") {
    result.then(
      (value) => {
        note("resolved", typeof value, value && String(value).slice(0, 180));
        finish();
      },
      (error) => {
        note("rejected", error && error.stack ? error.stack.split("\n").slice(0, 6).join(" | ") : error);
        finish();
      }
    );
    setTimeout(() => {
      note("timeout");
      finish();
    }, 2000);
  } else finish();
} catch (error) {
  note("throw", error && error.stack ? error.stack.split("\n").slice(0, 8).join(" | ") : error);
  finish();
}
