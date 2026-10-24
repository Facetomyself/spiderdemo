"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const notes = [];
function emit(message) {
  notes.push(message);
}

class FakeWS {
  constructor(url) {
    emit({ op: "open", url: String(url), proto: arguments.length });
    this.readyState = 0;
    this.binaryType = "blob";
  }
  send(data) {
    const n = typeof data === "string" ? data.length : (data && data.byteLength) || 0;
    emit({ op: "send", n, kind: typeof data });
  }
  close() {}
  addEventListener(type) { emit({ op: "ws-on", type }); }
}

let assigned = 0;
const workerGlobal = {
  console: { log(...a) { emit({ op: "log", n: a.length, t: a.map((x) => typeof x).join(",") }); }, error() {}, warn() {}, info() {}, debug() {} },
  setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask,
  URL, URLSearchParams, TextEncoder, TextDecoder,
  atob: (s) => Buffer.from(String(s), "base64").toString("binary"),
  btoa: (s) => Buffer.from(String(s), "binary").toString("base64"),
  WebSocket: FakeWS,
  crypto: require("crypto").webcrypto,
  performance: { now: () => Date.now() },
  navigator: { userAgent: "Mozilla/5.0", language: "zh-CN", hardwareConcurrency: 8 },
  location: { href: "https://www.spiderdemo.cn/static/js/authentication/sdk.min.js", origin: "https://www.spiderdemo.cn", hostname: "www.spiderdemo.cn" },
  importScripts() {},
  close() {},
  addEventListener(type) { emit({ op: "listen", type }); },
  removeEventListener() {},
  postMessage(data) { emit({ op: "post", type: data && data.type }); },
};
workerGlobal.self = workerGlobal;
workerGlobal.globalThis = workerGlobal;
vm.createContext(workerGlobal);
const source = fs.readFileSync(path.join(__dirname, "assets", "sdk.min.js"), "utf8");
try {
  vm.runInContext(source, workerGlobal, { timeout: 20000 });
  emit({ op: "ran" });
} catch (err) {
  emit({ op: "err", name: err.name, message: String(err.message).split("\n")[0] });
}
const info = vm.runInContext(`(() => {
  const names = Object.getOwnPropertyNames(globalThis);
  const interesting = names.filter((name) => /message|socket|connect|send|page|token|ws|handler|dispatch|finger/i.test(name));
  return { assignedLook: typeof __om, onType: typeof onmessage, interesting, count: names.length };
})()`, workerGlobal);
const snap = vm.runInContext("onmessage", workerGlobal);
const outer = workerGlobal.onmessage;
emit({
  op: "compare",
  snapType: typeof snap,
  outerType: typeof outer,
  same: snap === outer,
  snapName: snap && snap.name,
  outerName: outer && outer.name,
});
notes.length = 0;
const started = Date.now();
try {
  outer({
    data: {
      type: "INIT",
      data: { seed: "a".repeat(32), wsUrl: "wss://www.spiderdemo.cn/ws/", token: "b".repeat(94) },
    },
  });
  emit({ op: "outer-call", result: "returned", ms: Date.now() - started });
} catch (err) {
  emit({ op: "outer-call", result: err.name + ":" + String(err.message).split("\n")[0].slice(0, 180), ms: Date.now() - started });
}
if (!notes.some((item) => item.op === "open")) {
  try {
    snap({ data: { type: "INIT", data: { seed: "a", wsUrl: "wss://www.spiderdemo.cn/ws/", token: "b" } } });
    emit({ op: "snap-call", result: "returned" });
  } catch (err) {
    emit({ op: "snap-call", result: err.name + ":" + String(err.message).split("\n")[0].slice(0, 180) });
  }
}
process.stdout.write(JSON.stringify(notes, null, 2));
