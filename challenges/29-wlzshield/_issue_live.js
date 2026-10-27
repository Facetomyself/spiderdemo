const fs = require("fs");
const https = require("https");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const root = __dirname;
const SITE_KEY = "9d4295076aaef0b4c16e18e4f53b5120";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const PAGE = "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge?challenge_type=wlzshield_captcha_challenge";

function report(line) {
  process.stdout.write(String(line) + "\n");
}

const narrowMarked = new Set();
let narrowHook = null;

function installNarrow(win) {
  if (!narrowHook) {
    const raw = Function.prototype.toString;
    function toString() {
      if (this === toString || narrowMarked.has(this)) {
        const name = this === toString ? "toString" : String(this.name || "");
        return name ? "function " + name + "() { [native code] }" : "function () { [native code] }";
      }
      return raw.call(this);
    }
    try { delete toString.prototype; } catch (_error) {}
    narrowHook = toString;
  }
  const current = win.Function.prototype.toString;
  if (current === narrowHook) return;
  win.Object.defineProperty(win.Function.prototype, "toString", {
    configurable: true,
    writable: true,
    enumerable: false,
    value: narrowHook,
  });
  const quiet = (name, result) => {
    const fn = { alert() { return undefined; }, confirm() { return true; }, prompt() { return ""; } }[name];
    try { delete fn.prototype; } catch (_error) {}
    narrowMarked.add(fn);
    return fn;
  };
  win.alert = quiet("alert");
  win.confirm = quiet("confirm");
  win.prompt = quiet("prompt");
}

function markNatives(win) {
  const raw = win.Function.prototype.toString;
  if (raw.__marked) return;
  const nativeMark = new win.WeakMap();
  function toString() {
    win.__toStringCalls = (win.__toStringCalls || 0) + 1;
    if (this === toString) return "function toString() { [native code] }";
    if (nativeMark.has(this)) {
      win.__nativeHits = (win.__nativeHits || 0) + 1;
      return nativeMark.get(this);
    }
    win.__rawHits = (win.__rawHits || 0) + 1;
    let label = "unknown";
    try {
      const text = raw.call(this);
      const matched = /function\s+([A-Za-z0-9_]+)/.exec(text);
      label = matched ? matched[1] : text.slice(0, 24).replace(/\s+/g, " ");
    } catch (_error) {
      label = "throw";
    }
    if (!win.__rawNames) win.__rawNames = [];
    if (/^[A-Za-z_$][A-Za-z0-9_$]{3,}$/.test(label) && win.__rawNames.length < 20 && !win.__rawNames.includes(label)) win.__rawNames.push(label);
    return raw.call(this);
  }
  nativeMark.set(toString, "function toString() { [native code] }");
  try { delete toString.prototype; } catch (_error) {}
  win.Object.defineProperty(win.Function.prototype, "toString", { configurable: true, writable: true, value: toString });
  win.__mark = function mark(fn, name) {
    if (typeof fn === "function") nativeMark.set(fn, "function " + (name || "anonymous") + "() { [native code] }");
  };
  const roots = [win, win.document, win.navigator, win.history, win.console, win.performance, win.location, win.Object, win.JSON, win.Date, win.Math, win.Reflect, win.Array, win.String, win.Number, win.Promise, win.Map, win.Set, win.Function, win.Object && win.Object.prototype, win.Array && win.Array.prototype, win.String && win.String.prototype, win.Function && win.Function.prototype, win.Date && win.Date.prototype];
  const protos = [win.Document, win.Element, win.Node, win.HTMLElement, win.EventTarget, win.XMLHttpRequest, win.Storage, win.Window, win.Navigator, win.History, win.Performance, win.CanvasRenderingContext2D];
  for (const ctor of protos) {
    if (ctor && ctor.prototype) roots.push(ctor.prototype);
  }
  const seen = new Set();
  for (const root of roots) {
    if (!root || seen.has(root)) continue;
    seen.add(root);
    let names = [];
    try { names = Object.getOwnPropertyNames(root); } catch (_error) { continue; }
    for (const name of names) {
      let value;
      try { value = root[name]; } catch (_error) { continue; }
      if (typeof value === "function") win.__mark(value, name);
    }
  }
  raw.__marked = true;
}

function installStack(win) {
  const Orig = win.Error;
  if (!Orig || Orig.__clean) return;
  const pageStack = "Error\n    at " + PAGE + ":1:1";
  function CleanError(message) {
    const err = new Orig(message);
    const stack = "Error" + (message ? ": " + message : "") + "\n    at " + PAGE + ":1:1";
    try {
      win.Object.defineProperty(err, "stack", { configurable: true, get() { return stack; } });
    } catch (_error) {}
    return err;
  }
  CleanError.prototype = Orig.prototype;
  CleanError.stackTraceLimit = 10;
  CleanError.__clean = true;
  try { delete Orig.captureStackTrace; } catch (_error) {}
  win.Error = CleanError;
  if (typeof win.__mark === "function") win.__mark(CleanError, "Error");
}

function canvas2d() {
  const ctx = {
    canvas: null,
    fillStyle: "#000",
    font: "14px Arial",
    textBaseline: "alphabetic",
    fillRect() {},
    strokeRect() {},
    clearRect() {},
    beginPath() {},
    closePath() {},
    moveTo() {},
    lineTo() {},
    arc() {},
    fill() {},
    stroke() {},
    save() {},
    restore() {},
    scale() {},
    rotate() {},
    translate() {},
    fillText() {},
    strokeText() {},
    measureText(text) { return { width: String(text || "").length * 7.2 }; },
    getImageData(_x, _y, w, h) {
      const width = w || 1;
      const height = h || 1;
      const data = new Uint8ClampedArray(width * height * 4);
      for (let i = 0; i < data.length; i += 4) {
        data[i] = 12 + (i % 40);
        data[i + 1] = 80;
        data[i + 2] = 160;
        data[i + 3] = 255;
      }
      return { data, width, height };
    },
    putImageData() {},
    createLinearGradient() { return { addColorStop() {} }; },
    drawImage() {},
  };
  return ctx;
}

function webglContext() {
  return {
    getParameter(name) {
      const table = {
        7936: "WebKit",
        7937: "WebKit WebGL",
        7938: "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
        35724: "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
        37445: "Google Inc. (NVIDIA)",
        37446: "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        7938: "WebGL 1.0",
        3379: 16384,
        34076: 16384,
        34024: 16384,
        34921: 16,
        36347: 1024,
        36349: 30,
      };
      return Object.prototype.hasOwnProperty.call(table, name) ? table[name] : 0;
    },
    getExtension(name) {
      if (name === "WEBGL_debug_renderer_info") return { UNMASKED_VENDOR_WEBGL: 37445, UNMASKED_RENDERER_WEBGL: 37446 };
      return null;
    },
    getSupportedExtensions() { return ["WEBGL_debug_renderer_info", "OES_texture_float"]; },
    getShaderPrecisionFormat() { return { rangeMin: 127, rangeMax: 127, precision: 23 }; },
    getContextAttributes() { return { alpha: true, antialias: true, depth: true, stencil: false, premultipliedAlpha: true }; },
    createBuffer() { return {}; },
    bindBuffer() {},
    bufferData() {},
    createProgram() { return {}; },
    createShader() { return {}; },
    shaderSource() {},
    compileShader() {},
    attachShader() {},
    linkProgram() {},
    useProgram() {},
    getAttribLocation() { return 0; },
    enableVertexAttribArray() {},
    vertexAttribPointer() {},
    drawArrays() {},
    viewport() {},
    clearColor() {},
    clear() {},
    readPixels(x, y, w, h, format, type, pixels) {
      if (pixels) pixels.fill(8);
    },
    canvas: null,
  };
}

function installCanvas(win) {
  const proto = win.HTMLCanvasElement.prototype;
  proto.getContext = function getContext(kind) {
    const name = String(kind || "");
    if (name === "2d") return canvas2d();
    if (name.indexOf("webgl") >= 0) return webglContext();
    return null;
  };
  proto.toDataURL = function toDataURL() {
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
  };
  if (typeof win.__mark === "function") {
    win.__mark(proto.getContext, "getContext");
    win.__mark(proto.toDataURL, "toDataURL");
  }
}

function installAudio(win) {
  function AudioContext() {
    this.sampleRate = 48000;
    this.state = "running";
    this.destination = { channelCount: 2 };
  }
  AudioContext.prototype.createOscillator = function createOscillator() {
    return { connect() {}, start() {}, stop() {}, frequency: { value: 440 }, type: "triangle", disconnect() {} };
  };
  AudioContext.prototype.createDynamicsCompressor = function createDynamicsCompressor() {
    return { connect() {}, threshold: { value: -50 }, knee: { value: 40 }, ratio: { value: 12 }, attack: { value: 0 }, release: { value: 0.25 } };
  };
  AudioContext.prototype.createGain = function createGain() { return { connect() {}, gain: { value: 1 } }; };
  AudioContext.prototype.createAnalyser = function createAnalyser() {
    return { connect() {}, fftSize: 2048, frequencyBinCount: 1024, getFloatFrequencyData(arr) { if (arr) arr.fill(-48); } };
  };
  AudioContext.prototype.createBuffer = function createBuffer() {
    return { getChannelData() { return new win.Float32Array(128); }, sampleRate: 48000, length: 128, duration: 128 / 48000, numberOfChannels: 1 };
  };
  AudioContext.prototype.close = function close() { return win.Promise.resolve(); };
  function OfflineAudioContext(_channels, length) {
    AudioContext.call(this);
    this.length = length || 44100;
    this.state = "suspended";
  }
  OfflineAudioContext.prototype = Object.create(AudioContext.prototype);
  OfflineAudioContext.prototype.startRendering = function startRendering() {
    const data = new win.Float32Array(this.length || 256);
    for (let i = 0; i < data.length; i += 1) data[i] = Math.sin(i / 12) * 0.02;
    const buffer = { getChannelData() { return data; }, sampleRate: 44100, length: data.length, duration: data.length / 44100, numberOfChannels: 1 };
    return win.Promise.resolve(buffer);
  };
  win.AudioContext = AudioContext;
  win.webkitAudioContext = AudioContext;
  win.OfflineAudioContext = OfflineAudioContext;
  if (typeof win.__mark === "function") {
    win.__mark(AudioContext, "AudioContext");
    win.__mark(OfflineAudioContext, "OfflineAudioContext");
  }
}

function installRtc(win) {
  const sdp = "v=0\r\no=- 1 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\nm=application 9 UDP/DTLS/SCTP webrtc-datachannel\r\nc=IN IP4 0.0.0.0\r\na=ice-ufrag:abcd\r\na=ice-pwd:abcdefghijklmnopqrstuvwx\r\na=fingerprint:sha-256 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF\r\na=setup:actpass\r\na=mid:0\r\na=sctp-port:5000\r\n";
  function RTCPeerConnection() {
    this.iceConnectionState = "new";
    this.connectionState = "new";
    this.signalingState = "stable";
    this.iceGatheringState = "new";
    this.localDescription = null;
    this.remoteDescription = null;
    this.onicecandidate = null;
  }
  RTCPeerConnection.prototype.createDataChannel = function createDataChannel() { return { close() {}, send() {} }; };
  RTCPeerConnection.prototype.createOffer = function createOffer() { return win.Promise.resolve({ type: "offer", sdp }); };
  RTCPeerConnection.prototype.createAnswer = function createAnswer() { return win.Promise.resolve({ type: "answer", sdp }); };
  RTCPeerConnection.prototype.setLocalDescription = function setLocalDescription(desc) {
    this.localDescription = desc || { type: "offer", sdp };
    this.iceGatheringState = "complete";
    const callback = this.onicecandidate;
    if (typeof callback === "function") callback({ candidate: { candidate: "candidate:1 1 UDP 2122252543 192.168.1.8 54321 typ host", sdpMid: "0", sdpMLineIndex: 0 } });
    return win.Promise.resolve();
  };
  RTCPeerConnection.prototype.setRemoteDescription = function setRemoteDescription() { return win.Promise.resolve(); };
  RTCPeerConnection.prototype.addEventListener = function addEventListener() {};
  RTCPeerConnection.prototype.close = function close() {};
  RTCPeerConnection.prototype.addIceCandidate = function addIceCandidate() { return win.Promise.resolve(); };
  RTCPeerConnection.prototype.getStats = function getStats() { return win.Promise.resolve(new win.Map()); };
  win.RTCPeerConnection = RTCPeerConnection;
  win.webkitRTCPeerConnection = RTCPeerConnection;
  if (typeof win.__mark === "function") win.__mark(RTCPeerConnection, "RTCPeerConnection");
}

function defineGetter(obj, key, value) {
  try {
    Object.defineProperty(obj, key, { configurable: true, enumerable: true, writable: true, value });
    return;
  } catch (_error) {}
  try {
    obj[key] = value;
  } catch (_error) {}
}

function installNavigator(win) {
  const nav = win.navigator;
  defineGetter(nav, "language", "zh-CN");
  defineGetter(nav, "languages", ["zh-CN", "zh", "en-US", "en"]);
  defineGetter(nav, "platform", "Win32");
  defineGetter(nav, "vendor", "Google Inc.");
  defineGetter(nav, "vendorSub", "");
  defineGetter(nav, "productSub", "20030107");
  defineGetter(nav, "appVersion", "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
  defineGetter(nav, "hardwareConcurrency", 8);
  defineGetter(nav, "deviceMemory", 8);
  defineGetter(nav, "maxTouchPoints", 0);
  defineGetter(nav, "pdfViewerEnabled", true);
  defineGetter(nav, "cookieEnabled", true);
  defineGetter(nav, "onLine", true);
  defineGetter(nav, "doNotTrack", null);
  nav.javaEnabled = function javaEnabled() { return false; };
  nav.getBattery = function getBattery() {
    return win.Promise.resolve({ charging: true, chargingTime: 0, dischargingTime: Infinity, level: 0.86, addEventListener() {}, removeEventListener() {} });
  };
  const brands = [
    { brand: "Google Chrome", version: "120" },
    { brand: "Chromium", version: "120" },
    { brand: "Not_A Brand", version: "24" },
  ];
  defineGetter(nav, "userAgentData", {
    brands,
    mobile: false,
    platform: "Windows",
    getHighEntropyValues() {
      return win.Promise.resolve({ architecture: "x86", bitness: "64", model: "", platform: "Windows", platformVersion: "15.0.0", uaFullVersion: "120.0.0.0", fullVersionList: brands, mobile: false });
    },
  });
  defineGetter(nav, "connection", { effectiveType: "4g", rtt: 50, downlink: 10, saveData: false, addEventListener() {} });
  defineGetter(nav, "bluetooth", { getAvailability() { return win.Promise.resolve(true); }, requestDevice() { return win.Promise.reject(new win.Error("cancel")); }, addEventListener() {} });
  defineGetter(nav, "usb", { getDevices() { return win.Promise.resolve([]); }, addEventListener() {} });
  defineGetter(nav, "hid", { getDevices() { return win.Promise.resolve([]); }, addEventListener() {} });
  defineGetter(nav, "serial", { getPorts() { return win.Promise.resolve([]); }, addEventListener() {} });
  defineGetter(nav, "xr", { isSessionSupported() { return win.Promise.resolve(false); }, addEventListener() {} });
  defineGetter(nav, "credentials", { get() { return win.Promise.resolve(null); }, create() { return win.Promise.resolve(null); }, store() { return win.Promise.resolve(); } });
  defineGetter(nav, "clipboard", { readText() { return win.Promise.resolve(""); }, writeText() { return win.Promise.resolve(); } });
  defineGetter(nav, "locks", { request(_name, callback) { return win.Promise.resolve(callback({})); } });
  defineGetter(nav, "mediaDevices", { enumerateDevices() { return win.Promise.resolve([]); }, getUserMedia() { return win.Promise.reject(new win.Error("denied")); }, addEventListener() {} });
  defineGetter(nav, "storage", { estimate() { return win.Promise.resolve({ quota: 1000000000, usage: 1000 }); }, persisted() { return win.Promise.resolve(false); } });
  defineGetter(nav, "serviceWorker", { controller: null, ready: win.Promise.resolve({}), register() { return win.Promise.resolve({}); }, getRegistration() { return win.Promise.resolve(undefined); }, addEventListener() {} });
  defineGetter(nav, "permissions", { query() { return win.Promise.resolve({ state: "prompt", addEventListener() {} }); } });
  defineGetter(nav, "gpu", { requestAdapter() { return win.Promise.resolve(null); } });
  if (typeof win.__mark === "function") {
    win.__mark(nav.javaEnabled, "javaEnabled");
    win.__mark(nav.getBattery, "getBattery");
  }
  if (process.env.WLZ_FAKE_PLUGINS === "1") {
    const plugin = { name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", length: 1, 0: { type: "application/pdf" } };
    const plugins = Object.create(Object.getPrototypeOf(nav.plugins) || Object.prototype);
    plugins[0] = plugin;
    defineGetter(plugins, "length", 1);
    plugins.item = (index) => plugins[index] || null;
    plugins.namedItem = () => plugin;
    plugins.refresh = () => {};
    defineGetter(nav, "plugins", plugins);
    defineGetter(nav, "mimeTypes", { length: 1, 0: { type: "application/pdf" }, item() { return this[0]; } });
  }
  defineGetter(nav, "webdriver", false);
  win.chrome = {
    app: { isInstalled: false, getDetails() { return null; }, getIsInstalled() { return false; } },
    runtime: { OnInstalledReason: { CHROME_UPDATE: "chrome_update", INSTALL: "install", UPDATE: "update" }, connect() { return { onMessage: { addListener() {} }, postMessage() {}, disconnect() {} }; }, sendMessage() {} },
    csi() { return {}; },
    loadTimes() { return {}; },
  };
  function Notification(title) { this.title = title; }
  Notification.permission = "default";
  Notification.requestPermission = function requestPermission() { return win.Promise.resolve("default"); };
  win.Notification = Notification;
  function PaymentRequest() {}
  win.PaymentRequest = PaymentRequest;
  if (typeof win.__mark === "function") {
    win.__mark(Notification, "Notification");
    win.__mark(Notification.requestPermission, "requestPermission");
    win.__mark(PaymentRequest, "PaymentRequest");
    win.__mark(win.chrome.csi, "csi");
    win.__mark(win.chrome.loadTimes, "loadTimes");
  }
  if (win.performance) {
    const started = Date.now() - 1800;
    try {
      const host = (win.Performance && win.Performance.prototype) || win.performance;
      Object.defineProperty(host, "now", { configurable: true, writable: true, value() { return Date.now() - started; } });
    } catch (_error) {}
    let heap = 18000000;
    try {
      Object.defineProperty(win.performance, "memory", {
        configurable: true,
        get() {
          heap += 8192;
          return { jsHeapSizeLimit: 4294705152, totalJSHeapSize: 38000000 + (heap % 500000), usedJSHeapSize: heap };
        },
      });
    } catch (_error) {}
  }
  if (win.document) {
    try { defineGetter(win.document, "visibilityState", "visible"); } catch (_error) {}
    try { defineGetter(win.document, "hidden", false); } catch (_error) {}
    win.document.hasFocus = function hasFocus() { return true; };
  }
}

function installConsole(win) {
  if (!win.console) return;
  for (const name of ["log", "debug", "info", "warn", "error", "dir", "dirxml", "table", "trace", "group", "groupCollapsed", "groupEnd", "count", "time", "timeEnd"]) {
    try { win.console[name] = function () {}; } catch (_error) {}
  }
}

function calmHoneypot(inst) {
  let flipped = 0;
  const walk = (node) => {
    if (Array.isArray(node)) {
      for (const item of node) walk(item);
      return;
    }
    if (!node || typeof node !== "object") return;
    for (const name of Object.keys(node)) {
      const value = node[name];
      if (value === true) {
        node[name] = false;
        flipped += 1;
      } else if (value && typeof value === "object") {
        walk(value);
      }
    }
  };
  if (inst && inst.honeypotLog) walk(inst.honeypotLog);
  if (inst) inst.cachedFingerprints = null;
  return flipped;
}

function installTrust(win) {
  const Orig = win.MouseEvent;
  if (typeof Orig !== "function" || Orig.__trusted) return;
  function MouseEvent(type, init) {
    const event = new Orig(type, init);
    try {
      win.Object.defineProperty(event, "isTrusted", { configurable: true, get() { return true; } });
    } catch (_error) {}
    return event;
  }
  MouseEvent.prototype = Orig.prototype;
  MouseEvent.__trusted = true;
  win.MouseEvent = MouseEvent;
  if (typeof win.__mark === "function") win.__mark(MouseEvent, "MouseEvent");
}

function installLayout(win) {
  defineGetter(win, "outerWidth", 1920);
  defineGetter(win, "outerHeight", 1040);
  defineGetter(win, "innerWidth", 1920);
  defineGetter(win, "innerHeight", 969);
  defineGetter(win, "devicePixelRatio", 1);
  if (typeof win.fetch !== "function" && typeof globalThis.fetch === "function") win.fetch = globalThis.fetch;
  if (typeof win.__mark === "function" && typeof win.fetch === "function") win.__mark(win.fetch, "fetch");
  defineGetter(win.history, "length", 5);
  const screen = win.screen;
  for (const [key, value] of Object.entries({ width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24 })) {
    defineGetter(screen, key, value);
  }
  const sizeOf = (el, axis) => {
    const tag = el && el.tagName;
    if (tag === "HTML" || tag === "BODY") return axis === "h" ? 969 : 1920;
    let node = el;
    while (node) {
      if (node.id === "login-captcha") return axis === "h" ? 60 : 300;
      node = node.parentElement;
    }
    return 0;
  };
  for (const key of ["offsetWidth", "clientWidth", "scrollWidth"]) {
    win.Object.defineProperty(win.HTMLElement.prototype, key, { configurable: true, get() { return sizeOf(this, "w"); } });
  }
  for (const key of ["offsetHeight", "clientHeight", "scrollHeight"]) {
    win.Object.defineProperty(win.HTMLElement.prototype, key, { configurable: true, get() { return sizeOf(this, "h"); } });
  }
  win.Element.prototype.getBoundingClientRect = function getBoundingClientRect() {
    const width = sizeOf(this, "w");
    const height = sizeOf(this, "h");
    if (!width || !height) return { x: 0, y: 0, width: 0, height: 0, top: 0, left: 0, right: 0, bottom: 0, toJSON() { return this; } };
    return { x: 8, y: 120, width, height, top: 120, left: 8, right: 8 + width, bottom: 120 + height, toJSON() { return this; } };
  };
  defineGetter(win, "visualViewport", { width: 1920, height: 969, offsetLeft: 0, offsetTop: 0, pageLeft: 0, pageTop: 0, scale: 1, addEventListener() {}, removeEventListener() {} });
  if (typeof win.__mark === "function") win.__mark(win.Element.prototype.getBoundingClientRect, "getBoundingClientRect");
  if (process.env.WLZ_NARROW !== "1" && process.env.WLZ_DIALOGS !== "native") {
    function alert() { return undefined; }
    function confirm() { return true; }
    function prompt() { return ""; }
    try { delete alert.prototype; delete confirm.prototype; delete prompt.prototype; } catch (_error) {}
    win.alert = alert;
    win.confirm = confirm;
    win.prompt = prompt;
    if (typeof win.__mark === "function") {
      win.__mark(win.alert, "alert");
      win.__mark(win.confirm, "confirm");
      win.__mark(win.prompt, "prompt");
    }
  }
}

function installHostQuirks(win) {
  if (!win || win.__quirks) return;
  win.__quirks = true;
  const doc = win.document;
  const impl = doc && doc.implementation;
  if (impl && typeof impl.createHTMLDocument === "function" && !impl.createHTMLDocument.__quirk) {
    const orig = impl.createHTMLDocument.bind(impl);
    function createHTMLDocument(title) {
      const created = orig(title == null ? "" : title);
      try {
        const view = created.defaultView;
        if (view && view !== win) {
          installStack(view);
          installNavigator(view);
          installLayout(view);
          installHostQuirks(view);
        }
        if (created.body == null && created.documentElement) created.documentElement.appendChild(created.createElement("body"));
      } catch (_error) {}
      return created;
    }
    createHTMLDocument.__quirk = true;
    impl.createHTMLDocument = createHTMLDocument;
  }
}

function primeBehavior(win, target, click) {
  if (!win || !target || !target.dispatchEvent) return;
  for (let i = 0; i < 28; i += 1) {
    const x = 20 + i * 6;
    const y = 128 + (i % 4);
    target.dispatchEvent(new win.MouseEvent("mousemove", { bubbles: true, cancelable: true, clientX: x, clientY: y, screenX: x + 8, screenY: y + 40 }));
  }
  if (!click) return;
  target.dispatchEvent(new win.MouseEvent("mousedown", { bubbles: true, cancelable: true, clientX: 48, clientY: 138, button: 0 }));
  target.dispatchEvent(new win.MouseEvent("mouseup", { bubbles: true, cancelable: true, clientX: 49, clientY: 139, button: 0 }));
  target.dispatchEvent(new win.MouseEvent("click", { bubbles: true, cancelable: true, clientX: 49, clientY: 139, button: 0 }));
  if (win.document && win.document.dispatchEvent) {
    win.document.dispatchEvent(new win.KeyboardEvent("keydown", { bubbles: true, key: "a", code: "KeyA" }));
    win.document.dispatchEvent(new win.KeyboardEvent("keyup", { bubbles: true, key: "a", code: "KeyA" }));
  }
}

function installFrames(win) {
  const proto = win.HTMLIFrameElement && win.HTMLIFrameElement.prototype;
  const desc = proto && Object.getOwnPropertyDescriptor(proto, "contentWindow");
  const orig = desc && desc.get;
  if (typeof orig !== "function") return;
  const patched = new win.WeakSet();
  function contentWindow() {
    const child = orig.call(this);
    if (child && !patched.has(child)) {
      patched.add(child);
      try {
        if (process.env.WLZ_NARROW === "1") installNarrow(child);
        else if (process.env.WLZ_NOMARK !== "1") markNatives(child);
        installStack(child);
        installNavigator(child);
        installLayout(child);
        installCanvas(child);
        installAudio(child);
        installRtc(child);
        installHostQuirks(child);
        installWorker(child);
        if (process.env.WLZ_XHR === "1") installBridge(child);
      } catch (error) {
        report("frame-install " + String(error && error.message || error).slice(0, 80));
      }
    }
    return child;
  }
  Object.defineProperty(proto, "contentWindow", { configurable: true, get: contentWindow });
  if (typeof win.__mark === "function") win.__mark(contentWindow, "get contentWindow");
}

function installWorker(win) {
  const vm = require("vm");
  const blobs = new Map();
  let seq = 0;
  function Blob(parts, options) {
    this.type = (options && options.type) || "";
    this.__text = Array.from(parts || []).map((part) => typeof part === "string" ? part : "").join("");
    this.size = this.__text.length;
  }
  win.Blob = Blob;
  if (typeof win.__mark === "function") win.__mark(Blob, "Blob");
  if (!win.URL) win.URL = function URL() {};
  const create = typeof win.URL.createObjectURL === "function" ? win.URL.createObjectURL.bind(win.URL) : null;
  win.URL.createObjectURL = function createObjectURL(obj) {
    if (obj && typeof obj.__text === "string") {
      const id = "blob:local/" + (++seq);
      blobs.set(id, obj.__text);
      return id;
    }
    return create ? create(obj) : "";
  };
  if (typeof win.__mark === "function") win.__mark(win.URL.createObjectURL, "createObjectURL");
  win.URL.revokeObjectURL = function revokeObjectURL() {};
  function Worker(url) {
    this.onmessage = null;
    this.onerror = null;
    const listeners = [];
    this.addEventListener = (type, fn) => { if (type === "message") listeners.push(fn); };
    this.removeEventListener = () => {};
    this.terminate = () => {};
    const handlers = [];
    const context = {
      addEventListener(type, fn) { if (type === "message") handlers.push(fn); },
      removeEventListener() {},
      close() {},
      console: { log() {}, info() {}, debug() {}, warn() {}, error() {} },
      Uint8Array, Uint16Array, Uint32Array, Int8Array, Int16Array, Int32Array, Float32Array, Float64Array,
      ArrayBuffer, DataView, TextEncoder, TextDecoder,
      atob(text) { return Buffer.from(String(text), "base64").toString("binary"); },
      btoa(text) { return Buffer.from(String(text), "binary").toString("base64"); },
      crypto: globalThis.crypto,
      setTimeout, clearTimeout, Promise,
      Math, Date, JSON, Object, Array, String, Number, Boolean, RegExp, Error, TypeError, RangeError, Map, Set, WeakMap, WeakSet, Symbol, Proxy, Reflect, parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, decodeURIComponent, escape, unescape,
    };
    context.self = context;
    context.globalThis = context;
    context.postMessage = (data) => {
      const event = { data };
      if (typeof this.onmessage === "function") this.onmessage(event);
      for (const fn of listeners) fn(event);
    };
    const src = blobs.get(String(url)) || "";
    win.__workerBytes = src.length;
    if (process.env.WLZ_WORKER_OUT && src) fs.writeFileSync(process.env.WLZ_WORKER_OUT, src);
    try {
      vm.runInContext(src, vm.createContext(context), { filename: "wlz-worker.js" });
      win.__workerBoot = "ok";
    } catch (error) {
      win.__workerBoot = String(error && error.message || error).slice(0, 100);
    }
    this.postMessage = (data, _transfer) => {
      win.__workerMsgs = (win.__workerMsgs || 0) + 1;
      if (process.env.WLZ_CALM === "1" && data && data[0] && typeof data[0].byteLength === "number") {
        try {
          const text = Buffer.from(data[0]).toString("utf8");
          const parsed = JSON.parse(text);
          if (parsed && parsed.payload && Array.isArray(parsed.payload.risks)) {
            for (const item of parsed.payload.risks) if (item && typeof item === "object") item.detected = false;
            const hasher = win.__inst && win.__inst.calculateHash;
            const fingerprints = parsed.payload.fingerprints;
            if (typeof hasher === "function" && Array.isArray(fingerprints)) {
              try {
                const nextHash = hasher.call(win.__inst, fingerprints, parsed.payload.risks);
                const hashLen = typeof nextHash === "string" ? nextHash.length : -1;
                const same = typeof nextHash === "string" && nextHash === parsed.payload.hash;
                report("rehash " + hashLen + " same " + same + " keep " + (process.env.WLZ_KEEP === "1"));
                if (hashLen > 20 && process.env.WLZ_KEEP !== "1") parsed.payload.hash = nextHash;
              } catch (error) {
                report("rehash fail " + String(error && error.message || error).slice(0, 80));
              }
            }
            const next = Buffer.from(JSON.stringify(parsed));
            data[0] = new Uint8Array(next);
          }
        } catch (_error) {}
      }
      const trapBytes = data && data[0] && typeof data[0].byteLength === "number" ? Buffer.from(data[0]) : null;
      if (process.env.WLZ_TRAPS === "1" && trapBytes && !win.__trapsDumped) {
        try {
          const trapParsed = JSON.parse(trapBytes.toString("utf8"));
          const trapRisks = trapParsed && trapParsed.payload && trapParsed.payload.risks;
          if (Array.isArray(trapRisks)) {
            win.__trapsDumped = true;
            for (const item of trapRisks) {
              const det = item && item.detected;
              const bad = det && typeof det === "object" ? Object.keys(det).filter((key) => det[key] === true) : [];
              report("trap " + String(item && item.trapName || "?").slice(0, 48) + " " + bad.length + "/" + (det && typeof det === "object" ? Object.keys(det).length : 0) + " " + bad.join(","));
            }
          }
        } catch (_error) {}
      }
      if (process.env.WLZ_CAP === "1" && win.__workerMsgs <= 3) {
        let brief = typeof data;
        const bytes = data && data[0] && typeof data[0].byteLength === "number" ? Buffer.from(data[0]) : null;
        if (bytes) {
          const text = bytes.toString("utf8");
          brief = "bytes" + bytes.length;
          if (text.startsWith("{") || text.startsWith("[")) {
            try {
              const parsed = JSON.parse(text);
              const keys = parsed && typeof parsed === "object" && !Array.isArray(parsed) ? Object.keys(parsed) : [];
              const briefKeys = keys.slice(0, 8).map((key) => {
                const value = parsed[key];
                if (value && typeof value === "object" && !Array.isArray(value)) return key + ":{" + Object.keys(value).slice(0, 8).join("|") + "}";
                if (typeof value === "string") return key + ":s" + value.length;
                if (Array.isArray(value)) return key + ":a" + value.length;
                return key + ":" + typeof value;
              });
              brief += " " + briefKeys.join(",");
              const inner = parsed && parsed.payload;
              if (inner && typeof inner === "object") {
                const risks = inner.risks;
                if (Array.isArray(risks)) {
                  const sample = risks[0];
                  const sampleKeys = sample && typeof sample === "object" ? Object.keys(sample).join("|") : typeof sample;
                  const names = risks.slice(0, 20).map((item) => String(item && item.trapName || "?") + (item && item.detected ? "*" : "")).join(",");
                  report("risks arr " + risks.length + " keys " + sampleKeys + " " + names);
                } else if (risks && typeof risks === "object") {
                  const bad = Object.keys(risks).filter((key) => risks[key] === true);
                  report("risks " + bad.length + "/" + Object.keys(risks).length + " " + bad.slice(0, 20).join(","));
                } else {
                  report("risks " + (risks == null ? "null" : typeof risks));
                }
                const hash = inner.hash;
                const behavior = inner.behavior;
                const tracks = inner.tracks;
                const fp = inner.fingerprints;
                const fp0 = Array.isArray(fp) && fp[0] && typeof fp[0] === "object" ? Object.keys(fp[0]).slice(0, 6).join("|") : typeof fp;
                if (Array.isArray(fp)) {
                  const focus = new Set(["navigator", "environment", "location"]);
                  for (const item of fp) {
                    if (!item || !focus.has(item.key) || !item.value || typeof item.value !== "object") continue;
                    const known = new Set(["undefined", "true", "false", "object", "function", "string", "number", "null"]);
                    const bits = Object.keys(item.value).map((key) => {
                      const value = item.value[key];
                      if (typeof value === "string" && known.has(value)) return key + ":" + value;
                      if (typeof value === "string") return key + ":s" + value.length;
                      if (typeof value === "boolean" || typeof value === "number") return key + ":" + String(value);
                      if (Array.isArray(value)) return key + ":a" + value.length;
                      return key + ":" + typeof value;
                    });
                    report("fp " + item.key + " " + bits.join(","));
                    if (item.key === "environment" && win.__inst && typeof win.__inst.decryptValue === "function") {
                      const samples = ["hasProcess", "hasChromeObject", "hasChromeRuntime", "alertIntegrity", "confirmIntegrity", "evalIntegrity", "toStringIntegrity", "webdriverFlag", "webdriverIntegrity", "hasAutomationInStack", "hasFocus", "isWebView", "realBrowser", "browserEngine", "notificationPermission", "documentVisibility"];
                      const bits = samples.map((key) => {
                        try {
                          const plain = win.__inst.decryptValue.call(win.__inst, item.value[key]);
                          if (typeof plain === "boolean" || typeof plain === "number") return key + "=" + String(plain);
                          if (typeof plain === "string" && plain.length <= 24) return key + "=" + plain;
                          return key + ":" + (plain == null ? "null" : typeof plain === "string" ? "s" + plain.length : typeof plain);
                        } catch (_error) {
                          return key + ":err";
                        }
                      });
                      report("plain " + bits.join(","));
                    }
                    if (item.key === "environment" && win.__guess && typeof item.value.hasProcess === "string") {
                      const matched = Object.entries(win.__guess).filter(([, value]) => value && value === item.value.hasProcess).map(([key]) => key);
                      report("process-match " + (matched.join(",") || "none"));
                    }
                    if (item.key === "environment" && process.env.WLZ_FP_OUT) fs.writeFileSync(process.env.WLZ_FP_OUT, JSON.stringify(item.value));
                  }
                }
                if (process.env.WLZ_FIELD === "1" && Array.isArray(fp)) {
                  const known = ["Win32", "Gecko", "Windows", "chrome", "default", "prompt", "visible", "Mozilla", "Google", "Linux", "MacIntel", "true", "false"];
                  let seen = 0;
                  const hits = [];
                  const xorAt = (cipher, plain) => {
                    if (cipher.length < plain.length || cipher.length > plain.length + 8) return "";
                    for (let start = 0; start <= cipher.length - plain.length; start += 1) {
                      const keyByte = cipher.charCodeAt(start) ^ plain.charCodeAt(0);
                      const addByte = (cipher.charCodeAt(start) - plain.charCodeAt(0) + 65536) % 65536;
                      let xorGood = true;
                      let addGood = true;
                      const stream = [];
                      for (let i = 0; i < plain.length; i += 1) {
                        const left = cipher.charCodeAt(start + i);
                        const right = plain.charCodeAt(i);
                        stream.push(left ^ right);
                        if ((left ^ keyByte) !== right) xorGood = false;
                        if ((left - right + 65536) % 65536 !== addByte) addGood = false;
                      }
                      if (xorGood) return "xor@" + start + "+" + (cipher.length - plain.length);
                      if (addGood) return "add@" + start + "+" + (cipher.length - plain.length);
                      for (let period = 2; period <= 3 && period < plain.length; period += 1) {
                        let periodGood = true;
                        for (let i = 0; i < stream.length; i += 1) if (stream[i] !== stream[i % period]) periodGood = false;
                        if (periodGood) return "rxor" + period + "@" + start + "+" + (cipher.length - plain.length);
                      }
                    }
                    return "";
                  };
                  const walk = (item) => {
                    if (typeof item === "string") {
                      if (item.length < 4 || item.length > 48) return;
                      seen += 1;
                      if (hits.length >= 16) return;
                      for (const plain of known) {
                        const mode = item.indexOf(plain) >= 0 ? "contains" + item.indexOf(plain) : xorAt(item, plain);
                        if (mode) hits.push(plain.length + ":" + mode + " L" + item.length);
                      }
                      const sample = win.__sampleCipher;
                      if (sample && item.length >= sample.length && item.length <= sample.length + 4) {
                        const mode = item.indexOf(sample) >= 0 ? "sample-contains" : xorAt(item, sample);
                        if (mode) hits.push("sample:" + mode);
                      }
                      return;
                    }
                    if (!item || typeof item !== "object") return;
                    for (const child of Object.values(item)) walk(child);
                  };
                  for (const item of fp) walk(item && item.value);
                  report("peel seen " + seen + " hits " + (hits.join(" | ") || "none") + " sample " + (win.__sampleCipher ? "yes" : "no"));
                }
                report("parts hash " + (typeof hash === "string" ? hash.length : typeof hash) + " behavior " + (Array.isArray(behavior) ? behavior.length : typeof behavior) + " tracks " + (Array.isArray(tracks) ? tracks.length : typeof tracks) + " fp " + (Array.isArray(fp) ? fp.length : typeof fp) + " fp0 " + fp0);
              }
            } catch (_error) {
              brief += " text";
            }
          }
        } else if (data && typeof data === "object") {
          brief = "obj " + Object.keys(data).slice(0, 12).join(",");
        }
        report("worker-msg " + win.__workerMsgs + " " + brief.slice(0, 300));
      }
      const event = { data };
      const fns = handlers.slice();
      if (typeof context.onmessage === "function") fns.push(context.onmessage);
      for (const fn of fns) {
        try { fn(event); } catch (error) {
          win.__workerRun = String(error && error.message || error).slice(0, 100);
        }
      }
    };
    if (typeof win.__mark === "function") win.__mark(this.postMessage, "postMessage");
  }
  win.Worker = Worker;
  if (typeof win.__mark === "function") win.__mark(Worker, "Worker");
}

function installBridge(win) {
  const https = require("https");
  function XHR() {
    this.readyState = 0;
    this.status = 0;
    this.responseText = "";
    this.response = "";
    this.responseType = "";
    this.timeout = 0;
    this.withCredentials = false;
    this.onreadystatechange = null;
    this.onload = null;
    this.onerror = null;
    this.ontimeout = null;
    this.upload = { addEventListener() {} };
    this._headers = {};
  }
  XHR.prototype.open = function open(method, url) {
    this._method = String(method || "GET");
    this._url = String(url || "");
    this.readyState = 1;
  };
  XHR.prototype.setRequestHeader = function setRequestHeader(key, value) {
    this._headers[String(key).toLowerCase()] = String(value);
  };
  XHR.prototype.getAllResponseHeaders = function getAllResponseHeaders() { return this._rawHeaders || ""; };
  XHR.prototype.getResponseHeader = function getResponseHeader(name) {
    return (this._headerMap && this._headerMap[String(name).toLowerCase()]) || null;
  };
  XHR.prototype.abort = function abort() {};
  XHR.prototype.addEventListener = function addEventListener() {};
  XHR.prototype.overrideMimeType = function overrideMimeType() {};
  XHR.prototype.send = function send(body) {
    const urlText = this._url || "";
    let host = "";
    let path = urlText;
    try {
      const parsed = new URL(urlText, PAGE);
      host = parsed.host;
      path = parsed.pathname + parsed.search;
    } catch (_error) {}
    if (host !== "captcha.wangluozhe.com") {
      this.status = 0;
      this.readyState = 4;
      if (typeof this.onerror === "function") this.onerror();
      return;
    }
    const bodyKind = body == null ? "null" : typeof body;
    const bodyLen = body == null ? 0 : typeof body === "string" ? body.length : -1;
    if (!this._headers.origin) this._headers.origin = "https://www.spiderdemo.cn";
    if (!this._headers.referer) this._headers.referer = PAGE;
    if (!this._headers["user-agent"]) this._headers["user-agent"] = UA;
    if (process.env.WLZ_CAP === "1") {
      const names = Object.keys(this._headers).sort().join(",");
      let brief = bodyKind + ":" + bodyLen;
      if (typeof body === "string") {
        try {
          const parsed = JSON.parse(body);
          brief = Object.keys(parsed).map((key) => key + ":" + (typeof parsed[key] === "string" ? parsed[key].length : typeof parsed[key])).join(",");
        } catch (_error) {
          brief = "text:" + body.length;
        }
      }
      report("sdk-post " + this._method + " " + path + " hdr " + names.slice(0, 160) + " " + brief.slice(0, 180));
    }
    const payload = body == null ? Buffer.alloc(0) : Buffer.from(String(body));
    const headers = Object.assign({ "content-type": "application/json", "content-length": payload.length }, this._headers);
    const xhr = this;
    const req = https.request({ hostname: host, path, method: this._method, headers }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        xhr.responseText = Buffer.concat(chunks).toString("utf8");
        xhr.response = xhr.responseText;
        xhr.status = res.statusCode || 0;
        xhr.readyState = 4;
        xhr._headerMap = {};
        xhr._rawHeaders = Object.entries(res.headers).map(([key, value]) => key + ": " + value).join("\r\n");
        for (const [key, value] of Object.entries(res.headers)) xhr._headerMap[key.toLowerCase()] = Array.isArray(value) ? value.join(", ") : String(value);
        if (process.env.WLZ_CAP === "1") {
          let msg = "";
          let tokenLen = 0;
          let statusField = false;
          try {
            const parsed = JSON.parse(xhr.responseText);
            msg = String(parsed.msg || parsed.message || "");
            tokenLen = parsed.wsToken ? String(parsed.wsToken).length : 0;
            statusField = !!parsed.status;
          } catch (_error) {
            msg = "raw";
          }
          const msgClass = /成功/.test(msg) ? "auth-ok" : /失败/.test(msg) ? "auth-fail" : msg ? "other" : "empty";
          report("sdk-res " + xhr.status + " " + path + " " + msgClass + " tokenlen " + tokenLen + " statusField " + statusField);
        }
        if (typeof xhr.onreadystatechange === "function") xhr.onreadystatechange();
        if (typeof xhr.onload === "function") xhr.onload();
      });
    });
    req.on("error", () => {
      xhr.readyState = 4;
      if (typeof xhr.onerror === "function") xhr.onerror();
    });
    req.write(payload);
    req.end();
  };
  win.XMLHttpRequest = XHR;
  if (typeof win.__mark === "function") win.__mark(XHR, "XMLHttpRequest");
}

function installXhr(win) {
  const proto = win.XMLHttpRequest && win.XMLHttpRequest.prototype;
  if (!proto) return;
  for (const name of ["open", "send", "setRequestHeader", "abort", "getAllResponseHeaders", "getResponseHeader", "overrideMimeType"]) {
    if (typeof proto[name] === "function" && typeof win.__mark === "function") win.__mark(proto[name], name);
  }
  if (typeof win.__mark === "function") win.__mark(win.XMLHttpRequest, "XMLHttpRequest");
}

function postChallenge(wlzData) {
  const body = JSON.stringify({ timestamp: Date.now(), wlzData, siteKey: SITE_KEY, type: "checkbox" });
  return new Promise((resolve) => {
    const req = https.request({
      hostname: "captcha.wangluozhe.com",
      path: "/api/challenge",
      method: "POST",
      headers: {
        "content-type": "application/json",
        "content-length": Buffer.byteLength(body),
        "user-agent": UA,
        origin: "https://www.spiderdemo.cn",
        referer: PAGE,
      },
    }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        const text = Buffer.concat(chunks).toString("utf8");
        let msg = "";
        let token = "";
        let statusField = false;
        try {
          const parsed = JSON.parse(text);
          msg = String((parsed && (parsed.msg || parsed.message || parsed.error)) || "");
          token = parsed && parsed.wsToken ? String(parsed.wsToken) : "";
          statusField = !!(parsed && parsed.status);
        } catch (_error) {
          msg = "raw";
        }
        resolve({ http: res.statusCode, msg, token, statusField });
      });
    });
    req.on("error", (error) => resolve({ http: 0, msg: String(error.message || "error"), token: "", statusField: false }));
    req.write(body);
    req.end();
  });
}

function breakFieldCipher(root, inst) {
  const UA_APP = "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
  const expect = {
    platform: ["Win32"],
    product: ["Gecko"],
    productSub: ["20030107"],
    appCodeName: ["Mozilla"],
    appName: ["Netscape"],
    vendor: ["Google Inc."],
    language: ["zh-CN"],
    userAgent: [UA],
    appVersion: [UA_APP],
    protocol: ["https:"],
    hostname: ["www.spiderdemo.cn"],
    host: ["www.spiderdemo.cn"],
    origin: ["https://www.spiderdemo.cn"],
    href: [PAGE],
    pathname: ["/captcha/wlzshield_captcha_challenge"],
    webdriverFlag: ["true", "false"],
    webdriverIntegrity: ["true", "false"],
    hasProcess: ["true", "false"],
    hasGlobal: ["true", "false"],
    hasBuffer: ["true", "false"],
    hasRequire: ["true", "false"],
    hasModule: ["true", "false"],
    hasChromeObject: ["true", "false"],
    hasChromeRuntime: ["true", "false"],
    alertIntegrity: ["true", "false"],
    confirmIntegrity: ["true", "false"],
    evalIntegrity: ["true", "false"],
    toStringIntegrity: ["true", "false"],
    mobile: ["true", "false"],
    onLine: ["true", "false"],
    cookieEnabled: ["true", "false"],
    isTopLevel: ["true", "false"],
    inIframe: ["true", "false"],
    hasFocus: ["true", "false"],
    notificationPermission: ["default", "prompt", "granted", "denied"],
    documentVisibility: ["visible", "hidden"],
    version: ["WebGL 1.0", "WebGL 2.0"],
  };
  const confident = new Set(["platform", "product", "productSub", "appCodeName", "appName", "language", "protocol", "userAgent", "appVersion"]);
  const fields = [];
  const walk = (node, path) => {
    if (typeof node === "string") {
      fields.push({ path, name: path.split(".").pop(), value: node });
      return;
    }
    if (Array.isArray(node)) {
      if (node.length && node[0] && typeof node[0] === "object" && node[0].key && Object.prototype.hasOwnProperty.call(node[0], "value")) {
        for (const item of node) walk(item.value, path ? path + "." + item.key : String(item.key || ""));
        return;
      }
      return;
    }
    if (node && typeof node === "object") {
      for (const key of Object.keys(node)) walk(node[key], path ? path + "." + key : key);
    }
  };
  walk(root, "");
  const seed = inst && inst.seed != null ? String(inst.seed) : "";
  const keys = {
    fp: "wlz_fp_secret_key_2025",
    trap: "wlz_trap_seed_x9",
    secure: "__WLZ_SECURE_KEY__",
    magic: "wlz_shield_magic_2024",
    site: SITE_KEY,
    seed,
  };
  const hits = [];
  const consider = (label, cipher, plain, key) => {
    const extra = cipher.length - plain.length;
    if (extra < 0 || extra > 8 || !key) return;
    for (let start = 0; start <= extra; start += 1) {
      const modes = ["xor", "add", "xor-seed", "add-seed"];
      for (const mode of modes) {
        let good = true;
        for (let i = 0; i < plain.length; i += 1) {
          const left = cipher.charCodeAt(start + i);
          const right = plain.charCodeAt(i);
          const k = key.charCodeAt(i % key.length);
          const s = seed ? seed.charCodeAt(i % seed.length) : 0;
          let got = left ^ k;
          if (mode === "add") got = (left - k + 256) % 256;
          if (mode === "xor-seed") got = left ^ k ^ s;
          if (mode === "add-seed") got = (left - k - s + 512) % 256;
          if (got !== right) {
            good = false;
            break;
          }
        }
        if (good) hits.push(label + " " + mode + " x" + extra + "@" + start);
      }
    }
  };
  for (const field of fields) {
    const plains = expect[field.name];
    if (!plains || !confident.has(field.name)) continue;
    for (const plain of plains) {
      for (const [keyName, key] of Object.entries(keys)) consider(field.name + ":" + keyName, field.value, plain, key);
    }
  }
  report("break direct " + (hits.slice(0, 12).join(" | ") || "none") + " seedLen " + seed.length + " fields " + fields.length);
  const shortNames = new Set(["platform", "product", "productSub", "appCodeName", "appName", "language", "protocol"]);
  const shortFields = fields.filter((field) => shortNames.has(field.name));
  const tagHits = [];
  for (const field of shortFields) {
    const plain = (expect[field.name] || [])[0];
    if (!plain) continue;
    const extra = field.value.length - plain.length;
    if (extra < 1 || extra > 6) continue;
    const splits = [
      { start: extra, tag: field.value.slice(0, extra), where: "pre" },
      { start: 0, tag: field.value.slice(plain.length), where: "suf" },
    ];
    for (const split of splits) {
      const body = field.value.slice(split.start, split.start + plain.length);
      const checks = {
        "tag-xor": (i) => body.charCodeAt(i) ^ split.tag.charCodeAt(i % split.tag.length),
        "tag-add": (i) => (body.charCodeAt(i) - split.tag.charCodeAt(i % split.tag.length) + 256) % 256,
        "seed-xor": (i) => body.charCodeAt(i) ^ (seed ? seed.charCodeAt(i % seed.length) : 0),
        chain: (i) => body.charCodeAt(i) ^ (i === 0 ? split.tag.charCodeAt(0) : body.charCodeAt(i - 1)),
      };
      for (const [mode, fn] of Object.entries(checks)) {
        let good = seed || mode.indexOf("seed") !== 0;
        for (let i = 0; i < plain.length && good; i += 1) if (fn(i) !== plain.charCodeAt(i)) good = false;
        if (good) tagHits.push(field.name + " " + mode + " " + split.where + extra);
      }
    }
  }
  report("break tag " + (tagHits.join(" | ") || "none") + " short " + shortFields.length);
  const mixRank = [];
  for (const extra of [2, 3, 4]) {
    for (const where of ["pre", "suf"]) {
      const rows = [];
      for (const field of shortFields) {
        const plain = (expect[field.name] || [])[0];
        if (!plain || field.value.length !== plain.length + extra) continue;
        const tag = where === "pre" ? field.value.slice(0, extra) : field.value.slice(plain.length);
        const start = where === "pre" ? extra : 0;
        const ks = [];
        for (let i = 0; i < plain.length; i += 1) ks.push(field.value.charCodeAt(start + i) ^ plain.charCodeAt(i) ^ tag.charCodeAt(i % tag.length));
        rows.push({ name: field.name, ks });
      }
      if (rows.length < 3) continue;
      const width = Math.max(...rows.map((row) => row.ks.length));
      let agreed = 0;
      let total = 0;
      for (let index = 0; index < width; index += 1) {
        const votes = new Map();
        for (const row of rows) {
          if (index >= row.ks.length) continue;
          const byte = row.ks[index];
          votes.set(byte, (votes.get(byte) || 0) + 1);
          total += 1;
        }
        agreed += Math.max(0, ...votes.values());
      }
      mixRank.push(where + extra + " r" + (total ? (agreed / total).toFixed(2) : "0") + " n" + rows.length);
    }
  }
  report("break mix " + (mixRank.join(" ") || "none"));
  const boolFields = fields.filter((field) => field.path.indexOf("environment.") === 0);
  const byValue = new Map();
  for (const field of boolFields) {
    if (!byValue.has(field.value)) byValue.set(field.value, []);
    byValue.get(field.value).push(field);
  }
  const big = [...byValue.entries()].filter(([, names]) => names.length >= 8).slice(0, 2);
  const boolHits = [];
  for (const [cipher, group] of big) {
    for (const plain of ["true", "false", "1", "0"]) {
      if (cipher.length < plain.length || cipher.length > plain.length + 4) continue;
      const extra = cipher.length - plain.length;
      for (const where of ["pre", "suf"]) {
        const tag = where === "pre" ? cipher.slice(0, extra) : cipher.slice(plain.length);
        const start = where === "pre" ? extra : 0;
        if (!tag.length) continue;
        let xorGood = true;
        let addGood = true;
        for (let i = 0; i < plain.length; i += 1) {
          const left = cipher.charCodeAt(start + i);
          const mix = tag.charCodeAt(i % tag.length);
          if ((left ^ mix) !== plain.charCodeAt(i)) xorGood = false;
          if ((left - mix + 256) % 256 !== plain.charCodeAt(i)) addGood = false;
        }
        if (xorGood || addGood) boolHits.push((xorGood ? "xor" : "add") + " " + where + extra + " L" + cipher.length + " g" + group.length);
      }
    }
  }
  report("break bool " + (boolHits.join(" | ") || "none") + " groups " + big.length);
  const envStrings = fields.filter((field) => field.path.indexOf("environment.") === 0 && typeof field.value === "string");
  const clusters = new Map();
  for (const field of envStrings) {
    const id = field.value.length + ":" + field.value;
    if (!clusters.has(id)) clusters.set(id, []);
    clusters.get(id).push(field.name);
  }
  const clusterNote = [...clusters.values()]
    .filter((names) => names.length >= 2)
    .sort((a, b) => b.length - a.length)
    .slice(0, 4)
    .map((names) => names.length + ":" + names[0] + "+");
  report("break clusters " + (clusterNote.join(" ") || "none") + " env " + envStrings.length);
  let fnNote = "none";
  const mods = inst && inst.modules;
  if (mods && typeof mods === "object") {
    const found = [];
    const seen = new Set();
    const scan = (node, depth) => {
      if (!node || typeof node !== "object" || depth > 2 || seen.has(node)) return;
      seen.add(node);
      for (const key of Object.keys(node).slice(0, 40)) {
        if (/encrypt|decrypt|seed|cipher/i.test(key)) found.push(key);
        const child = node[key];
        if (typeof child === "function" && /encrypt|decrypt/i.test(child.name || "")) found.push(child.name);
        if (child && typeof child === "object") scan(child, depth + 1);
      }
    };
    scan(mods, 0);
    const keyNames = Array.isArray(mods) ? "a" + mods.length : Object.keys(mods).slice(0, 20).join(",");
    fnNote = keyNames + " fn " + (found.slice(0, 12).join(",") || "none");
  }
  const wanted = ["decryptValue", "encryptValue", "encryptWithSeed", "encryptAES"];
  const foundFn = [];
  const seenFn = new Set();
  const hunt = (node, depth) => {
    if (!node || typeof node !== "object" || depth > 3 || seenFn.has(node) || seenFn.size > 250) return;
    seenFn.add(node);
    let keys = [];
    try { keys = Object.getOwnPropertyNames(node); } catch (_error) { return; }
    for (const key of keys) {
      if (wanted.includes(key) && typeof node[key] === "function") foundFn.push(key);
      if (depth < 3 && node[key] && typeof node[key] === "object") hunt(node[key], depth + 1);
    }
  };
  hunt(inst, 0);
  report("break modules " + fnNote + " hunt " + (foundFn.join(",") || "none"));
  const rc4Bytes = (key, plain) => {
    const s = new Uint8Array(256);
    for (let i = 0; i < 256; i += 1) s[i] = i;
    let j = 0;
    const source = Buffer.from(String(key));
    for (let i = 0; i < 256; i += 1) {
      j = (j + s[i] + source[i % source.length]) & 255;
      const swap = s[i];
      s[i] = s[j];
      s[j] = swap;
    }
    let i = 0;
    j = 0;
    const text = Buffer.from(String(plain));
    const out = Buffer.alloc(text.length);
    for (let n = 0; n < text.length; n += 1) {
      i = (i + 1) & 255;
      j = (j + s[i]) & 255;
      const swap = s[i];
      s[i] = s[j];
      s[j] = swap;
      out[n] = text[n] ^ s[(s[i] + s[j]) & 255];
    }
    return out;
  };
  const crypto = require("crypto");
  const digest = (name, text) => crypto.createHash(name).update(String(text)).digest();
  const streamHit = (cipher, plain, stream) => {
    if (!stream || !stream.length || cipher.length < plain.length) return "";
    const extra = cipher.length - plain.length;
    if (extra > 8) return "";
    for (let start = 0; start <= extra; start += 1) {
      let good = true;
      for (let i = 0; i < plain.length; i += 1) {
        const left = cipher.charCodeAt(start + i);
        const k = stream[i % stream.length];
        if ((left ^ k) !== plain.charCodeAt(i) && (left - k + 256) % 256 !== plain.charCodeAt(i)) {
          good = false;
          break;
        }
      }
      if (good) return "@" + start;
    }
    return "";
  };
  const rc4Note = [];
  const streamNote = [];
  for (const field of shortFields) {
    const plain = (expect[field.name] || [])[0];
    if (!plain) continue;
    for (const [keyName, key] of Object.entries(keys)) {
      if (!key) continue;
      const raw = rc4Bytes(key, plain);
      const asText = raw.toString("latin1");
      const asB64 = raw.toString("base64").replace(/=+$/, "");
      if (field.value.includes(asText) || field.value.includes(asB64)) rc4Note.push(field.name + ":" + keyName);
      const md5 = digest("md5", key);
      const sha = digest("sha256", key);
      const where = streamHit(field.value, plain, md5) || streamHit(field.value, plain, sha);
      if (where) streamNote.push(field.name + ":" + keyName + where);
    }
  }
  let hashRel = "nohash";
  const platformField = fields.find((field) => field.name === "platform" && field.path.indexOf("navigator.") === 0);
  if (platformField && inst && typeof inst.hash === "function") {
    try {
      const hashed = String(inst.hash("Win32"));
      hashRel = platformField.value.includes(hashed) ? "inside" : "apart";
      hashRel += " h" + hashed.length;
    } catch (_error) {
      hashRel = "err";
    }
  }
  report("break rc4 " + (rc4Note.join(" ") || "none") + " stream " + (streamNote.join(" ") || "none") + " hash " + hashRel);
  const platform = fields.find((field) => field.name === "platform" && field.path.indexOf("navigator.") === 0);
  if (platform) {
    let printable = 0;
    let b64 = 0;
    for (const ch of platform.value) {
      const code = ch.charCodeAt(0);
      if (code >= 32 && code < 127) printable += 1;
      if (/[A-Za-z0-9+/=_-]/.test(ch)) b64 += 1;
    }
    report("break platform len " + platform.value.length + " print " + printable + " b64 " + b64);
  }
}

async function main() {
  const virtualConsole = new VirtualConsole();
  let jsdomNotes = 0;
  virtualConsole.on("jsdomError", (error) => {
    if (jsdomNotes >= 8) return;
    jsdomNotes += 1;
    report("jsdom " + String(error && error.message || error).slice(0, 160));
  });
  const dom = new JSDOM("<!doctype html><html><head><script src=\"https://captcha.wangluozhe.com/vendors.min.js\"></script><script src=\"https://captcha.wangluozhe.com/wlzshield.min.js\"></script></head><body><div id=\"login-captcha\"></div><script src=\"https://www.spiderdemo.cn/static/js/captcha/wlzshield_captcha_challenge.js\"></script></body></html>", {
    url: PAGE,
    pretendToBeVisual: true,
    runScripts: "outside-only",
    resources: { userAgent: UA },
    virtualConsole,
  });
  const win = dom.window;
  const nativeRandom = win.Math.random.bind(win.Math);
  const firstR = [];
  const lastR = [];
  win.Math.random = function mathRandom() {
    const value = nativeRandom();
    win.__mathN = (win.__mathN || 0) + 1;
    if (firstR.length < 24) firstR.push(value);
    lastR.push(value);
    if (lastR.length > 64) lastR.shift();
    return value;
  };
  win.__mathFirst = firstR;
  win.__mathLast = lastR;
  if (win.crypto && !win.crypto.subtle) {
    Object.defineProperty(win.crypto, "subtle", {
      value: require("crypto").webcrypto.subtle,
      configurable: true,
    });
  }
  if (win.crypto && typeof win.crypto.getRandomValues === "function") {
    const randomValues = win.crypto.getRandomValues.bind(win.crypto);
    win.crypto.getRandomValues = function getRandomValues(array) {
      win.__randN = (win.__randN || 0) + 1;
      if (!win.__randSizes) win.__randSizes = [];
      if (win.__randSizes.length < 8 && array && typeof array.length === "number") win.__randSizes.push(array.length);
      return randomValues(array);
    };
  }
  if (process.env.WLZ_AES_CALM === "1") win.__aesCalm = true;
  if (process.env.WLZ_REPACK === "1") win.__aesRepack = true;
  win.__keyClass = (key, cfg, out) => {
    const crypto = require("crypto");
    const wordsToBuf = (wordArray) => {
      if (!wordArray || !wordArray.words) return Buffer.alloc(0);
      const size = wordArray.sigBytes || 0;
      const buf = Buffer.alloc(size);
      for (let i = 0; i < size; i += 1) {
        const word = wordArray.words[i >>> 2] >>> 0;
        buf[i] = (word >>> (24 - (i % 4) * 8)) & 255;
      }
      return buf;
    };
    const keyBuf = wordsToBuf(key);
    const ivBuf = cfg && cfg.iv ? wordsToBuf(cfg.iv) : Buffer.alloc(0);
    const eq = (buf) => buf.length === keyBuf.length && buf.equals(keyBuf);
    const md5 = (text) => crypto.createHash("md5").update(String(text)).digest();
    const names = [];
    if (eq(md5(SITE_KEY))) names.push("md5site");
    if (eq(Buffer.from(SITE_KEY, "hex"))) names.push("sitehex");
    if (eq(crypto.createHash("sha256").update(SITE_KEY).digest().subarray(0, 16))) names.push("sha16");
    const inst = win.__inst;
    const sid = inst && inst.sessionId;
    const did = inst && inst.deviceId;
    if (typeof sid === "string") {
      if (eq(md5(sid))) names.push("md5sid");
      if (eq(md5(SITE_KEY + sid))) names.push("md5site+sid");
      if (eq(md5(sid + SITE_KEY))) names.push("md5sid+site");
      if (eq(Buffer.from(String(sid).replace(/[^0-9a-f]/gi, "").slice(0, 32), "hex"))) names.push("sidhex");
    }
    if (typeof did === "string" && eq(md5(did))) names.push("md5did");
    const fromFloats = (floats) => {
      const found = [];
      const take = (buf, label) => {
        if (buf.length === keyBuf.length && buf.equals(keyBuf)) found.push(label + "key");
        if (buf.length === ivBuf.length && ivBuf.length > 0 && buf.equals(ivBuf)) found.push(label + "iv");
      };
      for (let i = 0; i + 4 <= floats.length; i += 1) {
        const be = Buffer.alloc(16);
        const le = Buffer.alloc(16);
        for (let w = 0; w < 4; w += 1) {
          const word = (floats[i + w] * 0x100000000) >>> 0;
          be.writeUInt32BE(word, w * 4);
          le.writeUInt32LE(word, w * 4);
        }
        take(be, "wbe" + i);
        take(le, "wle" + i);
        if (i > 8) break;
      }
      if (floats.length >= 16) {
        const bytes = Buffer.alloc(16);
        for (let b = 0; b < 16; b += 1) bytes[b] = Math.floor(floats[b] * 256) & 255;
        take(bytes, "b");
      }
      return found;
    };
    names.push(...fromFloats(win.__mathFirst || []).map((item) => "first" + item));
    names.push(...fromFloats(win.__mathLast || []).map((item) => "last" + item));
    const ct = out && out.ciphertext ? wordsToBuf(out.ciphertext) : Buffer.alloc(0);
    const ivAt = ivBuf.length && ct.length >= ivBuf.length ? ct.indexOf(ivBuf) : -1;
    win.__aesKey = keyBuf;
    win.__aesIv = ivBuf;
    win.__aesCt = ct;
    return (names.join(",") || "unmatched") + " iv" + ivBuf.length + " " + (ivAt >= 0 ? "iv-in-ct" : "iv-apart") + " ct" + ct.length;
  };
  win.__gunzipShape = (bytes) => {
    try {
      const text = require("zlib").gunzipSync(Buffer.from(bytes)).toString("utf8");
      const parsed = JSON.parse(text);
      const inner = parsed && parsed.payload && typeof parsed.payload === "object" ? parsed.payload : parsed;
      const keys = inner && typeof inner === "object" ? Object.keys(inner).slice(0, 8).join("|") : typeof inner;
      const risks = inner && Array.isArray(inner.risks) ? inner.risks : [];
      const stars = risks.filter((item) => item && item.detected === true).length;
      const det = risks[0] && risks[0].detected;
      const detKind = det === true ? "true" : det === false ? "false" : det && typeof det === "object" ? "obj" + Object.keys(det).length : typeof det;
      let nested = 0;
      for (const item of risks) {
        if (!item || !item.detected || typeof item.detected !== "object") continue;
        nested += Object.values(item.detected).filter((value) => value === true).length;
      }
      const behavior = inner && Array.isArray(inner.behavior) ? inner.behavior.length : -1;
      return "ok " + keys + " stars" + stars + "/" + risks.length + " det" + detKind + " nested" + nested + " beh" + behavior + " text" + text.length;
    } catch (error) {
      return "bad " + String(error && (error.code || error.message || "err")).slice(0, 40);
    }
  };
  const bare = process.env.WLZ_BARE === "1" || process.env.WLZ_MIN === "1";
  if (!bare) {
    if (process.env.WLZ_NARROW === "1") installNarrow(win);
    else if (process.env.WLZ_NOMARK !== "1") markNatives(win);
    installStack(win);
    installXhr(win);
    installConsole(win);
    installTrust(win);
    installFrames(win);
  }
  installWorker(win);
  if (process.env.WLZ_XHR === "1") installBridge(win);
  if (process.env.WLZ_NET === "1") {
    const origOpen = win.XMLHttpRequest && win.XMLHttpRequest.prototype.open;
    if (origOpen) {
      win.XMLHttpRequest.prototype.open = function open(method, url) {
        report("xhr " + method + " " + String(url).split("?")[0].slice(0, 100));
        return origOpen.apply(this, arguments);
      };
    }
    if (typeof win.fetch === "function") {
      const origFetch = win.fetch;
      win.fetch = function fetch(input) {
        const url = typeof input === "string" ? input : input && input.url;
        report("fetch " + String(url || "").split("?")[0].slice(0, 100));
        return origFetch.apply(this, arguments);
      };
    }
  }
  if (process.env.WLZ_MIN === "1") installStack(win);
  if (process.env.WLZ_MIN !== "1") {
    installNavigator(win);
    installLayout(win);
    installCanvas(win);
    installAudio(win);
    installRtc(win);
    installHostQuirks(win);
  }
  const uaBad = /jsdom|headless/i.test(win.navigator.userAgent);
  const stack = String(new win.Error("x").stack || "");
  report("env uaBad " + uaBad + " webdriver " + win.navigator.webdriver + " plugins " + win.navigator.plugins.length + " screen " + win.screen.width + " stackNode " + /node:|jsdom/i.test(stack) + " fetch " + typeof win.fetch + " history " + win.history.length + " all " + typeof win.document.all);
  if (process.env.WLZ_PATCH === "1") {
    const OrigPromise = win.Promise;
    function notePromise(value) {
      if (!win.__capOn || typeof value !== "string") return;
      win.__pres = (win.__pres || 0) + 1;
      if (value.length === 0) {
        win.__pre0 = (win.__pre0 || 0) + 1;
        if (!win.__preStack) {
          win.__preStack = String(new Error("p").stack || "").split("\n").slice(1, 5).map((line) => line.trim().replace(root, "").slice(0, 90)).join(" || ");
        }
      }
      if (value.length > (win.__preBest || 0)) {
        win.__preBest = value.length;
        win.__preVal = value;
      }
    }
    function CapPromise(executor) {
      return new OrigPromise((resolve, reject) => executor((value) => {
        notePromise(value);
        resolve(value);
      }, reject));
    }
    CapPromise.prototype = OrigPromise.prototype;
    for (const name of ["reject", "all", "race", "allSettled", "any"]) CapPromise[name] = OrigPromise[name];
    CapPromise.resolve = function resolve(value) {
      notePromise(value);
      return OrigPromise.resolve(value);
    };
    win.Promise = CapPromise;
    if (typeof win.__mark === "function") win.__mark(CapPromise, "Promise");
  }
  let vendors = fs.readFileSync(path.join(root, "vendors.min.js"), "utf8");
  if (process.env.WLZ_AES === "1") {
    const marker = "t.AES=e._createHelper(v)}(),n.AES)}()";
    if (!vendors.includes(marker)) report("aes-marker-missing");
    else vendors = vendors.replace(marker, fs.readFileSync(path.join(root, "_aes_hook.js"), "utf8"));
  }
  if (process.env.WLZ_PATCH === "1") {
    const awaitThrow = "function s(t){try{c(r.throw(t))}catch(t){o(t)}}";
    if (!vendors.includes(awaitThrow)) {
      report("FAIL await-shape");
      win.close();
      process.exit(1);
    }
    vendors = vendors.replace(awaitThrow, "function s(t){try{if(globalThis.__capOn){var __m=String(t&&t.message||t).slice(0,120);var __e=globalThis.__awaitErr||(globalThis.__awaitErr=[]);if(__e.length<6&&__e.indexOf(__m)<0)__e.push(__m);}c(r.throw(t))}catch(t){o(t)}}");
  }
  const vm = require("vm");
  const context = vm.createContext(win);
  const runInPage = (code, filename) => vm.runInContext(code, context, { filename: filename || PAGE });
  win.eval = (code) => runInPage(code, PAGE);
  runInPage(vendors, "https://captcha.wangluozhe.com/vendors.min.js");
  if (process.env.WLZ_AES === "1") report("aesExport " + typeof (win.__AES && win.__AES.encrypt));
  if (process.env.WLZ_CAP === "1") {
    const leaked = runInPage("typeof process + '/' + typeof Buffer + '/' + typeof require");
    const stackBad = runInPage("var s=String(new Error('x').stack||''); /evalmachine|node:|jsdom/i.test(s)");
    report("realm leak " + leaked + " stackBad " + stackBad);
  }
  let sdk = fs.readFileSync(path.join(root, "wlzshield.min.js"), "utf8");
  if (process.env.WLZ_PATCH === "1") {
    const retOp = "if(26<Lb)return Kd[--yC-Lb+27];";
    const catchOp = "try{return Cc()}catch(qC){return WG()}";
    if (!sdk.includes(retOp) || !sdk.includes(catchOp)) {
      report("FAIL sdk-shape");
      win.close();
      process.exit(1);
    }
    const entry = "function LX(R,RM,Kd,Gd,XM){RM=RM||[],Kd=Kd||[],Gd=Gd||[];";
    const ziEntry = "function zi(bM,MB,eT,Bn,MA){MB=MB||[],eT=eT||[],Bn=Bn||[];";
    const ziRet = "else return eT[--jb+--BC-44];";
    if (!sdk.includes(ziEntry) || !sdk.includes(ziRet)) {
      report("FAIL zi-shape");
      win.close();
      process.exit(1);
    }
    sdk = sdk.replace(entry, "function LX(R,RM,Kd,Gd,XM){if(globalThis.__capOn)globalThis.__lx=(globalThis.__lx||0)+1;RM=RM||[],Kd=Kd||[],Gd=Gd||[];");
    sdk = sdk.replace(ziEntry, "function zi(bM,MB,eT,Bn,MA){if(globalThis.__capOn)globalThis.__zi=(globalThis.__zi||0)+1;MB=MB||[],eT=eT||[],Bn=Bn||[];");
    sdk = sdk.replace(ziRet, "else{var __v=eT[--jb+--BC-44];if(globalThis.__capOn){var __k=typeof __v;globalThis.__retN=(globalThis.__retN||0)+1;globalThis.__retK=globalThis.__retK||{};globalThis.__retK[__k]=(globalThis.__retK[__k]||0)+1;if(__k===\"string\"){globalThis.__strN=(globalThis.__strN||0)+1;if(__v.length===0)globalThis.__emptyN=(globalThis.__emptyN||0)+1;if(__v.length>=8&&__v.length<=48&&/detected|integrity|webdriver|Stack|native|process|hook|proxy|sandbox|chrome|plugin|iframe|hidden|timing|network|behavior|fingerprint|capture|eval|alert|devtools|headless|node/.test(__v)){var __w=globalThis.__words||(globalThis.__words=[]);if(__w.length<120&&__w.indexOf(__v)<0)__w.push(__v);}if(__v.length>40){var __a=globalThis.__lens||(globalThis.__lens=[]);if(__a.length<40)__a.push(__v.length);if(__v.length>(globalThis.__bestLen||0)){globalThis.__bestLen=__v.length;globalThis.__best=__v;}}}}return __v;}");
    const decoder = "if(nz!==void 0)return nz";
    if (sdk.includes(decoder)) {
      sdk = sdk.replace(decoder, "if(nz!==void 0){if(globalThis.__capOn&&typeof nz===\"string\"&&nz.length>=4&&nz.length<=42&&/^[A-Za-z_][A-Za-z0-9_]+$/.test(nz)){var __w=globalThis.__words||(globalThis.__words=[]);if(__w.length<220&&__w.indexOf(nz)<0)__w.push(nz);}return nz}");
    }
    const ziCatch = "try{return bT()}catch(MC){return bi()}";
    sdk = sdk.replace(ziCatch, "try{return bT()}catch(MC){if(globalThis.__capOn){var __m=String(MC&&MC.message||MC).slice(0,70);var __e=globalThis.__errs||(globalThis.__errs=[]);if(__e.length<8&&__e.indexOf(__m)<0)__e.push(__m);}return bi()}");
    sdk = sdk.replace(retOp, "if(26<Lb){var __v=Kd[--yC-Lb+27];if(globalThis.__capOn){var __k=typeof __v;globalThis.__retN=(globalThis.__retN||0)+1;globalThis.__retK=globalThis.__retK||{};globalThis.__retK[__k]=(globalThis.__retK[__k]||0)+1;if(__k===\"string\"){globalThis.__strN=(globalThis.__strN||0)+1;if(__v.length===0)globalThis.__emptyN=(globalThis.__emptyN||0)+1;if(__v.length>40){var __a=globalThis.__lens||(globalThis.__lens=[]);if(__a.length<40)__a.push(__v.length);if(__v.length>(globalThis.__bestLen||0)){globalThis.__bestLen=__v.length;globalThis.__best=__v;}}}}return __v;}");
    sdk = sdk.replace(catchOp, "try{return Cc()}catch(qC){if(globalThis.__capOn){var __m=String(qC&&qC.message||qC).slice(0,60);var __e=globalThis.__errs||(globalThis.__errs=[]);if(__e.length<6&&__e.indexOf(__m)<0)__e.push(__m);}return WG()}");
  }
  if (process.env.WLZ_PATCH === "1") win.__capOn = true;
  if (process.env.WLZ_FIELD === "1") {
    const fieldRet = "else return eT[--jb+--BC-44];";
    if (!sdk.includes(fieldRet)) report("field-shape-missing");
    else {
      const allow = new Set(["visible", "hidden", "default", "Win32", "Gecko", "Windows", "chrome", "prompt", "granted", "denied", "Google", "Mozilla", "Linux", "MacIntel", "desktop", "mobile", "WebKit", "Blink", "Win64"]);
      const seen = new Set();
      win.__fieldBag = [];
      win.__fieldProbe = (stack, jb, bc) => {
        const idx = jb + bc - 44;
        const value = stack[idx];
        win.__fieldN = (win.__fieldN || 0) + 1;
        if (typeof value === "string" && allow.has(value)) win.__lastPlain = value;
        if (win.__fieldN > 500000 || win.__fieldBag.length >= 30 || typeof value !== "string" || value.length < 4 || value.length > 64) return value;
        if (win.__lastPlain && value.length === win.__lastPlain.length + 4 && value.indexOf(win.__lastPlain) < 0) {
          const plain = win.__lastPlain;
          const tag = "next+" + plain.length;
          if (!seen.has(tag)) {
            const keyByte = value.charCodeAt(0) ^ plain.charCodeAt(0);
            let good = value.length >= plain.length;
            for (let j = 1; j < plain.length && good; j += 1) if ((value.charCodeAt(j) ^ keyByte) !== plain.charCodeAt(j)) good = false;
            if (good) {
              seen.add(tag);
              win.__fieldBag.push(tag + ":nextxor L" + value.length);
            }
          }
        }
        const lo = Math.max(0, idx - 8);
        const hi = Math.min(stack.length - 1, idx + 6);
        for (let i = lo; i <= hi; i += 1) {
          if (i === idx) continue;
          const plain = stack[i];
          if (typeof plain !== "string" || !allow.has(plain)) continue;
          const tag = plain + "@" + (i - idx);
          if (seen.has(tag)) continue;
          seen.add(tag);
          let mode = "opaque";
          const at = value.indexOf(plain);
          if (at >= 0) {
            mode = "contains" + at;
            if (at === 1 && value.length === plain.length + 2) {
              const pre = value.charCodeAt(0);
              const suf = value.charCodeAt(value.length - 1);
              if (win.__fieldPre == null) {
                win.__fieldPre = pre;
                win.__fieldSuf = suf;
                win.__fieldAffixSame = true;
              } else if (win.__fieldPre !== pre || win.__fieldSuf !== suf) win.__fieldAffixSame = false;
              win.__fieldAffixN = (win.__fieldAffixN || 0) + 1;
              if (plain === "Win32" && !win.__sampleCipher) win.__sampleCipher = value;
            }
          }
          else if (value.length >= plain.length) {
            for (let start = 0; start <= Math.min(6, value.length - plain.length); start += 1) {
              const keyByte = value.charCodeAt(start) ^ plain.charCodeAt(0);
              let good = true;
              for (let j = 1; j < plain.length; j += 1) {
                if ((value.charCodeAt(start + j) ^ keyByte) !== plain.charCodeAt(j)) good = false;
              }
              if (good) {
                mode = "xor" + start + "+" + (value.length - plain.length);
                win.__fieldK = keyByte;
                win.__fieldSt = start;
                break;
              }
            }
          }
          if (!mode.startsWith("contains")) win.__fieldBag.push(tag + ":" + mode + " L" + value.length);
        }
        return value;
      };
      sdk = sdk.replace(fieldRet, "else return globalThis.__fieldProbe(eT,--jb,--BC);");
    }
  }
  if (process.env.WLZ_PAIR === "1") {
    const ziRet = "else return eT[--jb+--BC-44];";
    if (!sdk.includes(ziRet)) report("pair-shape-missing");
    else {
      sdk = sdk.replace(ziRet, "else{var __jb=--jb,__bc=--BC,__idx=__jb+__bc-44,__v=eT[__idx];if(globalThis.__pair){globalThis.__pairN=(globalThis.__pairN||0)+1;var __bag=globalThis.__pairs||(globalThis.__pairs=[]);var __seen=globalThis.__pairSeen||(globalThis.__pairSeen={});if(__bag.length<80){var __ok={visible:1,hidden:1,default:1,Win32:1,jsdom:1,Blink:1,Gecko:1,Chrome:1,desktop:1,mobile:1,prompt:1,granted:1,denied:1,Windows:1,nodejs:1,headless:1,WebKit:1,chrome:1,MacIntel:1,Linux:1,Google:1};var __hit=\"\";if(typeof __v===\"string\"&&__ok[__v])__hit=__v+\"=self\"+__v.length;else if(typeof __v===\"string\"&&__v.length>=4&&__v.length<=40){var __lo=Math.max(0,__idx-12),__hi=Math.min(eT.length-1,__idx+8);for(var __i=__lo;__i<=__hi&&!__hit;__i++){var __s=eT[__i];if(__ok[__s])__hit=__s+\"=>\"+__v.length;}}if(__hit&&!__seen[__hit]){__seen[__hit]=1;__bag.push(__hit);}}if(globalThis.__pairN>800000)globalThis.__pair=false;}return __v;}");
      win.__pair = true;
    }
  }
  runInPage(sdk, "https://captcha.wangluozhe.com/wlzshield.min.js");
  const shield = win.WlzShield;
  if (!shield || typeof shield.initCollector !== "function") {
    report("FAIL no-collector");
    win.close();
    process.exit(1);
  }
  report("shield " + Object.getOwnPropertyNames(shield).join(","));
  if (process.env.WLZ_LOG === "1") {
    const seenBad = new Set();
    const origStringify = win.JSON.stringify;
    win.JSON.stringify = function stringify(value) {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const bad = Object.keys(value).filter((key) => value[key] === true);
        if (bad.length && bad.length < 80 && seenBad.size < 20) {
          const sig = bad.join(",");
          if (!seenBad.has(sig)) {
            seenBad.add(sig);
            report("flags " + sig);
          }
        }
      }
      return origStringify.apply(this, arguments);
    };
  }
  let widget = null;
  try {
    if (win.document && win.document.body) primeBehavior(win, win.document.body, false);
    widget = new shield.CheckboxCaptcha({
      siteKey: SITE_KEY,
      containerId: "#login-captcha",
      width: 300,
      height: 60,
    });
    const box = win.document.querySelector("#login-captcha");
    if (box) primeBehavior(win, box, true);
    report("widget children " + (box ? box.children.length : -1) + " body " + win.document.body.children.length);
    if (process.env.WLZ_CAP === "1") {
      const names = widget ? Object.getOwnPropertyNames(widget).filter((key) => typeof widget[key] === "function").slice(0, 20) : [];
      report("widget fn " + names.join(","));
      const frames = Array.from(win.document.querySelectorAll("iframe")).map((frame) => {
        let kids = -1;
        try { kids = frame.contentDocument && frame.contentDocument.body ? frame.contentDocument.body.children.length : -2; } catch (_error) { kids = -3; }
        return (frame.src ? "src" + frame.src.length : "nosrc") + ":kids" + kids;
      });
      const shadow = box && box.shadowRoot;
      const tree = (el, depth) => {
        if (!el || depth > 4) return "";
        const kids = Array.from(el.children || []).map((kid) => tree(kid, depth + 1)).filter(Boolean).join(",");
        return el.tagName + (el.id ? "#" + el.id : "") + (kids ? "(" + kids + ")" : "");
      };
      report("frames " + frames.join(",") + " scripts " + win.document.scripts.length + " shadow " + (shadow && shadow.firstElementChild ? tree(shadow.firstElementChild, 0) : "none"));
    }
    if (process.env.WLZ_XHR === "1") {
      const tags = Array.from(win.document.body.children).map((el) => el.tagName + (el.id ? "#" + el.id : "")).join(",");
      report("body-tags " + tags.slice(0, 200));
      const clickable = [win.document];
      const shadow = box && box.shadowRoot;
      if (shadow) clickable.push(shadow);
      for (const root of clickable) {
        for (const el of root.querySelectorAll("button, input, label, div, span")) {
          el.dispatchEvent(new win.MouseEvent("click", { bubbles: true, composed: true, clientX: 20, clientY: 20 }));
        }
      }
    }
  } catch (error) {
    report("widget fail " + String(error && error.message || error).slice(0, 120));
  }
  if (process.env.WLZ_PROTO === "1" && widget) {
    const names = [];
    let cursor = widget;
    while (cursor && cursor !== Object.prototype) {
      for (const name of Object.getOwnPropertyNames(cursor)) {
        if (typeof widget[name] === "function" && !names.includes(name)) names.push(name);
      }
      cursor = Object.getPrototypeOf(cursor);
    }
    report("proto " + names.join(","));
    if (process.env.WLZ_START === "1") {
      const steps = ["initDOM", "createEmbedLayout", "createTriggerWidget", "initLayout", "initWlzShield", "toggleMouseTracker", "startWlz", "startVerification", "triggerSubmission", "sendRequest"];
      for (const name of steps) {
        if (typeof widget[name] !== "function") continue;
        try {
          const out = widget[name]();
          if (out && typeof out.then === "function") {
            report("call " + name + " promise");
            await Promise.race([out.then(() => "done", (error) => "rej " + String(error && error.message || error).slice(0, 60)), new Promise((resolve) => setTimeout(() => resolve("timeout"), 15000))]).then((status) => report("call " + name + " " + status));
          } else {
            report("call " + name + " " + typeof out);
          }
        } catch (error) {
          report("call " + name + " fail " + String(error && error.message || error).slice(0, 100));
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 3000));
      const box = win.document.querySelector("#login-captcha");
      report("after-start children " + (box ? box.children.length : -1));
      win.close();
      process.exit(2);
    }
    if (process.env.WLZ_PROTO_ONLY === "1") {
      win.close();
      process.exit(2);
    }
  }
  const inst = shield.initCollector({ siteKey: SITE_KEY });
  win.__inst = inst;
  if (process.env.WLZ_CAP === "1" && inst) {
    const names = [];
    let cursor = inst;
    while (cursor && cursor !== Object.prototype) {
      for (const name of Object.getOwnPropertyNames(cursor)) {
        if (typeof cursor[name] === "function" && !names.includes(name)) names.push(name);
      }
      cursor = Object.getPrototypeOf(cursor);
    }
    report("methods " + names.join(","));
    const fields = Object.getOwnPropertyNames(inst).filter((name) => typeof inst[name] !== "function");
    report("fields " + fields.join(","));
    const show = (item) => {
      if (typeof item === "boolean" || typeof item === "number") return String(item);
      if (typeof item === "string") return /^[\x20-\x7e]{1,80}$/.test(item) && !/[+/=]{4,}/.test(item) ? item : "s" + item.length;
      if (Array.isArray(item)) return "a" + item.length;
      if (item && typeof item === "object") return Object.keys(item).slice(0, 8).map((key) => key + ":" + show(item[key])).join(",");
      return item == null ? "null" : typeof item;
    };
    for (const key of ["behaviorLog", "honeypotLog", "traceLog"]) {
      const value = inst[key];
      const size = Array.isArray(value) ? value.length : value && typeof value === "object" ? Object.keys(value).length : typeof value;
      const sample = Array.isArray(value) ? value.map(show).join(" || ") : show(value);
      report("log " + key + " " + size + " " + String(sample).slice(0, 4000));
    }
  }
  if (inst && inst.collectPromise) await inst.collectPromise;
  if (process.env.WLZ_PRECALM === "1" && inst) {
    const flipped = calmHoneypot(inst);
    report("precalm " + flipped);
  }
  if (process.env.WLZ_CAP === "1") {
    const host = win.document.querySelector("#login-captcha");
    const shadow = host && host.shadowRoot;
    const tree = (el, depth) => {
      if (!el || depth > 4) return "";
      const kids = Array.from(el.children || []).map((kid) => tree(kid, depth + 1)).filter(Boolean).join(",");
      return el.tagName + (kids ? "(" + kids + ")" : "");
    };
    report("shadow-later " + (shadow && shadow.firstElementChild ? tree(shadow.firstElementChild, 0) : "none") + " nodes " + (shadow ? shadow.childNodes.length : 0));
  }
  const flipped = 0;
  let captured = "";
  if (process.env.WLZ_FNS === "1" && inst) {
    const names = [];
    let cursor = inst;
    while (cursor && cursor !== Object.prototype) {
      for (const name of Object.getOwnPropertyNames(cursor)) if (typeof inst[name] === "function" && !names.includes(name)) names.push(name);
      cursor = Object.getPrototypeOf(cursor);
    }
    const lines = [];
    for (const name of names) {
      if (["getEncryptedPayload", "getPayload", "reportRisk", "constructor"].includes(name)) continue;
      try {
        const out = inst[name]("false");
        lines.push(name + ":" + (out == null ? "null" : typeof out === "string" ? "s" + out.length : typeof out));
      } catch (_error) {
        lines.push(name + ":err");
      }
    }
    report("fns " + lines.join(",").slice(0, 500));
  }
  if (process.env.WLZ_CAP === "1" && inst && typeof inst.hash === "function") {
    win.__guess = {};
    for (const guess of ["true", "false", "undefined", "object", "function", "1", "0", "null", "node"]) {
      try {
        win.__guess[guess] = String(inst.hash(guess));
      } catch (_error) {
        win.__guess[guess] = "";
      }
    }
    report("guess lens " + Object.entries(win.__guess).map(([key, value]) => key + ":" + value.length).join(","));
  }
  try { win.opener = null; } catch (_error) {}
  if (win.document) win.document.title = "T31-无感验证码";
  if (process.env.WLZ_XHR === "1") {
    for (const el of Array.from(win.document.querySelectorAll("button, label, input, [class]"))) {
      try { el.dispatchEvent(new win.MouseEvent("click", { bubbles: true, clientX: 30, clientY: 30 })); } catch (_error) {}
    }
    await new Promise((resolve) => setTimeout(resolve, 1200));
  }
  if (process.env.WLZ_PRECALM !== "1" && inst && typeof inst.resolveFingerprints === "function") {
    try {
      let value = inst.resolveFingerprints();
      if (value && typeof value.then === "function") value = await value;
      const briefValue = (item) => {
        if (typeof item === "boolean" || typeof item === "number") return String(item);
        if (typeof item === "string") {
          const known = ["true", "false", "undefined", "null", "0", "1", "visible", "hidden", "default", "granted", "denied", "prompt", "chrome", "Windows", "Win32"];
          return known.includes(item) ? item : "s" + item.length;
        }
        if (Array.isArray(item)) {
          if (item.length && item[0] && typeof item[0] === "object" && item[0].key) {
            return item.map((entry) => String(entry.key) + "{" + briefValue(entry.value) + "}").join(" ");
          }
          return "a" + item.length;
        }
        if (item && typeof item === "object") {
          return Object.keys(item).slice(0, 12).map((key) => key + ":" + briefValue(item[key])).join(",");
        }
        return item == null ? "null" : typeof item;
      };
      report("resolved " + briefValue(value).slice(0, 2200));
      if (process.env.WLZ_BREAK === "1") {
        try {
          breakFieldCipher(value, inst);
        } catch (error) {
          report("break fail " + String(error && error.message || error).slice(0, 120));
        }
        win.close();
        process.exit(2);
      }
    } catch (error) {
      report("call resolve fail " + String(error && error.message || error).slice(0, 100));
    }
  }
  if (process.env.WLZ_HASHWRAP === "1" && inst && typeof inst.calculateHash === "function") {
    const origHash = inst.calculateHash;
    let seen = 0;
    const describe = (value) => {
      if (value == null) return "null";
      if (Array.isArray(value)) return "a" + value.length;
      if (typeof value === "string") return "s" + value.length;
      if (typeof value === "number" || typeof value === "boolean") return typeof value;
      if (typeof value === "object") return "{" + Object.keys(value).slice(0, 10).join("|") + "}";
      return typeof value;
    };
    const calmDetected = (value, depth) => {
      if (!value || typeof value !== "object" || depth > 5) return 0;
      let count = 0;
      if (Array.isArray(value)) {
        for (const item of value) count += calmDetected(item, depth + 1);
        return count;
      }
      if (value.detected === true) {
        value.detected = false;
        count += 1;
      } else if (value.detected && typeof value.detected === "object") {
        for (const flag of Object.keys(value.detected)) {
          if (value.detected[flag] === true) {
            value.detected[flag] = false;
            count += 1;
          }
        }
      }
      for (const key of Object.keys(value)) {
        if (key === "value" || key === "hash") continue;
        const child = value[key];
        if (child && typeof child === "object") count += calmDetected(child, depth + 1);
      }
      return count;
    };
    inst.calculateHash = function calculateHash(...args) {
      seen += 1;
      let calmed = 0;
      if (seen === 1 && Array.isArray(args[1]) && args[1][0]) {
        const sample = args[1][0];
        const det = sample && sample.detected;
        const kind = det === true || det === false ? String(det) : det && typeof det === "object" ? "obj" + Object.keys(det).length : typeof det;
        report("hashb " + (sample && sample.trapName ? String(sample.trapName).slice(0, 40) : describe(sample)) + " det " + kind);
      }
      if (seen === 1 && process.env.WLZ_AES === "1" && Array.isArray(args[0]) && typeof origHash !== "undefined") {
        const env = args[0].find((item) => item && item.key === "environment" && item.value);
        const token = env && env.value && env.value.hasChromeObject;
        const tries = ["true", "false", "1", "0", "True", "False", "yes", "no"];
        const matched = tries.filter((item) => {
          try { return inst.hash(item) === token; } catch (_error) { return false; }
        });
        let hashLen = -1;
        try { hashLen = String(inst.hash("true")).length; } catch (_error) { hashLen = -1; }
        report("hashMatch " + (matched.join(",") || "none") + " hashLen " + hashLen + " tokenLen " + (typeof token === "string" ? token.length : -1));
        const xorPlain = (cipher) => {
          if (typeof cipher !== "string" || cipher.length < 4 || cipher.length > 24) return "";
          const bytes = Buffer.from(cipher, "utf8");
          const found = [];
          for (let key = 1; key < 256 && found.length < 2; key++) {
            let plain = "";
            let ok = true;
            for (const byte of bytes) {
              const next = byte ^ key;
              if (next < 32 || next > 126) { ok = false; break; }
              plain += String.fromCharCode(next);
            }
            if (ok) found.push(plain);
          }
          return found.join("/");
        };
        const engine = env && env.value ? env.value.browserEngine : "";
        const real = env && env.value ? env.value.realBrowser : "";
        report("xor true " + (xorPlain(token) || "none") + " engine " + (xorPlain(engine) || "none") + " real " + (xorPlain(real) || "none"));
      }
      if (seen === 1 && process.env.WLZ_SWAP === "1" && Array.isArray(args[0])) {
        const env = args[0].find((item) => item && item.key === "environment" && item.value);
        const value = env && env.value;
        const good = value && value.hasChromeObject;
        const bad = value && value.hasProcess;
        if (typeof good === "string" && typeof bad === "string") {
          const truth = [];
          const falses = [];
          const other = [];
          for (const key of Object.keys(value)) {
            const item = value[key];
            if (item === good) truth.push(key);
            else if (item === bad) falses.push(key);
            else other.push(key + ":" + (typeof item === "string" ? item.length : typeof item));
          }
          report("trueclass " + truth.join(","));
          report("falseclass " + falses.join(","));
          report("otherclass " + other.join(","));
        }
        const keys = ["alertIntegrity", "confirmIntegrity", "evalIntegrity", "toStringIntegrity"];
        let swapped = 0;
        if (typeof good === "string") {
          for (const key of keys) {
            if (typeof value[key] === "string" && value[key] !== good) {
              value[key] = good;
              swapped += 1;
            }
          }
        }
        report("swap " + swapped);
      }
      if (seen === 1 && process.env.WLZ_CALM_RISK === "1") {
        for (const arg of args) calmed += calmDetected(arg, 0);
      }
      const out = origHash.apply(this, args);
      if (seen <= 4) {
        report("hashcall " + seen + " argc " + args.length + " " + args.map(describe).join(" ") + " calmed " + calmed + " out " + (typeof out === "string" ? out.length : -1));
        if (Array.isArray(args[0]) && args[0][0] && typeof args[0][0] === "object") report("hashitem " + describe(args[0][0]));
      }
      return out;
    };
    if (typeof inst.stableJSONStringify === "function") {
      const origStringify = inst.stableJSONStringify;
      let stringSeen = 0;
      inst.stableJSONStringify = function stableJSONStringify(...args) {
        stringSeen += 1;
        const out = origStringify.apply(this, args);
        if (stringSeen <= 4) {
          const kind = args[0] == null ? "null" : Array.isArray(args[0]) ? "a" + args[0].length : typeof args[0] === "string" ? "s" + args[0].length : typeof args[0];
          report("stringify " + stringSeen + " argc " + args.length + " a0 " + kind + " out " + (typeof out === "string" ? out.length : typeof out));
        }
        return out;
      };
    }
    const modules = inst.modules;
    const moduleKind = Array.isArray(modules) ? "a" + modules.length : modules && typeof modules === "object" ? Object.keys(modules).slice(0, 24).join(",") : typeof modules;
    report("modules " + moduleKind);
    if (typeof inst.reportRisk === "function") {
      const origRisk = inst.reportRisk;
      inst.reportRisk = function reportRisk(...args) {
        win.__riskCalls = (win.__riskCalls || 0) + 1;
        for (const arg of args) {
          if (!arg || typeof arg !== "object") continue;
          for (const key of Object.keys(arg)) if (arg[key] === true) arg[key] = false;
        }
        return origRisk.apply(this, args);
      };
    }
    const origPush = win.Array.prototype.push;
    win.Array.prototype.push = function push(...items) {
      for (const item of items) {
        if (!item || typeof item !== "object" || typeof item.trapName !== "string") continue;
        win.__trapPush = (win.__trapPush || 0) + 1;
        if (item.detected && typeof item.detected === "object") {
          for (const key of Object.keys(item.detected)) if (item.detected[key] === true) item.detected[key] = false;
        } else if (item.detected === true) {
          item.detected = false;
        }
      }
      return origPush.apply(this, items);
    };
  }
  let packed = "";
  for (const gate of [win, globalThis]) {
    gate.__capOn = true;
    gate.__strN = 0;
    gate.__emptyN = 0;
    gate.__bestLen = 0;
    gate.__best = "";
    gate.__lens = [];
    gate.__errs = [];
    gate.__lx = 0;
    gate.__zi = 0;
    gate.__retN = 0;
    gate.__retK = {};
  }
  try {
    const encoded = await inst.getEncryptedPayload();
    if (typeof encoded === "string") packed = encoded;
    if (process.env.WLZ_CAP === "1") {
      const kind = encoded == null ? String(encoded) : typeof encoded;
      const extra = kind === "string" ? "len" + encoded.length : kind;
      report("enc-return " + extra);
    }
  } catch (_error) {
    report("enc-threw");
  }
  if (process.env.WLZ_TRAPS === "1") {
    report("traps done dumped " + !!win.__trapsDumped + " msgs " + (win.__workerMsgs || 0));
    if (process.env.WLZ_POST !== "1") {
      win.close();
      process.exit(2);
    }
  }
  if (process.env.WLZ_HASHWRAP === "1") report("watch riskCalls " + (win.__riskCalls || 0) + " trapPush " + (win.__trapPush || 0));
  if (process.env.WLZ_AES === "1" && win.__aesRec) {
    const rec = win.__aesRec;
    report("aesRec n " + rec.n + " msg " + rec.msg + " key " + rec.key + " cfg " + rec.cfg + " class " + (rec.keyClass || "none") + " head " + rec.head + " scan " + rec.scan + " calm " + rec.calm);
  }
  win.__capOn = false;
  globalThis.__capOn = false;
  if (process.env.WLZ_CAP === "1") {
    const gate = (win.__zi || win.__lx || win.__retN) ? win : globalThis;
    const kinds = Object.entries(gate.__retK || {}).map(([key, count]) => key + ":" + count).join(",");
    const lens = (gate.__lens || []).join(",");
    const errs = (gate.__errs || []).join("|");
    let shape = "na";
    try {
      const raw = Function.prototype.toString.call(inst.getEncryptedPayload);
      const names = [...new Set([...raw.matchAll(/([A-Za-z_$][\w$]{0,12})\(/g)].map((item) => item[1]))];
      shape = (raw.includes("LX(") ? "calls-lx" : "other") + " len" + raw.length + " calls " + names.join(",");
    } catch (_error) {
      shape = "throw";
    }
    report("cap lx " + (gate.__lx || 0) + " zi " + (gate.__zi || 0) + " ret " + (gate.__retN || 0) + " kinds " + kinds + " str " + (gate.__strN || 0) + " empty " + (gate.__emptyN || 0) + " best " + (gate.__bestLen || 0));
    report("cap lens " + lens);
    report("cap errs " + errs.slice(0, 180) + " fn " + shape);
    report("cap worker bytes " + (win.__workerBytes || 0) + " boot " + (win.__workerBoot || "none") + " run " + (win.__workerRun || "none"));
    report("cap promise n " + (win.__pres || 0) + " empty " + (win.__pre0 || 0) + " best " + (win.__preBest || 0));
    report("cap await " + ((win.__awaitErr || globalThis.__awaitErr || []).join(" | ")).slice(0, 300));
    const words = win.__words || globalThis.__words || [];
    if (words.length) report("words " + words.length + " " + words.join(" | ").slice(0, 4000));
    if (win.__preStack) report("cap promise-stack " + win.__preStack);
  }
  const vmBest = typeof (win.__best || globalThis.__best) === "string" ? (win.__best || globalThis.__best) : "";
  const promised = typeof win.__preVal === "string" ? win.__preVal : "";
  const wlzData = packed.length > 20 ? packed : (promised.length > 20 ? promised : (vmBest.length > captured.length ? vmBest : captured));
  if (process.env.WLZ_CAP === "1" && wlzData) {
    let kind = "other";
    if (wlzData[0] === "{") {
      try {
        const parsed = JSON.parse(wlzData);
        const brief = Object.keys(parsed).slice(0, 12).map((key) => {
          const value = parsed[key];
          const tag = value == null ? "null" : Array.isArray(value) ? "arr" + value.length : typeof value === "string" ? "s" + value.length : typeof value;
          return key + ":" + tag;
        }).join(",");
        kind = "json " + brief;
      } catch (_error) {
        kind = "brace";
      }
    } else if (/^[A-Za-z0-9+/=]+$/.test(wlzData.slice(0, 64))) kind = "b64";
    else if (/^[0-9a-f]+$/i.test(wlzData.slice(0, 64))) kind = "hex";
    const rest = wlzData.startsWith("1:") ? wlzData.slice(2) : "";
    let packedNote = "raw";
    if (rest && /^[A-Za-z0-9+/]+={0,2}$/.test(rest)) {
      try {
        const decoded = Buffer.from(rest, "base64");
        const zlib = require("zlib");
        let plain = "";
        try { plain = zlib.gunzipSync(decoded).toString("utf8").slice(0, 1); } catch (_error) { plain = "nogz"; }
        packedNote = "b64 " + decoded.length + " b0 " + decoded[0] + " b1 " + decoded[1] + " plain " + plain;
      } catch (_error) {
        packedNote = "b64-bad";
      }
    }
    const codes = Array.from(wlzData.slice(0, 8)).map((ch) => ch.charCodeAt(0)).join(".");
    const oddCodes = [...new Set(Array.from(wlzData).filter((ch) => !/[A-Za-z0-9+/=:]/.test(ch)))].slice(0, 8).map((ch) => ch.charCodeAt(0)).join(".");
    report("payload " + kind + " " + packedNote + " codes " + codes + " odd " + (oddCodes || "none"));
  }
  report("lens packed " + packed.length + " captured " + captured.length + " flipped " + flipped + " native " + (win.__nativeHits || 0) + " raw " + (win.__rawHits || 0) + " names " + ((win.__rawNames || []).join(",")));
  if (!wlzData) {
    report("FAIL empty-payload");
    win.close();
    process.exit(1);
  }
  if (process.env.WLZ_FIELD === "1") {
    const bag = win.__fieldBag || globalThis.__fieldBag || [];
    const pairs = win.__fieldPairs || globalThis.__fieldPairs || [];
    const extra = [];
    for (const pair of pairs) {
      const plain = String(pair[0]);
      const cipher = String(pair[1]);
      let mode = "opaque";
      const latin = Buffer.from(cipher, "latin1");
      const text = Buffer.from(plain, "utf8");
      const b64 = (() => { try { return Buffer.from(cipher, "base64"); } catch (_error) { return Buffer.alloc(0); } })();
      if (b64.includes(text)) mode = "b64";
      else if (Buffer.from(cipher, "hex").includes(text)) mode = "hex";
      else if (latin.length >= text.length) {
        for (let start = 0; start <= Math.min(6, latin.length - text.length); start += 1) {
          const keyByte = latin[start] ^ text[0];
          let good = true;
          for (let i = 1; i < text.length; i += 1) if ((latin[start + i] ^ keyByte) !== text[i]) good = false;
          if (good) {
            mode = "latinxor" + start;
            break;
          }
        }
      }
      extra.push(plain.length + ":" + mode + " c" + cipher.length);
    }
    const affixClass = (code) => code == null ? "none" : code < 32 ? "ctl" : code < 127 ? "ascii" : "hi";
    report("affix n " + (win.__fieldAffixN || 0) + " same " + (win.__fieldAffixSame === true) + " pre " + affixClass(win.__fieldPre) + " suf " + affixClass(win.__fieldSuf));
    report("field n " + (win.__fieldN || globalThis.__fieldN || 0) + " " + bag.join(" | "));
    if (extra.length) report("field-extra " + extra.join(" | "));
  }
  if (process.env.WLZ_PAIR === "1") {
    const pairs = win.__pairs || globalThis.__pairs || [];
    report("pairs n " + (win.__pairN || globalThis.__pairN || 0) + " hit " + pairs.length + " " + pairs.join(" | "));
  }
  if (process.env.WLZ_AES === "1" && win.__aesIv && wlzData.startsWith("1:")) {
    const raw = Buffer.from(wlzData.slice(2), "base64");
    const iv = win.__aesIv;
    const key = win.__aesKey;
    const ct = win.__aesCt || Buffer.alloc(0);
    const same = (buf, start) => buf.length > 0 && raw.length >= start + buf.length && raw.subarray(start, start + buf.length).equals(buf);
    const crypto = require("crypto");
    const md5 = (text) => crypto.createHash("md5").update(String(text)).digest();
    const eq = (buf) => buf.length === key.length && buf.equals(key);
    const extra = [];
    if (eq(md5(iv.toString("hex")))) extra.push("md5ivhex");
    if (eq(md5(SITE_KEY + iv.toString("hex")))) extra.push("md5site+ivhex");
    if (eq(md5(iv.toString("hex") + SITE_KEY))) extra.push("md5ivhex+site");
    const headerLen = ct.length > 0 && raw.length >= ct.length ? raw.length - ct.length : -1;
    const header = headerLen > 0 ? raw.subarray(0, headerLen) : Buffer.alloc(0);
    const ascii = header.length > 0 && [...header].every((byte) => byte >= 32 && byte < 127);
    const now = Date.now();
    const nearTime = (value) => Number.isFinite(value) && Math.abs(value - now) < 172800000;
    let beTime = false;
    let leTime = false;
    if (header.length >= 8) {
      try { beTime = nearTime(Number(header.readBigUInt64BE(0))); } catch (_error) { beTime = false; }
      try { leTime = nearTime(Number(header.readBigUInt64LE(0))); } catch (_error) { leTime = false; }
    }
    const evp = (pass, salt) => {
      const chunks = [];
      let prev = Buffer.alloc(0);
      while (Buffer.concat(chunks).length < 32) {
        prev = crypto.createHash("md5").update(Buffer.concat([prev, Buffer.from(String(pass)), salt])).digest();
        chunks.push(prev);
      }
      const material = Buffer.concat(chunks);
      return eq(material.subarray(0, 16)) && iv.length === 16 && material.subarray(16, 32).equals(iv);
    };
    const salts = [];
    if (header.length >= 8) salts.push(["h0", header.subarray(0, 8)], ["h4", header.subarray(Math.max(0, header.length - 8))]);
    const evpHits = [];
    for (const [label, salt] of salts) {
      if (evp(SITE_KEY, salt)) evpHits.push(label);
    }
    const pattern = [...header].map((byte) => (byte < 32 ? "s" + byte : "H")).join(".");
    const md5buf = (buf) => crypto.createHash("md5").update(buf).digest();
    const kdfHits = [];
    const mark = (label, buf) => { if (eq(buf)) kdfHits.push(label); };
    if (header.length) {
      mark("md5h", md5buf(header));
      mark("md5h+site", md5buf(Buffer.concat([header, Buffer.from(SITE_KEY)])));
      mark("md5site+h", md5buf(Buffer.concat([Buffer.from(SITE_KEY), header])));
      mark("md5hhex", md5(header.toString("hex")));
    }
    const timeHits = [];
    const nowMs = Date.now();
    for (let offset = 0; offset + 4 <= header.length; offset += 1) {
      const be = header.readUInt32BE(offset);
      const le = header.readUInt32LE(offset);
      if (Math.abs(be * 1000 - nowMs) < 172800000 || Math.abs(be - Math.floor(nowMs / 1000)) < 172800) timeHits.push("be" + offset);
      if (Math.abs(le * 1000 - nowMs) < 172800000 || Math.abs(le - Math.floor(nowMs / 1000)) < 172800) timeHits.push("le" + offset);
    }
    let opened = "skip";
    if (key.length === 16 && iv.length === 16 && ct.length > 16) {
      try {
        const decipher = crypto.createDecipheriv("aes-128-cbc", key, iv);
        const plain = Buffer.concat([decipher.update(ct), decipher.final()]);
        const low = plain.length > 4 ? plain[3] : -1;
        const keyInPlain = plain.includes(key);
        const ivInPlain = plain.includes(iv);
        opened = "ok " + plain.length + " b3 " + low + " keyIn " + keyInPlain + " ivIn " + ivInPlain;
      } catch (error) {
        opened = "fail " + String(error && error.code || "err").slice(0, 24);
      }
    }
    const keyAt = (file) => {
      const buf = fs.readFileSync(path.join(root, file));
      return { raw: buf.indexOf(key), hex: buf.indexOf(Buffer.from(key.toString("hex"))), b64: buf.indexOf(Buffer.from(key.toString("base64"))) };
    };
    const sdkAt = key.length === 16 ? keyAt("wlzshield.min.js") : { raw: -1, hex: -1, b64: -1 };
    const vendorAt = key.length === 16 ? keyAt("vendors.min.js") : { raw: -1, hex: -1, b64: -1 };
    report("keyfile sdk " + sdkAt.raw + "/" + sdkAt.hex + "/" + sdkAt.b64 + " vendors " + vendorAt.raw + "/" + vendorAt.hex + "/" + vendorAt.b64);
    const keyInHeader = key.length > 0 && header.includes(key);
    const ivInHeader = iv.length > 0 && header.includes(iv);
    report("envelope header" + header.length + " pat " + pattern + " open " + opened + " kdf " + (kdfHits.join(",") || "none") + " time " + (timeHits.join(",") || "none") + " rnd " + ((win.__rnd || []).join(",")) + " hash " + ((win.__kdf || []).join(",")) + " webcrypto " + (win.__randN || 0) + ":" + ((win.__randSizes || []).join(",")) + " math " + (win.__mathN || 0) + " inHeader " + keyInHeader + "/" + ivInHeader + " subtle " + typeof (win.crypto && win.crypto.subtle));
  }
  if (process.env.WLZ_KEYMUT === "1" && win.__aesKey) {
    const key1 = Buffer.from(win.__aesKey);
    try { defineGetter(win.navigator, "webdriver", true); } catch (_error) {}
    try { delete win.chrome; } catch (_error) {}
    try {
      const inst2 = shield.initCollector({ siteKey: SITE_KEY });
      if (inst2 && inst2.collectPromise) await inst2.collectPromise;
      await inst2.getEncryptedPayload();
      const sameKey = !!(win.__aesKey && key1.equals(win.__aesKey));
      report("keymut sameKey " + sameKey + " webdriver " + win.navigator.webdriver + " chrome " + typeof win.chrome);
    } catch (error) {
      report("keymut fail " + String(error && error.message || error).slice(0, 80));
    }
    win.close();
    process.exit(2);
  }
  if (process.env.WLZ_AES2 === "1" && win.__aesKey && win.__aesIv) {
    const key1 = Buffer.from(win.__aesKey);
    const iv1 = Buffer.from(win.__aesIv);
    const math1 = win.__mathN || 0;
    try {
      const inst2 = shield.initCollector({ siteKey: SITE_KEY });
      if (inst2 && inst2.collectPromise) await inst2.collectPromise;
      await inst2.getEncryptedPayload();
      const sameKey = !!(win.__aesKey && key1.equals(win.__aesKey));
      const sameIv = !!(win.__aesIv && iv1.equals(win.__aesIv));
      report("aes2 sameKey " + sameKey + " sameIv " + sameIv + " math " + math1 + "->" + (win.__mathN || 0));
    } catch (error) {
      report("aes2 fail " + String(error && error.message || error).slice(0, 80));
    }
  }
  if (process.env.WLZ_PROOF === "1" && win.__aesKey && win.__aesIv && wlzData.startsWith("1:")) {
    const crypto = require("crypto");
    const zlib = require("zlib");
    const raw = Buffer.from(wlzData.slice(2), "base64");
    const ct = Buffer.from(win.__aesCt);
    const headerLen = raw.length > ct.length ? raw.length - ct.length : 0;
    const header = headerLen > 0 ? raw.subarray(0, headerLen) : Buffer.alloc(0);
    const tail = ct.length > 0 && raw.length >= ct.length ? raw.subarray(raw.length - ct.length) : Buffer.alloc(0);
    const decipher = crypto.createDecipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
    const plain = Buffer.concat([decipher.update(ct), decipher.final()]);
    const cipher = crypto.createCipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
    const again = Buffer.concat([cipher.update(plain), cipher.final()]);
    let sparse = plain.length % 4 === 0;
    let high = 0;
    if (sparse) {
      for (let i = 0; i < plain.length; i += 1) if (i % 4 !== 3 && plain[i] !== 0) high += 1;
    }
    const gzip = Buffer.alloc(sparse ? plain.length / 4 : 0);
    if (sparse) for (let i = 0; i < gzip.length; i += 1) gzip[i] = plain[i * 4 + 3];
    const mis = Buffer.alloc(gzip.length * 4);
    for (let i = 0; i < gzip.length; i += 1) mis[i * 4 + 3] = gzip[i];
    const repackCipher = crypto.createCipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
    const repacked = gzip.length ? Buffer.concat([repackCipher.update(mis), repackCipher.final()]) : Buffer.alloc(0);
    const wire = "1:" + Buffer.concat([header, repacked]).toString("base64");
    const origB64 = wlzData.slice(2);
    const nextB64 = Buffer.concat([header, repacked]).toString("base64");
    let diffAt = -1;
    const diffN = Math.min(origB64.length, nextB64.length);
    for (let i = 0; i < diffN; i += 1) if (origB64.charCodeAt(i) !== nextB64.charCodeAt(i)) { diffAt = i; break; }
    if (diffAt < 0 && origB64.length !== nextB64.length) diffAt = diffN;
    let wireSep = -1;
    if (diffAt === 16 && origB64.length === nextB64.length + 1) {
      const stripped = origB64.slice(0, 16) + origB64.slice(17);
      if (stripped === nextB64) wireSep = origB64.charCodeAt(16);
    }
    report("proof tail " + tail.equals(ct) + " reenc " + again.equals(ct) + " sparse " + sparse + " high " + high + " mis " + (gzip.length > 0 && mis.equals(plain)) + " repack " + (repacked.length > 0 && repacked.equals(ct)) + " wire " + (wire === wlzData) + " b64 " + origB64.length + "/" + nextB64.length + " diffAt " + diffAt + " sep " + wireSep);
    const b12 = Array.isArray(win.__b12) ? Buffer.from(win.__b12) : Buffer.alloc(0);
    report("proof b64lens " + ((win.__b64n || []).join(",") || "none") + " b12 " + (b12.length === header.length && header.length > 0 && b12.equals(header)));
    const crcHit = (label, buf) => {
      if (!buf || !buf.length || header.length < 4) return;
      const sum = zlib.crc32(buf);
      for (let offset = 0; offset + 4 <= header.length; offset += 1) {
        if (header.readUInt32BE(offset) === sum) report("proof crc " + label + " be@" + offset);
        if (header.readUInt32LE(offset) === sum) report("proof crc " + label + " le@" + offset);
      }
      const md5 = crypto.createHash("md5").update(buf).digest();
      const sha = crypto.createHash("sha256").update(buf).digest();
      if (header.equals(md5.subarray(0, header.length))) report("proof mac md5 " + label);
      if (header.equals(sha.subarray(0, header.length))) report("proof mac sha " + label);
    };
    crcHit("ct", ct);
    crcHit("plain", plain);
    crcHit("gzip", gzip);
    const pattern = [...header].map((byte) => (byte < 32 ? "s" + byte : byte < 127 ? "A" : "H")).join(".");
    report("proof header " + header.length + " pat " + pattern);
    let shapeNote = "nogz";
    let riskBody = "";
    try {
      const parsed = JSON.parse(zlib.gunzipSync(gzip).toString("utf8"));
      const brief = (value, depth) => {
        if (value == null) return "null";
        if (typeof value === "boolean") return value ? "true" : "false";
        if (typeof value === "number") return Number.isInteger(value) ? "int" : "num";
        if (typeof value === "string") return "s" + value.length;
        if (Array.isArray(value)) {
          if (!value.length) return "a0";
          if (depth > 2) return "a" + value.length;
          const sample = value[0];
          if (typeof sample === "string") {
            const hex = /^[0-9a-f]+$/i.test(sample);
            const b64 = /^[A-Za-z0-9+/=_-]+$/.test(sample);
            return "a" + value.length + ":" + (hex ? "hex" : b64 ? "b64" : "text") + sample.length;
          }
          if (sample && sample.key && sample.value && typeof sample.value === "object" && !Array.isArray(sample.value)) {
            return "a" + value.length + "[" + value.map((item) => {
              const fields = item && item.value && typeof item.value === "object" ? Object.keys(item.value).slice(0, 10).map((key) => {
                const field = item.value[key];
                if (typeof field === "string") return key + ":s" + field.length;
                if (typeof field === "boolean") return key + ":" + field;
                if (typeof field === "number") return key + ":n";
                if (Array.isArray(field)) return key + ":a" + field.length;
                return key + ":" + (field == null ? "null" : typeof field);
              }).join("|") : "x";
              return String(item && item.key || "").slice(0, 24) + "{" + fields + "}";
            }).join(" ") + "]";
          }
          if (sample && typeof sample === "object" && !Array.isArray(sample) && (sample.trapName || sample.key)) {
            return "a" + value.length + "[" + value.slice(0, 24).map((item) => {
              const name = String(item.trapName || item.key || "").slice(0, 32);
              const det = item.detected;
              const flag = det === true ? "T" : det === false ? "F" : det && typeof det === "object" ? "o" + Object.values(det).filter((bit) => bit === true).length + "/" + Object.keys(det).length : "x";
              return name + ":" + flag;
            }).join(",") + "]";
          }
          return "a" + value.length + ":" + brief(sample, depth + 1);
        }
        if (typeof value === "object") {
          if (depth > 3) return "keys" + Object.keys(value).length;
          return "{" + Object.keys(value).slice(0, 16).map((key) => key + ":" + brief(value[key], depth + 1)).join(",") + "}";
        }
        return typeof value;
      };
      shapeNote = brief(parsed, 0).slice(0, 8000);
      const inner = parsed && parsed.payload && typeof parsed.payload === "object" ? parsed.payload : parsed;
      if (inner && Array.isArray(inner.risks)) {
        for (const item of inner.risks) {
          if (item && item.detected && typeof item.detected === "object") {
            for (const key of Object.keys(item.detected)) item.detected[key] = false;
          } else if (item) item.detected = false;
        }
      }
      const nextGz = zlib.gzipSync(Buffer.from(JSON.stringify(parsed)));
      const nextMis = Buffer.alloc(nextGz.length * 4);
      for (let i = 0; i < nextGz.length; i += 1) nextMis[i * 4 + 3] = nextGz[i];
      const nextCipher = crypto.createCipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
      const nextCt = Buffer.concat([nextCipher.update(nextMis), nextCipher.final()]);
      let riskB64 = Buffer.concat([header, nextCt]).toString("base64");
      if (wireSep >= 0) riskB64 = riskB64.slice(0, 16) + String.fromCharCode(wireSep) + riskB64.slice(16);
      riskBody = "1:" + riskB64;
    } catch (error) {
      shapeNote = "err " + String(error && error.message || error).slice(0, 80);
    }
    report("proof shape " + shapeNote);
    const posted = async (label, data) => {
      const result = await postChallenge(data);
      const msg = String(result.msg || "");
      const kind = /成功/.test(msg) ? "auth-ok" : /失败/.test(msg) ? "auth-fail" : msg ? "other" : "empty";
      report("proof post " + label + " " + result.http + " " + kind + " tokenlen " + result.token.length + " status " + result.statusField);
    };
    await posted("orig", wlzData);
    if (riskBody) await posted("risk", riskBody);
    await posted("empty", "");
    win.close();
    process.exit(2);
  }
  if (process.env.WLZ_DIFF === "1" && win.__aesKey && win.__aesIv && wlzData.startsWith("1:")) {
    const raw = Buffer.from(wlzData.slice(2), "base64");
    const ct = Buffer.from(win.__aesCt);
    const headerLen = raw.length > ct.length ? raw.length - ct.length : 0;
    const header = headerLen > 0 ? raw.subarray(0, headerLen) : Buffer.alloc(0);
    const classify = (result) => {
      const msg = String(result.msg || "");
      const kind = /成功/.test(msg) ? "auth-ok" : /失败/.test(msg) ? "auth-fail" : msg ? "other" : "empty";
      return result.http + " " + kind + " tokenlen " + result.token.length + " status " + result.statusField;
    };
    const pack = (cipher) => "1:" + Buffer.concat([header, cipher]).toString("base64");
    const flipped = Buffer.from(ct);
    if (flipped.length) flipped[flipped.length - 2] ^= 255;
    const orig = await postChallenge(wlzData);
    const flip = await postChallenge(pack(flipped));
    report("diff orig " + classify(orig));
    report("diff flip " + classify(flip) + " header " + headerLen + " ct " + ct.length);
    let plainNote = "skip";
    try {
      const decipher = require("crypto").createDecipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
      const plain = Buffer.concat([decipher.update(ct), decipher.final()]);
      const gzip = Buffer.alloc(Math.floor(plain.length / 4));
      for (let i = 0; i < gzip.length; i += 1) gzip[i] = plain[i * 4 + 3];
      let gunzipOk = false;
      try { require("zlib").gunzipSync(gzip); gunzipOk = true; } catch (_error) { gunzipOk = false; }
      plainNote = "plain " + plain.length + " gz " + gzip.length + " magic " + (gzip[0] === 31 && gzip[1] === 139) + " gunzip " + gunzipOk;
      if (gunzipOk) {
        const text = require("zlib").gunzipSync(gzip).toString("utf8");
        const parsed = JSON.parse(text);
        const inner = parsed && parsed.payload && typeof parsed.payload === "object" ? parsed.payload : parsed;
        if (inner && Array.isArray(inner.risks)) {
          for (const item of inner.risks) {
            if (item && item.detected && typeof item.detected === "object") {
              for (const key of Object.keys(item.detected)) item.detected[key] = false;
            } else if (item) item.detected = false;
          }
        }
        let hashNote = "nohash";
        if (inner && inst && typeof inst.calculateHash === "function" && Array.isArray(inner.fingerprints) && Array.isArray(inner.risks)) {
          try {
            const nextHash = inst.calculateHash(inner.fingerprints, inner.risks);
            if (typeof nextHash === "string" && nextHash.length > 20) {
              inner.hash = nextHash;
              hashNote = "rehash " + nextHash.length;
            } else hashNote = "short";
          } catch (_error) {
            hashNote = "hasherr";
          }
        }
        const nextGz = require("zlib").gzipSync(Buffer.from(JSON.stringify(parsed)));
        const misLen = nextGz.length * 4;
        const mis = Buffer.alloc(misLen);
        for (let i = 0; i < nextGz.length; i += 1) mis[i * 4 + 3] = nextGz[i];
        const cipher = require("crypto").createCipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
        const nextCt = Buffer.concat([cipher.update(mis), cipher.final()]);
        const back = require("crypto").createDecipheriv("aes-128-cbc", win.__aesKey, win.__aesIv);
        const backPlain = Buffer.concat([back.update(nextCt), back.final()]);
        let roundtrip = backPlain.length === misLen;
        if (roundtrip) {
          for (let i = 0; i < nextGz.length; i += 1) if (backPlain[i * 4 + 3] !== nextGz[i]) roundtrip = false;
        }
        const calm = await postChallenge(pack(nextCt));
        report("diff calm " + classify(calm) + " " + hashNote + " roundtrip " + roundtrip);
      }
    } catch (error) {
      plainNote = "err " + String(error && error.message || error).slice(0, 60);
    }
    report("diff pack " + plainNote);
    win.close();
    process.exit(2);
  }
  if (process.env.WLZ_FOREIGN === "1") {
    const say = (line) => report("shape " + line);
    const errClass = (error) => {
      const code = error && error.code;
      return typeof code === "string" && /^[A-Z][A-Z0-9_]{0,47}$/.test(code) ? code : "ERR";
    };
    try {
      const crypto = require("crypto");
      const zlib = require("zlib");
      const packetPath = "D:\\reverse_ENV\\workspace\\spiderdemo\\evidence\\web\\ruyitrace\\rt_20261025090734_84aef8a9bb\\raw\\http_packet\\000083_POST_200_captcha.wangluozhe.com_api_challenge_69dbecc2_pid32816_400000063.http_packet.json";
      const packet = JSON.parse(fs.readFileSync(packetPath, "utf8"));
      const foreign = packet && packet.params && packet.params.postJson ? packet.params.postJson.wlzData : "";
      const key = win.__aesKey;
      const iv = win.__aesIv;
      const keyOk = Buffer.isBuffer(key) && key.length === 16;
      const ivOk = Buffer.isBuffer(iv) && iv.length === 16;
      const foreignText = typeof foreign === "string" ? foreign : "";
      say("key16 " + keyOk + " iv16 " + ivOk + " packed " + packed.length + " foreign " + foreignText.length);
      const idKey = (name) => (/^[A-Za-z_][A-Za-z0-9_]{0,40}$/.test(name) ? name : "k" + String(name).length);
      const brief = (value, depth) => {
        if (value == null) return "null";
        if (typeof value === "boolean") return "bool";
        if (typeof value === "number") return Number.isInteger(value) ? "int" : "num";
        if (typeof value === "string") return "s" + value.length;
        if (Array.isArray(value)) {
          if (!value.length) return "a0";
          if (depth > 2) return "a" + value.length;
          const kinds = new Map();
          for (const item of value) {
            const tag = brief(item, depth + 1);
            kinds.set(tag, (kinds.get(tag) || 0) + 1);
          }
          const mix = [...kinds.entries()].slice(0, 8).map(([tag, count]) => tag + "x" + count).join(",");
          return "a" + value.length + ":" + mix;
        }
        if (typeof value === "object") {
          if (depth > 2) return "o" + Object.keys(value).length;
          const parts = Object.keys(value).slice(0, 16).map((name) => idKey(name) + ":" + brief(value[name], depth + 1));
          return "o{" + parts.join(",") + "}";
        }
        return "other";
      };
      const emitPlain = (label, plain) => {
        say(label + " pkcs7 true plain " + plain.length);
        if (plain.length % 4 !== 0) {
          say(label + " sparse false rem " + (plain.length % 4));
          return;
        }
        const gzip = Buffer.alloc(plain.length / 4);
        for (let i = 0; i < gzip.length; i += 1) gzip[i] = plain[i * 4 + 3];
        const magic = gzip.length >= 2 && gzip[0] === 31 && gzip[1] === 139;
        say(label + " magic " + magic + " gz " + gzip.length);
        if (!magic) return;
        let text = "";
        try {
          text = zlib.gunzipSync(gzip).toString("utf8");
        } catch (error) {
          say(label + " gunzip false " + errClass(error));
          return;
        }
        say(label + " gunzip true text " + text.length);
        let parsed;
        try {
          parsed = JSON.parse(text);
        } catch (error) {
          say(label + " json false " + errClass(error));
          return;
        }
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          say(label + " json true top " + (Array.isArray(parsed) ? "a" + parsed.length : typeof parsed));
          return;
        }
        say(label + " top " + Object.keys(parsed).map(idKey).join(","));
        const payload = parsed.payload && typeof parsed.payload === "object" && !Array.isArray(parsed.payload) ? parsed.payload : null;
        const inner = payload || parsed;
        say(label + " payloadKeys " + Object.keys(inner).map(idKey).join(","));
        let fieldLine = Object.keys(inner).slice(0, 24).map((name) => idKey(name) + ":" + brief(inner[name], 0)).join(",");
        if (fieldLine.length > 1500) fieldLine = fieldLine.slice(0, 1500);
        say(label + " fields " + fieldLine);
        const risks = Array.isArray(inner.risks) ? inner.risks : [];
        let detectedTrue = 0;
        for (const item of risks) if (item && item.detected === true) detectedTrue += 1;
        say(label + " risks a" + risks.length + " detectedTrue " + detectedTrue);
      };
      const openCt = (label, ct) => {
        if (!keyOk || !ivOk) {
          say(label + " pkcs7 false nokey");
          return false;
        }
        if (!ct || ct.length === 0 || ct.length % 16 !== 0) {
          say(label + " pkcs7 false len " + (ct ? ct.length : 0));
          return false;
        }
        try {
          const decipher = crypto.createDecipheriv("aes-128-cbc", key, iv);
          const plain = Buffer.concat([decipher.update(ct), decipher.final()]);
          emitPlain(label, plain);
          return true;
        } catch (error) {
          say(label + " pkcs7 false " + errClass(error));
          return false;
        }
      };
      let opened = false;
      if (!foreignText.startsWith("1:")) {
        say("prefix false");
      } else {
        const rest = foreignText.slice(2);
        const sepAt = [];
        let colonCount = 0;
        for (let i = 0; i < rest.length; i += 1) {
          if (rest.charCodeAt(i) !== 58) continue;
          colonCount += 1;
          if (sepAt.length < 8) sepAt.push(i);
        }
        say("colons " + colonCount + " sepAt " + (sepAt.join(",") || "none"));
        const sep16 = rest.length > 16 && rest.charCodeAt(16) === 58;
        say("sep16 " + sep16);
        if (sep16) {
          const raw = Buffer.from(rest.slice(0, 16) + rest.slice(17), "base64");
          say("step1 decoded " + raw.length);
          if (raw.length > 12) {
            say("step1 header 12 ct " + (raw.length - 12));
            if (openCt("step1", raw.subarray(12))) opened = true;
          } else say("step1 pkcs7 false short " + raw.length);
        } else say("step1 skip sep16 false");
        const parts = foreignText.split(":");
        say("parts " + parts.length);
        if (parts.length >= 2) {
          const trySeg = (nth) => {
            if (parts.length < nth) {
              say("step2 seg" + nth + " absent");
              return;
            }
            const raw = Buffer.from(parts[nth - 1], "base64");
            say("step2 seg" + nth + " decoded " + raw.length);
            if (openCt("step2 seg" + nth, raw)) opened = true;
          };
          trySeg(2);
          trySeg(3);
        } else say("step2 skip parts " + parts.length);
      }
      say("opened " + opened);
    } catch (error) {
      say("fatal " + errClass(error));
    }
    try { win.close(); } catch (_error) {}
    process.exit(2);
  }
  if (process.env.WLZ_NOPOST === "1") {
    report("nopost packed " + packed.length);
    win.close();
    process.exit(packed ? 2 : 1);
  }
  const result = await postChallenge(wlzData);
  report("live " + result.http + " " + result.msg.slice(0, 40) + " tokenlen " + result.token.length + " statusField " + result.statusField);
  const outPath = process.env.WLZ_TOKEN_OUT;
  if (result.token && outPath) fs.writeFileSync(outPath, result.token, { encoding: "utf8" });
  win.close();
  process.exit(result.token ? 0 : 2);
}

main().catch((error) => {
  const frames = String(error && error.stack || "").split("\n").slice(0, 6).map((line) => line.trim().replace(root, "").slice(0, 140));
  report("FAIL " + String(error && error.message || error).slice(0, 180));
  report("STACK " + frames.join(" || "));
  process.exit(1);
});
