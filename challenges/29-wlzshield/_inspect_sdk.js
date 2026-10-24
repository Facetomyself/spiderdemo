const fs = require("fs");
const vm = require("vm");
const path = require("path");

const root = __dirname;
const logs = [];
const note = (line) => logs.push(String(line));

function element(tag) {
  const node = {
    tagName: String(tag || "div").toUpperCase(),
    style: {},
    children: [],
    childNodes: [],
    attributes: {},
    className: "",
    classList: {
      add() {},
      remove() {},
      contains() { return false; },
      toggle() {},
    },
    dataset: {},
    appendChild(child) { node.children.push(child); node.childNodes.push(child); return child; },
    removeChild(child) {
      node.children = node.children.filter((item) => item !== child);
      return child;
    },
    insertBefore(child) { return node.appendChild(child); },
    setAttribute(name, value) { node.attributes[name] = String(value); },
    getAttribute(name) { return Object.prototype.hasOwnProperty.call(node.attributes, name) ? node.attributes[name] : null; },
    removeAttribute(name) { delete node.attributes[name]; },
    addEventListener(type, fn) { node._listeners[type] = fn; },
    removeEventListener() {},
    dispatchEvent(event) {
      const fn = node._listeners[event.type];
      if (fn) fn(event);
      return true;
    },
    _listeners: {},
    getContext() {
      return {
        fillRect() {},
        clearRect() {},
        getImageData() { return { data: new Uint8ClampedArray(16) }; },
        putImageData() {},
        measureText() { return { width: 12 }; },
        fillText() {},
        beginPath() {},
        arc() {},
        fill() {},
        stroke() {},
        moveTo() {},
        lineTo() {},
        canvas: node,
      };
    },
    getBoundingClientRect() {
      return { x: 0, y: 0, width: 300, height: 60, top: 0, left: 0, right: 300, bottom: 60 };
    },
    querySelector() { return element("div"); },
    querySelectorAll() { return []; },
    getElementsByTagName() { return []; },
    innerHTML: "",
    textContent: "",
    id: "",
    width: 300,
    height: 60,
    offsetWidth: 300,
    offsetHeight: 60,
    clientWidth: 300,
    clientHeight: 60,
  };
  return node;
}

const captchaBox = element("div");
captchaBox.id = "login-captcha";

const document = {
  cookie: "",
  readyState: "complete",
  visibilityState: "visible",
  hidden: false,
  characterSet: "UTF-8",
  compatMode: "CSS1Compat",
  documentElement: element("html"),
  body: element("body"),
  head: element("head"),
  createElement: element,
  createElementNS: (_ns, tag) => element(tag),
  getElementById(id) { return id === "login-captcha" ? captchaBox : element("div"); },
  querySelector(sel) { return sel === "#login-captcha" ? captchaBox : element("div"); },
  querySelectorAll() { return []; },
  getElementsByTagName() { return []; },
  addEventListener() {},
  removeEventListener() {},
  createEvent() { return { initEvent() {} }; },
  hasFocus() { return true; },
};

function summarizeBody(body) {
  if (body == null) return "empty";
  const text = typeof body === "string" ? body : Buffer.from(body).toString("utf8");
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return "json-keys " + Object.keys(parsed).join(",");
    }
  } catch (_error) {}
  return "len " + text.length;
}

const sandbox = {
  console: {
    log: (...args) => note("console " + args.map((item) => typeof item === "string" ? item.slice(0, 180) : typeof item).join(" ")),
    info() {},
    warn: (...args) => note("warn " + args.map((item) => String(item).slice(0, 180)).join(" ")),
    error: (...args) => note("error " + args.map((item) => String(item).slice(0, 240)).join(" ")),
    debug() {},
  },
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  queueMicrotask,
  requestAnimationFrame(fn) { return setTimeout(() => fn(Date.now()), 16); },
  cancelAnimationFrame: clearTimeout,
  URL,
  URLSearchParams,
  TextEncoder,
  TextDecoder,
  Blob: class Blob { constructor(parts, options) { this.parts = parts; this.type = options && options.type; } },
  File: class File { constructor(parts, name) { this.parts = parts; this.name = name; } },
  FormData: class FormData {
    constructor() { this._pairs = []; }
    append(key) { this._pairs.push(key); }
    keys() { return this._pairs; }
  },
  Headers: class Headers { constructor() {} },
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: globalThis.crypto,
  performance: { now: () => Number(process.hrtime.bigint()) / 1e6, timeOrigin: Date.now() },
  navigator: {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    appVersion: "5.0",
    language: "zh-CN",
    languages: ["zh-CN", "zh", "en"],
    platform: "Win32",
    vendor: "Google Inc.",
    hardwareConcurrency: 8,
    deviceMemory: 8,
    webdriver: false,
    plugins: { length: 0 },
    mimeTypes: { length: 0 },
    cookieEnabled: true,
    maxTouchPoints: 0,
    doNotTrack: null,
    product: "Gecko",
    productSub: "20030107",
    onLine: true,
  },
  location: {
    href: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge?challenge_type=wlzshield_captcha_challenge",
    origin: "https://www.spiderdemo.cn",
    protocol: "https:",
    host: "www.spiderdemo.cn",
    hostname: "www.spiderdemo.cn",
    pathname: "/captcha/wlzshield_captcha_challenge",
    search: "?challenge_type=wlzshield_captcha_challenge",
    hash: "",
  },
  history: { length: 1, pushState() {}, replaceState() {} },
  document,
  screen: { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24 },
  innerWidth: 1920,
  innerHeight: 1080,
  outerWidth: 1920,
  outerHeight: 1040,
  devicePixelRatio: 1,
  localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
  sessionStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
  fetch: async (url, options = {}) => {
    note("fetch " + (options.method || "GET") + " " + url + " " + summarizeBody(options.body));
    return {
      ok: false,
      status: 599,
      headers: { get() { return null; } },
      json: async () => ({}),
      text: async () => "",
      arrayBuffer: async () => new ArrayBuffer(0),
    };
  },
  XMLHttpRequest: function XMLHttpRequest() {
    this.readyState = 0;
    this.status = 0;
    this.responseText = "";
    this.response = "";
    this.open = (method, url) => { this._method = method; this._url = url; note("xhr " + method + " " + url); };
    this.setRequestHeader = () => {};
    this.getResponseHeader = () => null;
    this.send = (body) => { note("xhr-send " + summarizeBody(body)); };
    this.addEventListener = () => {};
    this.abort = () => {};
  },
  Image: function Image() { this.addEventListener = () => {}; },
  MutationObserver: function MutationObserver() { this.observe = () => {}; this.disconnect = () => {}; },
  IntersectionObserver: function IntersectionObserver() { this.observe = () => {}; this.disconnect = () => {}; },
  ResizeObserver: function ResizeObserver() { this.observe = () => {}; this.disconnect = () => {}; },
  Worker: function Worker() { throw new Error("worker-blocked"); },
  WebSocket: function WebSocket() { this.addEventListener = () => {}; this.send = () => {}; this.close = () => {}; },
  matchMedia: () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {} }),
  getComputedStyle: () => new Proxy({}, { get: () => "" }),
  addEventListener() {},
  removeEventListener() {},
  postMessage() {},
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;
sandbox.frames = [];
vm.createContext(sandbox);

function load(name) {
  const code = fs.readFileSync(path.join(root, name), "utf8");
  vm.runInContext(code, sandbox, { filename: name });
}

load("vendors.min.js");
load("wlzshield.min.js");
const shield = sandbox.WlzShield;
note("version " + shield.version);
note("instance " + Object.keys(shield.instance || {}).join(","));
const proto = shield.CheckboxCaptcha && shield.CheckboxCaptcha.prototype;
note("checkbox-proto " + (proto ? Object.getOwnPropertyNames(proto).join(",") : "none"));
try {
  const payload = shield.getPayload();
  note("payload-type " + typeof payload);
  if (payload && typeof payload === "object") note("payload-keys " + Object.keys(payload).join(","));
  else note("payload-len " + String(payload).length);
} catch (error) {
  note("payload-error " + error.message);
}
try {
  const collector = shield.initCollector({ siteKey: "9d4295076aaef0b4c16e18e4f53b5120" });
  note("collector " + typeof collector + " " + (collector && Object.keys(collector).slice(0, 20).join(",")));
} catch (error) {
  note("collector-error " + String(error && error.message).slice(0, 240));
}

let widget;
try {
  widget = new shield.CheckboxCaptcha({
    siteKey: "9d4295076aaef0b4c16e18e4f53b5120",
    containerId: "#login-captcha",
    width: 300,
    height: 60,
    onSuccess(result) {
      const keys = result && typeof result === "object" ? Object.keys(result).join(",") : typeof result;
      note("success-keys " + keys);
    },
    onFailure(result) { note("failure " + (result && result.message ? result.message : typeof result)); },
    onError(result) { note("onerror " + (result && result.message ? result.message : String(result).slice(0, 180))); },
  });
  note("widget " + Object.getOwnPropertyNames(widget).slice(0, 30).join(","));
  const methods = [];
  let cursor = widget;
  while (cursor && cursor !== Object.prototype) {
    for (const name of Object.getOwnPropertyNames(cursor)) {
      if (typeof widget[name] === "function" && !methods.includes(name)) methods.push(name);
    }
    cursor = Object.getPrototypeOf(cursor);
  }
  note("methods " + methods.join(","));
} catch (error) {
  note("widget-error " + String(error && error.stack || error).split("\n").slice(0, 6).join(" | "));
}

setTimeout(() => {
  fs.writeFileSync(path.join(root, "_inspect_log.txt"), logs.join("\n"), "utf8");
  process.exit(0);
}, 1500);
