const fs = require("fs");
const path = require("path");
const vm = require("vm");

const notes = [];
function note(kind, detail) {
  if (notes.length > 2500) return;
  const text = String(detail);
  const safe = /sessionid|password|token_seed/i.test(text) ? "[redacted]" : text.slice(0, 400);
  notes.push(kind + " " + safe);
}

function redactValue(value, key) {
  if (Array.isArray(value)) return value.slice(0, 12).map((item) => redactValue(item, key));
  if (value && typeof value === "object") {
    const out = {};
    for (const [k, v] of Object.entries(value)) out[k] = redactValue(v, k);
    return out;
  }
  if (typeof value === "string") {
    if (/token|seed|sign|cookie|auth|password/i.test(key) || value.length > 24) return "str:" + value.length;
    return value;
  }
  return value;
}

function emit(message) {
  fs.writeSync(1, JSON.stringify(message) + "\n");
}

function tagBrand(obj, name) {
  if (process.env.SPIDER_TOSTRING_TAG !== "1" || !obj || (typeof obj !== "object" && typeof obj !== "function")) return obj;
  try {
    Object.defineProperty(obj, Symbol.toStringTag, { value: name, configurable: true });
  } catch { /* some host objects reject the tag */ }
  return obj;
}

const NATIVE_MARK = Symbol.for("spider.markNative");
const NATIVE_STATS = Symbol.for("spider.nativeStats");
const hostReads = [];
let scriptMark = 0;
function remember(group, prop) {
  if (typeof prop !== "string" || prop === "then" || prop.startsWith("_")) return;
  const label = group + "." + prop;
  if (hostReads.length < 80 && !hostReads.includes(label)) hostReads.push(label);
}
function watch(group, value) {
  return new Proxy(value, {
    get(target, prop, receiver) {
      remember(group, prop);
      const child = Reflect.get(target, prop, receiver);
      return typeof child === "function" ? child.bind(target) : child;
    },
    set(target, prop, valueToSet, receiver) {
      remember(group + "-set", prop);
      return Reflect.set(target, prop, valueToSet, receiver);
    },
  });
}

function installNativeMask(context) {
  vm.runInContext(`
    (() => {
      const orig = Function.prototype.toString;
      const spoofed = new WeakSet();
      const stats = { spoof: 0, host: 0, names: [] };
      function hooked() {
        let spoof = false;
        try { spoof = this === hooked || spoofed.has(this); } catch (err) { spoof = false; }
        if (spoof) {
          stats.spoof += 1;
          const name = this && typeof this.name === "string" ? this.name : "";
          if (stats.names.length < 30 && name) stats.names.push(name);
          return "function " + name + "() { [native code] }";
        }
        try {
          const text = orig.call(this);
          if (typeof text === "string" && text.includes("[native code]")) stats.host += 1;
          return text;
        } catch (err) {
          return "function () { [native code] }";
        }
      }
      Object.defineProperty(hooked, "name", { value: "toString" });
      Function.prototype.toString = hooked;
      spoofed.add(hooked);
      Object.defineProperty(globalThis, Symbol.for("spider.markNative"), {
        value(fn) {
          if (typeof fn === "function") spoofed.add(fn);
          return fn;
        },
        configurable: true,
      });
      Object.defineProperty(globalThis, Symbol.for("spider.nativeStats"), {
        value: stats,
        configurable: true,
      });
    })()
  `, context);
  emit({ op: "mask-install", hasMark: typeof context[NATIVE_MARK] });
}

function markHostTree(context) {
  const mark = context[NATIVE_MARK];
  if (typeof mark !== "function") {
    emit({ op: "mask-mark", ok: false, type: typeof mark });
    return;
  }
  const seen = new Set();
  function visit(value, depth) {
    if (value == null || depth > 3) return;
    if (typeof value === "function") {
      if (seen.has(value)) return;
      seen.add(value);
      try { mark(value); } catch (err) { return; }
      try { visit(value.prototype, depth + 1); } catch (err) { return; }
      return;
    }
    if (typeof value !== "object" || seen.has(value)) return;
    seen.add(value);
    let current = value;
    for (let level = 0; current && level < 2; level += 1) {
      let names = [];
      try { names = Object.getOwnPropertyNames(current); } catch (err) { break; }
      for (const name of names) {
        let desc;
        try { desc = Object.getOwnPropertyDescriptor(current, name); } catch (err) { continue; }
        if (!desc) continue;
        if (typeof desc.value === "function" || (desc.value && typeof desc.value === "object")) visit(desc.value, depth + 1);
        if (typeof desc.get === "function") visit(desc.get, depth + 1);
        if (typeof desc.set === "function") visit(desc.set, depth + 1);
      }
      try { current = Object.getPrototypeOf(current); } catch (err) { break; }
    }
  }
  visit(context, 0);
  const subtle = context.crypto && context.crypto.subtle;
  if (subtle) {
    for (const name of ["digest", "encrypt", "decrypt", "sign", "verify", "importKey", "exportKey", "generateKey", "deriveKey", "deriveBits", "wrapKey", "unwrapKey"]) {
      try {
        const fn = subtle[name];
        if (typeof fn === "function") mark(fn);
      } catch (err) { /* host getter */ }
    }
  }
}

function safeLabel(value) {
  const text = String(value);
  if (text.length > 0 && text.length <= 20 && /^[A-Za-z0-9!#$%&'*+\-.^_`|~]+$/.test(text)) return text;
  return "len:" + text.length;
}

function safePath(pathname) {
  return String(pathname || "").split("/").map((part) => (part.length > 24 ? "len:" + part.length : part)).join("/");
}

function argType(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof URL !== "undefined" && value instanceof URL) return "URL";
  if (typeof Headers !== "undefined" && value instanceof Headers) return "Headers";
  return typeof value;
}

function headerEntries(obj, keys, values) {
  if (!obj) return;
  if (typeof Headers !== "undefined" && obj instanceof Headers) {
    obj.forEach((value, key) => {
      keys.push(String(key).toLowerCase());
      values[String(key)] = String(value);
    });
    return;
  }
  if (Array.isArray(obj)) {
    for (const item of obj) {
      if (Array.isArray(item) && item.length >= 2) {
        keys.push(String(item[0]).toLowerCase());
        values[String(item[0])] = String(item[1]);
      }
    }
    return;
  }
  if (typeof obj === "object") {
    for (const key of Object.keys(obj)) {
      keys.push(String(key).toLowerCase());
      values[String(key)] = String(obj[key]);
    }
  }
}

function takeProtocols(value, labels, wire) {
  if (typeof value === "string") {
    labels.push(safeLabel(value));
    wire.push(value);
  } else if (Array.isArray(value)) {
    for (const item of value) takeProtocols(item, labels, wire);
  }
}

function hrefOf(value) {
  if (typeof URL !== "undefined" && value instanceof URL) return value.href;
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    if (typeof value.url === "string") return value.url;
    if (typeof value.href === "string") return value.href;
    if (typeof URL !== "undefined" && value.url instanceof URL) return value.url.href;
  }
  return "";
}

function describeWs(args) {
  const labels = [];
  const wireProtocols = [];
  const headerKeys = [];
  const headerValues = {};
  const optionKeys = [];
  let href = hrefOf(args[0]);
  for (let i = 0; i < args.length; i += 1) {
    const value = args[i];
    if (i > 0 && (typeof value === "string" || Array.isArray(value))) takeProtocols(value, labels, wireProtocols);
    if (value && typeof value === "object") {
      const keys = Object.keys(value).map((key) => (key.length > 24 ? "len:" + key.length : key));
      optionKeys.push(keys);
      if (i === 0 && !href) href = hrefOf(value);
      if (value.protocol) takeProtocols(value.protocol, labels, wireProtocols);
      if (value.protocols) takeProtocols(value.protocols, labels, wireProtocols);
      headerEntries(value.headers, headerKeys, headerValues);
    }
  }
  let path = "";
  let queryKeys = [];
  if (href) {
    try {
      const parsed = new URL(href, "https://www.spiderdemo.cn");
      path = safePath(parsed.pathname);
      queryKeys = [...parsed.searchParams.keys()].map((key) => (key.length > 24 ? "len:" + key.length : key));
      href = parsed.href;
    } catch {
      href = "";
    }
  }
  return {
    safe: {
      argc: args.length,
      types: args.map(argType),
      path,
      queryKeys,
      protocols: labels,
      headerKeys,
      optionKeys,
    },
    href,
    protocols: wireProtocols,
    headers: headerValues,
  };
}

class FakeWS {
  constructor(url, protocols) {
    emit({ op: "ws-ctor" });
    const described = describeWs(Array.from(arguments));
    this._described = described;
    note("ws", "argc=" + described.safe.argc + " path=" + described.safe.path + " keys=" + described.safe.queryKeys.join(","));
    this.url = described.href;
    this.readyState = 0;
    this.binaryType = "blob";
    this.protocol = "";
    FakeWS.instances.push(this);
    FakeWS.current = this;
    queueMicrotask(() => {
      if (this.readyState === 3) return;
      const headerKeys = described.safe.headerKeys.slice();
      const headerValues = Object.assign({}, described.headers);
      if (this.headers) headerEntries(this.headers, headerKeys, headerValues);
      const labels = described.safe.protocols.slice();
      const wireProtocols = described.protocols.slice();
      if (typeof this.protocol === "string" && this.protocol) takeProtocols(this.protocol, labels, wireProtocols);
      const reserved = new Set(["url", "readyState", "binaryType", "protocol", "onopen", "onmessage", "onerror", "onclose", "headers"]);
      const extraKeys = Object.keys(this).filter((key) => !reserved.has(key) && !key.startsWith("_")).map((key) => (key.length > 24 ? "len:" + key.length : key));
      const call = Object.assign({}, described.safe, { protocols: labels, headerKeys, extraKeys });
      emit({ op: "ws-call", call });
      if (process.env.SPIDER_WS_COOKIE === "1" && cookieJar.size) {
        headerValues.cookie = [...cookieJar.entries()].map(([name, value]) => name + "=" + value).join("; ");
      }
      emit({ op: "open", url: described.href, protocols: wireProtocols, headers: headerValues, call });
      this._fireOpen = () => {
        if (this.readyState !== 0) return;
        this.readyState = 1;
        if (typeof this.onopen === "function") this.onopen({ type: "open", target: this });
      };
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
    if (lastToken) {
      emit({
        op: "frame-bind",
        hasToken: bytes.includes(Buffer.from(lastToken)),
        frameLen: bytes.length,
      });
      emit({
        op: "fp-reads",
        stage: "send",
        n: hostReads.length,
        names: hostReads.slice(0, 80),
        hit: hostReads.filter((name) => /plugin|language|hardware|Touch|screen|pixel|Context|DataURL|fillText|speech|pdf|userAgent|platform|colorDepth|round/.test(name)),
      });
    }
    emit({ op: "send", binary, data: bytes.toString("base64") });
  }
  close(code, reason) {
    note("ws-close", code + " " + reason);
    this.readyState = 3;
  }
  addEventListener(type, fn) {
    this["on" + type] = fn;
  }
  removeEventListener() {}
}
FakeWS.instances = [];
FakeWS.CONNECTING = 0;
FakeWS.OPEN = 1;
FakeWS.CLOSING = 2;
FakeWS.CLOSED = 3;

function element(id) {
  const el = {
    id: id || "",
    tagName: "DIV",
    style: {},
    className: "",
    _html: "",
    set innerHTML(value) {
      this._html = String(value);
      const text = String(value).replace(/<[^>]*>/g, " ");
      const nums = text.match(/\d+/g);
      if (id === "numbersGrid" && nums && nums.length) emit({ op: "grid", numbers: nums.map(Number) });
    },
    get innerHTML() { return this._html; },
    set textContent(value) { this.innerHTML = value; },
    get textContent() { return this._html; },
    value: "",
    disabled: false,
    children: [],
    childNodes: [],
    attributes: {},
    setAttribute(name, value) {
      const key = String(name);
      remember("attr", key.toLowerCase());
      const text = String(value);
      this.attributes[key] = text;
      if (key.toLowerCase() === "id" && domQueries.tags.length < 12) {
        const kind = /^[0-9]+$/.test(text) ? "digit" : /^[A-Za-z0-9_-]+$/.test(text) ? "url" : "other";
        const idRow = "id:" + text.length + ":" + kind;
        if (!domQueries.tags.includes(idRow)) domQueries.tags.push(idRow);
      }
      if (key.toLowerCase() === "href") this.href = text;
    },
    getAttribute(name) {
      const key = String(name);
      remember("attr-get", key.toLowerCase());
      if (Object.prototype.hasOwnProperty.call(this.attributes, key)) return this.attributes[key];
      return null;
    },
    appendChild(child) { this.children.push(child); return child; },
    removeChild(child) { return child; },
    addEventListener(type) { note("listen", (id || "el") + " " + type); },
    removeEventListener() {},
    querySelector(sel) { return queryPage(sel); },
    querySelectorAll() { return []; },
    getElementsByTagName() { return []; },
    getContext() { return { fillRect() {}, measureText() { return { width: 10 }; }, font: "16px Arial" }; },
    toDataURL() { return "data:image/png;base64,"; },
    click() { note("click", id); },
    focus() {},
    remove() {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
  };
  return el;
}

const PAGE_NODES = {
  loginAlert: ["DIV", "login-alert", ""],
  loadingOverlay: ["DIV", "loading-overlay", ""],
  currentPageNum: ["SPAN", "stat-number", "1"],
  totalPages: ["SPAN", "stat-number", "100"],
  collectedPages: ["SPAN", "stat-number", "0"],
  numbersGrid: ["DIV", "numbers-grid", ""],
  paginationInfo: ["DIV", "pagination-info", "第 1 页，共 100 页 | 当前页面包含 10 个数字"],
  paginationControls: ["DIV", "pagination", ""],
  prevBtn: ["BUTTON", "page-btn", ""],
  nextBtn: ["BUTTON", "page-btn", ""],
  answerInput: ["INPUT", "answer-input", ""],
  resultMessage: ["DIV", "result-message", ""],
  ...(process.env.SPIDER_NO_TITLES === "1" ? {} : {
    pageTitle: ["H1", "page-title", "T30-WebSocket+jsvmp"],
    challengeTitle: ["H2", "challenge-title", "🎯 任务: 采集这100页的全部数字，计算加和并提交结果"],
  }),
  currentPageNum2: ["DIV", "stat-simple-value", "1"],
  totalPages2: ["DIV", "stat-simple-value", "100"],
  collectedPages2: ["DIV", "stat-simple-value", "0"],
};
const pageNodes = new Map();
const domQueries = { byId: [], qs: [], tags: [], href: [] };
let lastHrefRaw = "";
let lastToken = "";

function pathNameOf(abs) {
  try { return new URL(abs).pathname.includes("/init/"); } catch { return false; }
}

function classifyHref(text) {
  if (/^https?:\/\//i.test(text)) return "abs";
  if (text.startsWith("/")) return "path";
  if (text.startsWith("?")) return "search";
  if (text.startsWith("#")) return "hash";
  if (text === "") return "empty";
  return "other";
}

function observeElement(node, group) {
  return new Proxy(node, {
    get(target, prop, receiver) {
      if (typeof prop === "string") remember(group, prop);
      const value = Reflect.get(target, prop, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
    set(target, prop, value, receiver) {
      if (typeof prop === "string") remember(group + "-set", prop);
      return Reflect.set(target, prop, value, receiver);
    },
  });
}

function cssStyle() {
  const store = Object.create(null);
  tagBrand(store, "CSSStyleDeclaration");
  return new Proxy(store, {
    get(target, prop) {
      if (typeof prop !== "string") return Reflect.get(target, prop);
      remember("style", prop);
      if (prop === "getPropertyValue") {
        return (name) => {
          remember("style", String(name));
          return target[name] || "";
        };
      }
      if (prop === "setProperty") {
        return (name, value) => {
          target[String(name)] = String(value);
        };
      }
      if (prop === "removeProperty") {
        return (name) => {
          const prev = target[name] || "";
          delete target[name];
          return prev;
        };
      }
      return Object.prototype.hasOwnProperty.call(target, prop) ? target[prop] : "";
    },
    set(target, prop, value) {
      target[prop] = String(value);
      return true;
    },
  });
}

function rememberQuery(bucket, value, hit) {
  const text = String(value).slice(0, 80);
  const row = text + (hit ? "=hit" : "=miss");
  if (domQueries[bucket].length < 24 && !domQueries[bucket].includes(row)) domQueries[bucket].push(row);
}

function pageNode(id) {
  const spec = PAGE_NODES[id];
  if (!spec) return null;
  if (pageNodes.has(id)) return pageNodes.get(id);
  const node = element(id);
  node.tagName = spec[0];
  node.className = spec[1];
  node._html = spec[2];
  if (spec[0] === "INPUT") node.value = "";
  if (id === "prevBtn") node.disabled = true;
  node.style = cssStyle();
  const observed = new Proxy(node, {
    get(target, prop, receiver) {
      if (typeof prop === "string") remember("dom", prop);
      const value = Reflect.get(target, prop, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
    set(target, prop, valueToSet, receiver) {
      if (typeof prop === "string") remember("dom-set", prop);
      if (prop === "innerHTML" || prop === "textContent") {
        const text = String(valueToSet);
        const tags = [];
        const matcher = /<\/?([a-zA-Z][a-zA-Z0-9-]*)/g;
        let found = matcher.exec(text);
        while (found && tags.length < 8) {
          const tag = found[1].toLowerCase();
          if (!tags.includes(tag)) tags.push(tag);
          found = matcher.exec(text);
        }
        emit({
          op: "dom-html",
          prop,
          len: text.length,
          tags,
          hasAnchor: /<a[\s>/]/i.test(text),
          hasId: /\sid\s*=/i.test(text),
        });
      }
      return Reflect.set(target, prop, valueToSet, receiver);
    },
  });
  pageNodes.set(id, observed);
  return observed;
}

function createdElement(tag) {
  const el = element(tag);
  const htmlTag = process.env.SPIDER_LOWER_A === "1" ? String(tag || "") : String(tag || "").toUpperCase();
  el.tagName = htmlTag;
  el.nodeName = htmlTag;
  tagBrand(el, htmlTag === "A" ? "HTMLAnchorElement" : "HTMLElement");
  if (htmlTag === "A") {
    let href = "";
    Object.defineProperty(el, "href", {
      configurable: true,
      enumerable: true,
      get() { return href; },
      set(value) {
        const raw = String(value);
        lastHrefRaw = raw;
        const url = new URL(raw, locationStub.href);
        const marks = ["colon", "slash", "query", "hash", "dot", "plus", "eq", "pct", "under", "dash"].filter((name) => {
          const ch = { colon: ":", slash: "/", query: "?", hash: "#", dot: ".", plus: "+", eq: "=", pct: "%", under: "_", dash: "-" }[name];
          return raw.includes(ch);
        });
        const row = [classifyHref(raw), raw.length, "out" + url.href.length, url.pathname.endsWith("/" + raw) ? "append" : "rewrite", marks.join("+") || "plain"].join(":");
        if (domQueries.href.length < 6 && !domQueries.href.includes(row)) domQueries.href.push(row);
        href = process.env.SPIDER_RAW_HREF === "1" ? raw : url.href;
        el.protocol = url.protocol;
        el.hostname = url.hostname;
        el.host = url.host;
        el.port = url.port;
        el.pathname = url.pathname;
        el.search = url.search;
        el.hash = url.hash;
        el.origin = url.origin;
      },
    });
  }
  return new Proxy(el, {
    get(target, prop, receiver) {
      if (typeof prop === "string") remember("el", prop);
      const value = Reflect.get(target, prop, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
    set(target, prop, value, receiver) {
      if (typeof prop === "string") remember("el-set", prop);
      return Reflect.set(target, prop, value, receiver);
    },
  });
}

function queryPage(sel) {
  const text = String(sel);
  let hit = null;
  if (text.startsWith("#")) hit = pageNode(text.slice(1));
  else if (text.startsWith(".") && !/[\s>#]/.test(text)) {
    const cls = text.slice(1);
    for (const id of Object.keys(PAGE_NODES)) {
      if (PAGE_NODES[id][1].split(/\s+/).includes(cls)) {
        hit = pageNode(id);
        break;
      }
    }
  } else if (PAGE_NODES[text]) hit = pageNode(text);
  rememberQuery("qs", text, Boolean(hit));
  return hit;
}

function hostCtor(name, parent) {
  const fn = function Host() {};
  Object.defineProperty(fn, "name", { value: name, configurable: true });
  fn.prototype = Object.create(parent ? parent.prototype : Object.prototype);
  Object.defineProperty(fn.prototype, "constructor", { value: fn, writable: true, configurable: true });
  return fn;
}

const EventTargetCtor = hostCtor("EventTarget");
const NodeCtor = hostCtor("Node", EventTargetCtor);
const DocumentCtor = hostCtor("Document", NodeCtor);
const HTMLDocumentCtor = hostCtor("HTMLDocument", DocumentCtor);
const plainDoc = process.env.SPIDER_PLAIN_DOC === "1";
const documentProto = plainDoc ? {} : HTMLDocumentCtor.prototype;
const documentStub = Object.create(documentProto);
const cookieJar = new Map();
let rawCookie = "";

function installDocumentMember(key, descriptor) {
  Object.defineProperty(plainDoc ? documentStub : documentProto, key, descriptor);
}

installDocumentMember("cookie", {
  enumerable: true,
  configurable: true,
  set(value) {
    const parts = String(value).split(";");
    const pair = parts[0];
    const eq = pair.indexOf("=");
    const name = (eq >= 0 ? pair.slice(0, eq) : pair).trim();
    const cookieValue = eq >= 0 ? pair.slice(eq + 1).trim() : "";
    if (!name) return;
    cookieJar.set(name, cookieValue);
    rawCookie = String(value);
    note("cookie-set", name);
    const stored = [...cookieJar.entries()].map(([cookieName, cookieValue]) => cookieName + "=" + cookieValue).join("; ");
    emit({
      op: "cookie",
      raw: String(value).length,
      len: cookieValue.length,
      attrCount: Math.max(0, parts.length - 1),
      getLen: stored.length,
    });
  },
  get() {
    if (process.env.SPIDER_RAW_COOKIE === "1") return rawCookie;
    return [...cookieJar.entries()].map(([name, value]) => name + "=" + value).join("; ");
  },
});
for (const [key, value] of Object.entries({
  readyState: "complete",
  visibilityState: "visible",
  hidden: false,
  referrer: "https://www.spiderdemo.cn/",
  title: "T30-WebSocket+jsvmp",
  characterSet: "UTF-8",
  compatMode: "CSS1Compat",
  documentElement: observeElement(element("html"), "root"),
  body: observeElement(element("body"), "body"),
  head: observeElement(element("head"), "head"),
})) {
  installDocumentMember(key, { enumerable: true, configurable: true, writable: true, value });
}
installDocumentMember("createElement", {
  enumerable: true,
  configurable: true,
  writable: true,
  value: (tag) => {
    const name = String(tag).slice(0, 40);
    if (domQueries.tags.length < 12 && !domQueries.tags.includes(name)) domQueries.tags.push(name);
    return createdElement(name);
  },
});
installDocumentMember("createElementNS", { enumerable: true, configurable: true, writable: true, value: (ns, tag) => element(tag) });
installDocumentMember("getElementById", {
  enumerable: true,
  configurable: true,
  writable: true,
  value: (id) => {
    const hit = pageNode(String(id));
    rememberQuery("byId", id, Boolean(hit));
    return hit;
  },
});
installDocumentMember("querySelector", { enumerable: true, configurable: true, writable: true, value: (sel) => queryPage(sel) });
installDocumentMember("querySelectorAll", { enumerable: true, configurable: true, writable: true, value: (sel) => { note("qsa", sel); return []; } });
installDocumentMember("getElementsByTagName", { enumerable: true, configurable: true, writable: true, value: () => [] });
installDocumentMember("getElementsByClassName", { enumerable: true, configurable: true, writable: true, value: () => [] });
installDocumentMember("addEventListener", {
  enumerable: true,
  configurable: true,
  writable: true,
  value(type, fn) {
    note("doc-on", type);
    if (type === "DOMContentLoaded" || type === "load") {
      queueMicrotask(() => {
        emit({ op: "dom", type });
        fn({ type });
      });
    }
  },
});
installDocumentMember("removeEventListener", { enumerable: true, configurable: true, writable: true, value() {} });
installDocumentMember("createTextNode", { enumerable: true, configurable: true, writable: true, value: (text) => ({ textContent: text, nodeType: 3 }) });
installDocumentMember("createEvent", { enumerable: true, configurable: true, writable: true, value: () => ({ initEvent() {} }) });
installDocumentMember("hasFocus", { enumerable: true, configurable: true, writable: true, value: () => true });

// Host read document.all. V8 undetectable covers typeof/truthiness/== null.
// Do not wrap this object: a Proxy drops [[IsHTMLDDA]].
function probeAll(allObject) {
  const probe = { mode: "bare" };
  try {
    probe.type = typeof allObject;
    probe.eqUndef = allObject === undefined;
    probe.eqNull = allObject == null;
    probe.truthy = Boolean(allObject);
  } catch (err) {
    probe.error = err.name;
  }
  emit({ op: "all-probe", ...probe });
}
{
  const v8 = require("v8");
  v8.setFlagsFromString("--allow-natives-syntax");
  try {
    let allObject;
    if (process.env.SPIDER_ALL_OBJECT === "1") allObject = {};
    else if (process.env.SPIDER_ALL_OFF !== "1") allObject = tagBrand(vm.runInThisContext("%GetUndetectable()"), "HTMLAllCollection");
    if (allObject !== undefined && allObject !== null) {
      probeAll(allObject);
      installDocumentMember("all", {
        enumerable: true,
        configurable: true,
        get() { return allObject; },
      });
    } else {
      emit({ op: "all-probe", mode: "off" });
    }
  } finally {
    v8.setFlagsFromString("--no-allow-natives-syntax");
  }
}

const locationStub = {
  origin: "https://www.spiderdemo.cn",
  protocol: "https:",
  host: "www.spiderdemo.cn",
  hostname: "www.spiderdemo.cn",
  port: "",
  pathname: "/authentication/jsvmp2_challenge/",
  search: process.env.SPIDER_BAD_SEARCH === "1" ? "?x=1" : "?challenge_type=jsvmp2_challenge",
  hash: "",
  toString() { return this.href; },
};
{
  let hrefValue = "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge";
  const dataHref = process.env.SPIDER_DATA_HREF === "1";
  Object.defineProperty(locationStub, "href", dataHref ? {
    enumerable: true,
    configurable: true,
    writable: true,
    value: hrefValue,
  } : {
    enumerable: true,
    configurable: false,
    get() { return hrefValue; },
    set(value) { hrefValue = String(value); },
  });
}
const locationProxy = watch("location", locationStub);
Object.defineProperty(documentStub, "location", {
  enumerable: true,
  configurable: false,
  get() { return locationProxy; },
  set() { return true; },
});
emit({
  op: "doc-shape",
  chain: Object.getPrototypeOf(documentStub) && Object.getPrototypeOf(documentStub).constructor
    ? Object.getPrototypeOf(documentStub).constructor.name
    : "none",
  own: Reflect.ownKeys(documentStub).filter((key) => typeof key === "string"),
  hrefAccess: Boolean(Object.getOwnPropertyDescriptor(locationStub, "href") && Object.getOwnPropertyDescriptor(locationStub, "href").get),
});

const sandbox = {
  console: {
    log: (...args) => note("log", args.map((x) => typeof x === "string" ? x : typeof x).join(" ")),
    error: (...args) => note("error", args.map((x) => typeof x === "string" ? x : (x && x.message) || typeof x).join(" ")),
    warn: (...args) => note("warn", args.join(" ")),
    info: (...args) => note("info", args.join(" ")),
    debug() {},
  },
  setTimeout: (fn, ms) => setTimeout(fn, Math.min(Number(ms) || 0, 8000)),
  clearTimeout,
  setInterval: (fn, ms) => setInterval(fn, Math.max(ms || 200, 200)),
  clearInterval,
  queueMicrotask,
  atob: (s) => {
    const out = Buffer.from(String(s), "base64").toString("binary");
    note("atob", "in=" + String(s).length + " out=" + out.length);
    emit({ op: "codec", name: "atob", in: String(s).length, out: out.length });
    return out;
  },
  btoa: (s) => {
    const out = Buffer.from(String(s), "binary").toString("base64");
    globalThis.__LAST_BTOA = out;
    note("btoa", "in=" + String(s).length + " out=" + out.length);
    const raw = Buffer.from(String(s), "binary");
    emit({
      op: "codec",
      name: "btoa",
      in: raw.length,
      out: out.length,
      bytes: [],
    });
    return out;
  },
  alert: (m) => note("alert", m),
  confirm: () => true,
  prompt: () => "",
  requestAnimationFrame: (fn) => setTimeout(() => fn(Date.now()), 16),
  cancelAnimationFrame: clearTimeout,
  getComputedStyle: () => new Proxy({}, { get: () => "" }),
  MutationObserver: class { observe() {} disconnect() {} },
  WebSocket: FakeWS,
  document: watch("document", documentStub),
  location: locationProxy,
  navigator: new Proxy({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0",
    appVersion: "5.0 (Windows)",
    appName: "Netscape",
    vendor: "",
    webdriver: process.env.SPIDER_WEBDRIVER === "1",
    language: "en-US",
    languages: ["en-US", "en"],
    platform: "Win32",
    hardwareConcurrency: 8,
    deviceMemory: 8,
    plugins: { length: 0 },
    mimeTypes: { length: 0 },
    cookieEnabled: true,
    onLine: true,
    maxTouchPoints: 0,
  }, {
    get(target, prop, receiver) {
      remember("navigator", prop);
      const value = Reflect.get(target, prop, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
  }),
  localStorage: { getItem: () => null, setItem(k) { note("ls", k); }, removeItem() {}, key: () => null, length: 0 },
  sessionStorage: { getItem: () => null, setItem(k) { note("ss", k); }, removeItem() {}, key: () => null, length: 0 },
  history: { pushState() {}, replaceState() {}, back() {}, length: 1, state: null },
  screen: watch("screen", { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24 }),
  performance: watch("performance", {
    now() {
      remember("performance", "now");
      return Date.now();
    },
    timeOrigin: Date.now(),
  }),
  crypto: (() => {
    const webcrypto = require("crypto").webcrypto;
    const subtle = webcrypto.subtle;
    const logging = Object.create(subtle);
    for (const name of ["digest", "encrypt", "decrypt", "sign", "verify", "importKey", "exportKey", "generateKey", "deriveKey", "deriveBits", "wrapKey", "unwrapKey"]) {
      const fn = subtle[name];
      if (typeof fn !== "function") continue;
      const wrapped = function subtleMethod(...args) {
        const algo = args[0] && typeof args[0] === "object" ? (args[0].name || args[0].hash || "obj") : args[0];
        emit({ op: "subtle", name, algo: String(algo).slice(0, 40), argc: args.length });
        return fn.apply(subtle, args);
      };
      Object.defineProperty(wrapped, "name", { value: name });
      logging[name] = wrapped;
    }
    return {
      getRandomValues: (arr) => {
        emit({ op: "rand", n: arr && arr.length || 0 });
        return webcrypto.getRandomValues(arr);
      },
      randomUUID: () => webcrypto.randomUUID(),
      subtle: logging,
    };
  })(),
  isSecureContext: true,
  crossOriginIsolated: false,
  XMLHttpRequest: class {
    open(method, url) {
      this._url = url;
      let pathName = "";
      try { pathName = new URL(String(url), "https://www.spiderdemo.cn").pathname; } catch { pathName = ""; }
      emit({ op: "xhr", method: String(method), path: pathName });
    }
    setRequestHeader(k, v) { if (!/cookie|auth/i.test(k)) note("xhr-h", k); }
    send(body) { note("xhr-body", typeof body === "string" ? body.slice(0, 200) : typeof body); }
    addEventListener() {}
    getAllResponseHeaders() { return ""; }
  },
  fetch: async (url, opts) => {
    const abs = new URL(String(url), "https://www.spiderdemo.cn").toString();
    const method = (opts && opts.method) || "GET";
    note("fetch", method + " " + abs);
    emit({ op: "fetch", method, url: abs.split("?")[0], ulen: abs.length });
    emit({ op: "codec", name: "fetch", in: abs.length, out: abs.split("?")[0].length });
    emit({ op: "fetch-go" });
    const headers = new Headers(opts && opts.headers || {});
    if (process.env.SPIDER_COOKIE) headers.set("cookie", process.env.SPIDER_COOKIE);
    headers.set("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0");
    headers.set("referer", "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge");
    headers.set("origin", "https://www.spiderdemo.cn");
    headers.set("accept", "application/json, text/plain, */*");
    const initFile = process.env.SPIDER_INIT_FILE || "";
    const replayInit = pathNameOf(abs) && initFile && process.env.SPIDER_INIT_REPLAY === "1" && fs.existsSync(initFile);
    let res;
    let text;
    if (replayInit) {
      text = fs.readFileSync(initFile, "utf8");
      res = { status: 200, ok: true, headers: { get: () => null } };
      emit({ op: "fetch-back", status: 200, replay: true });
    } else {
      res = await fetch(abs, { method, headers, body: opts && opts.body });
      emit({ op: "fetch-back", status: res.status });
      text = await res.text();
      if (initFile && process.env.SPIDER_INIT_SAVE === "1" && pathNameOf(abs)) {
        fs.writeFileSync(initFile, text);
      }
    }
    let parsed = null;
    try { parsed = JSON.parse(text); } catch { parsed = null; }
    const pathName = new URL(abs).pathname;
    if (pathName.includes("/init/") && parsed && typeof parsed === "object") {
      const lengths = {};
      for (const [key, value] of Object.entries(parsed)) {
        if (typeof value === "string") lengths[key] = value.length;
        else if (Array.isArray(value)) lengths[key] = value.length;
        else lengths[key] = typeof value;
      }
      emit({ op: "init-shape", status: res.status, lengths });
    }
    return {
      ok: res.ok,
      status: res.status,
      headers: { get: (name) => res.headers.get(name) },
      json: async () => parsed !== null ? parsed : JSON.parse(text),
      text: async () => text,
      arrayBuffer: async () => Buffer.from(text),
      clone() { return this; },
    };
  },
  Image: class { set src(v) { note("img", v); } },
  Event: class { constructor(type) { this.type = type; } },
  CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init && init.detail; } },
  WebSocketImpl: FakeWS,
};
sandbox.version = "Concurrency V2026 WX:Jsvmp6";
for (const name of ["URL", "URLSearchParams", "TextEncoder", "TextDecoder", "Blob", "File", "FormData", "Headers", "Request", "Response", "AbortController", "AbortSignal", "DOMException", "TextDecoderStream", "TextEncoderStream", "ReadableStream", "WritableStream", "TransformStream", "CompressionStream", "DecompressionStream", "MessageChannel", "MessagePort", "BroadcastChannel", "structuredClone", "queueMicrotask", "performance"]) {
  if (globalThis[name] !== undefined) sandbox[name] = globalThis[name];
}
sandbox.DOMParser = class { parseFromString() { return documentStub; } };
sandbox.XMLSerializer = class { serializeToString() { return ""; } };
const blobs = new Map();
let blobSeq = 0;
sandbox.Blob = class Blob {
  constructor(parts = [], opts = {}) {
    this._parts = parts;
    this.type = (opts && opts.type) || "";
    this.size = parts.reduce((sum, part) => sum + String(part).length, 0);
  }
  async text() {
    return this._parts.map((part) => String(part)).join("");
  }
};
sandbox.URL.createObjectURL = (obj) => {
  const id = "blob:sandbox/" + (++blobSeq);
  blobs.set(id, obj);
  note("blob", id + " type=" + (obj && obj.type) + " size=" + (obj && obj.size));
  return id;
};
sandbox.URL.revokeObjectURL = (id) => { blobs.delete(id); };
class WorkerStub {
  constructor(url) {
    this.url = String(url);
    this.listeners = {};
    note("worker", this.url);
    emit({ op: "worker", url: String(this.url).slice(0, 80) });
    const sdkPath = path.join(__dirname, "assets", "sdk.min.js");
    const source = fs.existsSync(sdkPath) ? fs.readFileSync(sdkPath, "utf8") : "";
    const bridge = this;
    const workerGlobal = {
      console: sandbox.console,
      setTimeout: sandbox.setTimeout,
      clearTimeout,
      setInterval: sandbox.setInterval,
      clearInterval,
      URL: sandbox.URL,
      URLSearchParams: sandbox.URLSearchParams,
      TextEncoder: sandbox.TextEncoder,
      TextDecoder: sandbox.TextDecoder,
      WebSocket: FakeWS,
      atob: sandbox.atob,
      btoa: sandbox.btoa,
      crypto: sandbox.crypto,
      isSecureContext: true,
      crossOriginIsolated: false,
      performance: sandbox.performance,
      navigator: sandbox.navigator,
      location: {
        href: "https://www.spiderdemo.cn/static/js/authentication/sdk.min.js",
        origin: "https://www.spiderdemo.cn",
        protocol: "https:",
        host: "www.spiderdemo.cn",
        hostname: "www.spiderdemo.cn",
        pathname: "/static/js/authentication/sdk.min.js",
      },
      importScripts() {},
      close() {},
      postMessage(data) {
        try { note("from-worker", JSON.stringify(redactValue(data))); }
        catch { note("from-worker", typeof data); }
        emit({ op: "msg", data: data && data.type ? { type: data.type } : { kind: typeof data } });
        const event = { data };
        if (typeof bridge.onmessage === "function") bridge.onmessage(event);
        for (const fn of Object.values(bridge.listeners)) {
          try { fn(event); } catch (err) { note("main-handler", err.message); }
        }
      },
      addEventListener(type, fn) {
        if (type === "message") this.onmessage = fn;
      },
      removeEventListener() {},
    };
    workerGlobal.self = workerGlobal;
    workerGlobal.globalThis = workerGlobal;
    workerGlobal.window = workerGlobal;
    this.context = vm.createContext(workerGlobal);
    installNativeMask(workerGlobal);
    markHostTree(workerGlobal);
    try {
      vm.runInContext(source, workerGlobal);
      note("worker-run", "ok");
      emit({ op: "worker-ok" });
    } catch (err) {
      note("worker-err", err.name + " " + String(err.message).split("\n")[0]);
      emit({ op: "error", message: "worker " + err.name + " " + String(err.message).split("\n")[0] });
    }
  }
  postMessage(data) {
    emit({
      op: "fp-reads",
      stage: "pre",
      n: Math.max(0, hostReads.length - scriptMark),
      names: hostReads.slice(scriptMark, scriptMark + 80),
      qs: domQueries.qs,
      byId: domQueries.byId,
      tags: domQueries.tags,
      href: domQueries.href,
    });
    try { note("worker-post", JSON.stringify(redactValue(data))); }
    catch { note("worker-post", typeof data); }
    if (data && data.type === "INIT" && data.data && typeof data.data.token === "string") {
      const token = data.data.token;
      lastToken = token;
      const parts = token.split(".");
      const alphabet = parts.every((part) => /^[A-Za-z0-9_-]+$/.test(part)) ? "url" : "other";
      note("token-shape", parts.map((part) => String(part.length)).join(".") + " " + alphabet);
      const pad = (text) => text + "=".repeat((4 - (text.length % 4)) % 4);
      const decodedLen = (text) => {
        try {
          return Buffer.from(pad(text).replace(/-/g, "+").replace(/_/g, "/"), "base64").length;
        } catch (error) {
          return -1;
        }
      };
      emit({ op: "dom-query", byId: domQueries.byId, qs: domQueries.qs, tags: domQueries.tags, href: domQueries.href });
      emit({
        op: "token-id",
        id: require("crypto").createHash("sha256").update(token).digest("hex").slice(0, 12),
        parts: parts.map((part) => part.length),
      });
      emit({ op: "host-reads", names: hostReads.slice(0, 80) });
      const fields = {};
      for (const [key, value] of Object.entries(data.data)) {
        if (typeof value === "string") fields[key] = "str:" + value.length;
        else if (typeof value === "number") fields[key] = "num";
        else fields[key] = typeof value;
      }
      emit({ op: "init-msg", type: data.type, fields, cookieLen: documentStub.cookie.length });
      const prefix = parts[0] || "";
      const prefixClass = /^[0-9]+$/.test(prefix) ? "digit" : /^[0-9a-f]+$/.test(prefix) ? "hex" : alphabet === "url" ? "url" : "other";
      emit({
        op: "token-shape",
        parts: parts.map((part) => part.length),
        alphabet,
        prefixClass,
        prefixMatch: token.slice(0, 8) === globalThis.__LAST_BTOA,
        secondLen: parts[1] ? decodedLen(parts[1]) : -1,
        secondHead: (() => {
          if (!parts[1]) return [];
          const text = pad(parts[1]).replace(/-/g, "+").replace(/_/g, "/");
          const raw = Buffer.from(text, "base64");
          return [raw[0], raw[1], raw.length];
        })(),
        prefixDelta: (() => {
          const raw = Buffer.from(pad(prefix).replace(/-/g, "+").replace(/_/g, "/"), "base64");
          if (raw.length < 4) return null;
          return raw.readUInt32BE(0) - Math.floor(Date.now() / 1000);
        })(),
        cookieIsToken: cookieJar.get("ads-baidu") === token,
        hrefIsPrefix: prefix === lastHrefRaw,
        hrefIsSeedHead: lastHrefRaw.length > 0 && lastHrefRaw === String(data.data.seed || "").slice(0, lastHrefRaw.length),
        hrefIsSeedTail: lastHrefRaw.length > 0 && lastHrefRaw === String(data.data.seed || "").slice(-lastHrefRaw.length),
        prefixIsSeedHead: prefix.length > 0 && prefix === String(data.data.seed || "").slice(0, prefix.length),
        prefixIsSeedTail: prefix.length > 0 && prefix === String(data.data.seed || "").slice(-prefix.length),
        bodyHasDash: Boolean(parts[1] && parts[1].includes("-")),
        bodyHasUnder: Boolean(parts[1] && parts[1].includes("_")),
        secInToken: token.includes(String(Math.floor((frozenNow || realDate.now()) / 1000))),
        msInToken: token.includes(String(frozenNow || realDate.now())),
        bodyHasPlus: Boolean(parts[1] && parts[1].includes("+")),
        bodyHasSlash: Boolean(parts[1] && parts[1].includes("/")),
      });
      const bodyText = parts[1] || "";
      const decoded = Buffer.from(pad(bodyText).replace(/-/g, "+").replace(/_/g, "/"), "base64");
      const stampMs = frozenNow || realDate.now();
      const stampSec = Math.floor(stampMs / 1000);
      let secAt = -1;
      let msAt = -1;
      for (let i = 0; i + 4 <= decoded.length; i += 1) {
        const be = decoded.readUInt32BE(i);
        const le = decoded.readUInt32LE(i);
        if (be === stampSec || le === stampSec) secAt = i;
      }
      for (let i = 0; i + 6 <= decoded.length; i += 1) {
        const be = decoded.readUIntBE(i, 6);
        const le = decoded.readUIntLE(i, 6);
        if (be === stampMs || le === stampMs) msAt = i;
      }
      let printable = 0;
      for (const byte of decoded) if (byte >= 32 && byte < 127) printable += 1;
      const seed = String(data.data.seed || "");
      let inflateLen = -1;
      let rawInflateLen = -1;
      try { inflateLen = require("zlib").inflateSync(decoded).length; } catch { inflateLen = -1; }
      try { rawInflateLen = require("zlib").inflateRawSync(decoded).length; } catch { rawInflateLen = -1; }
      emit({
        op: "body-probe",
        decoded: decoded.length,
        printable,
        secAt,
        msAt,
        seedBytes: decoded.indexOf(Buffer.from(seed)) >= 0,
        inflateLen,
        rawInflateLen,
      });
    }
    const inner = data && data.data;
    emit({
      op: "to-worker",
      type: data && data.type,
      shape: inner && typeof inner === "object" ? Object.fromEntries(Object.entries(inner).map(([key, value]) => [key, typeof value === "string" ? "str:" + value.length : typeof value])) : typeof inner,
    });
    const deliver = () => {
      emit({ op: "deliver-start" });
      const handler = this.context && this.context.onmessage;
      if (typeof handler !== "function") {
        note("worker-drop", "no onmessage");
        emit({ op: "error", message: "no worker onmessage" });
        return;
      }
      try { handler({ data }); emit({ op: "deliver-done" }); }
      catch (err) {
        note("worker-handler", err.message);
        emit({ op: "error", message: "handler " + String(err.message).split("\n")[0] });
      }
    };
    queueMicrotask(deliver);
  }
  terminate() { note("worker", "terminate"); }
  addEventListener(type, fn) {
    this.listeners[type] = fn;
    if (type === "message") this.onmessage = fn;
    note("worker-on", type);
  }
  removeEventListener() {}
}
sandbox.Worker = WorkerStub;
delete sandbox.SharedWorker;
sandbox.ResizeObserver = class { observe() {} disconnect() {} };
sandbox.IntersectionObserver = class { observe() {} disconnect() {} };
sandbox.MutationObserver = class { observe() {} disconnect() {} };
sandbox.FileReader = class {
  readAsText() { this.result = ""; queueMicrotask(() => this.onload && this.onload()); }
  readAsArrayBuffer() { this.result = new ArrayBuffer(0); queueMicrotask(() => this.onload && this.onload()); }
  readAsDataURL() { this.result = "data:"; queueMicrotask(() => this.onload && this.onload()); }
  addEventListener(type, fn) { this["on" + type] = fn; }
};
sandbox.Image = class { set src(value) { note("img", value); } };
sandbox.Audio = class { play() { return Promise.resolve(); } };
sandbox.WebAssembly = { compile() { return Promise.reject(new Error("no wasm")); }, instantiate() { return Promise.reject(new Error("no wasm")); } };
tagBrand(documentStub, "HTMLDocument");
tagBrand(locationStub, "Location");
tagBrand(sandbox.navigator, "Navigator");
tagBrand(sandbox, "Window");
const namedOnly = process.env.SPIDER_WIN_NAME_ONLY === "1";
const plainWin = process.env.SPIDER_PLAIN_WIN === "1";
const winDepth = namedOnly || plainWin ? 0 : Number(process.env.SPIDER_WIN_DEPTH || "3");
let windowCtor = null;
if (namedOnly) {
  windowCtor = hostCtor("Window");
  Object.defineProperty(sandbox, "constructor", { value: windowCtor, configurable: true, writable: true });
} else if (winDepth > 0) {
  windowCtor = hostCtor("Window");
  if (winDepth === 1) {
    Object.setPrototypeOf(sandbox, EventTargetCtor.prototype);
  } else {
    if (winDepth >= 3) {
      const windowProperties = Object.create(EventTargetCtor.prototype);
      if (process.env.SPIDER_WIN_BARE === "1") {
        Object.defineProperty(windowProperties, "constructor", { value: undefined, writable: true, configurable: true });
      }
      Object.setPrototypeOf(windowCtor.prototype, windowProperties);
    }
    Object.defineProperty(windowCtor.prototype, "HTMLDocument", { value: HTMLDocumentCtor, configurable: true });
    Object.defineProperty(windowCtor.prototype, "Document", { value: DocumentCtor, configurable: true });
    Object.defineProperty(windowCtor.prototype, "Node", { value: NodeCtor, configurable: true });
    Object.defineProperty(windowCtor.prototype, "EventTarget", { value: EventTargetCtor, configurable: true });
    Object.defineProperty(windowCtor.prototype, "Window", { value: windowCtor, configurable: true });
    Object.setPrototypeOf(sandbox, windowCtor.prototype);
  }
}
{
  const names = [];
  let cur = sandbox;
  const seen = new Set();
  while (cur && names.length < 6 && !seen.has(cur)) {
    seen.add(cur);
    const ctor = cur.constructor;
    names.push(ctor && typeof ctor.name === "string" && ctor.name ? ctor.name : "none");
    cur = Object.getPrototypeOf(cur);
  }
  emit({ op: "win-shape", depth: winDepth, names });
}
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;
sandbox.globalThis = sandbox;
sandbox.frames = sandbox;
sandbox.frameElement = null;
sandbox.clientInformation = sandbox.navigator;
const windowMetrics = {
  innerWidth: 1920,
  innerHeight: 969,
  outerWidth: 1920,
  outerHeight: 1040,
  devicePixelRatio: 1,
  screenX: 0,
  screenY: 0,
  pageXOffset: 0,
  pageYOffset: 0,
  scrollX: 0,
  scrollY: 0,
};
for (const [metric, metricValue] of Object.entries(windowMetrics)) {
  Object.defineProperty(sandbox, metric, {
    configurable: true,
    enumerable: true,
    get() {
      remember("global", metric);
      return metricValue;
    },
  });
}

process.on("uncaughtException", (err) => {
  note("uncaught", err && err.message ? err.message.split("\n")[0] : err);
  fs.writeFileSync(path.join(__dirname, "_sandbox.txt"), notes.join("\n"), "utf8");
  process.exit(0);
});
process.on("unhandledRejection", (err) => {
  note("reject", err && err.message ? err.message.split("\n")[0] : err);
});
const realDate = Date;
const freezeMs = Number(process.env.SPIDER_FREEZE_MS || "");
const frozenNow = Number.isFinite(freezeMs) && freezeMs > 0 ? freezeMs : 0;
function SandboxDate(...args) {
  remember("Date", "new");
  if (!args.length && frozenNow) return new realDate(frozenNow);
  return args.length ? new realDate(...args) : new realDate();
}
SandboxDate.now = () => {
  remember("Date", "now");
  return frozenNow || realDate.now();
};
SandboxDate.parse = realDate.parse;
SandboxDate.UTC = realDate.UTC;
SandboxDate.prototype = realDate.prototype;
sandbox.Date = SandboxDate;
const loggedRandom = () => {
  remember("Math", "random");
  return Math.random();
};
sandbox.Math = new Proxy(Math, {
  get(target, prop, receiver) {
    remember("Math", prop);
    if (prop === "random") return loggedRandom;
    const value = Reflect.get(target, prop, receiver);
    return typeof value === "function" ? value.bind(target) : value;
  },
});
vm.createContext(sandbox);
if (process.env.SPIDER_NO_REPAIR !== "1" && process.env.SPIDER_WIN_NAME_ONLY !== "1") {
  vm.runInContext(`(() => {
    function hostCtor(name, parent) {
      const fn = function Host() {};
      Object.defineProperty(fn, "name", { value: name, configurable: true });
      fn.prototype = Object.create(parent || Object.prototype);
      Object.defineProperty(fn.prototype, "constructor", { value: fn, writable: true, configurable: true });
      return fn;
    }
    const EventTarget = hostCtor("EventTarget", Object.prototype);
    const Window = hostCtor("Window", EventTarget.prototype);
    const windowProperties = Object.create(EventTarget.prototype);
    Object.defineProperty(windowProperties, "constructor", { value: undefined, writable: true, configurable: true });
    Object.setPrototypeOf(Window.prototype, windowProperties);
    const kept = { EventTarget, Window };
    for (const key of ["HTMLDocument", "Document", "Node"]) {
      if (typeof globalThis[key] === "function") kept[key] = globalThis[key];
    }
    for (const [key, value] of Object.entries(kept)) {
      Object.defineProperty(Window.prototype, key, { value, configurable: true });
    }
    Object.setPrototypeOf(globalThis, Window.prototype);
    for (const key of Object.keys(kept)) {
      if (Object.prototype.hasOwnProperty.call(globalThis, key)) delete globalThis[key];
    }
  })()`, sandbox);
}
installNativeMask(sandbox);
markHostTree(sandbox);
if (typeof sandbox[NATIVE_MARK] === "function") {
  sandbox[NATIVE_MARK](loggedRandom);
  sandbox[NATIVE_MARK](SandboxDate);
  sandbox[NATIVE_MARK](SandboxDate.now);
}
const maskProbe = vm.runInContext(`({
  btoa: Function.prototype.toString.call(btoa).includes("[native code]"),
  atob: Function.prototype.toString.call(atob).includes("[native code]"),
  ws: Function.prototype.toString.call(WebSocket).includes("[native code]"),
  fetch: Function.prototype.toString.call(fetch).includes("[native code]"),
  timer: Function.prototype.toString.call(setTimeout).includes("[native code]"),
  digest: Function.prototype.toString.call(crypto.subtle.digest).includes("[native code]"),
  random: Function.prototype.toString.call(crypto.getRandomValues).includes("[native code]")
})`, sandbox);
emit({ op: "native-mask", ok: Object.values(maskProbe).every(Boolean), probe: maskProbe });
const realmNames = vm.runInContext(`(() => {
  const nameOf = (fn) => (fn && typeof fn.name === "string" && fn.name ? fn.name : "empty");
  const chain = (obj) => {
    const names = [];
    let cur = obj;
    const seen = new Set();
    while (cur && names.length < 6 && !seen.has(cur)) {
      seen.add(cur);
      names.push(nameOf(cur.constructor));
      cur = Object.getPrototypeOf(cur);
    }
    return names;
  };
  const proto = Object.getPrototypeOf(globalThis);
  return {
    win: typeof globalThis.Window,
    winName: nameOf(globalThis.Window),
    htmlName: nameOf(globalThis.HTMLDocument),
    ownWindow: Object.prototype.hasOwnProperty.call(globalThis, "Window"),
    protoWindow: !!(proto && Object.prototype.hasOwnProperty.call(proto, "Window")),
    winChain: chain(globalThis),
    docChain: chain(document),
    allType: typeof document.all,
    allEq: document.all == null,
    allSame: document.all === undefined,
  };
})()`, sandbox);
emit({ op: "realm-names", ...realmNames });
if (process.env.SPIDER_MASK_ONLY === "1") process.exit(0);
sandbox.addEventListener = (type, fn) => {
  note("win-on", type);
  if ((type === "load" || type === "DOMContentLoaded") && typeof fn === "function") queueMicrotask(() => fn({ type }));
};
sandbox.removeEventListener = () => {};
sandbox.dispatchEvent = () => true;
const markNative = sandbox[NATIVE_MARK];
if (typeof markNative === "function") {
  markNative(sandbox.addEventListener);
  markNative(sandbox.removeEventListener);
  markNative(sandbox.dispatchEvent);
}
const beforeKeys = new Set(Object.getOwnPropertyNames(sandbox));
for (const fileName of ["anti_automation.js", "login-alert.js"]) {
  const filePath = path.join(__dirname, "assets", fileName);
  if (!fs.existsSync(filePath)) {
    emit({ op: "preload", file: fileName, ok: false });
    continue;
  }
  try {
    vm.runInContext(fs.readFileSync(filePath, "utf8"), sandbox, { timeout: 8000 });
    emit({ op: "preload", file: fileName, ok: true });
  } catch (err) {
    emit({ op: "preload", file: fileName, ok: false, message: err.name + " " + String(err.message).split("\n")[0].slice(0, 120) });
  }
}
if (process.env.SPIDER_PRELOAD_ONLY === "1") {
  const added = Object.getOwnPropertyNames(sandbox).filter((key) => !beforeKeys.has(key) && key.length <= 40);
  emit({ op: "anti-keys", keys: added.slice(0, 40) });
  const anti = sandbox.AntiAutomation;
  const antiKeys = anti && typeof anti === "object" ? Object.getOwnPropertyNames(anti).filter((key) => key.length <= 40).slice(0, 30) : [];
  emit({
    op: "anti-api",
    validate: typeof sandbox.validatePageNavigation,
    anti: typeof anti,
    keys: antiKeys,
  });
  const realm = vm.runInContext(`({
    process: typeof process,
    buffer: typeof Buffer,
    escaped: Function("return this")() === globalThis,
    antiHasProcess: typeof __globalObject !== "undefined" && __globalObject !== null && typeof __globalObject.process === "object"
  })`, sandbox);
  emit({ op: "realm", ...realm });
  process.exit(0);
}
{
  const hide = process.env.SPIDER_HIDE_ENUM === "1";
  let own = 0;
  let enumerable = 0;
  let hidden = 0;
  let frozen = 0;
  for (const key of Object.getOwnPropertyNames(sandbox)) {
    own += 1;
    const desc = Object.getOwnPropertyDescriptor(sandbox, key);
    if (!desc || !desc.enumerable) continue;
    enumerable += 1;
    if (!hide) continue;
    if (!desc.configurable) {
      frozen += 1;
      continue;
    }
    Object.defineProperty(sandbox, key, { enumerable: false });
    hidden += 1;
  }
  emit({
    op: "key-shape",
    own,
    enumerable,
    hidden,
    frozen,
    after: hide ? Object.keys(sandbox).length : enumerable,
  });
}
if (process.env.SPIDER_NAME_PROBE === "1") {
  vm.runInContext(`(() => {
    const probe = { keys: 0, names: 0, symbols: 0, own: 0 };
    Object.defineProperty(globalThis, "__nameProbe", { value: probe, configurable: true });
    const wrap = (label, fn) => function probed(...args) {
      probe[label] += 1;
      return fn.apply(this, args);
    };
    const mark = globalThis[Symbol.for("spider.markNative")];
    for (const [label, host, key] of [
      ["keys", Object, "keys"],
      ["names", Object, "getOwnPropertyNames"],
      ["symbols", Object, "getOwnPropertySymbols"],
      ["own", Reflect, "ownKeys"],
    ]) {
      const probed = wrap(label, host[key]);
      Object.defineProperty(host, key, { value: probed, configurable: true, writable: true });
      if (typeof mark === "function") mark(probed);
    }
  })()`, sandbox);
}
const escapeProbe = vm.runInContext(`({
  require: typeof require,
  process: typeof process,
  module: typeof module,
  buffer: typeof Buffer,
  global: typeof global,
  window: typeof window,
  escaped: Function("return this")() === globalThis
})`, sandbox);
emit({ op: "realm-escape", ...escapeProbe });
if (process.env.SPIDER_ESCAPE_ONLY === "1") process.exit(0);
const src = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const expr = src.split(/\r?\n/).slice(2).join("\n");
scriptMark = hostReads.length;
try {
  const result = vm.runInContext(expr, sandbox, { timeout: 15000 });
  note("result", typeof result);
} catch (err) {
  note("throw", err.name + " " + String(err.message).split("\n")[0]);
  emit({ op: "error", message: err.name + " " + String(err.message).split("\n")[0] });
}
emit({
  op: "fp-reads",
  stage: "script",
  n: hostReads.length,
  hit: hostReads.filter((name) => /plugin|language|hardware|Touch|screen|pixel|Context|DataURL|fillText|speech|pdf|userAgent|platform|colorDepth|round/.test(name)),
});
if (process.env.SPIDER_NAME_PROBE === "1") {
  const counts = sandbox.__nameProbe || {};
  emit({
    op: "name-probe",
    keys: counts.keys || 0,
    names: counts.names || 0,
    symbols: counts.symbols || 0,
    own: counts.own || 0,
  });
}
{
  const stats = sandbox[NATIVE_STATS] || {};
  emit({
    op: "tostr-stats",
    spoof: stats.spoof || 0,
    host: stats.host || 0,
    names: Array.isArray(stats.names) ? stats.names.slice(0, 30) : [],
  });
}
function deliverRecv(message) {
  const ws = FakeWS.current;
  if (!ws || typeof ws.onmessage !== "function") return;
  const raw = Buffer.from(message.data, "base64");
  let payload = message.binary ? raw : raw.toString("utf8");
  if (message.binary && ws.binaryType === "arraybuffer") {
    payload = raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength);
  }
  ws.onmessage({ data: payload, type: "message", target: ws });
}

const rl = require("readline").createInterface({ input: process.stdin });
rl.on("line", (line) => {
  let message;
  try { message = JSON.parse(line); } catch { return; }
  try {
    if (message.op === "recv") deliverRecv(message);
    else if (message.op === "opened" && FakeWS.current && typeof FakeWS.current._fireOpen === "function") FakeWS.current._fireOpen();
    else if (message.op === "page" && typeof sandbox.changePage === "function") sandbox.changePage(message.page);
    else if (message.op === "submit" && typeof sandbox.submitAnswer === "function") sandbox.submitAnswer();
  } catch (err) {
    emit({ op: "error", message: String(err.message).split("\n")[0] });
  }
});
rl.on("close", () => {
  fs.writeFileSync(path.join(__dirname, "_sandbox.txt"), notes.join("\n"), "utf8");
  process.exit(0);
});
emit({ op: "bridge-ready", changePage: typeof sandbox.changePage, submit: typeof sandbox.submitAnswer });
setTimeout(() => {
  const stats = sandbox[NATIVE_STATS] || {};
  emit({
    op: "tostr-stats",
    spoof: stats.spoof || 0,
    host: stats.host || 0,
    names: Array.isArray(stats.names) ? stats.names.slice(0, 30) : [],
  });
  emit({ op: "trace", notes: notes.slice(-18).map((line) => String(line).slice(0, 110)) });
  emit({
    op: "fp-reads",
    stage: "late",
    n: hostReads.length,
    hit: hostReads.filter((name) => /plugin|language|hardware|Touch|screen|pixel|Context|DataURL|fillText|speech|pdf|userAgent|platform|colorDepth|round/.test(name)),
  });
}, 2000);
