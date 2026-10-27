const fs = require("fs");
const vm = require("vm");
const path = require("path");
const https = require("https");
const { URL } = require("url");

const root = __dirname;
const logs = [];
const note = (line) => logs.push(String(line).slice(0, 500));
process.on("uncaughtException", (error) => note("uncaught " + String(error && error.stack || error).split("\n").slice(0, 4).join(" | ")));
process.on("unhandledRejection", (error) => note("reject " + String(error && error.message || error).slice(0, 240)));

function makeNode() {
  const node = {
    style: {},
    children: [],
    childNodes: [],
    attributes: {},
    dataset: {},
    classList: { add() {}, remove() {}, contains() { return false; }, toggle() {} },
    _listeners: {},
    appendChild(child) { this.children.push(child); return child; },
    removeChild(child) { return child; },
    insertBefore(child) { return this.appendChild(child); },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    getAttribute(name) { return this.attributes[name] || null; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(type, fn) { this._listeners[type] = fn; },
    removeEventListener() {},
    dispatchEvent(event) {
      const fn = this._listeners[event && event.type];
      if (typeof fn === "function") fn(event);
      return true;
    },
    getBoundingClientRect() { return { x: 8, y: 8, width: 300, height: 60, top: 8, left: 8, right: 308, bottom: 68 }; },
    querySelector() { return makeNode(); },
    querySelectorAll() { return []; },
    getContext() {
      return new Proxy({}, { get: () => () => {} });
    },
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

function shapeOf(body) {
  if (!body) return "empty";
  const text = typeof body === "string" ? body : Buffer.from(body).toString("utf8");
  try {
    const parsed = JSON.parse(text);
    if (!parsed || typeof parsed !== "object") return "scalar";
    return Object.keys(parsed).map((key) => {
      const value = parsed[key];
      const kind = value == null ? "null" : Array.isArray(value) ? "arr" + value.length : typeof value;
      const size = value == null ? 0 : String(value).length;
      return key + ":" + kind + ":" + size;
    }).join(",");
  } catch (_error) {
    return "raw:" + text.length;
  }
}

function responseShape(text) {
  try {
    const parsed = JSON.parse(text);
    const keys = parsed && typeof parsed === "object" ? Object.keys(parsed) : [];
    const msg = parsed && (parsed.msg || parsed.message || parsed.error) || "";
    const tokenLen = parsed && parsed.wsToken ? String(parsed.wsToken).length : 0;
    return "keys " + keys.join(",") + " msg " + String(msg).slice(0, 40) + " tokenlen " + tokenLen;
  } catch (_error) {
    return "raw " + String(text).length;
  }
}

function request(method, url, body, headers, done) {
  note("http " + method + " " + url + " " + shapeOf(body));
  let parsed;
  try { parsed = new URL(url); } catch (error) { note("bad-url " + url); done(0, ""); return; }
  const lib = parsed.protocol === "http:" ? require("http") : https;
  const req = lib.request({
    protocol: parsed.protocol,
    hostname: parsed.hostname,
    port: parsed.port || (parsed.protocol === "http:" ? 80 : 443),
    path: parsed.pathname + parsed.search,
    method,
    headers: Object.assign({ "content-type": "application/json", "user-agent": "Mozilla/5.0" }, headers || {}),
  }, (res) => {
    const chunks = [];
    res.on("data", (chunk) => chunks.push(chunk));
    res.on("end", () => {
      const text = Buffer.concat(chunks).toString("utf8");
      note("status " + res.statusCode + " " + responseShape(text));
      done(res.statusCode, text);
    });
  });
  req.on("error", (error) => { note("http-error " + error.message); done(0, ""); });
  if (body) req.write(typeof body === "string" ? body : Buffer.from(body));
  req.end();
}

const sandbox = {
  console: {
    log: (...args) => note("log " + args.map((item) => typeof item === "string" ? item.slice(0, 160) : typeof item).join(" ")),
    info() {}, debug() {},
    warn: (...args) => note("warn " + args.join(" ").slice(0, 200)),
    error: (...args) => note("error " + args.join(" ").slice(0, 240)),
  },
  setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask,
  requestAnimationFrame(fn) { return setTimeout(() => fn(Date.now()), 16); },
  cancelAnimationFrame(id) { clearTimeout(id); },
  URL, URLSearchParams, TextEncoder, TextDecoder,
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: globalThis.crypto,
  performance: { now: () => Date.now(), timeOrigin: Date.now(), getEntriesByType: () => [] },
  navigator: {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    language: "zh-CN", languages: ["zh-CN", "zh"], platform: "Win32", vendor: "Google Inc.",
    webdriver: false, hardwareConcurrency: 8, deviceMemory: 8, cookieEnabled: true,
    maxTouchPoints: 0, onLine: true, plugins: { length: 0, item() { return null; } },
    mimeTypes: { length: 0 }, appVersion: "5.0 (Windows NT 10.0; Win64; x64)", product: "Gecko", productSub: "20030107",
  },
  location: {
    href: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge?challenge_type=wlzshield_captcha_challenge",
    origin: "https://www.spiderdemo.cn", protocol: "https:", host: "www.spiderdemo.cn",
    hostname: "www.spiderdemo.cn", pathname: "/captcha/wlzshield_captcha_challenge",
    search: "?challenge_type=wlzshield_captcha_challenge", hash: "",
  },
  screen: { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24 },
  innerWidth: 1920, innerHeight: 1080, outerWidth: 1920, outerHeight: 1040, devicePixelRatio: 1,
  localStorage: { getItem() { return null; }, setItem() {}, removeItem() {}, key() { return null; }, length: 0 },
  sessionStorage: { getItem() { return null; }, setItem() {}, removeItem() {}, key() { return null; }, length: 0 },
  history: { length: 2, pushState() {}, replaceState() {} },
  matchMedia: () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {} }),
  getComputedStyle: () => new Proxy({}, { get: () => "" }),
  addEventListener() {}, removeEventListener() {}, postMessage() {},
};
const box = makeNode();
box.id = "login-captcha";
sandbox.document = {
  cookie: "", readyState: "complete", visibilityState: "visible", hidden: false,
  characterSet: "UTF-8", compatMode: "CSS1Compat", title: "T31",
  documentElement: makeNode(), body: makeNode(), head: makeNode(),
  createElement: () => makeNode(),
  createElementNS: () => makeNode(),
  getElementById: (id) => (id === "login-captcha" ? box : makeNode()),
  querySelector: (sel) => (sel === "#login-captcha" ? box : makeNode()),
  querySelectorAll: () => [],
  getElementsByTagName: () => [],
  addEventListener() {}, removeEventListener() {},
  createEvent() { return { initEvent() {} }; },
  hasFocus() { return true; },
  elementFromPoint() { return box; },
};
sandbox.fetch = (url, options = {}) => new Promise((resolve) => {
  request(options.method || "GET", String(url), options.body, options.headers, (status, text) => {
    resolve({
      ok: status >= 200 && status < 300,
      status,
      headers: { get() { return null; } },
      json: async () => { try { return JSON.parse(text); } catch (_e) { return {}; } },
      text: async () => text,
      arrayBuffer: async () => Buffer.from(text),
    });
  });
});
function XMLHttpRequest() {
  this.readyState = 0;
  this.status = 0;
  this.responseText = "";
  this.response = "";
  this._headers = {};
  this.onreadystatechange = null;
  this.onload = null;
  this.onerror = null;
}
XMLHttpRequest.prototype.open = function open(method, url) { this._method = method; this._url = url; note("xhr " + method + " " + url); };
XMLHttpRequest.prototype.setRequestHeader = function setRequestHeader(name, value) { this._headers[name] = value; };
XMLHttpRequest.prototype.getResponseHeader = function getResponseHeader() { return null; };
XMLHttpRequest.prototype.addEventListener = function addEventListener(type, fn) { this["on" + type] = fn; };
XMLHttpRequest.prototype.abort = function abort() {};
XMLHttpRequest.prototype.send = function send(body) {
  request(this._method || "GET", this._url, body, this._headers, (status, text) => {
    this.status = status;
    this.readyState = 4;
    this.responseText = text;
    this.response = text;
    if (typeof this.onreadystatechange === "function") this.onreadystatechange();
    if (status && typeof this.onload === "function") this.onload();
    if (!status && typeof this.onerror === "function") this.onerror();
  });
};
sandbox.XMLHttpRequest = XMLHttpRequest;
sandbox.Image = function Image() { this.addEventListener = () => {}; };
sandbox.MutationObserver = function MutationObserver() { this.observe = () => {}; this.disconnect = () => {}; };
sandbox.IntersectionObserver = function IntersectionObserver() { this.observe = () => {}; this.disconnect = () => {}; };
sandbox.ResizeObserver = function ResizeObserver() { this.observe = () => {}; this.disconnect = () => {}; };
sandbox.Worker = function Worker() { this.postMessage = () => {}; this.terminate = () => {}; };
sandbox.WebSocket = function WebSocket() { this.send = () => {}; this.close = () => {}; this.addEventListener = () => {}; };
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;
vm.createContext(sandbox);

vm.runInContext(fs.readFileSync(path.join(root, "vendors.min.js"), "utf8"), sandbox, { filename: "vendors.min.js" });
vm.runInContext(fs.readFileSync(path.join(root, "wlzshield.min.js"), "utf8"), sandbox, { filename: "wlzshield.min.js" });
const seen = new Set();
const cache = Object.create(null);
const originalProto = Object.getPrototypeOf(sandbox);
const fallback = new Proxy(originalProto, {
  get(target, prop, receiver) {
    const value = Reflect.get(target, prop, receiver);
    if (value !== undefined || typeof prop !== "string" || prop === "then") return value;
    if (!Object.prototype.hasOwnProperty.call(cache, prop)) {
      if (seen.size < 60) note("fallback " + prop);
      seen.add(prop);
      const fn = function dummy() { return cache[prop]; };
      cache[prop] = fn;
    }
    return cache[prop];
  },
});
Object.setPrototypeOf(sandbox, fallback);
note("version " + sandbox.WlzShield.version);
let widget;
try {
  widget = new sandbox.WlzShield.CheckboxCaptcha({
    siteKey: "9d4295076aaef0b4c16e18e4f53b5120",
    containerId: "#login-captcha",
    width: 300,
    height: 60,
    challengeUrl: "https://captcha.wangluozhe.com/api/challenge",
    onSuccess(data) {
      const keys = data && typeof data === "object" ? Object.keys(data).join(",") : typeof data;
      note("success " + keys + " tokenlen " + (data && data.wsToken ? String(data.wsToken).length : 0));
    },
    onFailure(data) { note("failure " + JSON.stringify(data).slice(0, 200)); },
    onError(data) { note("onerror " + (data && data.message ? data.message : JSON.stringify(data).slice(0, 200))); },
  });
  note("constructed");
  const names = [];
  let cursor = widget;
  while (cursor && cursor !== Object.prototype && cursor !== Function.prototype) {
    for (const name of Object.getOwnPropertyNames(cursor)) {
      if (typeof widget[name] === "function") names.push(name);
    }
    cursor = Object.getPrototypeOf(cursor);
  }
  note("methods " + names.join(","));
} catch (error) {
  note("construct-fail " + String(error && error.stack || error).split("\n").slice(0, 8).join(" | "));
}

setTimeout(() => {
  if (box._listeners.click) {
    note("click");
    try { box._listeners.click({ type: "click", target: box, preventDefault() {}, stopPropagation() {} }); } catch (error) { note("click-fail " + error.message); }
  } else {
    note("listeners " + Object.keys(box._listeners).join(","));
    note("children " + box.children.length);
  }
  if (widget && typeof widget.startVerification === "function") {
    try { widget.startVerification(); note("started"); } catch (error) { note("start-fail " + error.message); }
  }
}, 800);

setTimeout(() => {
  fs.writeFileSync(path.join(root, "_env_log.txt"), logs.join("\n"), "utf8");
  process.exit(0);
}, 12000);
