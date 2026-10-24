const fs = require("fs");
const vm = require("vm");
const path = require("path");
const root = __dirname;
const logs = [];
const note = (line) => logs.push(String(line).slice(0, 800));
const sandbox = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask,
  URL, URLSearchParams, TextEncoder, TextDecoder,
  atob: (v) => Buffer.from(String(v), "base64").toString("binary"),
  btoa: (v) => Buffer.from(String(v), "binary").toString("base64"),
  crypto: globalThis.crypto,
  performance: { now: () => Date.now() },
  navigator: { userAgent: "Mozilla/5.0", language: "zh-CN", languages: ["zh-CN"], platform: "Win32", webdriver: false, plugins: [], mimeTypes: [], cookieEnabled: true, hardwareConcurrency: 8 },
  location: { href: "https://www.spiderdemo.cn/", origin: "https://www.spiderdemo.cn", protocol: "https:", host: "www.spiderdemo.cn", hostname: "www.spiderdemo.cn", pathname: "/", search: "", hash: "" },
  document: { cookie: "", createElement() { return { style: {} }; }, getElementById() { return null; }, addEventListener() {}, documentElement: {}, body: {}, head: {} },
  addEventListener() {},
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, "vendors.min.js"), "utf8"), sandbox, { filename: "vendors.min.js" });
vm.runInContext(fs.readFileSync(path.join(root, "wlzshield.min.js"), "utf8"), sandbox, { filename: "wlzshield.min.js" });
const inst = sandbox.WlzShield.instance;
const mods = inst.modules || {};
note("module-keys " + Object.keys(mods).join(","));
for (const [key, value] of Object.entries(mods)) {
  if (!value || typeof value !== "object") {
    note(key + " " + typeof value);
    continue;
  }
  note(key + " " + Object.keys(value).slice(0, 25).join(","));
}
note("behavior " + (Array.isArray(inst.behaviorLog) ? inst.behaviorLog.length : typeof inst.behaviorLog));
note("seed-type " + typeof inst.seed);
note("session-type " + typeof inst.sessionId + " device-type " + typeof inst.deviceId);
note("first-type " + typeof inst.first + " consumed " + inst.isConsumed);
fs.writeFileSync(path.join(root, "_modules_log.txt"), logs.join("\n"), "utf8");
process.exit(0);
