"use strict";

const fs = require("fs");
const http = require("http");
const https = require("https");
const path = require("path");
const vm = require("vm");
const { URL } = require("url");

const ZW_ALPHABET = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"];
const ZW_INDEX = new Map(ZW_ALPHABET.map((ch, pos) => [ch, pos]));
const mintDir = path.join(__dirname, "_mint");
const minting = process.env.MINT === "1";
const mintLimit = Number(process.env.MINT_LIMIT || "100");
let mintNext = 2;
let mintBusy = false;
const mintManifest = [];

function zwDecode(text) {
  const raw = Buffer.alloc(text.length / 3);
  for (let offset = 0, at = 0; offset < text.length; offset += 3, at += 1) {
    raw[at] = (ZW_INDEX.get(text[offset]) << 6) | (ZW_INDEX.get(text[offset + 1]) << 3) | ZW_INDEX.get(text[offset + 2]);
  }
  return JSON.parse(raw.toString("utf8"));
}

function zwEncode(value) {
  const bytes = Buffer.from(JSON.stringify(value), "utf8");
  let out = "";
  for (const byte of bytes) out += ZW_ALPHABET[(byte >> 6) & 7] + ZW_ALPHABET[(byte >> 3) & 7] + ZW_ALPHABET[byte & 7];
  return out;
}

const code = fs.readFileSync(path.join(__dirname, "spiderking_challenge.js"), "utf8");
const cookie = process.env.SPIDER_COOKIE || "";
const lines = [];
const traceDir = path.join(__dirname, "_trace");
fs.mkdirSync(traceDir, { recursive: true });
let traceSeq = 0;

function publicText(value) {
  return String(value).replace(/[0-9a-f]{8,}/gi, "H");
}

function note(kind, value) {
  const text = value == null ? "" : typeof value === "string" ? value : JSON.stringify(value);
  const line = kind + " " + publicText(text).slice(0, 500);
  lines.push(line);
  const interesting = kind.startsWith("mint") || kind === "deadline" || text.includes("resultMessage");
  if (lines.length <= 12 || interesting) console.log(line);
  if (minting && interesting) {
    fs.mkdirSync(mintDir, { recursive: true });
    fs.appendFileSync(path.join(mintDir, "status.log"), line + "\n");
  }
}

function element(id) {
  const el = {
    id: id || "",
    style: {},
    textContent: "",
    innerHTML: "",
    value: "",
    disabled: false,
    className: "",
    children: [],
    appendChild() {},
    removeChild() {},
    setAttribute(name, value) { note("attr", (id || "?") + " " + name + "=" + String(value).slice(0, 120)); },
    addEventListener(type, fn) {
      note("el.on", (id || "?") + " " + type);
      el["on" + type] = fn;
    },
    removeEventListener() {},
    querySelector() { return element(); },
    querySelectorAll() { return []; },
    getContext() { return {}; },
    click() { if (typeof el.onclick === "function") el.onclick({}); },
  };
  const wrap = (field) => {
    let current = "";
    Object.defineProperty(el, field, {
      get() { return current; },
      set(value) {
        current = value == null ? "" : String(value);
        if (current) note("dom." + field, (id || "?") + " " + current.slice(0, 240));
      },
    });
  };
  wrap("textContent");
  wrap("innerHTML");
  return el;
}

const elements = new Map();
function byId(id) {
  if (!elements.has(id)) elements.set(id, element(id));
  return elements.get(id);
}

const documentStub = {
  cookie: "",
  readyState: "complete",
  visibilityState: "visible",
  hidden: false,
  characterSet: "UTF-8",
  compatMode: "CSS1Compat",
  getElementById(id) { note("getElementById", id); return byId(id); },
  getElementsByTagName() { return [element("tag")]; },
  getElementsByClassName() { return []; },
  querySelector(sel) { note("querySelector", sel); return element(String(sel)); },
  querySelectorAll() { return []; },
  createElement(tag) { note("createElement", tag); return element(tag); },
  createElementNS(ns, tag) { note("createElementNS", tag); return element(tag); },
  addEventListener(type) { note("doc.on", type); },
  removeEventListener() {},
  createTextNode(text) { return { textContent: text }; },
  hasFocus() { return true; },
};
documentStub.documentElement = element("html");
documentStub.body = element("body");
documentStub.head = element("head");

const navigatorStub = {
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
  appVersion: "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  language: "zh-CN",
  languages: ["zh-CN", "zh", "en"],
  platform: "Win32",
  vendor: "Google Inc.",
  hardwareConcurrency: 8,
  deviceMemory: 8,
  maxTouchPoints: 0,
  webdriver: false,
  cookieEnabled: true,
  plugins: { length: 0, item() { return null; }, namedItem() { return null; } },
  mimeTypes: { length: 0, item() { return null; } },
  connection: { effectiveType: "4g", rtt: 50, downlink: 10 },
};

const locationStub = {
  href: "https://www.spiderdemo.cn/authentication/spiderking_challenge/",
  origin: "https://www.spiderdemo.cn",
  protocol: "https:",
  host: "www.spiderdemo.cn",
  hostname: "www.spiderdemo.cn",
  port: "",
  pathname: "/authentication/spiderking_challenge/",
  search: "",
  hash: "",
  toString() { return this.href; },
};

function storage() {
  const bag = new Map();
  return {
    getItem(key) { return bag.has(String(key)) ? bag.get(String(key)) : null; },
    setItem(key, value) { bag.set(String(key), String(value)); note("storage", String(key) + "=" + String(value).slice(0, 80)); },
    removeItem(key) { bag.delete(String(key)); },
    clear() { bag.clear(); },
    key(index) { return Array.from(bag.keys())[index] || null; },
    get length() { return bag.size; },
  };
}

function requestText(target, options) {
  return new Promise((resolve, reject) => {
    const lib = target.protocol === "http:" ? http : https;
    const headers = Object.assign({}, options.headers || {});
    const req = lib.request(target, { method: options.method || "GET", headers }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve({ status: res.statusCode || 0, headers: res.headers, body: Buffer.concat(chunks) }));
    });
    req.on("error", reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function fetchStub(url, options) {
  const abs = new URL(String(url), "https://www.spiderdemo.cn/");
  const method = (options && options.method) || "GET";
  const headers = {
    Accept: "application/json, text/plain, */*",
    Referer: locationStub.href,
    Origin: locationStub.origin,
    "User-Agent": navigatorStub.userAgent,
  };
  if (cookie) headers.Cookie = cookie;
  if (options && options.headers) {
    const source = options.headers;
    if (typeof source.forEach === "function") {
      source.forEach((value, key) => { headers[key] = value; });
    } else {
      Object.assign(headers, source);
    }
  }
  let body = options && options.body != null ? options.body : null;
  if (body && typeof body !== "string" && !Buffer.isBuffer(body)) body = String(body);
  const headerNames = Object.keys(headers).filter((key) => key.toLowerCase() !== "cookie" && key.toLowerCase() !== "x-csrftoken");
  const contentType = headers["Content-Type"] || headers["content-type"] || "";
  note("fetch", method + " " + abs.pathname + " headers " + headerNames.join(",") + " ctype " + contentType);
  const seq = ++traceSeq;
  const slug = abs.pathname.replace(/[^a-z0-9]+/gi, "_").slice(0, 80);
  if (body) {
    const raw = Buffer.isBuffer(body) ? body : Buffer.from(String(body), "utf8");
    fs.writeFileSync(path.join(traceDir, seq + "_" + method + "_req_" + slug + ".bin"), raw);
    note("fetch.body_bytes", String(raw.length));
  }
  if (abs.pathname.includes("/submit") && body) {
    try {
      fs.mkdirSync(mintDir, { recursive: true });
      fs.writeFileSync(path.join(mintDir, "submit_shape.json"), nativeStringify(redact(zwDecode(String(body)), 0)), "utf8");
      note("mint_submit_shape", "written");
    } catch (error) {
      note("mint_submit_shape_error", error.message);
    }
  }
  if (minting && body && abs.pathname.includes("/page/")) {
    fs.mkdirSync(mintDir, { recursive: true });
    const text = String(body);
    const decoded = zwDecode(text);
    const pageNo = Number(decoded.page);
    const file = "page-" + String(pageNo).padStart(3, "0") + ".bin";
    fs.writeFileSync(path.join(mintDir, file), text, "utf8");
    mintManifest.push({ kind: "page", page: pageNo, path: abs.pathname, file });
    fs.writeFileSync(path.join(mintDir, "manifest.json"), nativeStringify(mintManifest), "utf8");
    note("mint_saved", "page " + pageNo);
    const payload = { page: pageNo, success: true, values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] };
    const encoded = zwEncode(payload);
    queueMintAdvance();
    return {
      ok: true,
      status: 200,
      statusText: "200",
      url: abs.toString(),
      headers: { get() { return "application/json"; }, has() { return true; } },
      text: async () => encoded,
      json: async () => payload,
      arrayBuffer: async () => Buffer.from(encoded).buffer,
      clone() { return this; },
    };
  }
  const result = await requestText(abs, { method, headers, body });
  fs.writeFileSync(path.join(traceDir, seq + "_" + result.status + "_res_" + slug + ".bin"), result.body);
  const text = result.body.toString("utf8");
  const visible = text.replace(/[\u200b\u200c\u200d\u2060-\u2064\ufeff]/g, "");
  note("fetch.status", result.status + " bytes " + result.body.length + " visible " + JSON.stringify(visible.slice(0, 180)));
  if (abs.pathname.includes("/submit")) writeSubmitPublic(text, result.status);
  if (abs.pathname.includes("/page/") && !global.triedNext) {
    global.triedNext = true;
    setTimeout(() => {
      const extra = Object.getOwnPropertyNames(sandbox).filter((name) => !(name in global));
      note("extra", extra.slice(0, 60).join(","));
      note("changePage", typeof sandbox.changePage);
      if (typeof sandbox.changePage === "function") {
        try { sandbox.changePage(2); note("called", "changePage 2"); }
        catch (error) { note("change_error", error.message); }
      }
    }, 300);
  }
  const headerKeys = Object.keys(result.headers).filter((key) => key !== "set-cookie");
  note("fetch.resp_headers", headerKeys.join(","));
  return {
    ok: result.status >= 200 && result.status < 300,
    status: result.status,
    statusText: String(result.status),
    url: abs.toString(),
    headers: {
      get(name) { return result.headers[String(name).toLowerCase()] || null; },
      has(name) { return String(name).toLowerCase() in result.headers; },
    },
    text: async () => text,
    json: async () => JSON.parse(text),
    arrayBuffer: async () => result.body.buffer.slice(result.body.byteOffset, result.body.byteOffset + result.body.byteLength),
    clone() { return this; },
  };
}

function writeSubmitPublic(text, status) {
  let payload;
  try {
    payload = zwDecode(text);
  } catch (_) {
    const visible = String(text).replace(/[\u200b\u200c\u200d\u2060-\u2064\ufeff]/g, "");
    payload = { error: visible.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 180) };
  }
  const kept = {};
  for (const key of ["success", "message", "msg", "error", "score", "correct", "is_correct", "completed"]) {
    if (payload && Object.prototype.hasOwnProperty.call(payload, key)) kept[key] = payload[key];
  }
  fs.mkdirSync(mintDir, { recursive: true });
  fs.writeFileSync(path.join(mintDir, "submit_public.json"), nativeStringify(kept), "utf8");
  note("mint_submit_status", String(status) + " keys " + Object.keys(kept).join(","));
}

function waitForAnswer() {
  const timer = setInterval(() => {
    const file = path.join(mintDir, "answer.txt");
    if (!fs.existsSync(file)) return;
    const answer = fs.readFileSync(file, "utf8").trim();
    if (!/^\d+$/.test(answer)) return;
    clearInterval(timer);
    try {
      const input = byId("answerInput");
      input.value = answer;
      input.setAttribute("value", answer);
      note("mint_answer_set", String(answer.length));
      const button = byId("submitBtn");
      button.disabled = false;
      button.click();
    } catch (error) {
      note("mint_submit_error", error.message);
    }
  }, 200);
}

function queueMintAdvance() {
  if (!minting || mintBusy) return;
  mintBusy = true;
  setTimeout(() => {
    mintBusy = false;
    if (mintNext <= mintLimit) {
      const page = mintNext++;
      note("mint_go", String(page));
      try { sandbox.changePage(page); }
      catch (error) { note("mint_error", error.message); }
    } else if (mintNext === mintLimit + 1) {
      mintNext += 1;
      if (process.env.WAIT_ANSWER === "1") {
        note("mint_wait", String(mintManifest.length));
        waitForAnswer();
        return;
      }
      note("mint_submit", "");
      try {
        const button = byId("submitBtn");
        button.disabled = false;
        button.click();
      } catch (error) { note("mint_submit_error", error.message); }
    }
  }, 0);
}

function summarize(data) {
  if (data == null || typeof data !== "object") return String(data).slice(0, 160);
  return JSON.stringify({
    cmd: data.cmd,
    success: data.success,
    error: data.error ? String(data.error).slice(0, 80) : undefined,
    keys: Object.keys(data).slice(0, 12),
  });
}

function redact(value, depth) {
  if (value == null || typeof value === "number" || typeof value === "boolean") return value;
  if (typeof value === "string") {
    if (/^[0-9a-f]{8,}$/i.test(value)) return "H" + value.length;
    if (value.length > 48) return "S" + value.length;
    return value;
  }
  if (depth > 5) return typeof value;
  if (Array.isArray(value)) return value.slice(0, 6).map((item) => redact(item, depth + 1));
  if (typeof value === "object") {
    const out = {};
    for (const key of Object.keys(value).slice(0, 30)) out[key] = redact(value[key], depth + 1);
    return out;
  }
  return typeof value;
}

function makeWorkerBox() {
  const box = {};
  for (const key of Object.getOwnPropertyNames(global)) {
    if (key === "process" || key === "module" || key === "require" || key === "exports") continue;
    try { box[key] = global[key]; } catch (_) {}
  }
  box.TextEncoder = TracingEncoder;
  Object.assign(box, {
    console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
    fetch: fetchStub,
    location: locationStub,
    navigator: navigatorStub,
    postMessage() {},
    close() {},
    name: "SharedWorkerGlobalScope",
  });
  Object.defineProperty(box, Symbol.toStringTag, { value: "SharedWorkerGlobalScope" });
  box.globalThis = box;
  box.self = box;
  return box;
}

function SharedWorker(url) {
  note("SharedWorker", String(url));
  const workerPort = {
    onmessage: null,
    start() { note("workerPort.start", ""); },
    postMessage(data) {
      note("worker->page", summarize(data));
      const handler = pagePort.onmessage;
      if (typeof handler === "function") {
        Promise.resolve().then(() => handler({ data })).catch((error) => note("page handler", error.message));
      }
    },
    addEventListener(type, fn) {
      if (type === "message") this.onmessage = fn;
    },
    removeEventListener() {},
    close() {},
  };
  const pagePort = {
    onmessage: null,
    start() { note("pagePort.start", ""); },
    postMessage(data) {
      note("page->worker", summarize(data));
      if (data && data.state) {
        fs.writeFileSync(path.join(__dirname, "_state_shape.json"), nativeStringify(redact(data.state), null, 2), "utf8");
      }
      const handler = workerPort.onmessage;
      if (typeof handler === "function") {
        Promise.resolve().then(() => handler({ data })).catch((error) => note("worker handler", error.message));
      }
    },
    addEventListener(type, fn) {
      if (type === "message") this.onmessage = fn;
    },
    removeEventListener() {},
    close() {},
  };
  const box = makeWorkerBox();
  const workerSrc = fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8");
  vm.runInNewContext(workerSrc, box, { filename: "baidu.js", timeout: 8000 });
  if (typeof box.onconnect === "function") box.onconnect({ ports: [workerPort] });
  else note("worker", "missing onconnect");
  this.port = pagePort;
}

function WorkerCtor(url) {
  note("Worker", String(url));
  this.postMessage = function (data) { note("worker.post", data); };
  this.addEventListener = function (type) { note("worker.on", type); };
  this.terminate = function () {};
}

const stringifyLog = [];
const blobs = [];
let captureBlobs = false;
const nativeStringify = JSON.stringify;
const nativeJoin = Array.prototype.join;
const realEncoder = new TextEncoder();

function remember(kind, value) {
  if (!captureBlobs || blobs.length >= 800) return;
  const text = value == null ? "" : String(value);
  if (text.length > 6000) return;
  if (kind !== "utf8" && text.length < 16) return;
  if (kind !== "utf8" && text.indexOf("{") < 0 && text.indexOf("|") < 0 && text.indexOf("spider") < 0) return;
  blobs.push(kind + "\t" + text.length + "\t" + text);
}

Array.prototype.join = function joined(sep) {
  const text = nativeJoin.call(this, sep);
  if (typeof text === "string" && text.length >= 24) remember("join", text);
  return text;
};

function TracingEncoder() {}
TracingEncoder.prototype.encode = function encode(input) {
  remember("utf8", input);
  return realEncoder.encode(input == null ? "" : String(input));
};
TracingEncoder.prototype.encodeInto = function encodeInto(input, dest) {
  remember("utf8", input);
  return realEncoder.encodeInto(String(input), dest);
};
const sandbox = {};
for (const key of Object.getOwnPropertyNames(global)) {
  if (key === "process" || key === "module" || key === "require" || key === "exports") continue;
  try { sandbox[key] = global[key]; } catch (_) {}
}
Object.assign(sandbox, {
  console,
  document: documentStub,
  navigator: navigatorStub,
  location: locationStub,
  innerWidth: 1920,
  innerHeight: 1080,
  outerWidth: 1920,
  outerHeight: 1040,
  screenX: 0,
  screenY: 0,
  devicePixelRatio: 1,
  localStorage: storage(),
  sessionStorage: storage(),
  fetch: fetchStub,
  SharedWorker,
  Worker: WorkerCtor,
  screen: { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24 },
  history: { length: 2, state: null, pushState() {}, replaceState() {} },
  performance: { now: () => Date.now(), timeOrigin: Date.now() },
  addEventListener() {},
  removeEventListener() {},
  postMessage() {},
  requestAnimationFrame(fn) { return setTimeout(() => fn(Date.now()), 16); },
  cancelAnimationFrame(id) { clearTimeout(id); },
  getComputedStyle() { return { getPropertyValue() { return ""; } }; },
  matchMedia() { return { matches: false, addEventListener() {}, removeEventListener() {} }; },
  origin: locationStub.origin,
  isSecureContext: true,
  chrome: { runtime: {} },
  TextEncoder: TracingEncoder,
  TextDecoder,
});
const nativeSetTimeout = setTimeout;
const nativeSetInterval = setInterval;
sandbox.setTimeout = () => 0;
sandbox.setInterval = () => 0;
sandbox.JSON = {
  parse: JSON.parse,
  stringify(value, replacer, space) {
    const text = nativeStringify(value, replacer, space);
    if (typeof text === "string" && stringifyLog.length < 800) stringifyLog.push(text);
    return text;
  },
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
sandbox.parent = sandbox;
sandbox.top = sandbox;
sandbox.frames = sandbox;
sandbox.document = documentStub;

const hostNames = [];
function noteHost(kind, args) {
  const key = args.find((item) => typeof item === "string" && item.length > 0 && item.length < 80);
  if (!key || hostNames.length >= 250) return;
  const line = kind + " " + key;
  if (hostNames.includes(line)) return;
  hostNames.push(line);
}
sandbox.__vmpHostGet = function (...args) {
  noteHost("get", args);
  const key = args.length > 1 ? args[1] : args[0];
  const obj = args.length > 1 ? args[0] : sandbox;
  if (obj != null && (typeof key === "string" || typeof key === "symbol")) {
    try { return obj[key]; } catch (_) { return undefined; }
  }
  return undefined;
};
sandbox.__vmpHostHas = function (...args) {
  noteHost("has", args);
  const key = args.length > 1 ? args[1] : args[0];
  const obj = args.length > 1 ? args[0] : sandbox;
  try { return obj != null && key in Object(obj); } catch (_) { return false; }
};
sandbox.__vmpHostSet = function (...args) {
  noteHost("set", args);
  if (args.length >= 3 && args[0] != null) {
    try { args[0][args[1]] = args[2]; return true; } catch (_) { return false; }
  }
  return false;
};
sandbox.__vmpHostCanSet = function () { return true; };
sandbox.__vmpHostTypeof = function (...args) {
  noteHost("typeof", args);
  const key = args.length > 1 ? args[1] : args[0];
  const obj = args.length > 1 ? args[0] : sandbox;
  try { return typeof obj[key]; } catch (_) { return "undefined"; }
};

const deadline = setTimeout(() => {
  note("deadline", "exit");
  fs.writeFileSync(path.join(__dirname, "_vm_calls.txt"), lines.join("\n"), "utf8");
  fs.writeFileSync(path.join(__dirname, "_stringify.txt"), stringifyLog.join("\n"), "utf8");
  process.exit(0);
}, minting ? 900000 : 20000);
deadline.unref();

for (const name of fs.readdirSync(traceDir)) fs.unlinkSync(path.join(traceDir, name));
captureBlobs = true;
try {
  vm.runInNewContext(code, sandbox, { filename: "spiderking_challenge.js", timeout: 18000 });
  note("done", "returned");
} catch (error) {
  const name = error && error.name ? error.name : "Error";
  const message = error && error.message ? error.message : "";
  note("sync_error", name + " " + message);
}
fs.writeFileSync(path.join(__dirname, "_vm_calls.txt"), lines.join("\n"), "utf8");
function loadCodec() {
  const box = {};
  for (const key of Object.getOwnPropertyNames(global)) {
    if (key === "process" || key === "module" || key === "require" || key === "exports") continue;
    try { box[key] = global[key]; } catch (_) {}
  }
  box.console = { log() {}, info() {}, warn() {}, error() {}, debug() {} };
  box.TextEncoder = TextEncoder;
  box.TextDecoder = TextDecoder;
  box.self = box;
  box.globalThis = box;
  const previous = captureBlobs;
  captureBlobs = false;
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });
  captureBlobs = previous;
  return box;
}

function collectSeals() {
  const seals = new Map();
  const zw = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"];
  const index = new Map(zw.map((ch, pos) => [ch, pos]));
  function decode(text) {
    const raw = Buffer.alloc(text.length / 3);
    for (let offset = 0, at = 0; offset < text.length; offset += 3, at += 1) {
      raw[at] = (index.get(text[offset]) << 6) | (index.get(text[offset + 1]) << 3) | index.get(text[offset + 2]);
    }
    return JSON.parse(raw.toString("utf8"));
  }
  function walk(value, pathName) {
    if (typeof value === "string" && /^[0-9a-f]{32}$/.test(value)) seals.set(pathName, value);
    else if (value && typeof value === "object") {
      for (const key of Object.keys(value)) walk(value[key], pathName ? pathName + "." + key : key);
    }
  }
  for (const name of fs.readdirSync(traceDir)) {
    if (!name.includes("POST_req")) continue;
    try { walk(decode(fs.readFileSync(path.join(traceDir, name), "utf8")), name.slice(0, 1)); } catch (_) {}
  }
  return seals;
}

function redactText(text) {
  return text
    .replace(/[0-9a-f]{8,}/gi, (item) => "H" + item.length)
    .replace(/[\u0000-\u001f]/g, (ch) => "\\x" + ch.charCodeAt(0).toString(16).padStart(2, "0"))
    .slice(0, 220);
}

function matchBlobs() {
  const nodeCrypto = require("crypto");
  const codec = loadCodec();
  const seals = collectSeals();
  const roles = ["main", "page", "worker", "submit", "proof", "gate", "pulse", "seal", "env", "media", "report"];
  const linesOut = [];
  const templates = [];
  linesOut.push("blobs " + blobs.length);
  linesOut.push("seals " + Array.from(seals.keys()).join(","));
  const wanted = new Set(seals.values());
  const seen = new Set();
  const parsed = blobs.map((blob) => {
    const parts = blob.split("\t");
    return { kind: parts[0], text: parts.slice(2).join("\t") };
  });
  parsed.forEach((item, index) => templates.push(index + " " + item.kind + " " + item.text.length + " " + redactText(item.text)));
  function hit(digest, label, template) {
    if (!wanted.has(digest) || seen.has(digest + "|" + label)) return;
    seen.add(digest + "|" + label);
    const names = Array.from(seals.entries()).filter((entry) => entry[1] === digest).map((entry) => entry[0]);
    linesOut.push("MATCH " + names.join("|") + " " + label + " " + template);
  }
  for (const item of parsed) {
    const template = redactText(item.text);
    hit(codec.digest(item.text), item.kind + " raw", template);
    for (const role of roles) {
      hit(codec.digest("spiderdemo-spiderking/v1|" + role + "|" + item.text), item.kind + " d:" + role, template);
    }
    for (const alg of ["md5", "sha1", "sha256"]) {
      const full = nodeCrypto.createHash(alg).update(item.text, "utf8").digest("hex");
      hit(full.slice(0, 32), item.kind + " " + alg, template);
    }
  }
  const salts = [];
  try {
    const initName = fs.readdirSync(traceDir).find((name) => name.includes("init_") && name.includes("_res_"));
    if (initName) {
      const zw = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"];
      const index = new Map(zw.map((ch, pos) => [ch, pos]));
      const text = fs.readFileSync(path.join(traceDir, initName), "utf8");
      const raw = Buffer.alloc(text.length / 3);
      for (let offset = 0, at = 0; offset < text.length; offset += 3, at += 1) {
        raw[at] = (index.get(text[offset]) << 6) | (index.get(text[offset + 1]) << 3) | index.get(text[offset + 2]);
      }
      const init = JSON.parse(raw.toString("utf8"));
      for (const [name, value] of Object.entries(init.salts || {})) salts.push([name + "Salt", value]);
      salts.push(["ticket", init.ticket], ["sid", init.sid]);
    }
  } catch (_) {}
  const cn = (lines.join("\n").match(/cn=([0-9a-f]{32})/) || [])[1];
  if (cn) salts.push(["cn", cn]);
  for (const item of parsed) {
    if (item.text.length > 400) continue;
    for (const [saltName, salt] of salts) {
      const pairs = [
        [saltName + "+t", salt + item.text],
        ["t+" + saltName, item.text + salt],
        [saltName + "|t", salt + "|" + item.text],
        ["t|" + saltName, item.text + "|" + salt],
      ];
      for (const [label, material] of pairs) hit(codec.digest(material), label, redactText(item.text));
    }
  }
  if (!linesOut.some((line) => line.startsWith("MATCH "))) linesOut.push("no seal match");
  const rev = new Map();
  for (const [saltName, salt] of salts) rev.set(salt, saltName);
  for (const [sealName, seal] of seals) rev.set(seal, sealName);
  const labeled = parsed.map((item, index) => {
    let shown = rev.get(item.text);
    if (!shown && item.text.includes("|")) {
      shown = item.text.split("|").map((part) => rev.get(part) || (/^[0-9a-f]{6,}$/i.test(part) ? "H" + part.length : part)).join(" | ");
    }
    if (!shown && item.text.startsWith("{")) {
      try {
        const obj = JSON.parse(item.text);
        const out = {};
        for (const [key, value] of Object.entries(obj)) {
          out[key] = typeof value === "string" && rev.has(value) ? rev.get(value) : value;
        }
        shown = JSON.stringify(out);
      } catch (_) {}
    }
    return index + " " + item.kind + " " + (shown || redactText(item.text));
  });
  fs.writeFileSync(path.join(__dirname, "_labeled.txt"), labeled.join("\n"), "utf8");
  fs.writeFileSync(path.join(__dirname, "_seal_matches.txt"), linesOut.join("\n"), "utf8");
  fs.writeFileSync(path.join(__dirname, "_blob_templates.txt"), templates.join("\n"), "utf8");
  fs.writeFileSync(path.join(__dirname, "_host_names.txt"), hostNames.join("\n"), "utf8");
  note("match_lines", String(linesOut.length));
  note("host_names", String(hostNames.length));
}

process.on("beforeExit", () => {
  captureBlobs = false;
  if (minting) {
    note("mint_manifest", String(mintManifest.length));
    fs.writeFileSync(path.join(__dirname, "_vm_calls.txt"), lines.join("\n"), "utf8");
    return;
  }
  note("stringify_count", String(stringifyLog.length));
  note("blob_count", String(blobs.length));
  fs.writeFileSync(path.join(__dirname, "_vm_calls.txt"), lines.join("\n"), "utf8");
  fs.writeFileSync(path.join(__dirname, "_stringify.txt"), stringifyLog.join("\n"), "utf8");
  try { matchBlobs(); } catch (error) { note("match_error", error.message); }
  fs.writeFileSync(path.join(__dirname, "_vm_calls.txt"), lines.join("\n"), "utf8");
});
