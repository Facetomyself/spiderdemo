const fs = require("fs");
const vm = require("vm");
const path = require("path");

const root = __dirname;
const logs = [];
const note = (line) => logs.push(String(line).slice(0, 500));

function makeSandbox() {
  const base = {
    console: { log() {}, info() {}, warn() {}, error(...a) { note("err " + a.join(" ").slice(0, 200)); }, debug() {} },
    setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask,
    URL, URLSearchParams, TextEncoder, TextDecoder,
    atob: (v) => Buffer.from(String(v), "base64").toString("binary"),
    btoa: (v) => Buffer.from(String(v), "binary").toString("base64"),
    crypto: globalThis.crypto,
    performance: { now: () => Date.now(), timeOrigin: Date.now() },
    navigator: {
      userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
      language: "zh-CN", languages: ["zh-CN"], platform: "Win32", webdriver: false,
      plugins: { length: 0 }, mimeTypes: { length: 0 }, cookieEnabled: true, hardwareConcurrency: 8, deviceMemory: 8,
      vendor: "Google Inc.", appVersion: "5.0", maxTouchPoints: 0, onLine: true,
    },
    location: {
      href: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge",
      origin: "https://www.spiderdemo.cn", protocol: "https:", host: "www.spiderdemo.cn",
      hostname: "www.spiderdemo.cn", pathname: "/captcha/wlzshield_captcha_challenge", search: "", hash: "",
    },
    document: {
      cookie: "", readyState: "complete", hidden: false, visibilityState: "visible",
      documentElement: { style: {} }, body: { style: {}, appendChild() {}, clientWidth: 1200, clientHeight: 800 },
      head: { appendChild() {} },
      createElement() { return { style: {}, appendChild() {}, setAttribute() {}, addEventListener() {}, getContext() { return null; }, width: 300, height: 150 }; },
      getElementById() { return { style: {}, appendChild() {}, innerHTML: "" }; },
      querySelector() { return { style: {}, appendChild() {}, innerHTML: "" }; },
      addEventListener() {},
    },
    screen: { width: 1920, height: 1080, colorDepth: 24 },
    localStorage: { getItem() { return null; }, setItem() {} },
    sessionStorage: { getItem() { return null; }, setItem() {} },
    addEventListener() {},
    fetch: async (url) => { note("fetch " + url); return { ok: false, status: 0, json: async () => ({}), text: async () => "" }; },
  };
  const seen = new Set();
  const sandbox = new Proxy(base, {
    get(target, key, receiver) {
      if (base.__watch && typeof key === "string" && !(key in target) && !seen.has(key)) {
        seen.add(key);
        note("missing " + key);
      }
      return Reflect.get(target, key, receiver);
    },
  });
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  sandbox.globalThis = sandbox;
  sandbox.top = sandbox;
  sandbox.parent = sandbox;
  return sandbox;
}

const sandbox = makeSandbox();
vm.createContext(sandbox);
function load(name) {
  vm.runInContext(fs.readFileSync(path.join(root, name), "utf8"), sandbox, { filename: name });
}
load("vendors.min.js");
load("wlzshield.min.js");
const shield = sandbox.WlzShield;
const inst = shield.instance;
note("modules " + (inst.modules && Object.keys(inst.modules).join(",")));
const names = [];
let cursor = inst;
while (cursor && cursor !== Object.prototype) {
  for (const name of Object.getOwnPropertyNames(cursor)) {
    if (!names.includes(name)) names.push(name + ":" + typeof inst[name]);
  }
  cursor = Object.getPrototypeOf(cursor);
}
note("own " + names.join(" | "));
sandbox.__watch = true;
for (const name of Object.keys(inst)) {
  if (typeof inst[name] === "function") {
    try {
      const value = inst[name]();
      note("call " + name + " -> " + typeof value + " " + (value && typeof value === "object" ? Object.keys(value).slice(0, 12).join(",") : ""));
    } catch (error) {
      note("call " + name + " ERR " + String(error.message).slice(0, 180));
    }
  }
}
try {
  const value = shield.getPayload("9d4295076aaef0b4c16e18e4f53b5120");
  note("payload2 " + typeof value + " " + (value && typeof value === "object" ? Object.keys(value).join(",") : String(value).slice(0, 80)));
} catch (error) {
  note("payload2 ERR " + error.message);
}
fs.writeFileSync(path.join(root, "_collector_log.txt"), logs.join("\n"), "utf8");
process.exit(0);
