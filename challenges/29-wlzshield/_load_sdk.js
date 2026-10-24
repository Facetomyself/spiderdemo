const fs = require("fs");
const vm = require("vm");
const path = require("path");

const root = __dirname;
const logs = [];

function element(tag) {
  return {
    tagName: String(tag || "div").toUpperCase(),
    style: {},
    children: [],
    attributes: {},
    classList: { add() {}, remove() {}, contains() { return false; } },
    appendChild(node) { this.children.push(node); return node; },
    removeChild(node) { this.children = this.children.filter((item) => item !== node); return node; },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    getAttribute(name) { return this.attributes[name] || null; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener() {},
    removeEventListener() {},
    getContext() { return null; },
    getBoundingClientRect() { return { x: 0, y: 0, width: 300, height: 60, top: 0, left: 0, right: 300, bottom: 60 }; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    innerHTML: "",
    textContent: "",
    id: "",
    width: 300,
    height: 150,
  };
}

const document = {
  cookie: "",
  readyState: "complete",
  visibilityState: "visible",
  hidden: false,
  documentElement: element("html"),
  body: element("body"),
  head: element("head"),
  createElement: element,
  createElementNS: (_ns, tag) => element(tag),
  getElementById(id) {
    if (id === "login-captcha") return element("div");
    return null;
  },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  removeEventListener() {},
  createEvent() { return { initEvent() {} }; },
};

const sandbox = {
  console,
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  queueMicrotask,
  URL,
  URLSearchParams,
  TextEncoder,
  TextDecoder,
  atob: (value) => Buffer.from(value, "base64").toString("binary"),
  btoa: (value) => Buffer.from(value, "binary").toString("base64"),
  crypto: globalThis.crypto,
  performance: { now: () => Date.now(), timeOrigin: Date.now() },
  navigator: {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    language: "zh-CN",
    languages: ["zh-CN", "zh"],
    platform: "Win32",
    hardwareConcurrency: 8,
    deviceMemory: 8,
    webdriver: false,
    plugins: [],
    mimeTypes: [],
    cookieEnabled: true,
    maxTouchPoints: 0,
  },
  location: {
    href: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge?challenge_type=wlzshield_captcha_challenge",
    origin: "https://www.spiderdemo.cn",
    protocol: "https:",
    host: "www.spiderdemo.cn",
    hostname: "www.spiderdemo.cn",
    pathname: "/captcha/wlzshield_captcha_challenge",
    search: "?challenge_type=wlzshield_captcha_challenge",
  },
  document,
  screen: { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24 },
  innerWidth: 1920,
  innerHeight: 1080,
  devicePixelRatio: 1,
  fetch: async (url, options) => {
    logs.push("fetch " + url);
    return { ok: false, status: 0, json: async () => ({}), text: async () => "" };
  },
  XMLHttpRequest: function XMLHttpRequest() {
    this.readyState = 0;
    this.status = 0;
    this.responseText = "";
    this.open = (method, url) => { logs.push("xhr " + method + " " + url); };
    this.setRequestHeader = () => {};
    this.send = () => { logs.push("xhr-send"); };
    this.addEventListener = () => {};
  },
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;
vm.createContext(sandbox);

function load(name) {
  const code = fs.readFileSync(path.join(root, name), "utf8");
  vm.runInContext(code, sandbox, { filename: name, timeout: 20000 });
}

try {
  load("vendors.min.js");
  logs.push("vendors-ok");
  load("wlzshield.min.js");
  logs.push("sdk-ok");
} catch (error) {
  logs.push("load-error " + error.name + " " + String(error.message).slice(0, 300));
  logs.push(String(error.stack || "").split("\n").slice(0, 8).join(" | "));
}

const shield = sandbox.WlzShield;
logs.push("type " + typeof shield);
if (shield && typeof shield === "object") {
  logs.push("keys " + Object.keys(shield).slice(0, 40).join(","));
  for (const key of Object.keys(shield)) {
    logs.push("member " + key + " " + typeof shield[key]);
  }
}
fs.writeFileSync(path.join(root, "_load_log.txt"), logs.join("\n"), "utf8");
