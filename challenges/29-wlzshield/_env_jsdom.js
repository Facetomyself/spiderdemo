const fs = require("fs");
const https = require("https");
const http = require("http");
const path = require("path");
const { URL } = require("url");
const { JSDOM, VirtualConsole } = require("jsdom");
const { brief } = require("./_brief");

const root = __dirname;
const logs = [];
const note = (line) => logs.push(String(line).slice(0, 420));
const localServer = http.createServer((req, res) => {
  const origin = "https://www.spiderdemo.cn";
  res.setHeader("access-control-allow-origin", origin);
  res.setHeader("access-control-allow-credentials", "true");
  res.setHeader("access-control-allow-methods", "POST, OPTIONS");
  res.setHeader("access-control-allow-headers", "content-type");
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }
  const chunks = [];
  req.on("data", (chunk) => chunks.push(chunk));
  req.on("end", () => {
    const text = Buffer.concat(chunks).toString("utf8");
    let keys = "";
    try { keys = Object.keys(JSON.parse(text)).join(","); } catch (_error) { keys = "len" + text.length; }
    note("local " + req.method + " " + keys);
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ status: true, msg: "ok", wsToken: "aaa.bbb.ccc" }));
  });
});
const localPort = 18765;
localServer.listen(localPort, "127.0.0.1");

const virtualConsole = new VirtualConsole();
virtualConsole.on("jsdomError", (error) => note("jsdom " + String(error && error.message || error).slice(0, 180)));
const dom = new JSDOM(
  "<!doctype html><html><head></head><body><div id=\"login-captcha\" style=\"width:300px;height:60px\"></div></body></html>",
  {
    url: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge?challenge_type=wlzshield_captcha_challenge",
    pretendToBeVisual: true,
    runScripts: "outside-only",
    resources: {
      userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      interceptors: [
        (next) => (opts, handler) => {
          const target = String((opts && opts.origin) || "") + String((opts && opts.path) || "");
          const method = (opts && opts.method) || "GET";
          if (!target.includes("/api/challenge")) return next(opts, handler);
          let bodyNote = "optkeys " + Object.keys(opts || {}).join(",");
          const body = opts && opts.body;
          if (typeof body === "string" || Buffer.isBuffer(body)) {
            const text = Buffer.isBuffer(body) ? body.toString("utf8") : body;
            try {
              const parsed = JSON.parse(text);
              bodyNote = "wlz " + String(parsed.wlzData == null ? "" : parsed.wlzData).length;
            } catch (_error) {
              bodyNote = "len" + text.length;
            }
          }
          const opaque = (opts && opts.opaque) || {};
          note("fake " + method + " " + bodyNote + " originOk " + (opaque.origin === "https://www.spiderdemo.cn") + " cred " + !!opaque.withCredentials + " pre " + !!opaque.preflight);
          const cors = {
            "access-control-allow-origin": "https://www.spiderdemo.cn",
            "access-control-allow-credentials": "true",
            "access-control-allow-methods": "POST, OPTIONS",
            "access-control-allow-headers": "*",
            "content-type": "application/json",
          };
          const status = method === "OPTIONS" ? 204 : 200;
          const statusText = status === 204 ? "No Content" : "OK";
          const payload = status === 204 ? Buffer.alloc(0) : Buffer.from(JSON.stringify({ status: true, msg: "ok", wsToken: "aaa.bbb.ccc" }));
          try {
            if (typeof handler.onHeaders === "function") {
              handler.onHeaders(status, Object.entries(cors), () => {}, statusText);
              if (payload.length) handler.onData?.(payload);
              handler.onComplete?.([]);
            } else {
              const controller = { resume() {}, pause() {}, abort() {}, paused: false, aborted: false, reason: null };
              handler.onRequestStart?.(controller, {});
              handler.onResponseStart?.(controller, status, cors, statusText);
              if (payload.length) handler.onResponseData?.(controller, payload);
              handler.onResponseEnd?.(controller, {});
            }
            note("fake-ok");
          } catch (error) {
            note("fake-throw " + error.message);
          }
          return true;
        },
      ],
    },
    virtualConsole,
  }
);
const window = dom.window;

function stubContext() {
  return new Proxy(Object.create(null), {
    get(_target, prop) {
      if (prop === "canvas") return null;
      if (typeof prop !== "string") return undefined;
      return function method() {
        if (prop === "getImageData") return { data: new Uint8ClampedArray(16), width: 1, height: 1 };
        if (prop === "measureText") return { width: 8 };
        return method;
      };
    },
  });
}

note("before subtle " + typeof (window.crypto && window.crypto.subtle) + " ws " + typeof window.WebSocket + " rtc " + typeof window.RTCPeerConnection + " fetch " + typeof window.fetch);
if (!window.crypto || !window.crypto.subtle) {
  try {
    Object.defineProperty(window, "crypto", { configurable: true, value: globalThis.crypto });
  } catch (_error) {
    try { window.crypto.subtle = globalThis.crypto.subtle; } catch (_assign) { note("crypto-assign-fail"); }
  }
}
if (typeof window.fetch !== "function" && typeof globalThis.fetch === "function") {
  window.fetch = globalThis.fetch;
}
if (typeof window.WebSocket !== "function" && typeof globalThis.WebSocket === "function") {
  window.WebSocket = globalThis.WebSocket;
}
for (const name of ["Request", "Response", "Headers", "AbortController", "ReadableStream", "MessageChannel", "Blob", "File", "FormData"]) {
  if (typeof window[name] === "undefined" && typeof globalThis[name] === "function") window[name] = globalThis[name];
}
function AudioContext() { this.sampleRate = 48000; this.state = "running"; this.destination = {}; }
AudioContext.prototype.createOscillator = function createOscillator() { return { connect() {}, start() {}, stop() {}, frequency: { value: 0 }, type: "triangle" }; };
AudioContext.prototype.createDynamicsCompressor = function createDynamicsCompressor() { return { connect() {}, threshold: {}, knee: {}, ratio: {}, attack: {}, release: {} }; };
AudioContext.prototype.createGain = function createGain() { return { connect() {}, gain: { value: 1 } }; };
AudioContext.prototype.createAnalyser = function createAnalyser() { return { connect() {}, getFloatFrequencyData() {}, fftSize: 2048, frequencyBinCount: 1024 }; };
AudioContext.prototype.createBuffer = function createBuffer() { return { getChannelData() { return new Float32Array(8); } }; };
AudioContext.prototype.startRendering = function startRendering() { return Promise.resolve({ getChannelData() { return new Float32Array(8); }, sampleRate: 48000, length: 8, duration: 0, numberOfChannels: 1 }); };
AudioContext.prototype.close = function close() { return Promise.resolve(); };
window.AudioContext = AudioContext;
window.webkitAudioContext = AudioContext;
window.OfflineAudioContext = AudioContext;
window.speechSynthesis = { getVoices() { return []; }, addEventListener() {}, speak() {}, cancel() {} };
window.chrome = { runtime: {}, app: {}, csi() { return {}; }, loadTimes() { return {}; } };
if (!window.navigator.mediaDevices) {
  window.navigator.mediaDevices = {
    getUserMedia() { return Promise.reject(Object.assign(new Error("denied"), { name: "NotAllowedError" })); },
    enumerateDevices() { return Promise.resolve([]); },
  };
}
function RTCSessionDescription(init) { this.type = init && init.type || ""; this.sdp = init && init.sdp || ""; }
function RTCIceCandidate(init) { this.candidate = init && init.candidate || ""; }
window.RTCSessionDescription = RTCSessionDescription;
window.RTCIceCandidate = RTCIceCandidate;
function MediaStream() { this.getTracks = () => []; }
window.MediaStream = MediaStream;
window.HTMLCanvasElement.prototype.getContext = function getContext() { return stubContext(); };
window.HTMLCanvasElement.prototype.toDataURL = function toDataURL() { return "data:image/png;base64,AA=="; };

function shape(value, depth) {
  if (value === null) return "null";
  const kind = typeof value;
  if (kind === "string") {
    let form = "other";
    if (/^[A-Za-z0-9+/=_-]+$/.test(value)) form = "b64ish";
    if (/^[a-f0-9]+$/i.test(value)) form = "hex";
    if (value.split(".").length === 3) form = "dot3";
    return "str" + value.length + form;
  }
  if (kind === "number" || kind === "boolean") return kind;
  if (Array.isArray(value)) return "arr" + value.length;
  if (kind === "object") {
    const keys = Object.keys(value);
    if (depth >= 2) return "obj" + keys.length;
    return "{" + keys.map((key) => key + ":" + shape(value[key], depth + 1)).join(",") + "}";
  }
  return kind;
}

process.on("uncaughtException", (error) => note("uncaught " + String(error && error.stack || error).split("\n").slice(0, 5).join(" | ")));
process.on("unhandledRejection", (error) => note("reject " + String(error && error.message || error).slice(0, 240)));

window.__notes = [];
window.eval(
  "console.log=console.info=console.debug=console.warn=console.error=function(){" +
  "var parts=[]; for (var i=0;i<arguments.length && i<5;i++){ var v=arguments[i];" +
  " if(v instanceof Error) parts.push('Error:'+String(v.message||'').slice(0,80));" +
  " else if(typeof v==='string') parts.push('s'+v.length);" +
  " else if(Array.isArray(v)) parts.push('arr'+v.length);" +
  " else if(v&&v.tagName) parts.push(v.tagName);" +
  " else parts.push(typeof v);} window.__notes.push(parts.join(' ')); };"
);
const origStringify = window.JSON.stringify;
let jsonSeen = 0;
let flagsLogged = 0;
fs.writeFileSync(path.join(root, "_flags.txt"), "", "utf8");
window.JSON.stringify = function stringify(value) {
  jsonSeen += 1;
  if (value && typeof value === "object" && (Object.prototype.hasOwnProperty.call(value, "siteKey") || Object.prototype.hasOwnProperty.call(value, "wlzData") || Object.prototype.hasOwnProperty.call(value, "wsToken"))) {
    note("jsonbody " + shape(value, 0).slice(0, 360) + " checkbox " + (value.type === "checkbox"));
  }
  if (flagsLogged < 4 && value && typeof value === "object" && Object.prototype.hasOwnProperty.call(value, "xhr_missing")) {
    flagsLogged += 1;
    const flags = Object.keys(value)
      .filter((key) => typeof value[key] === "boolean")
      .map((key) => key + "=" + value[key]);
    const stack = String(new Error("flags").stack || "").split("\n").slice(1, 6).map((line) => line.trim().slice(0, 100)).join(" | ");
    fs.appendFileSync(path.join(root, "_flags.txt"), flags.join(",") + "\n" + stack + "\n---\n", "utf8");
  }
  return origStringify.apply(this, arguments);
};
window.eval([
  "var rawToString=Function.prototype.toString;",
  "var nativeMark=new WeakMap();",
  "function toString(){ if(this===toString) return 'function toString() { [native code] }'; if(nativeMark.has(this)) return nativeMark.get(this); return rawToString.call(this); }",
  "nativeMark.set(toString,'function toString() { [native code] }');",
  "Object.defineProperty(Function.prototype,'toString',{configurable:true,writable:true,value:toString});",
  "function mark(fn,name){ if(typeof fn==='function') nativeMark.set(fn,'function '+name+'() { [native code] }'); }",
  "window.__mark=mark;",
  "mark(XMLHttpRequest,'XMLHttpRequest');",
  "mark(XMLHttpRequest.prototype.open,'open');",
  "mark(XMLHttpRequest.prototype.send,'send');",
  "mark(XMLHttpRequest.prototype.setRequestHeader,'setRequestHeader');",
  "mark(XMLHttpRequest.prototype.getAllResponseHeaders,'getAllResponseHeaders');",
  "mark(XMLHttpRequest.prototype.getResponseHeader,'getResponseHeader');",
  "mark(WebSocket,'WebSocket');",
  "mark(WebSocket.prototype.send,'send');",
  "mark(WebSocket.prototype.close,'close');",
  "mark(Document.prototype.createElement,'createElement');",
  "var origCreate=Document.prototype.createElement;",
  "function bindFrame(el){ if(!el||String(el.tagName).toUpperCase()!=='IFRAME') return; try{ Object.defineProperty(el,'contentWindow',{configurable:true,get:function(){return window;}}); Object.defineProperty(el,'contentDocument',{configurable:true,get:function(){return document;}}); }catch(e){} }",
  "Document.prototype.createElement=function(tag){ var el=origCreate.apply(this,arguments); bindFrame(el); return el; };",
  "var origNS=Document.prototype.createElementNS;",
  "Document.prototype.createElementNS=function(ns,tag){ var el=origNS.apply(this,arguments); bindFrame(el); return el; };",
  "mark(Document.prototype.createElementNS,'createElementNS');",
  "new MutationObserver(function(records){ records.forEach(function(rec){ Array.prototype.forEach.call(rec.addedNodes||[], function visit(node){ bindFrame(node); if(node&&node.children) Array.prototype.forEach.call(node.children, visit); }); }); }).observe(document.documentElement,{childList:true,subtree:true});",
  "mark(Document.prototype.createElement,'createElement');",
  "function RTCPeerConnection(){ this.iceConnectionState='new'; this.connectionState='new'; this.signalingState='stable'; this.iceGatheringState='new'; this.localDescription=null; this.remoteDescription=null; }",
  "RTCPeerConnection.prototype.createDataChannel=function(){return {close:function(){},send:function(){}};};",
  "RTCPeerConnection.prototype.createOffer=function(){return Promise.resolve({type:'offer',sdp:''});};",
  "RTCPeerConnection.prototype.createAnswer=function(){return Promise.resolve({type:'answer',sdp:''});};",
  "RTCPeerConnection.prototype.setLocalDescription=function(){return Promise.resolve();};",
  "RTCPeerConnection.prototype.setRemoteDescription=function(){return Promise.resolve();};",
  "RTCPeerConnection.prototype.addEventListener=function(){};",
  "RTCPeerConnection.prototype.close=function(){};",
  "RTCPeerConnection.prototype.addIceCandidate=function(){return Promise.resolve();};",
  "Object.defineProperty(RTCPeerConnection.prototype,Symbol.toStringTag,{value:'RTCPeerConnection'});",
  "window.RTCPeerConnection=RTCPeerConnection;",
  "window.webkitRTCPeerConnection=RTCPeerConnection;",
  "mark(RTCPeerConnection,'RTCPeerConnection');",
  "['createDataChannel','createOffer','createAnswer','setLocalDescription','setRemoteDescription','close','addIceCandidate','addEventListener'].forEach(function(name){ mark(RTCPeerConnection.prototype[name], name); });",
  "['AudioContext','webkitAudioContext','OfflineAudioContext','RTCSessionDescription','RTCIceCandidate','MediaStream','Request','Response','Headers','fetch','Error'].forEach(function(name){ mark(window[name], name); });",
].join("\n"));
window.__mark(window.JSON.stringify, "stringify");
window.__mark(window.HTMLCanvasElement.prototype.getContext, "getContext");
window.__mark(window.HTMLCanvasElement.prototype.toDataURL, "toDataURL");
window.__mark(window.console.log, "log");
window.__mark(window.fetch, "fetch");
window.eval([
  "var OrigError=Error;",
  "function CleanError(message){",
  "  var err=new OrigError(message);",
  "  var stack='Error: '+(message||'')+'\\n    at https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge:1:1';",
  "  try{ Object.defineProperty(err,'stack',{configurable:true,get:function(){return stack;}}); }catch(e){}",
  "  return err;",
  "}",
  "CleanError.prototype=OrigError.prototype;",
  "CleanError.captureStackTrace=function(){};",
  "window.Error=CleanError;",
].join("\n"));
note("types " + window.eval(
  "(function(){return ['Request',typeof Request,'Response',typeof Response,'fetch',typeof fetch,'wsClose',typeof WebSocket.CLOSING,'rtc',typeof RTCPeerConnection].join(' ');})()"
));
note("tells " + window.eval(
  "(function(){var s=''; try{s=String(new Error('x').stack||'');}catch(e){s='throw';} return ['jsdom',/jsdom/i.test(s),'node',/node:|\\\\node_modules/i.test(s),'webdriver',navigator.webdriver,'outer',window.outerWidth,'plugins',navigator.plugins&&navigator.plugins.length,'langs',navigator.languages&&navigator.languages.length].join(' ');})()"
));
note("ns " + window.eval(
  "(function(){function desc(obj,name){var d=Object.getOwnPropertyDescriptor(obj,name)||{};return name+':w'+!!d.writable+'c'+!!d.configurable+'e'+!!d.enumerable+'g'+(typeof d.get);} var el=document.createElementNS('http://www.w3.org/1999/xhtml','iframe'); document.body.appendChild(el); var other=el.contentWindow; return [desc(XMLHttpRequest.prototype,'open'),desc(XMLHttpRequest.prototype,'send'),'same '+(other===window),'fetch '+(other&&typeof other.fetch),'xhr '+(other&&other.XMLHttpRequest===XMLHttpRequest)].join(' ');})()"
));
note("iframe " + window.eval(
  "(function(){var el=document.createElement('iframe'); document.body.appendChild(el); return 'cw '+(el.contentWindow===window)+' fetch '+(el.contentWindow&&typeof el.contentWindow.fetch)+' xhr '+(el.contentWindow&&el.contentWindow.XMLHttpRequest===XMLHttpRequest);})()"
));
note("native " + window.eval(
  "(function(){function native(fn){try{return Function.prototype.toString.call(fn).indexOf('[native code]')>=0;}catch(e){return 'err';}}" +
  "return ['xhr',native(XMLHttpRequest),'open',native(XMLHttpRequest.prototype.open),'send',native(XMLHttpRequest.prototype.send)," +
  "'ws',native(WebSocket),'fetch',native(window.fetch),'rtc',native(window.RTCPeerConnection)].join(' ');})()"
));
function hardenXhr(win) {
  const proto = win.XMLHttpRequest && win.XMLHttpRequest.prototype;
  if (!proto || proto.__hardened) return;
  proto.__hardened = true;
  for (const name of ["open", "send", "setRequestHeader", "abort", "getAllResponseHeaders", "getResponseHeader", "overrideMimeType"]) {
    const orig = proto[name];
    if (typeof orig !== "function") continue;
    const wrapped = function xhrMethod() {
      if (!(this instanceof win.XMLHttpRequest)) {
        throw new win.TypeError("Failed to execute '" + name + "' on 'XMLHttpRequest': Illegal invocation");
      }
      return orig.apply(this, arguments);
    };
    try { Object.defineProperty(wrapped, "length", { value: orig.length }); } catch (_error) {}
    proto[name] = wrapped;
    if (typeof win.__mark === "function") win.__mark(wrapped, name);
  }
  if (typeof win.__mark === "function") win.__mark(win.XMLHttpRequest, "XMLHttpRequest");
}
hardenXhr(window);
const seenChr = new Set();
const origFromCharCode = window.String.fromCharCode;
window.String.fromCharCode = function fromCharCode() {
  const text = origFromCharCode.apply(window.String, arguments);
  if (seenChr.size < 80 && text.length > 6 && /xhr|missing|hook|illegal|native|wlz|encrypt|token|unimplemented|Error|fail|exception/i.test(text) && !seenChr.has(text)) {
    seenChr.add(text);
    note("chr " + text.slice(0, 120));
  }
  return text;
};
window.__mark(window.String.fromCharCode, "fromCharCode");
const seenJson = new Set();
const seenBad = new Set();
const prevStringify = window.JSON.stringify;
window.JSON.stringify = function stringify(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const bad = Object.keys(value).filter((key) => value[key] === true);
    if (bad.length && bad.length < 50) {
      const sig = bad.join(",");
      if (!seenBad.has(sig) && seenBad.size < 40) {
        seenBad.add(sig);
        note("flags-true " + sig);
      }
    }
    const keys = Object.keys(value);
    if (keys.length >= 8) {
      const sig = keys.length + ":" + keys.slice(0, 6).join(",");
      if (!seenJson.has(sig) && seenJson.size < 30) {
        seenJson.add(sig);
        note("bigjson " + sig);
      }
    }
  }
  return prevStringify.apply(this, arguments);
};
window.__mark(window.JSON.stringify, "stringify");
window.eval(fs.readFileSync(path.join(root, "vendors.min.js"), "utf8"));
note("CryptoJS " + typeof window.CryptoJS);
if (window.CryptoJS && window.CryptoJS.AES && typeof window.CryptoJS.AES.encrypt === "function") {
  const encrypt = window.CryptoJS.AES.encrypt;
  window.CryptoJS.AES.encrypt = function aesEncrypt() {
    note("aes argc " + arguments.length);
    try {
      const out = encrypt.apply(this, arguments);
      note("aes ok");
      return out;
    } catch (error) {
      note("aes fail " + error.message);
      throw error;
    }
  };
}
window.eval(fs.readFileSync(path.join(root, "wlzshield.min.js"), "utf8"));
try {
  const host = window.document.createElement("div");
  window.document.body.appendChild(host);
  const shadow = host.attachShadow({ mode: "open" });
  shadow.innerHTML = "<span></span>";
  note("shadow " + shadow.childNodes.length);
} catch (error) {
  note("shadow-fail " + error.message);
}
note("version " + (window.WlzShield && window.WlzShield.version));
note("uaJsdom " + /jsdom/i.test(window.navigator.userAgent));

let widget;
try {
  widget = new window.WlzShield.CheckboxCaptcha({
    siteKey: "9d4295076aaef0b4c16e18e4f53b5120",
    containerId: "#login-captcha",
    width: 300,
    height: 60,
    challengeUrl: "https://captcha.wangluozhe.com/api/challenge",
    onSuccess(data) {
      const keys = data && typeof data === "object" ? Object.keys(data).join(",") : typeof data;
      const tokenLength = data && data.wsToken ? String(data.wsToken).length : 0;
      note("success keys " + keys + " tokenlen " + tokenLength);
    },
    onFailure(data) {
      note("failure type " + typeof data);
    },
    onError(data) {
      note("onerror " + (data && data.message ? String(data.message).slice(0, 160) : typeof data));
    },
  });
  note("constructed localUrl " + String(widget && widget.config && widget.config.challengeUrl || "").includes("127.0.0.1"));
  const names = [];
  let cursor = widget;
  while (cursor && cursor !== Object.prototype && cursor !== Function.prototype) {
    for (const name of Object.getOwnPropertyNames(cursor)) {
      if (name !== "constructor" && typeof widget[name] === "function") names.push(name);
    }
    cursor = Object.getPrototypeOf(cursor);
  }
  note("methods " + names.join(","));
  note("host " + ["process", "Buffer", "require", "module", "global"].map((name) => name + ":" + typeof window[name]).join(","));
  note("crypto " + typeof window.crypto + " subtle " + typeof (window.crypto && window.crypto.subtle));
  fs.writeFileSync(path.join(root, "_fn_send.js"), Function.prototype.toString.call(widget.sendRequest), "utf8");
  fs.writeFileSync(path.join(root, "_fn_payload.js"), Function.prototype.toString.call(window.WlzShield.getPayload), "utf8");
  fs.writeFileSync(path.join(root, "_fn_init.js"), Function.prototype.toString.call(window.WlzShield.initCollector), "utf8");
} catch (error) {
  note("construct-fail " + String(error && error.stack || error).split("\n").slice(0, 6).join(" | "));
}

setTimeout(async () => {
  const box = window.document.getElementById("login-captcha");
  note("children " + (box ? box.children.length : -1));
  if (widget) {
    for (const name of ["onWlzReady", "initLayout", "initDOM", "createEmbedLayout"]) {
      try {
        const result = widget[name]();
        note(name + " " + (result && typeof result.then === "function" ? "promise" : typeof result));
        if (result && typeof result.then === "function") await result;
      } catch (error) {
        note(name + " fail " + String(error && error.stack || error).split("\n").slice(0, 3).join(" | "));
      }
    }
  }
  note("children2 " + (box ? box.children.length : -1));
  try {
    const inst = window.WlzShield.initCollector({ siteKey: "9d4295076aaef0b4c16e18e4f53b5120" });
    if (inst && inst.collectPromise && typeof inst.collectPromise.then === "function") {
      await inst.collectPromise;
      note("collected");
    } else {
      note("no-collect-promise");
    }
  } catch (error) {
    note("collect-fail " + String(error && error.message || error).slice(0, 160));
  }
  try {
    window.eval(
      "var p=WlzShield.getPayload();" +
      "window.__notes.push('ptype '+Object.prototype.toString.call(p));" +
      "window.__notes.push('pkeys '+(p&&typeof p==='object'?Object.keys(p).slice(0,30).join(','):typeof p));" +
      "var inst=WlzShield.instance;" +
      "window.__notes.push('ikeys '+Object.keys(inst).slice(0,40).join(','));"
    );
    note("inside " + Array.from(window.__notes).slice(-6).join(" || "));
  } catch (error) {
    note("inside-fail " + error.message);
  }
  try {
    const live = window.WlzShield && window.WlzShield.instance;
    note("before-payload jsonSeen " + jsonSeen + " consumed " + !!(live && live.isConsumed) + " first " + !!(live && live.first));
    const payload = await window.WlzShield.getPayload();
    note("resolved " + shape(payload, 0));
  } catch (error) {
    note("payload2-fail " + String(error && error.message || error).slice(0, 180));
  }
  if (widget && typeof widget.startVerification === "function") {
    try { widget.startVerification(); note("started"); } catch (error) { note("start-fail " + error.message); }
  }
}, 600);

setTimeout(async () => {
  const inst = window.WlzShield && window.WlzShield.instance;
  if (inst) {
    note("behavior " + (inst.behaviorLog && inst.behaviorLog.length));
    note("traceN " + (inst.traceLog && inst.traceLog.length) + " honey " + (inst.honeypotLog && inst.honeypotLog.length));
    note("export " + Object.getOwnPropertyNames(window.WlzShield).join(","));
    const protoNames = [];
    let cursor = inst;
    while (cursor && cursor !== Object.prototype) {
      for (const name of Object.getOwnPropertyNames(cursor)) {
        if (typeof inst[name] === "function") protoNames.push(name);
      }
      cursor = Object.getPrototypeOf(cursor);
    }
    note("instFn " + protoNames.join(","));
    note("own " + Object.keys(inst).map((key) => key + ":" + typeof inst[key]).join(","));
    const seenObjs = new Set();
    const flagHits = [];
    const stack = [{ value: inst, path: "inst" }, { value: window.WlzShield, path: "shield" }];
    while (stack.length && seenObjs.size < 4000 && flagHits.length < 6) {
      const item = stack.pop();
      const value = item.value;
      if (!value || typeof value !== "object" || seenObjs.has(value)) continue;
      seenObjs.add(value);
      if (Object.prototype.hasOwnProperty.call(value, "core_integrity_compromised") || Object.prototype.hasOwnProperty.call(value, "xhr_missing")) {
        flagHits.push(item.path);
      }
      const keys = Object.keys(value);
      for (let index = 0; index < keys.length && index < 40; index += 1) {
        stack.push({ value: value[keys[index]], path: item.path + "." + keys[index] });
      }
    }
    note("flagSearch seen " + seenObjs.size + " hits " + flagHits.join(" | "));
    if (Array.isArray(inst.traceLog)) {
      inst.traceLog.slice(0, 12).forEach((item, index) => note("trace " + index + " " + brief(item)));
    }
    note("modules " + Object.keys(inst.modules || {}).slice(0, 40).join(","));
    note("idlens " + ["seed", "sessionId", "deviceId"].map((key) => key + String(inst[key] == null ? 0 : String(inst[key]).length)).join(","));
    const fps = inst.cachedFingerprints;
    if (fps && typeof fps === "object") {
      for (const key of Object.keys(fps)) {
        const slot = fps[key] || {};
        note("slot " + key + " klen " + String(slot.key || "").length + " " + brief(slot.value));
        const value = slot.value;
        if (value && typeof value === "object") {
          for (const field of Object.keys(value)) {
            const item = value[field];
            if (typeof item === "string" && (item.length > 80 || /not implemented|undefined is not|jsdom|failed/i.test(item))) {
              note("long " + key + "." + field + " " + item.replace(/\s+/g, " ").slice(0, 100));
            }
          }
        }
      }
    } else {
      note("fp " + typeof fps);
    }
    note("sameFn " + (window.WlzShield.getPayload === window.WlzShield.initCollector));
    note("console " + Array.from(window.__notes || []).slice(0, 12).join(" || "));
    try { note("payload " + shape(window.WlzShield.getPayload(), 0)); } catch (error) { note("payload-fail " + error.message); }
    const subtle = window.crypto && window.crypto.subtle;
    if (subtle && typeof subtle.encrypt === "function" && !subtle.encrypt.__wrapped) {
      const origEncrypt = subtle.encrypt.bind(subtle);
      const wrappedEncrypt = function encrypt(algorithm, key, data) {
        const name = algorithm && (algorithm.name || algorithm);
        const size = data && (data.byteLength || data.length || 0);
        note("subtle " + name + " bytes " + size);
        return origEncrypt(algorithm, key, data).catch((error) => {
          note("subtle-fail " + String(error && error.message || error).slice(0, 160));
          throw error;
        });
      };
      wrappedEncrypt.__wrapped = true;
      subtle.encrypt = wrappedEncrypt;
    }
    const origBtoa = window.btoa;
    let btoaSeen = 0;
    window.btoa = function btoa(value) {
      if (btoaSeen < 8) note("btoa " + String(value == null ? "" : value).length);
      btoaSeen += 1;
      return origBtoa.apply(window, arguments);
    };
    const sizes = {};
    let captured = "";
    for (const name of ["stableJSONStringify", "hash", "calculateHash", "calculateDeviceId", "intToHex", "resolveFingerprints"]) {
      const orig = inst[name];
      if (typeof orig !== "function") continue;
      sizes[name] = 0;
      inst[name] = function wrapped() {
        if (name === "calculateHash" && sizes[name] < 2) {
          note("ch-args " + Array.from(arguments).map((item) => shape(item, 0).slice(0, 160)).join(" || "));
        }
        const out = orig.apply(this, arguments);
        sizes[name] += 1;
        const length = out == null ? -1 : String(out).length;
        if (name === "calculateHash" && typeof out === "string" && out.length > captured.length) captured = out;
        if (sizes[name] <= 2 || length === 0) {
          const word = out === "string" || out === "object" || out === "number" || out === "undefined" || out === "function" || out === "boolean";
          note("out " + name + " n " + sizes[name] + " len " + length + " kind " + typeof out + " word " + word + " " + shape(out, 0).slice(0, 80));
        }
        return out;
      };
    }
    try {
      const encoded = await inst.getEncryptedPayload();
      note("enc " + shape(encoded, 0) + " counts " + Object.entries(sizes).map(([key, count]) => key + count).join(",") + " captured " + captured.length);
      if (captured) {
        const posted = await new Promise((resolve) => {
          const body = JSON.stringify({
            timestamp: Date.now(),
            wlzData: captured,
            siteKey: "9d4295076aaef0b4c16e18e4f53b5120",
            type: "checkbox",
          });
          const req = https.request({
            protocol: "https:",
            hostname: "captcha.wangluozhe.com",
            path: "/api/challenge",
            method: "POST",
            headers: {
              "content-type": "application/json",
              "content-length": Buffer.byteLength(body),
              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
              origin: "https://www.spiderdemo.cn",
              referer: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge?challenge_type=wlzshield_captcha_challenge",
            },
          }, (res) => {
            const chunks = [];
            res.on("data", (chunk) => chunks.push(chunk));
            res.on("end", () => resolve({ status: res.statusCode, text: Buffer.concat(chunks).toString("utf8") }));
          });
          req.on("error", (error) => resolve({ status: 0, text: error.message }));
          req.write(body);
          req.end();
        });
        let tokenLen = 0;
        let msg = "";
        let keys = "";
        let statusField = false;
        try {
          const parsed = JSON.parse(posted.text);
          keys = parsed && typeof parsed === "object" ? Object.keys(parsed).join(",") : "";
          tokenLen = parsed && parsed.wsToken ? String(parsed.wsToken).length : 0;
          statusField = !!(parsed && parsed.status);
          msg = String((parsed && (parsed.msg || parsed.message || parsed.error)) || "").slice(0, 40);
        } catch (_error) {
          msg = "raw" + String(posted.text || "").length;
        }
        note("live " + posted.status + " keys " + keys + " " + msg + " tokenlen " + tokenLen + " statusField " + statusField);
      }
    } catch (error) {
      note("enc-throw " + String(error && error.stack || error).split("\n").slice(0, 6).join(" | "));
    }
    try {
      const stable = inst.stableJSONStringify(inst.cachedFingerprints);
      note("stable " + (stable == null ? "null" : typeof stable + String(stable).length));
    } catch (error) {
      note("stable-throw " + String(error && error.message || error).slice(0, 180));
    }
  }
  fs.writeFileSync(path.join(root, "_env_log.txt"), logs.join("\n"), "utf8");
  localServer.close();
  window.close();
  process.exit(0);
}, 8000);
