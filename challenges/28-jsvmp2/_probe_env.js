"use strict";

const fs = require("fs");
const path = require("path");

const events = [];
function note(kind, detail) {
  if (events.length > 4000) return;
  events.push(kind + " " + detail);
}

function redact(value) {
  const text = typeof value === "string" ? value : safe(value);
  if (/session|cookie|token|password/i.test(text)) return "[redacted len=" + text.length + "]";
  return text.length > 180 ? text.slice(0, 180) + "…(" + text.length + ")" : text;
}

function safe(value) {
  try {
    if (value === null || value === undefined) return String(value);
    if (typeof value === "function") return "fn " + (value.name || "anon");
    if (typeof value === "string") return JSON.stringify(value);
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    if (Array.isArray(value)) return "array[" + value.length + "]";
    return Object.prototype.toString.call(value);
  } catch (err) {
    return "unprintable";
  }
}

function proxy(label, target) {
  return new Proxy(target, {
    get(obj, prop, receiver) {
      if (prop === "then") return undefined;
      const key = String(prop);
      if (key !== "toJSON" && key !== Symbol.toPrimitive.description && typeof prop !== "symbol") {
        note("get", label + "." + key);
      }
      const value = Reflect.get(obj, prop, receiver);
      if (typeof value === "function") {
        return function (...args) {
          note(
            "call",
            label + "." + key + "(" + args.map((item) => redact(safe(item))).join(", ") + ")"
          );
          return value.apply(this === receiver ? obj : this, args);
        };
      }
      return value;
    },
    set(obj, prop, value) {
      note("set", label + "." + String(prop) + " = " + redact(safe(value)));
      obj[prop] = value;
      return true;
    },
  });
}

class FakeWS {
  constructor(url, protocols) {
    note("ws", "new " + redact(String(url)) + " proto " + redact(safe(protocols)));
    this.url = url;
    this.readyState = 0;
    this.binaryType = "blob";
    FakeWS.instances.push(this);
    setTimeout(() => {
      this.readyState = 1;
      if (typeof this.onopen === "function") this.onopen({ type: "open" });
    }, 0);
  }
  send(data) {
    note("ws-send", redact(typeof data === "string" ? data : safe(data)));
  }
  close() {
    note("ws", "close");
    this.readyState = 3;
  }
  addEventListener(type, fn) {
    note("ws-on", type);
    this["on" + type] = fn;
  }
}
FakeWS.instances = [];
FakeWS.CONNECTING = 0;
FakeWS.OPEN = 1;
FakeWS.CLOSING = 2;
FakeWS.CLOSED = 3;

const elements = new Map();
function makeElement(tag) {
  const el = {
    tagName: String(tag || "").toUpperCase(),
    style: proxy(tag + ".style", {}),
    children: [],
    childNodes: [],
    className: "",
    id: "",
    innerHTML: "",
    textContent: "",
    value: "",
    disabled: false,
    attributes: {},
    setAttribute(name, value) {
      note("dom", "setAttr " + tag + " " + name);
      this.attributes[name] = value;
    },
    getAttribute(name) {
      return this.attributes[name];
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    removeChild(child) {
      return child;
    },
    addEventListener(type) {
      note("dom", "listen " + tag + " " + type);
    },
    removeEventListener() {},
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
    getElementsByTagName() {
      return [];
    },
    getContext() {
      return proxy("canvas", { fillRect() {}, measureText() { return { width: 0 }; }, font: "" });
    },
    toDataURL() {
      return "data:";
    },
  };
  return proxy("el:" + tag, el);
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
  createElementNS: (ns, tag) => makeElement(tag),
  getElementById: (id) => {
    note("dom", "getElementById " + id);
    if (!elements.has(id)) elements.set(id, makeElement(id));
    return elements.get(id);
  },
  querySelector: (sel) => {
    note("dom", "query " + sel);
    return makeElement("q");
  },
  querySelectorAll: () => [],
  getElementsByTagName: () => [],
  getElementsByClassName: () => [],
  addEventListener(type, fn) {
    note("dom", "document listen " + type);
    if (type === "DOMContentLoaded") setTimeout(fn, 0);
  },
  removeEventListener() {},
  createTextNode: (text) => ({ textContent: text }),
  location: null,
};

const locationStub = {
  href: "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge",
  origin: "https://www.spiderdemo.cn",
  protocol: "https:",
  host: "www.spiderdemo.cn",
  hostname: "www.spiderdemo.cn",
  port: "",
  pathname: "/authentication/jsvmp2_challenge/",
  search: "?challenge_type=jsvmp2_challenge",
  hash: "",
  ancestorOrigins: {},
  toString() {
    return this.href;
  },
};
documentStub.location = locationStub;

const navigatorStub = {
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  webdriver: false,
  language: "zh-CN",
  languages: ["zh-CN", "zh"],
  platform: "Win32",
  hardwareConcurrency: 8,
  plugins: [],
  mimeTypes: [],
  cookieEnabled: true,
  onLine: true,
};

global.window = global;
global.self = global;
global.document = proxy("document", documentStub);
global.location = proxy("location", locationStub);
global.navigator = proxy("navigator", navigatorStub);
global.WebSocket = FakeWS;
global.localStorage = proxy("localStorage", { getItem() { return null; }, setItem() {}, removeItem() {} });
global.sessionStorage = proxy("sessionStorage", { getItem() { return null; }, setItem() {}, removeItem() {} });
global.history = proxy("history", { pushState() {}, replaceState() {} });
global.screen = { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24 };
global.performance = { now: () => Date.now() };
global.atob = (s) => Buffer.from(s, "base64").toString("binary");
global.btoa = (s) => Buffer.from(s, "binary").toString("base64");
global.requestAnimationFrame = (fn) => setTimeout(fn, 16);
global.cancelAnimationFrame = clearTimeout;
global.getComputedStyle = () => proxy("style", {});
global.MutationObserver = class { observe() {} disconnect() {} };
if (!global.crypto) {
  Object.defineProperty(global, "crypto", {
    value: { getRandomValues: (arr) => { require("crypto").randomFillSync(arr); return arr; } },
  });
}
global.alert = (msg) => note("alert", redact(String(msg)));
global.confirm = () => true;
global.prompt = () => "";
global.fetch = async (url, opts) => {
  note("fetch", redact(String(url)) + " " + (opts && opts.method));
  return { ok: false, status: 0, json: async () => ({}), text: async () => "" };
};
global.XMLHttpRequest = class {
  open(method, url) {
    note("xhr", method + " " + redact(String(url)));
    this._url = url;
  }
  setRequestHeader(k) {
    note("xhr-h", k);
  }
  send(body) {
    note("xhr-send", redact(safe(body)));
  }
  addEventListener() {}
};

const src = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const expr = src.split(/\r?\n/).slice(2).join("\n");
try {
  const result = eval(expr);
  note("result", safe(result));
} catch (err) {
  note("throw", err.name + " " + err.message.split("\n")[0]);
}

setTimeout(() => {
  fs.writeFileSync(path.join(__dirname, "_probe_env.txt"), events.join("\n"), "utf8");
}, 50);
