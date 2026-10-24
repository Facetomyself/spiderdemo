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
  Uint16Array,
  Uint32Array,
  Int8Array,
  Int16Array,
  Int32Array,
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
  WeakMap,
  Promise,
  Symbol,
  parseInt,
  parseFloat,
  isNaN,
  isFinite,
  encodeURIComponent,
  decodeURIComponent,
  escape,
  unescape,
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: global.crypto,
};
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
sandbox.window = sandbox;

const probe = `
;globalThis.__types = {
  stable: typeof stable,
  digest: typeof digest,
  derive: typeof derive,
  encode: typeof encode,
  decode: typeof decode,
  attest: typeof attest,
  ZW: typeof ZW,
  INDEX: typeof INDEX,
  API: typeof API,
  RING: typeof RING
};
globalThis.__vals = { ZW, INDEX, API, RING };
`;

vm.runInNewContext(code + probe, sandbox, { filename: "baidu.js", timeout: 8000 });
console.log(JSON.stringify(sandbox.__types));
const vals = sandbox.__vals || {};
for (const key of Object.keys(vals)) {
  const value = vals[key];
  const text = typeof value === "string" ? value.slice(0, 200) : JSON.stringify(value);
  console.log(key, typeof value, text && text.slice ? text.slice(0, 300) : text);
}
if (typeof sandbox.decode === "function") {
  const init = fs.readFileSync(path.join(__dirname, "_trace", "1_200_res__authentication_api_spiderking_challenge_init_.bin"));
  const text = init.toString("utf8");
  try {
    const decoded = sandbox.decode(text);
    console.log("decode(init)", typeof decoded, JSON.stringify(decoded).slice(0, 500));
  } catch (error) {
    console.log("decode threw", error && error.message);
  }
}
