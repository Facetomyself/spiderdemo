"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const code = fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8");
const sandbox = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, Math, JSON, Object, Array,
  String, Number, Boolean, RegExp, Date, Error, TypeError, Map, Set, WeakMap, Promise, Symbol,
  parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, decodeURIComponent,
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: global.crypto,
  fetch: async () => { throw new Error("no fetch"); },
  SharedWorker: function SharedWorker() {},
  navigator: { userAgent: "x", webdriver: false },
  innerWidth: 1920,
  innerHeight: 1080,
  devicePixelRatio: 1,
};
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
sandbox.window = sandbox;
vm.runInNewContext(code, sandbox, { filename: "baidu.js", timeout: 8000 });

const ZW = sandbox.ZW;
const index = new Map(ZW.map((ch, pos) => [ch, pos]));
function decode(text) {
  const raw = [];
  for (let i = 0; i < text.length; i += 3) raw.push((index.get(text[i]) << 6) | (index.get(text[i + 1]) << 3) | index.get(text[i + 2]));
  return JSON.parse(Buffer.from(raw).toString("utf8"));
}

const init = decode(fs.readFileSync(path.join(__dirname, "_trace", "1_200_res__authentication_api_spiderking_challenge_init_.bin"), "utf8"));
const notes = [];
const note = (label, value) => notes.push(label + " " + (typeof value === "string" ? value : JSON.stringify(value)));

const vectors = {};
for (let i = 0; i < 256; i++) vectors[i] = sandbox.digest(String.fromCharCode(i));
vectors.ab = sandbox.digest("ab");
vectors.ba = sandbox.digest("ba");
vectors.a0 = sandbox.digest("a\u0000");
vectors.empty = sandbox.digest("");
fs.writeFileSync(path.join(__dirname, "_digest_vectors.json"), JSON.stringify(vectors), "utf8");

async function settle(label, value) {
  try {
    const resolved = await value;
    note(label, typeof resolved === "string" ? resolved : JSON.stringify(resolved));
  } catch (error) {
    note(label + " error", error && error.message ? error.message : String(error));
  }
}

const replies = [];
const port = {
  onmessage: null,
  start() { note("port.start", ""); },
  postMessage(data) { replies.push(data); note("reply", data); },
  addEventListener(type, fn) { if (type === "message") this.onmessage = fn; },
  close() {},
};
async function main() {
  for (const role of ["main", "page", "submit", "worker"]) {
    await settle("derive " + role, sandbox.derive(role, init));
  }
  await settle("derive only role", sandbox.derive("main"));
  await settle("derive noarg", sandbox.derive());
  try {
    sandbox.onconnect({ ports: [port] });
    note("onconnect set", typeof port.onmessage);
    const state = Object.assign({
      cache: {},
      currentPage: 0,
      loading: true,
      clientNonce: "300b001e9c076c5c0749aa7db58c8c3c",
      csrfToken: "",
      mainSeal: "4d5f4853092d94064472dc55568cdc59",
    }, init);
    if (typeof port.onmessage === "function") {
      try {
        const ret = port.onmessage({ data: { cmd: "attest", state } });
        await settle("onmessage ret", ret);
      } catch (error) {
        note("onmessage throw", error && error.message ? error.message : String(error));
      }
    }
  } catch (error) {
    note("onconnect error", error.message);
  }
  await new Promise((resolve) => setTimeout(resolve, 200));
  note("replies", replies.length);
  fs.writeFileSync(path.join(__dirname, "_worker_notes.txt"), notes.join("\n"), "utf8");
  console.log(notes.join("\n"));
}

main();
