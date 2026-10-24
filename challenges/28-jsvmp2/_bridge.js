"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const readline = require("readline");

function emit(message) {
  fs.writeSync(1, JSON.stringify(message) + "\n");
}

function publicMsg(data) {
  if (!data || typeof data !== "object") return data;
  const out = {};
  for (const [key, value] of Object.entries(data)) {
    if (/seed|token|cookie|password/i.test(key)) continue;
    out[key] = value && typeof value === "object" ? publicMsg(value) : value;
  }
  return out;
}

class FakeWS {
  constructor(url) {
    this.url = String(url);
    this.readyState = 0;
    this.binaryType = "blob";
    FakeWS.current = this;
    emit({ op: "open", url: this.url });
    queueMicrotask(() => {
      if (this.readyState !== 0) return;
      this.readyState = 1;
      if (typeof this.onopen === "function") this.onopen({ type: "open", target: this });
    });
  }
  send(data) {
    let bytes;
    let binary = true;
    if (typeof data === "string") {
      bytes = Buffer.from(data, "utf8");
      binary = false;
    } else if (data instanceof ArrayBuffer) bytes = Buffer.from(data);
    else if (ArrayBuffer.isView(data)) bytes = Buffer.from(data.buffer, data.byteOffset, data.byteLength);
    else bytes = Buffer.from(String(data), "utf8");
    emit({ op: "send", binary, data: bytes.toString("base64") });
  }
  close() { this.readyState = 3; emit({ op: "ws-close" }); }
  addEventListener(type, fn) { this["on" + type] = fn; }
  removeEventListener() {}
}
FakeWS.current = null;

function openSocket() {
  const ws = FakeWS.current;
  if (!ws || ws.readyState === 1) return;
  ws.readyState = 1;
  if (typeof ws.onopen === "function") ws.onopen({ type: "open", target: ws });
}

function deliverRecv(message) {
  const ws = FakeWS.current;
  if (!ws || typeof ws.onmessage !== "function") return;
  const raw = Buffer.from(message.data, "base64");
  let data = message.binary ? raw : raw.toString("utf8");
  if (message.binary && ws.binaryType === "arraybuffer") {
    data = raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength);
  }
  ws.onmessage({ data, type: "message", target: ws });
}

function makeElement(id) {
  const el = {
    id: id || "",
    style: {},
    className: "",
    value: "",
    disabled: false,
    children: [],
    attributes: {},
    _html: "",
    set innerHTML(value) {
      this._html = String(value);
      const nums = String(value).match(/\d+/g);
      if (id === "numbersGrid" && nums && nums.length) emit({ op: "grid", numbers: nums.map(Number) });
    },
    get innerHTML() { return this._html; },
    set textContent(value) { this.innerHTML = value; },
    get textContent() { return this._html; },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    getAttribute(name) { return this.attributes[name] || null; },
    appendChild(child) { this.children.push(child); return child; },
    removeChild(child) { return child; },
    addEventListener() {},
    removeEventListener() {},
    querySelector() { return makeElement("q"); },
    querySelectorAll() { return []; },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
  };
  return el;
}

const documentStub = {
  cookie: "",
  readyState: "complete",
  visibilityState: "visible",
  hidden: false,
  referrer: "https://www.spiderdemo.cn/",
  title: "T30-WebSocket+jsvmp",
  documentElement: makeElement("html"),
  body: makeElement("body"),
  head: makeElement("head"),
  createElement: (tag) => makeElement(tag),
  getElementById: (id) => makeElement(id),
  querySelector: () => makeElement("q"),
  querySelectorAll: () => [],
  addEventListener(type, fn) {
    if (type === "DOMContentLoaded") queueMicrotask(() => fn({ type }));
  },
  removeEventListener() {},
  createTextNode: (text) => ({ textContent: text }),
  hasFocus: () => true,
};

const locationStub = {
  href: "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge",
  origin: "https://www.spiderdemo.cn",
  protocol: "https:",
  host: "www.spiderdemo.cn",
  hostname: "www.spiderdemo.cn",
  pathname: "/authentication/jsvmp2_challenge/",
  search: "?challenge_type=jsvmp2_challenge",
  hash: "",
  toString() { return this.href; },
};
documentStub.location = locationStub;

function loadWorker() {
  const handlers = [];
  const workerGlobal = {
    console: { log() {}, error() {}, warn() {}, info() {}, debug() {} },
    setTimeout, clearTimeout, setInterval, clearInterval,
    URL, URLSearchParams, TextEncoder, TextDecoder,
    atob: (s) => Buffer.from(String(s), "base64").toString("binary"),
    btoa: (s) => Buffer.from(String(s), "binary").toString("base64"),
    WebSocket: FakeWS,
    crypto: { getRandomValues: (arr) => { require("crypto").webcrypto.getRandomValues(arr); return arr; } },
    performance: { now: () => Date.now(), timeOrigin: Date.now() },
    navigator: { userAgent: "Mozilla/5.0", language: "zh-CN", hardwareConcurrency: 8, webdriver: false, platform: "Win32" },
    location: { href: "https://www.spiderdemo.cn/static/js/authentication/sdk.min.js", origin: "https://www.spiderdemo.cn", protocol: "https:", host: "www.spiderdemo.cn", hostname: "www.spiderdemo.cn", pathname: "/static/js/authentication/sdk.min.js" },
    importScripts() {},
    close() {},
    addEventListener(type, fn) {
      if (type === "message" && typeof fn === "function") {
        handlers.push(fn);
        emit({ op: "worker-listen", n: handlers.length, len: String(fn).length });
      }
    },
    removeEventListener() {},
    postMessage(data) {
      emit({ op: "msg", data: publicMsg(data) });
      const event = { data };
      if (typeof workerStub.onmessage === "function") workerStub.onmessage(event);
      for (const fn of Object.values(workerStub.listeners)) {
        try { fn(event); } catch (err) { emit({ op: "handler-error", message: err.message }); }
      }
    },
  };
  workerGlobal.self = workerGlobal;
  workerGlobal.window = workerGlobal;
  workerGlobal.globalThis = workerGlobal;
  vm.createContext(workerGlobal);
  const source = fs.readFileSync(path.join(__dirname, "assets", "sdk.min.js"), "utf8");
  vm.runInContext(source, workerGlobal, { timeout: 20000 });
  workerStub.handlers = handlers;
  return workerGlobal;
}

const workerStub = {
  listeners: {},
  onmessage: null,
  context: null,
  postMessage(data) {
    const inner = data && data.data;
    emit({
      op: "to-worker",
      type: data && data.type,
      keys: data && typeof data === "object" ? Object.keys(data) : typeof data,
      inner: inner && typeof inner === "object" ? Object.keys(inner) : typeof inner,
      shape: inner && typeof inner === "object" ? Object.fromEntries(Object.entries(inner).map(([key, value]) => [key, Array.isArray(value) ? "array:" + value.length : typeof value === "string" ? "str:" + value.length : typeof value])) : null,
      handlers: (this.handlers || []).length,
    });
    const context = this.context;
    queueMicrotask(() => {
      const started = Date.now();
      emit({ op: "deliver-start" });
      const fn = context && context.onmessage;
      if (typeof fn !== "function") {
        emit({ op: "error", message: "no worker onmessage" });
        return;
      }
      try {
        fn({ data });
        emit({ op: "deliver-done", ms: Date.now() - started, opened: !!(FakeWS.current && FakeWS.current.url) });
      } catch (err) {
        emit({ op: "error", message: "deliver " + err.name + " " + err.message.split("\n")[0], ms: Date.now() - started });
      }
    });
  },
  addEventListener(type, fn) { this.listeners[type] = fn; if (type === "message") this.onmessage = fn; },
  removeEventListener() {},
  terminate() {},
};

const sandbox = {
  version: "Concurrency V2026 WX:Jsvmp6",
  console: { log() {}, error() {}, warn() {}, info() {}, debug() {} },
  setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask,
  atob: (s) => Buffer.from(String(s), "base64").toString("binary"),
  btoa: (s) => Buffer.from(String(s), "binary").toString("base64"),
  alert() {}, confirm: () => true, prompt: () => "",
  requestAnimationFrame: (fn) => setTimeout(() => fn(Date.now()), 16),
  cancelAnimationFrame: clearTimeout,
  getComputedStyle: () => ({}),
  MutationObserver: class { observe() {} disconnect() {} },
  ResizeObserver: class { observe() {} disconnect() {} },
  IntersectionObserver: class { observe() {} disconnect() {} },
  WebSocket: FakeWS,
  document: documentStub,
  location: locationStub,
  navigator: {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    webdriver: false, language: "zh-CN", languages: ["zh-CN", "zh"], platform: "Win32",
    hardwareConcurrency: 8, deviceMemory: 8, plugins: { length: 0 }, mimeTypes: { length: 0 },
    cookieEnabled: true, onLine: true, maxTouchPoints: 0, vendor: "Google Inc.",
  },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {}, length: 0 },
  sessionStorage: { getItem: () => null, setItem() {}, removeItem() {}, length: 0 },
  history: { length: 1, state: null, pushState() {}, replaceState() {} },
  screen: { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24 },
  performance: { now: () => Date.now(), timeOrigin: Date.now() },
  crypto: { getRandomValues: (arr) => { require("crypto").webcrypto.getRandomValues(arr); return arr; } },
  URL, URLSearchParams, TextEncoder, TextDecoder,
  Blob: class { constructor(parts, opts) { this.parts = parts || []; this.type = opts && opts.type || ""; } },
  FileReader: class { readAsText() {} addEventListener() {} },
  XMLHttpRequest: class { open() {} setRequestHeader() {} send() {} addEventListener() {} },
  Image: class { set src(value) {} },
  Event: class { constructor(type) { this.type = type; } },
  CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init && init.detail; } },
  Worker: class {
    constructor(url) {
      emit({ op: "worker", url: String(url).slice(0, 80) });
      try {
        if (!workerStub.context) workerStub.context = loadWorker();
        emit({ op: "worker-ok" });
      } catch (err) {
        emit({ op: "error", message: "worker " + err.name + " " + err.message.split("\n")[0] });
        throw err;
      }
      return workerStub;
    }
  },
  fetch: async (url, opts) => {
    const abs = new URL(String(url), "https://www.spiderdemo.cn").toString();
    const method = (opts && opts.method) || "GET";
    emit({ op: "fetch", method, url: abs.split("?")[0] });
    const headers = new Headers(opts && opts.headers || {});
    if (process.env.SPIDER_COOKIE) headers.set("cookie", process.env.SPIDER_COOKIE);
    headers.set("referer", locationStub.href);
    headers.set("origin", "https://www.spiderdemo.cn");
    headers.set("accept", "application/json, text/plain, */*");
    const res = await fetch(abs, { method, headers, body: opts && opts.body });
    const text = await res.text();
    return {
      ok: res.ok,
      status: res.status,
      headers: { get: (name) => res.headers.get(name) },
      json: async () => JSON.parse(text),
      text: async () => text,
      clone() { return this; },
    };
  },
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

const pageSrc = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const expr = pageSrc.split(/\r?\n/).slice(2).join("\n");
try {
  vm.runInContext(expr, sandbox, { timeout: 20000 });
} catch (err) {
  emit({ op: "error", message: err.name + " " + err.message.split("\n")[0] });
}

const rl = readline.createInterface({ input: process.stdin });
rl.on("line", (line) => {
  let message;
  try { message = JSON.parse(line); } catch { return; }
  try {
    if (message.op === "open-ack") openSocket();
    else if (message.op === "recv") deliverRecv(message);
    else if (message.op === "page" && typeof sandbox.changePage === "function") sandbox.changePage(message.page);
    else if (message.op === "submit" && typeof sandbox.submitAnswer === "function") {
      const input = documentStub.getElementById("answerInput");
      input.value = String(message.answer);
      sandbox.submitAnswer();
    }
  } catch (err) {
    emit({ op: "error", message: err.message });
  }
});
process.on("unhandledRejection", (err) => {
  emit({ op: "error", message: "reject " + (err && err.message ? err.message.split("\n")[0] : err) });
});
emit({ op: "bridge-ready", changePage: typeof sandbox.changePage, submit: typeof sandbox.submitAnswer });
