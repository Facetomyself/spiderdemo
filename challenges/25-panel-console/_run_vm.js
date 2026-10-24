const fs = require("fs");
const path = require("path");

let source = fs.readFileSync(path.join(__dirname, "static__js__check_devtools_jsvmp.js"), "utf8");
source = source.replace(
  "return Cr[gm]=eN(nB)",
  "var __s=eN(nB);try{globalThis.__STRS.push(String(__s))}catch(e){}return Cr[gm]=__s"
);
globalThis.__STRS = [];
const logs = [];
const note = (kind, value) => logs.push(kind + " " + String(value).slice(0, 500));

let inspecting = false;
function inspectLikeDevtools(value) {
  if (inspecting || value == null || (typeof value !== "object" && typeof value !== "function")) return;
  inspecting = true;
  try {
    for (const name of ["id", "className", "name", "message", "stack"]) {
      try { void value[name]; } catch (error) { note("INSPECT_ERR", name + " " + error.message); }
    }
    for (const name of Object.getOwnPropertyNames(value).slice(0, 40)) {
      const desc = Object.getOwnPropertyDescriptor(value, name);
      if (desc && typeof desc.get === "function") {
        try { note("READ", name + "=" + String(value[name]).slice(0, 300)); }
        catch (error) { note("READ_ERR", name + " " + error.message); }
      }
    }
  } finally {
    inspecting = false;
  }
}

function makeConsole(label) {
  const target = {};
  for (const name of ["log", "debug", "info", "warn", "error", "table", "clear", "dir", "trace", "group", "groupCollapsed", "groupEnd"]) {
    target[name] = (...args) => {
      note("C." + label + "." + name, args.map((item) => {
        if (typeof item === "string") return item;
        try { return Object.prototype.toString.call(item); } catch (error) { return "?"; }
      }).join(" | "));
      for (const arg of args) inspectLikeDevtools(arg);
    };
  }
  return target;
}

function storage() {
  return { getItem() { return null; }, setItem() {}, removeItem() {}, clear() {}, key() { return null; }, length: 0 };
}

let tick = 1000;
function now() { tick += 150; return tick; }

function makeWindow(parent) {
  const win = function Window() {};
  win.window = win;
  win.self = win;
  win.top = parent ? parent.top : win;
  win.parent = parent || win;
  win.console = makeConsole(parent ? "frame" : "main");
  win.document = null;
  win.navigator = {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    language: "zh-CN",
    languages: ["zh-CN"],
    platform: "Win32",
    webdriver: false,
    hardwareConcurrency: 8,
    deviceMemory: 8,
    plugins: { length: 5 },
    mimeTypes: { length: 2 },
    vendor: "Google Inc.",
    maxTouchPoints: 0,
  };
  win.location = {
    href: "about:blank",
    replace(url) { note("REPLACE", url); },
    assign(url) { note("ASSIGN", url); },
  };
  win.localStorage = storage();
  win.sessionStorage = storage();
  win.performance = { now };
  win.outerWidth = 1600;
  win.innerWidth = 900;
  win.outerHeight = 1200;
  win.innerHeight = 500;
  win.devicePixelRatio = 1;
  win.chrome = { runtime: {} };
  win.screen = { width: 1920, height: 1080, colorDepth: 24 };
  win.history = { go() {}, back() {}, pushState() {}, replaceState() {} };
  win.HTMLElement = function HTMLElement() {};
  win.HTMLIFrameElement = function HTMLIFrameElement() {};
  win.Element = function Element() {};
  win.Node = function Node() {};
  win.Event = function Event(type) { this.type = type; };
  win.Error = Error;
  win.Promise = Promise;
  win.Object = Object;
  win.Array = Array;
  win.Function = Function;
  win.Symbol = Symbol;
  win.Date = Date;
  win.Math = Math;
  win.RegExp = RegExp;
  win.JSON = JSON;
  win.atob = (value) => Buffer.from(String(value), "base64").toString("binary");
  win.btoa = (value) => Buffer.from(String(value), "binary").toString("base64");
  win.alert = (message) => note("ALERT", message);
  win.addEventListener = (type, fn) => {
    note("ON", (parent ? "frame:" : "main:") + type);
    (win.__on || (win.__on = {}))[type] = fn;
  };
  win.removeEventListener = () => {};
  win.postMessage = (data) => {
    note("POST", typeof data === "string" ? data : JSON.stringify(data));
    const host = parent || win;
    const listener = host.__on && host.__on.message;
    if (listener) setTimeout(() => listener({ data, source: win }), 0);
  };
  win.requestAnimationFrame = (fn) => setTimeout(() => fn(now()), 16);
  win.setTimeout = setTimeout;
  win.clearTimeout = clearTimeout;
  win.setInterval = setInterval;
  win.clearInterval = clearInterval;
  win.Image = function Image() { return createElement("img", win); };
  win.getComputedStyle = () => ({ getPropertyValue() { return ""; } });
  win.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
  win.document = makeDocument(win);
  return win;
}

function createElement(tag, owner) {
  const node = {
    tagName: String(tag || "").toUpperCase(),
    style: {},
    id: "",
    className: "",
    innerHTML: "",
    textContent: "",
    children: [],
    setAttribute(name, value) { this[name] = value; },
    getAttribute(name) { return this[name] == null ? null : String(this[name]); },
    appendChild(child) { this.children.push(child); if (owner && owner.document && owner.document.body) return child; return child; },
    removeChild() {},
    addEventListener() {},
    removeEventListener() {},
    contains() { return false; },
    classList: { add() {}, remove() {}, contains() { return false; } },
  };
  if (String(tag).toLowerCase() === "iframe") {
    node.contentWindow = makeWindow(owner);
    node.contentDocument = node.contentWindow.document;
    Object.defineProperty(node, "srcdoc", {
      configurable: true,
      get() { return this.__srcdoc || ""; },
      set(value) {
        this.__srcdoc = String(value);
        note("SRCDOC", String(value).slice(0, 80));
        const match = String(value).match(/<script>([\s\S]*?)<\/script>/);
        if (match) setTimeout(() => runFrame(match[1], node.contentWindow), 0);
      },
    });
  }
  return node;
}

function makeDocument(win) {
  const body = createElement("body", win);
  return {
    readyState: "complete",
    hidden: false,
    visibilityState: "visible",
    body,
    head: createElement("head", win),
    documentElement: createElement("html", win),
    cookie: "",
    createElement(tag) { return createElement(tag, win); },
    getElementById() { return createElement("div", win); },
    querySelector() { return body; },
    querySelectorAll() { return []; },
    addEventListener(type, fn) {
      note("DOC_ON", type);
      if (type === "DOMContentLoaded") setTimeout(fn, 0);
    },
    removeEventListener() {},
    createEvent() { return { initEvent() {} }; },
    open() {},
    write() {},
    close() {},
    appendChild(child) { return child; },
  };
}

function runFrame(code, frameWindow) {
  const patched = code.replace(
    "return Gc[Js]=YA(AE)",
    "var __s=YA(AE);try{globalThis.__STRS.push(String(__s))}catch(e){}return Gc[Js]=__s"
  );
  try {
    const runner = new Function("frame", "with (frame) {\n" + patched + "\n}");
    runner(frameWindow);
    note("FRAME", "ok");
  } catch (error) {
    note("FRAME_ERR", error && error.stack ? error.stack.split("\n").slice(0, 4).join(" | ") : String(error));
  }
}

const root = makeWindow(null);
root.location.href = "https://www.spiderdemo.cn/authentication/panel_challenge/?challenge_type=panel_challenge";
root.location.pathname = "/authentication/panel_challenge/";
root.location.search = "?challenge_type=panel_challenge";
globalThis.window = globalThis;
globalThis.self = globalThis;
globalThis.top = globalThis;
globalThis.parent = globalThis;
globalThis.console = root.console;
globalThis.document = root.document;
globalThis.navigator = root.navigator;
globalThis.location = root.location;
globalThis.localStorage = root.localStorage;
globalThis.sessionStorage = root.sessionStorage;
globalThis.performance = root.performance;
globalThis.outerWidth = root.outerWidth;
globalThis.innerWidth = root.innerWidth;
globalThis.outerHeight = root.outerHeight;
globalThis.innerHeight = root.innerHeight;
globalThis.chrome = root.chrome;
globalThis.HTMLElement = root.HTMLElement;
globalThis.HTMLIFrameElement = root.HTMLIFrameElement;
globalThis.Image = root.Image;
globalThis.addEventListener = root.addEventListener.bind(root);
root.__on = {};
globalThis.__on = root.__on;
globalThis.postMessage = root.postMessage;
globalThis.history = root.history;
globalThis.screen = root.screen;

const savedInterval = global.setInterval;
const savedTimeout = global.setTimeout;
global.setInterval = (fn, ms, ...args) => {
  note("SET_INTERVAL", ms);
  let count = 0;
  return savedInterval(() => {
    count += 1;
    if (count > 6) return;
    try { fn(...args); }
    catch (error) { note("INTERVAL_ERR", error.stack ? error.stack.split("\n")[0] : String(error)); }
  }, 15);
};
global.setTimeout = (fn, ms, ...args) => {
  note("SET_TIMEOUT", ms);
  return savedTimeout(() => {
    try { fn(...args); }
    catch (error) { note("TIMEOUT_ERR", error.stack ? error.stack.split("\n").slice(0, 3).join(" | ") : String(error)); }
  }, Math.min(Number(ms) || 0, 50));
};
globalThis.setTimeout = global.setTimeout;
globalThis.setInterval = global.setInterval;

try {
  eval(source);
  note("EVAL", "ok strings=" + globalThis.__STRS.length);
} catch (error) {
  note("EVAL_ERR", error.stack ? error.stack.split("\n").slice(0, 6).join(" | ") : String(error));
}

savedTimeout(() => {
  const unique = [...new Set(globalThis.__STRS)];
  fs.writeFileSync(path.join(__dirname, "vm-run.json"), JSON.stringify({ unique, logs }, null, 2));
  process.stdout.write("strings " + unique.length + " logs " + logs.length + "\n");
  for (const line of logs) process.stdout.write(line.slice(0, 360) + "\n");
  process.stdout.write("---ODD STRINGS---\n");
  for (const item of unique) {
    if (item.length > 18 && !item.startsWith("\n") && item.length < 300) process.stdout.write("S " + item + "\n");
  }
  process.exit(0);
}, 1500);
