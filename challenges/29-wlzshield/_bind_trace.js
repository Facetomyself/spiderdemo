const fs = require("fs");
const vm = require("vm");
const path = require("path");

const root = __dirname;
const logs = [];
const note = (line) => logs.push(String(line).slice(0, 400));

const sandbox = {
  console: { log() {}, info() {}, warn() {}, error(...args) { note("err " + args.join(" ")); }, debug() {} },
  setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask,
  URL, URLSearchParams, TextEncoder, TextDecoder,
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: globalThis.crypto,
  performance: { now: () => Date.now() },
  navigator: { userAgent: "Mozilla/5.0", language: "zh-CN", languages: ["zh-CN"], platform: "Win32", webdriver: false, plugins: [], mimeTypes: [], cookieEnabled: true, hardwareConcurrency: 8 },
  location: { href: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge", origin: "https://www.spiderdemo.cn", protocol: "https:", host: "www.spiderdemo.cn", hostname: "www.spiderdemo.cn", pathname: "/captcha/wlzshield_captcha_challenge", search: "" },
  document: {
    cookie: "",
    documentElement: {},
    body: {},
    head: {},
    createElement: () => ({ style: {}, appendChild() {}, setAttribute() {}, addEventListener() {}, getContext: () => null }),
    getElementById: () => ({ style: {}, appendChild() {}, innerHTML: "" }),
    querySelector: () => ({ style: {}, appendChild() {}, innerHTML: "" }),
    addEventListener() {},
  },
  addEventListener() {},
  fetch: async () => ({ ok: false, status: 0, json: async () => ({}), text: async () => "" }),
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(`
Function.prototype.bind = new Proxy(Function.prototype.bind, {
  apply(target, thisArg, args) {
    if (typeof thisArg !== "function") {
      const stack = new Error("bind").stack.split("\\n").slice(1, 4).join(" | ");
      throw new TypeError("BIND_TARGET " + Object.prototype.toString.call(thisArg) + " " + stack);
    }
    return Reflect.apply(target, thisArg, args);
  }
});
`, sandbox);
function load(name) {
  vm.runInContext(fs.readFileSync(path.join(root, name), "utf8"), sandbox, { filename: name });
}
try {
  load("vendors.min.js");
  load("wlzshield.min.js");
  note("loaded " + sandbox.WlzShield.version);
  const widget = new sandbox.WlzShield.CheckboxCaptcha({
    siteKey: "9d4295076aaef0b4c16e18e4f53b5120",
    containerId: "#login-captcha",
    onSuccess() {},
    onFailure() {},
    onError() {},
  });
  note("widget-ok " + typeof widget);
} catch (error) {
  note(String(error && error.stack || error).split("\n").slice(0, 10).join(" | "));
}
fs.writeFileSync(path.join(root, "_bind_log.txt"), logs.join("\n"), "utf8");
process.exit(0);
