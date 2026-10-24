"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const code = fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8");
const sandbox = {
  console,
  TextEncoder,
  TextDecoder,
  Uint8Array,
  ArrayBuffer,
  DataView,
  Math,
  JSON,
  Object,
  Array,
  String,
  Number,
  Boolean,
  RegExp,
  Date,
  Error,
  TypeError,
  Map,
  Set,
  Promise,
  Symbol,
  parseInt,
  parseFloat,
  isNaN,
  isFinite,
  encodeURIComponent,
  decodeURIComponent,
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: global.crypto,
};
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
sandbox.window = sandbox;
vm.runInNewContext(code, sandbox, { filename: "baidu.js", timeout: 8000 });

function show(label, value) {
  let text;
  if (typeof value === "string") text = JSON.stringify(value.slice(0, 180));
  else {
    try { text = JSON.stringify(value); } catch (error) { text = String(value); }
  }
  console.log(label, text ? text.slice(0, 400) : text);
}

for (const name of ["stable", "digest", "derive", "encode", "decode", "attest"]) {
  const fn = sandbox[name];
  console.log("FN", name, "len", fn.length, "src", String(fn).slice(0, 120).replace(/\s+/g, " "));
}

const samples = ["0", "1", "42", "hello", "{\"a\":1}", "abc"];
for (const sample of samples) {
  try { show("encode " + sample, sandbox.encode(sample)); } catch (error) { console.log("encode", sample, "ERR", error.message); }
  try { show("decode " + sample, sandbox.decode(sample)); } catch (error) { console.log("decode", sample, "ERR", error.message); }
}

try {
  const encoded = sandbox.encode("hello");
  show("round", sandbox.decode(encoded));
  show("encoded codes", [...encoded].map((ch) => ch.codePointAt(0).toString(16)).join(" "));
} catch (error) {
  console.log("round ERR", error.message);
}

const init = fs.readFileSync(path.join(__dirname, "_trace", "1_200_res__authentication_api_spiderking_challenge_init_.bin")).toString("utf8");
const state = sandbox.decode(init);
show("state keys", Object.keys(state));

for (const args of [
  [state],
  ["main", state],
  [state, "main"],
  ["attest", state],
  [init],
]) {
  try { show("attest " + args.length, sandbox.attest(...args)); } catch (error) { console.log("attest ERR", error.message); }
  try { show("digest " + args.length, sandbox.digest(...args)); } catch (error) { console.log("digest ERR", error.message); }
  try { show("derive " + args.length, sandbox.derive(...args)); } catch (error) { console.log("derive ERR", error.message); }
  try { show("stable " + args.length, sandbox.stable(...args)); } catch (error) { console.log("stable ERR", error.message); }
}
