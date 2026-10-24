const fs = require("fs");
const path = require("path");

const sourcePath = path.join(__dirname, "assets", "jsvmp_patched.js");
const source = fs.readFileSync(sourcePath, "utf8") + `
globalThis.__API={};
for (const __n of ["loadPageData","changePage","submitAnswer","apiGetPageData","apiInitChallenge","apiSubmitAnswer","initializePage","renderNumbers","generateNumbers","_generateNumbers","renderServerMixedContent","_apiGetPageData","_apiInitChallenge","_apiSubmitAnswer","ProtobufAuth","BrowserFingerprint","ChallengePageRequest","ChallengePageResponse","ChallengeSubmitRequest","ProtobufAuthClient","protobufClient","CSSAntiCrawlerDecryptor","cssDecryptor"]) {
  try { globalThis.__API[__n] = eval(__n); }
  catch (error) { globalThis.__API[__n] = undefined; }
}
`;

globalThis.__STRS = [];
const logs = [];
function note(kind, value) {
  const text = typeof value === "string" ? value : JSON.stringify(value);
  logs.push(kind + " " + String(text).slice(0, 500));
}

function element() {
  const node = {
    style: {},
    className: "",
    innerHTML: "",
    textContent: "",
    value: "",
    children: [],
    classList: {
      add() {},
      remove() {},
      toggle() {},
      contains() { return false; },
    },
    setAttribute() {},
    getAttribute() { return null; },
    appendChild(child) { this.children.push(child); return child; },
    removeChild() {},
    addEventListener() {},
    removeEventListener() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    getContext(kind) {
      if (globalThis.__CANVAS_OK === false) return null;
      note("CTX", String(kind));
      return {
        canvas: node,
        fillRect() {},
        fillText() {},
        strokeText() {},
        measureText() { return { width: 12 }; },
        beginPath() {},
        closePath() {},
        moveTo() {},
        lineTo() {},
        arc() {},
        rect() {},
        fill() {},
        stroke() {},
        getImageData() { return { data: new Uint8Array(64) }; },
        font: "14px Arial",
        textBaseline: "top",
        fillStyle: "#000",
      };
    },
    toDataURL() {
      const url = "data:image/png;base64,iVBORw0KGgo=";
      if (process.env.WIRE_LOG === "1") console.log("CANVAS_URL", "len=" + url.length);
      return url;
    },
  };
  return node;
}

const listeners = [];
function remember(target, type, fn) {
  listeners.push({ target, type, fn });
  note("ON", target + " " + type);
}
const documentStub = {
  cookie: "",
  readyState: "complete",
  body: element(),
  head: element(),
  documentElement: element(),
  getElementById() { return element(); },
  querySelector() { return element(); },
  querySelectorAll() { return []; },
  createElement: nativeFn("createElement", (tag) => { note("CREATE", tag); return element(); }),
  addEventListener(type, fn) { remember("document", type, fn); },
  removeEventListener() {},
};

globalThis.window = globalThis;
globalThis.self = globalThis;
globalThis.addEventListener = (type, fn) => remember("window", type, fn);
Object.defineProperty(globalThis, "document", {
  get: nativeGet("document", () => documentStub),
  configurable: true,
});
const CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
function nativeGet(name, read) {
  const getter = function () { return read(); };
  getter.toString = () => "function get " + name + "() { [native code] }";
  return getter;
}
function nativeFn(name, fn) {
  const wrapped = function (...args) { return fn.apply(this, args); };
  wrapped.toString = () => "function " + name + "() { [native code] }";
  return wrapped;
}
class Navigator {
  constructor() {
    this.languages = ["zh-CN", "zh"];
    this.platform = "Win32";
    this.webdriver = false;
    this.hardwareConcurrency = 8;
    this.deviceMemory = 8;
    this.appName = "Netscape";
    this.vendor = "Google Inc.";
  }
}
function watchPlugin(item) {
  return new Proxy(item, {
    get(obj, prop, receiver) {
      if (process.env.WIRE_LOG === "1" && typeof prop === "string") console.log("PLUGIN_GET", prop);
      return Reflect.get(obj, prop, receiver);
    },
  });
}
const PLUGIN_LIST = [
  watchPlugin({ name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" }),
  watchPlugin({ name: "Chrome PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" }),
  watchPlugin({ name: "Chromium PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" }),
];
class PluginArray {}
PLUGIN_LIST.forEach((item, index) => { PluginArray.prototype[index] = item; });
Object.defineProperty(PluginArray.prototype, "length", { get: nativeGet("length", () => PLUGIN_LIST.length), configurable: true });
PluginArray.prototype.item = nativeFn("item", function item(index) { return PLUGIN_LIST[index] || null; });
PluginArray.prototype.namedItem = nativeFn("namedItem", function namedItem(name) { return PLUGIN_LIST.find((item) => item.name === name) || null; });
PluginArray.prototype.refresh = nativeFn("refresh", () => {});
globalThis.PluginArray = PluginArray;
const pluginArray = new PluginArray();
Object.defineProperty(Navigator.prototype, "userAgent", { get: nativeGet("userAgent", () => CHROME_UA), configurable: true });
Object.defineProperty(Navigator.prototype, "language", { get: nativeGet("language", () => "zh-CN"), configurable: true });
Object.defineProperty(Navigator.prototype, "cookieEnabled", { get: nativeGet("cookieEnabled", () => true), configurable: true });
Object.defineProperty(Navigator.prototype, "plugins", { get: nativeGet("plugins", () => pluginArray), configurable: true });
Navigator.prototype.javaEnabled = nativeFn("javaEnabled", () => false);
class Screen {
  constructor() {
    this.width = 1920;
    this.height = 1080;
    this.availWidth = 1920;
    this.availHeight = 1040;
    this.colorDepth = 24;
    this.pixelDepth = 24;
  }
}
class StorageBox {
  constructor() {
    this._data = {};
  }
  getItem(key) { note("LSGET", String(key)); return Object.prototype.hasOwnProperty.call(this._data, key) ? this._data[key] : null; }
  setItem(key, value) {
    const text = String(value);
    const codes = [...text].slice(0, 8).map((ch) => ch.charCodeAt(0)).join(".");
    note("LSSET", String(key) + " len=" + text.length + " codes=" + codes);
    this._data[key] = text;
  }
  removeItem(key) { delete this._data[key]; }
  clear() { this._data = {}; }
  key(index) { return Object.keys(this._data)[index] || null; }
  get length() { return Object.keys(this._data).length; }
}
function watch(label, target) {
  return new Proxy(target, {
    get(obj, prop, receiver) {
      if (prop !== "then" && typeof prop === "string") {
        note("GET", label + "." + prop);
        if (process.env.WIRE_LOG === "1" && label === "navigator") console.log("NAV", prop);
      }
      return Reflect.get(obj, prop, receiver);
    },
  });
}
globalThis.Navigator = Navigator;
globalThis.Screen = Screen;
globalThis.Storage = StorageBox;
globalThis.navigator = watch("navigator", new Navigator());
globalThis.location = {
  href: "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
  search: "?challenge_type=jsvmp_challenge",
  pathname: "/authentication/jsvmp_challenge",
  origin: "https://www.spiderdemo.cn",
  host: "www.spiderdemo.cn",
  hostname: "www.spiderdemo.cn",
  protocol: "https:",
};
const storage = () => ({
  getItem() { return null; },
  setItem() {},
  removeItem() {},
  clear() {},
  key() { return null; },
  length: 0,
});
globalThis.localStorage = new StorageBox();
globalThis.sessionStorage = new StorageBox();
globalThis.alert = (message) => note("ALERT", message);
globalThis.validatePageNavigation = () => true;
eval(fs.readFileSync(path.join(__dirname, "assets", "jsencrypt1.js"), "utf8"));
const RealJSEncrypt = globalThis.JSEncrypt;
globalThis.JSEncrypt = function JSEncrypt() {
  const inner = new RealJSEncrypt();
  this.setPublicKey = (key) => {
    if (process.env.ALIGN_ONLY !== "1" && process.env.COOKIE_SYNC !== "1" && process.env.PLAIN_SHAPE !== "1") note("PUBKEY", String(key).slice(0, 40));
    return inner.setPublicKey(key);
  };
  this.encrypt = (value) => {
    const text = String(value);
    const token = inner.encrypt(text);
    let decoded = "";
    try { decoded = Buffer.from(text, "base64").toString("utf8"); } catch (error) { decoded = ""; }
    const suffix = decoded.includes("_") ? decoded.slice(decoded.indexOf("_") + 1) : "";
    const head = decoded.slice(0, decoded.indexOf("_"));
    const year = (suffix.match(/^jsvmp_secret_key_(\d{4})$/) || [])[1] || "";
    globalThis.__LAST_TOKEN = token;
    globalThis.__LAST_YEAR = year;
    if (process.env.ALIGN_ONLY !== "1" && process.env.COOKIE_SYNC !== "1" && process.env.PLAIN_SHAPE !== "1" && !globalThis.__MOD_LOGGED) {
      globalThis.__MOD_LOGGED = true;
      try {
        const modulus = inner.getKey().n.toString(16);
        note("MOD", "bits=" + inner.getKey().n.bitLength() + " head=" + modulus.slice(0, 8) + " tail=" + modulus.slice(-8));
      } catch (error) {
        note("MOD_ERR", error.message);
      }
    }
    if (!globalThis.__ENC) globalThis.__ENC = [];
    globalThis.__ENC.push({ year, ts: /^\d{10}$/.test(head) ? Number(head) : null, len: text.length, token });
    let btoaForm = false;
    if (/^[A-Za-z0-9+/]+={0,2}$/.test(text) && text.length % 4 === 0) {
      btoaForm = Buffer.from(decoded, "binary").toString("base64") === text;
    } else {
      decoded = "";
    }
    const matched = decoded.match(/^(\d{10})_jsvmp_secret_key_(\d{4})$/);
    const template = Boolean(matched && btoaForm);
    if (!globalThis.__PLAINS) globalThis.__PLAINS = [];
    globalThis.__PLAINS.push({
      year: matched ? matched[2] : year,
      len: text.length,
      text,
      token,
      template,
      ts: matched ? Number(matched[1]) : null,
      btoaForm,
    });
    if (process.env.PLAIN_SHAPE === "1") {
      console.log(
        "SHAPE",
        "len=" + text.length,
        "btoa=" + btoaForm,
        "decoded_len=" + (btoaForm ? decoded.length : 0),
        "template=" + template,
        "year=" + (matched ? matched[2] : ""),
        "out_len=" + (token ? String(token).length : 0),
      );
      if (template && token && !globalThis.__PKCS_DONE) {
        globalThis.__PKCS_DONE = true;
        try {
          const pagePub = inner.getPublicKey();
          console.log("PKCS", JSON.stringify(comparePkcs(text, token, pagePub)));
        } catch (error) {
          console.log("PKCS_FAIL", error && error.name ? error.name : "error");
        }
      }
    }
    if (process.env.ALIGN_ONLY !== "1" && process.env.COOKIE_SYNC !== "1" && process.env.PLAIN_SHAPE !== "1") {
      const preview = year ? "" : text.slice(0, 16).replace(/[^\x20-\x7e]/g, "?");
      note("ENCRYPT", "len=" + text.length + " out=" + (token ? token.length : 0) + " year=" + year + " ts=" + (year ? head : "") + " preview=" + preview);
    }
    return token;
  };
};
globalThis.confirm = () => true;
globalThis.atob = (value) => Buffer.from(value, "base64").toString("binary");
globalThis.btoa = (value) => {
  const sourceText = String(value);
  const template = /^\d{10}_jsvmp_secret_key_\d{4}$/.test(sourceText);
  if (process.env.PLAIN_SHAPE === "1") {
    console.log("BTOA", "in_len=" + sourceText.length, "template=" + template);
  }
  if (process.env.INIT_CHECK === "1") {
    if (template) globalThis.__BTOA_LEN = sourceText.length;
    const seen = new Map();
    for (const item of initLeaves(initPayload)) {
      const contains = item.text.length > 0 && sourceText.includes(item.text);
      seen.set(item.key, (seen.get(item.key) || false) || contains);
    }
    for (const [key, contains] of seen) console.log("INIT_IN", key, "contains=" + contains);
    console.log("BTOA", "in_len=" + sourceText.length, "template=" + template);
  }
  return Buffer.from(sourceText, "binary").toString("base64");
};
function initLeaves(value, key = "") {
  if (Array.isArray(value)) {
    const name = key || "[]";
    const texts = value.map((item) => (item == null ? "" : String(item)));
    return [
      { key: name, text: texts.join(",") },
      { key: name, text: JSON.stringify(value) },
      ...texts.map((text) => ({ key: name, text })),
    ];
  }
  if (value && typeof value === "object") {
    const rows = [];
    for (const name of Object.keys(value)) {
      const child = name;
      const path = key ? key + "." + child : child;
      rows.push(...initLeaves(value[name], path));
    }
    return rows;
  }
  return [{ key: key || "value", text: value == null ? "" : String(value) }];
}
function watchInit(value, path) {
  if (!value || typeof value !== "object") return value;
  return new Proxy(value, {
    get(target, prop, receiver) {
      if (typeof prop === "string") console.log("INIT_READ", (path ? path + "." : "") + prop);
      const child = Reflect.get(target, prop, receiver);
      if (child && typeof child === "object") return watchInit(child, (path ? path + "." : "") + String(prop));
      return child;
    },
  });
}
function comparePkcs(plain, pageToken, pagePub) {
  const crypto = require("crypto");
  const { spawnSync } = require("child_process");
  const pair = crypto.generateKeyPairSync("rsa", { modulusLength: 1024, publicExponent: 65537 });
  const temp = new RealJSEncrypt();
  temp.setPublicKey(pair.publicKey.export({ type: "spki", format: "pem" }).toString());
  const jsTemp = temp.encrypt(plain);
  const pageRaw = Buffer.from(String(pageToken || ""), "base64").length;
  const base = {
    page_b64_len: String(pageToken || "").length,
    page_raw_len: pageRaw,
    js_encrypt_ok: Boolean(jsTemp),
  };
  if (!jsTemp) return base;
  const proc = spawnSync(
    "D:\\reverse_ENV\\.venv\\Scripts\\python.exe",
    [path.join(__dirname, "_cmp_pkcs.py")],
    {
      input: JSON.stringify({
        plain,
        page_pub: pagePub,
        priv: pair.privateKey.export({ type: "pkcs8", format: "pem" }).toString(),
        js_temp: jsTemp,
      }),
      encoding: "utf-8",
    },
  );
  if (proc.status !== 0 || !proc.stdout) {
    base.py_ok_proc = false;
    return base;
  }
  const parsed = JSON.parse(proc.stdout);
  parsed.page_b64_len = base.page_b64_len;
  parsed.page_raw_len = base.page_raw_len;
  parsed.b64_len_eq = parsed.page_b64_len === parsed.py_b64_len;
  parsed.raw_len_eq = parsed.page_raw_len === parsed.py_raw_len;
  parsed.js_encrypt_ok = true;
  return parsed;
}
function encodedLen(value) {
  if (typeof value !== "number" || value < 0) return 1;
  let left = value;
  let size = 1;
  while (left > 127) {
    left = Math.floor(left / 128);
    size += 1;
  }
  return size;
}
function hookWriter() {
  const auth = globalThis.__API && globalThis.__API.ProtobufAuth;
  const Orig = auth && auth.BinaryWriter;
  if (typeof Orig !== "function") {
    console.log("WRITER_MISSING");
    return;
  }
  const wireOf = {
    writeString: 2,
    writeMessage: 2,
    writeBytes: 2,
    writeBool: 0,
    writeInt32: 0,
    writeRepeatedInt32: 2,
  };
  const names = Object.getOwnPropertyNames(Orig.prototype).filter((name) => name !== "constructor" && typeof Orig.prototype[name] === "function");
  console.log("WRITER_METHODS", names.join(","));
  let buffers = 0;
  const wrap = (fn, name) => function wrappedWrite(...args) {
    if (name === "getResultBuffer") {
      const out = fn.apply(this, args);
      const len = out && (out.byteLength || out.length) ? (out.byteLength || out.length) : 0;
      buffers += 1;
      console.log("WRITE_BUF", "n=" + buffers, "len=" + len);
      return out;
    }
    const wire = wireOf[name];
    if (wire === undefined) return fn.apply(this, args);
    const field = typeof args[0] === "number" ? args[0] : -1;
    const value = args[1];
    let len = 0;
    if (typeof value === "string") len = value.length;
    else if (typeof value === "boolean") len = 1;
    else if (typeof value === "number") len = encodedLen(value);
    else if (value && (value.byteLength || value.length)) len = value.byteLength || value.length;
    console.log("WRITE", "field=" + field, "wire=" + wire, "len=" + len);
    return fn.apply(this, args);
  };
  for (const name of names) Orig.prototype[name] = wrap(Orig.prototype[name], name);
}
function hookFingerprints() {
  const Client = globalThis.__API && globalThis.__API.ProtobufAuthClient;
  if (!Client || !Client.prototype) {
    console.log("FP_MISSING");
    return;
  }
  for (const name of ["getCanvasFingerprint", "getAudioFingerprint", "getPlugins", "getUserAgent"]) {
    const fn = Client.prototype[name];
    if (typeof fn !== "function") continue;
    Client.prototype[name] = function wrappedFp(...args) {
      const value = fn.apply(this, args);
      const kind = value == null ? "null" : typeof value;
      const len = typeof value === "string" ? value.length : 0;
      console.log("FP", name, "type=" + kind, "len=" + len);
      return value;
    };
  }
}
const https = require("https");
const initPayload = process.env.INIT_CHECK === "1"
  ? JSON.parse(fs.readFileSync(0, "utf8"))
  : JSON.parse(fs.readFileSync(path.join(__dirname, "init.json"), "utf8"));
if (process.env.INIT_CHECK === "1") {
  const realParse = JSON.parse;
  JSON.parse = function parseInit(text, reviver) {
    const value = realParse.call(this, text, reviver);
    if (value && typeof value === "object" && Object.prototype.hasOwnProperty.call(value, "page_data")) {
      console.log("INIT_PARSE", Object.keys(value).join(","));
      return watchInit(value, "");
    }
    return value;
  };
}
function nodeRequest(absolute, method, headers, body) {
  return new Promise((resolve, reject) => {
    const target = new URL(absolute);
    const req = https.request(
      { hostname: target.hostname, path: target.pathname + target.search, method, headers },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }));
      },
    );
    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}
globalThis.fetch = async (url, options) => {
  const target = String(url);
  const absolute = target.startsWith("http") ? target : "https://www.spiderdemo.cn" + target;
  const headers = Object.assign({}, options && options.headers);
  if (process.env.SPIDER_COOKIE) headers.Cookie = process.env.SPIDER_COOKIE;
  headers.Origin = "https://www.spiderdemo.cn";
  headers.Referer = "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge";
  headers["User-Agent"] = CHROME_UA;
  headers["Accept-Language"] = "zh-CN,zh;q=0.9";
  const raw = options && options.body ? Buffer.from(options.body) : null;
  const headerNames = Object.keys(headers).map((name) => name + ":" + String(headers[name]).length);
  note("FETCH", { url: target, method: options && options.method, body: raw ? raw.length : 0, headers: headerNames });
  function walkProto(buf, start, end, depth) {
    const parts = [];
    let offset = start;
    while (offset < end) {
      let tag = 0;
      let shift = 0;
      const tagAt = offset;
      while (offset < end) {
        const byte = buf[offset++];
        tag |= (byte & 0x7f) << shift;
        if ((byte & 0x80) === 0) break;
        shift += 7;
        if (shift > 28) return parts;
      }
      const field = tag >> 3;
      const wire = tag & 7;
      if (wire === 0) {
        let value = 0;
        shift = 0;
        while (offset < end) {
          const byte = buf[offset++];
          value |= (byte & 0x7f) << shift;
          if ((byte & 0x80) === 0) break;
          shift += 7;
          if (shift > 28) return parts;
        }
        parts.push(field + ":v=" + value);
      } else if (wire === 2) {
        let size = 0;
        shift = 0;
        while (offset < end) {
          const byte = buf[offset++];
          size |= (byte & 0x7f) << shift;
          if ((byte & 0x80) === 0) break;
          shift += 7;
        }
        const sliceEnd = offset + size;
        if (sliceEnd > end) {
          parts.push(field + ":truncated");
          break;
        }
        const text = buf.slice(offset, sliceEnd).toString("utf8");
        const printable = /^[\x20-\x7e]+$/.test(text);
        if (printable && text.length <= 80) {
          parts.push(field + ":" + JSON.stringify(text));
        } else if (printable && text.length > 80) {
          const hit = (globalThis.__ENC || []).find((item) => item.token === text);
          parts.push(field + ":token y=" + (hit ? hit.year : "?") + " ts=" + (hit ? hit.ts : "?") + " in=" + (hit ? hit.len : "?"));
        } else if (depth < 1) {
          parts.push(field + ":{" + walkProto(buf, offset, sliceEnd, depth + 1).join(";") + "}");
        } else {
          parts.push(field + ":b=" + size);
        }
        offset = sliceEnd;
      } else {
        parts.push(field + ":w=" + wire + "@" + tagAt);
        break;
      }
    }
    return parts;
  }
  if (process.env.COOKIE_SYNC !== "1" && process.env.PLAIN_SHAPE !== "1" && process.env.INIT_CHECK !== "1" && process.env.WIRE_LOG !== "1" && raw && raw.length > 5 && raw[0] === 0) {
    const frameLen = raw.readUInt32BE(1);
    const parts = walkProto(raw, 5, raw.length, 0);
    note("FRAME", "len=" + frameLen + " " + parts.join(","));
  }
  if (target.includes("/init/")) {
    const body = JSON.stringify(initPayload);
    const payload = process.env.INIT_CHECK === "1" ? watchInit(initPayload, "") : initPayload;
    return {
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      arrayBuffer: async () => Buffer.from(body),
      json: async () => payload,
      text: async () => body,
    };
  }
  if ((process.env.ALIGN_ONLY === "1" || process.env.COOKIE_SYNC === "1") && target.includes("/submit")) {
    console.log("ALIGN_SKIP_SUBMIT");
    return {
      ok: false,
      status: 0,
      headers: { get: () => null },
      arrayBuffer: async () => Buffer.alloc(0),
      json: async () => ({}),
      text: async () => "",
    };
  }
  const isPagePost = /\/page\/\d+\//.test(target) && String((options && options.method) || "GET").toUpperCase() === "POST";
  let uaEq = null;
  let cookieEq = null;
  let uaPlain = null;
  let cookieField = null;
  if ((process.env.ALIGN_ONLY === "1" || process.env.COOKIE_SYNC === "1") && isPagePost && raw && raw.length > 5 && raw[0] === 0) {
    const readVarint = (buf, offset, end) => {
      let value = 0;
      let shift = 0;
      while (offset < end) {
        const byte = buf[offset++];
        value |= (byte & 0x7f) << shift;
        if ((byte & 0x80) === 0) return { value, offset };
        shift += 7;
        if (shift > 35) return null;
      }
      return null;
    };
    const readFields = (buf, start, end) => {
      const fields = [];
      let offset = start;
      while (offset < end) {
        const tag = readVarint(buf, offset, end);
        if (!tag) break;
        offset = tag.offset;
        const field = tag.value >>> 3;
        const wire = tag.value & 7;
        if (wire === 0) {
          const body = readVarint(buf, offset, end);
          if (!body) break;
          offset = body.offset;
          fields.push({ field, wire, value: body.value });
        } else if (wire === 2) {
          const size = readVarint(buf, offset, end);
          if (!size) break;
          offset = size.offset;
          const sliceEnd = offset + size.value;
          if (sliceEnd > end) break;
          const slice = buf.slice(offset, sliceEnd);
          fields.push({ field, wire, text: slice.toString("utf8"), size: size.value, slice });
          offset = sliceEnd;
        } else {
          break;
        }
      }
      return fields;
    };
    const top = readFields(raw, 5, raw.length);
    const fp = top.find((item) => item.field === 5 && item.slice);
    const nested = fp ? readFields(fp.slice, 0, fp.slice.length) : [];
    const uaField = nested.find((item) => item.field === 1 && item.wire === 2);
    cookieField = nested.find((item) => item.field === 6);
    const plains = globalThis.__PLAINS || [];
    if (uaField) uaPlain = plains.find((item) => item.token && item.token === uaField.text) || null;
    const uaHeader = String(headers["User-Agent"] || "");
    const cookieHeader = String(headers.Cookie || headers.cookie || "");
    uaEq = Boolean(uaPlain && uaPlain.text === uaHeader);
    let cookieFieldString = false;
    let cookieFieldLen = 0;
    if (cookieField && cookieField.wire === 2) {
      cookieFieldString = true;
      cookieFieldLen = cookieField.text.length;
      cookieEq = cookieField.text === cookieHeader;
    } else {
      cookieEq = false;
    }
    const cookieStringInFp = nested.some((item) => item.wire === 2 && item.text === cookieHeader);
    if (process.env.COOKIE_SYNC === "1") {
      const doc = sessionCookie;
      console.log(
        "COOKIE",
        "doc_nonempty=" + (doc.length > 0),
        "doc_len=" + doc.length,
        "doc_reads=" + cookieReads,
        "header_nonempty=" + (cookieHeader.length > 0),
        "header_len=" + cookieHeader.length,
        "doc_same=" + (doc === cookieHeader),
        "field_string=" + cookieFieldString,
        "field_len=" + cookieFieldLen,
        "field_nonempty=" + (cookieFieldLen > 0),
        "field_same=" + (cookieEq === true),
        "fp_string_same=" + cookieStringInFp,
      );
    }
    if (process.env.ALIGN_ONLY === "1") {
      console.log(
        "ALIGN",
        "ua_eq=" + uaEq,
        "ua_plain_len=" + (uaPlain ? uaPlain.text.length : -1),
        "ua_header_len=" + uaHeader.length,
        "cookie_eq=" + cookieEq,
        "cookie_field_string=" + cookieFieldString,
        "cookie_field_len=" + cookieFieldLen,
        "cookie_header_len=" + cookieHeader.length,
        "cookie_string_in_fp=" + cookieStringInFp,
      );
      console.log("ALIGN_HDR", Object.keys(headers).map((name) => name + ":" + String(headers[name] ?? "").length).sort().join(","));
    }
  }
  if (process.env.PLAIN_SHAPE === "1" && isPagePost && raw && raw.length > 5 && raw[0] === 0) {
    const readVarint = (buf, offset, end) => {
      let value = 0;
      let shift = 0;
      while (offset < end) {
        const byte = buf[offset++];
        value |= (byte & 0x7f) << shift;
        if ((byte & 0x80) === 0) return { value, offset };
        shift += 7;
        if (shift > 35) return null;
      }
      return null;
    };
    let offset = 5;
    let field4 = null;
    while (offset < raw.length) {
      const tag = readVarint(raw, offset, raw.length);
      if (!tag) break;
      offset = tag.offset;
      const field = tag.value >>> 3;
      const wire = tag.value & 7;
      if (wire === 0) {
        const body = readVarint(raw, offset, raw.length);
        if (!body) break;
        offset = body.offset;
        if (field === 4) field4 = body.value;
      } else if (wire === 2) {
        const size = readVarint(raw, offset, raw.length);
        if (!size) break;
        offset = size.offset + size.value;
      } else {
        break;
      }
    }
    const auth = (globalThis.__PLAINS || []).find((item) => item.template);
    console.log("TS_EQ", "has_template=" + Boolean(auth), "eq=" + Boolean(auth && field4 !== null && auth.ts === field4));
    if (auth) {
      console.log("SEND", "0", "reason=known_template");
      return {
        ok: false,
        status: 0,
        headers: { get: () => null },
        arrayBuffer: async () => Buffer.alloc(0),
        json: async () => ({}),
        text: async () => "",
      };
    }
  }
  if (process.env.WIRE_LOG === "1" && isPagePost && raw && raw.length > 5 && raw[0] === 0) {
    const payloadLen = raw.readUInt32BE(1);
    console.log("FRAME_LEN", "total=" + raw.length, "payload=" + payloadLen, "gap=" + (507 - payloadLen));
    const readVarint = (buf, offset, end) => {
      let value = 0;
      let shift = 0;
      let bytes = 0;
      while (offset < end) {
        const byte = buf[offset++];
        bytes += 1;
        value |= (byte & 0x7f) << shift;
        if ((byte & 0x80) === 0) return { value, offset, bytes };
        shift += 7;
        if (shift > 35) return null;
      }
      return null;
    };
    const dump = (buf, start, end, nested) => {
      let offset = start;
      while (offset < end) {
        const tag = readVarint(buf, offset, end);
        if (!tag) break;
        offset = tag.offset;
        const field = tag.value >>> 3;
        const wire = tag.value & 7;
        if (wire === 0) {
          const body = readVarint(buf, offset, end);
          if (!body) break;
          offset = body.offset;
          console.log("FIELD", (nested ? "fp" : "top"), "field=" + field, "wire=0", "len=" + body.bytes);
        } else if (wire === 2) {
          const size = readVarint(buf, offset, end);
          if (!size) break;
          offset = size.offset;
          console.log("FIELD", (nested ? "fp" : "top"), "field=" + field, "wire=2", "len=" + size.value);
          if (!nested && field === 5) dump(buf, offset, offset + size.value, true);
          offset += size.value;
        } else {
          break;
        }
      }
    };
    dump(raw, 5, 5 + payloadLen, false);
    console.log("SEND", "0", "reason=wire_log");
    return {
      ok: false,
      status: 0,
      headers: { get: () => null },
      arrayBuffer: async () => Buffer.alloc(0),
      json: async () => ({}),
      text: async () => "",
    };
  }
  if (process.env.INIT_CHECK === "1" && isPagePost) {
    console.log("SEND", "0", "reason=btoa_len=" + (globalThis.__BTOA_LEN || 0));
    return {
      ok: false,
      status: 0,
      headers: { get: () => null },
      arrayBuffer: async () => Buffer.alloc(0),
      json: async () => ({}),
      text: async () => "",
    };
  }
  let response = await nodeRequest(absolute, (options && options.method) || "GET", headers, raw);
  if (process.env.ALIGN_ONLY === "1" && isPagePost && (uaEq === false || cookieEq === false) && !globalThis.__ALIGN_RETRY) {
    globalThis.__ALIGN_RETRY = true;
    const headers2 = Object.assign({}, headers);
    let uaChanged = false;
    let cookieChanged = false;
    if (uaEq === false && uaPlain) {
      headers2["User-Agent"] = uaPlain.text;
      uaChanged = headers2["User-Agent"] !== headers["User-Agent"];
    }
    if (cookieEq === false && cookieField && cookieField.wire === 2) {
      headers2.Cookie = cookieField.text;
      cookieChanged = true;
    }
    console.log(
      "ALIGN_RETRY",
      "ua_changed=" + uaChanged,
      "ua_len=" + String(headers2["User-Agent"] || "").length,
      "ua_eq_after=" + Boolean(uaPlain && headers2["User-Agent"] === uaPlain.text),
      "cookie_changed=" + cookieChanged,
      "cookie_len=" + String(headers2.Cookie || headers2.cookie || "").length,
    );
    response = await nodeRequest(absolute, (options && options.method) || "GET", headers2, raw);
  }
  if (process.env.PLAIN_SHAPE === "1" && isPagePost) {
    let error = "";
    try { error = JSON.parse(response.body.toString("utf8")).error || ""; } catch (parseError) { error = ""; }
    console.log("PAGE1", "status=" + response.status, "body_len=" + response.body.length, "same_auth=" + (error === "Protobuf鉴权验证失败"), "error=" + error);
  } else if (process.env.COOKIE_SYNC === "1" && isPagePost) {
    let error = "";
    try { error = JSON.parse(response.body.toString("utf8")).error || ""; } catch (parseError) { error = ""; }
    console.log("PAGE1", "status=" + response.status, "body_len=" + response.body.length, "same_auth=" + (error === "Protobuf鉴权验证失败"), "error=" + error);
  } else {
    const preview = response.body.slice(0, 180).toString("utf8").replace(/\s+/g, " ");
    console.log("NET", response.status, response.body.length, preview);
  }
  if (process.env.ALIGN_ONLY === "1" && isPagePost) {
    let error = "";
    try { error = JSON.parse(response.body.toString("utf8")).error || ""; } catch (parseError) { error = ""; }
    console.log("ALIGN_RETRY_RESULT", "status=" + response.status, "body_len=" + response.body.length, "same_auth=" + (error === "Protobuf鉴权验证失败"), "error=" + error);
  }
  return {
    ok: response.status >= 200 && response.status < 300,
    status: response.status,
    headers: { get: (name) => response.headers[String(name).toLowerCase()] || null },
    arrayBuffer: async () => response.body.buffer.slice(response.body.byteOffset, response.body.byteOffset + response.body.byteLength),
    json: async () => JSON.parse(response.body.toString("utf8")),
    text: async () => response.body.toString("utf8"),
  };
};
globalThis.XMLHttpRequest = function XMLHttpRequest() {
  this.readyState = 0;
  this.status = 0;
  this.response = null;
  this.responseText = "";
  this.open = (method, url) => note("XHR", method + " " + url);
  this.send = (body) => note("XHRSEND", body && (body.byteLength || body.length || typeof body));
  this.setRequestHeader = (name, value) => note("XHRHDR", name + "=" + value);
  this.addEventListener = () => {};
  this.getResponseHeader = () => null;
};
let audioGets = 0;
function AudioNodeStub() {
  const node = {
    connect() { return node; },
    start() { note("AUDIO", "start"); },
    stop() {},
    disconnect() {},
    type: "triangle",
    frequency: { value: 440, setValueAtTime(value) { this.value = value; } },
    threshold: { value: -50, setValueAtTime(value) { this.value = value; } },
    knee: { value: 40, setValueAtTime(value) { this.value = value; } },
    ratio: { value: 12, setValueAtTime(value) { this.value = value; } },
    attack: { value: 0, setValueAtTime(value) { this.value = value; } },
    release: { value: 0.25, setValueAtTime(value) { this.value = value; } },
  };
  return new Proxy(node, {
    get(obj, prop, receiver) {
      if (typeof prop === "string" && audioGets < 60) {
        audioGets += 1;
        note("AGET", prop);
      }
      if (typeof prop === "string" && prop !== "then" && !Object.prototype.hasOwnProperty.call(obj, prop)) {
        obj[prop] = { value: 1, setValueAtTime(value) { this.value = value; } };
      }
      return Reflect.get(obj, prop, receiver);
    },
  });
}
function OfflineAudioContextStub() {
  if (globalThis.__AUDIO_OK === false) throw new Error("audio disabled");
  note("AUDIO", "len=" + arguments.length);
  this.sampleRate = 44100;
  this.currentTime = 0;
  this.destination = new AudioNodeStub();
  return new Proxy(this, {
    get(obj, prop, receiver) {
      if (typeof prop === "string" && prop !== "then" && audioGets < 40) {
        audioGets += 1;
        note("AGET", "ctx." + prop);
      }
      let value = Reflect.get(obj, prop, receiver);
      if (value === undefined && typeof prop === "string" && prop.startsWith("create")) {
        value = () => new AudioNodeStub();
      }
      return typeof value === "function" ? value.bind(obj) : value;
    },
  });
}
OfflineAudioContextStub.prototype.createOscillator = nativeFn("createOscillator", () => new AudioNodeStub());
OfflineAudioContextStub.prototype.createAnalyser = nativeFn("createAnalyser", () => {
  note("AUDIO", "analyser");
  return { connect() { return this; }, fftSize: 2048, frequencyBinCount: 1024, getFloatFrequencyData(buffer) { buffer.fill(-40); } };
});
OfflineAudioContextStub.prototype.createDynamicsCompressor = nativeFn("createDynamicsCompressor", () => new AudioNodeStub());
OfflineAudioContextStub.prototype.startRendering = nativeFn("startRendering", () => Promise.resolve({ getChannelData: () => new Float32Array([0.1, 0.2, 0.3]) }));
OfflineAudioContextStub.toString = () => "function OfflineAudioContext() { [native code] }";
globalThis.OfflineAudioContext = OfflineAudioContextStub;
globalThis.webkitOfflineAudioContext = OfflineAudioContextStub;
globalThis.crypto = {
  getRandomValues(buffer) {
    for (let i = 0; i < buffer.length; i += 1) buffer[i] = (i * 17) & 255;
    return buffer;
  },
};
globalThis.requestAnimationFrame = (fn) => setTimeout(fn, 0);
globalThis.cancelAnimationFrame = clearTimeout;
globalThis.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
globalThis.getComputedStyle = () => new Proxy({}, { get: () => "" });
const originalDescriptor = Object.getOwnPropertyDescriptor;
let descLogs = 0;
Object.getOwnPropertyDescriptor = function (obj, prop) {
  if (descLogs < 30) {
    const desc = originalDescriptor(obj, prop);
    const kind = desc ? (desc.get ? "get" : "value") : "missing";
    const native = desc && desc.get ? String(desc.get).includes("native code") : false;
    const label = obj === Navigator.prototype ? "NavProto" : (obj && obj.constructor && obj.constructor.name) || typeof obj;
    note("DESC", label + "." + String(prop) + " " + kind + " native=" + native);
    descLogs += 1;
  }
  return originalDescriptor.apply(this, arguments);
};
globalThis.screen = watch("screen", new Screen());
const realOffset = Date.prototype.getTimezoneOffset;
Date.prototype.getTimezoneOffset = function getTimezoneOffset() {
  const value = realOffset.call(this);
  note("TZ", String(value));
  return value;
};
let cookieReads = 0;
const sessionCookie = process.env.SPIDER_COOKIE || "";
Object.defineProperty(documentStub, "cookie", {
  configurable: true,
  enumerable: true,
  get: nativeGet("cookie", () => {
    cookieReads += 1;
    return sessionCookie;
  }),
  set: nativeFn("cookie", (value) => {
    globalThis.__COOKIE_SET = true;
    globalThis.__COOKIE_SET_LEN = String(value == null ? "" : value).length;
  }),
});
globalThis.history = { pushState() {}, replaceState() {} };
globalThis.performance = { now: () => Date.now() };

try {
  eval(source);
} catch (error) {
  note("ERROR", error && error.stack ? error.stack.split("\n").slice(0, 12).join(" | ") : String(error));
}
if (process.env.PLAIN_SHAPE === "1" || process.env.WIRE_LOG === "1") hookWriter();
if (process.env.WIRE_LOG === "1") hookFingerprints();
if (process.env.SKIP_BOOT === "1") {
  listeners.length = 0;
}
for (const item of listeners) {
  if (item.type === "DOMContentLoaded" || item.type === "load") {
    try {
      item.fn({ type: item.type, target: documentStub });
      note("FIRED", item.target + " " + item.type);
    } catch (error) {
      note("FIRE_ERROR", error && error.stack ? error.stack.split("\n").slice(0, 12).join(" | ") : String(error));
    }
  }
}

function flush() {
  const unique = [];
  const seen = new Set();
  for (const item of globalThis.__STRS) {
    if (!seen.has(item)) {
      seen.add(item);
      unique.push(item);
    }
  }
  fs.writeFileSync(path.join(__dirname, "vm-strings.json"), JSON.stringify({ count: globalThis.__STRS.length, unique, logs }, null, 2));
  if (Array.isArray(globalThis.__ALL)) {
    const hits = globalThis.__ALL.filter((item) => typeof item === "string" && /secret|BEGIN |key_|https?:|sign|css_|proto|auth/i.test(item));
    const readable = globalThis.__ALL.filter((item) => typeof item === "string" && item.length > 3 && /^[\x09\x0a\x0d\x20-\x7e]+$/.test(item)).length;
    console.log("ALL", globalThis.__ALL.length, "readable", readable, "key", globalThis.__DECKEY, "hits", hits.length);
    for (const item of hits) console.log("S", JSON.stringify(item).slice(0, 160));
  }
  console.log("strings", globalThis.__STRS.length, "unique", unique.length, "logs", logs.length);
  for (const item of unique) {
    if (/api|page|proto|submit|fetch|http|challenge|css|number|sign|encrypt|answer|\//i.test(item)) {
      console.log("HIT", JSON.stringify(item));
    }
  }
  for (const line of logs) console.log(line);
}
function describe(value) {
  if (value == null) return String(value);
  if (typeof value === "string") return "str:" + value.length;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (typeof value === "function") return "fn";
  if (typeof value === "object") return "obj:" + Object.keys(value).slice(0, 20).join(",");
  return typeof value;
}
setTimeout(() => {
  if (process.env.ALIGN_ONLY === "1" || process.env.COOKIE_SYNC === "1" || process.env.PLAIN_SHAPE === "1" || process.env.INIT_CHECK === "1" || process.env.WIRE_LOG === "1") return;
  const api = globalThis.__API || {};
  for (const name of Object.keys(api)) {
    const value = api[name];
    note("GLOBAL", name + " " + describe(value));
    if (typeof value === "function" && value.prototype) {
      const names = Object.getOwnPropertyNames(value.prototype).filter((item) => item !== "constructor");
      note("PROTO", name + " " + names.join(","));
    }
  }
  try {
    const fp = new api.BrowserFingerprint();
    for (const name of Object.getOwnPropertyNames(api.BrowserFingerprint.prototype)) {
      if (name === "constructor" || typeof fp[name] !== "function") continue;
      try {
        note("BF", name + " " + describe(fp[name]()));
      } catch (error) {
        note("BF_ERR", name + " " + error.message);
      }
    }
  } catch (error) {
    note("BF_NEW", error.message);
  }
  try {
    const auth = api.ProtobufAuth;
    note("AUTH_KEYS", Object.keys(auth).join(","));
    const Writer = auth.BinaryWriter;
    note("WPROTO", Object.getOwnPropertyNames(Writer.prototype).join(","));
    const writer = new Writer();
    if (typeof writer.writeInt32 === "function") writer.writeInt32(5, -480);
    if (typeof writer.writeString === "function") writer.writeString(4, "24");
    const out = writer.getResultBuffer ? writer.getResultBuffer() : writer.getResultBase64String ? writer.getResultBase64String() : null;
    const hex = Buffer.isBuffer(out) || out instanceof Uint8Array ? Buffer.from(out).toString("hex") : String(out).slice(0, 40);
    note("WOUT", hex);
  } catch (error) {
    note("AUTH_ERR", error.message);
  }
  try {
    const client = new api.ProtobufAuthClient();
    const names = Object.getOwnPropertyNames(api.ProtobufAuthClient.prototype);
    for (const name of names) {
      if (name === "constructor" || typeof client[name] !== "function") continue;
      if (name === "getPageData" || name === "buildGRPCWebRequest" || name === "parseGRPCWebResponse") continue;
      const before = globalThis.__STRS.length;
      fs.appendFileSync(path.join(__dirname, "_pac_progress.txt"), "call " + name + "\n");
      try {
        const result = client[name]();
        if (result && typeof result.then === "function") {
          result.then(
            (value) => fs.appendFileSync(path.join(__dirname, "_pac_progress.txt"), "async " + name + " " + describe(value) + "\n"),
            (error) => fs.appendFileSync(path.join(__dirname, "_pac_progress.txt"), "asyncerr " + name + " " + error.message + "\n"),
          );
        }
        if (name === "getPlugins") note("PLUGINS", String(result).slice(0, 80));
        if (name === "generateAuthHash" && result && typeof result === "object") {
          note("HASH", "ts=" + result.timestamp + " hashLen=" + String(result.hash == null ? "" : result.hash).length + " same=" + (result.hash === globalThis.__LAST_TOKEN) + " year=" + globalThis.__LAST_YEAR);
        }
        note("PAC", name + " " + describe(result));
        const fresh = globalThis.__STRS.slice(before).filter((item) => item.length < 80).slice(0, 12);
        fs.appendFileSync(path.join(__dirname, "_pac_progress.txt"), "ok " + name + " " + describe(result) + " strs=" + JSON.stringify(fresh) + "\n");
      } catch (error) {
        note("PAC_ERR", name + "() " + error.message);
        fs.appendFileSync(path.join(__dirname, "_pac_progress.txt"), "err " + name + " " + error.message + "\n");
      }
    }
  } catch (error) {
    note("PAC_NEW", error.message);
  }
  try {
    const held = api.protobufClient;
    const proto = Object.getPrototypeOf(held);
    note("HELD", (held && held.constructor && held.constructor.name) + " " + Object.getOwnPropertyNames(proto).join(","));
  } catch (error) {
    note("HELD_ERR", error.message);
  }
  try {
    const probe = new api.ProtobufAuthClient();
    for (const canvasOk of [false, true]) {
      for (const audioOk of [false, true]) {
        globalThis.__CANVAS_OK = canvasOk;
        globalThis.__AUDIO_OK = audioOk;
        globalThis.__LAST_YEAR = "";
        const result = probe.generateAuthHash();
        note("YEAR", "canvas=" + canvasOk + " audio=" + audioOk + " year=" + globalThis.__LAST_YEAR + " ts=" + (result && result.timestamp));
      }
    }
    globalThis.__CANVAS_OK = true;
    globalThis.__AUDIO_OK = true;
  } catch (error) {
    note("YEAR_ERR", error.message);
  }
  try {
    const css = new api.CSSAntiCrawlerDecryptor();
    for (const name of Object.getOwnPropertyNames(api.CSSAntiCrawlerDecryptor.prototype)) {
      if (typeof css[name] === "function") note("CSSLEN", name + " " + css[name].length);
    }
    const blobs = [
      { css_mixed_content: "<span class=\"context_kw0\">65</span>", css_encrypted_data: "MTA=" },
      { mixedContent: "<span class=\"context_kw0\">65</span>", encryptedData: "10,11" },
      { cssMixedContent: "<i class=\"context_kw1\">1</i>", cssEncryptedData: "YQ==" },
    ];
    for (const blob of blobs) {
      const before = globalThis.__STRS.length;
      try {
        const value = css.processCSSAntiCrawlerData(blob);
        const fresh = globalThis.__STRS.slice(before).filter((item) => item.length < 80).slice(0, 10);
        note("CSS", "process -> " + describe(value) + " strs=" + JSON.stringify(fresh));
      } catch (error) {
        note("CSS_ERR", "process " + error.message);
      }
    }
  } catch (error) {
    note("CSS_NEW", error.message);
  }
  const calls = [];
  let pending = Promise.resolve();
  for (const [name, args] of calls) {
    if (typeof api[name] === "function") {
      pending = pending.then(async () => {
        try {
          const value = await api[name](...args);
          note("CALL", name + " -> " + JSON.stringify(value).slice(0, 300));
        } catch (error) {
          note("CALL_ERROR", name + " " + (error && error.stack ? error.stack.split("\n").slice(0, 6).join(" | ") : error.message));
        }
      });
    }
  }
  pending.then(() => setTimeout(flush, 200));
}, 300);
