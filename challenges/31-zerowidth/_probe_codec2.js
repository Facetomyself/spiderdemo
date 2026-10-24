"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const crypto = require("crypto");

const code = fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8");
const sandbox = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
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

const md5 = (value) => crypto.createHash("md5").update(value).digest("hex");
const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const notes = [];
function note(label, value) {
  notes.push(label + " " + (typeof value === "string" ? value : JSON.stringify(value)));
}

const init = fs.readFileSync(path.join(__dirname, "_trace", "1_200_res__authentication_api_spiderking_challenge_init_.bin")).toString("utf8");
const state = sandbox.decode(init);
const stableState = sandbox.stable(state);
note("stable===json", stableState === JSON.stringify(state));
note("digest state", sandbox.digest(state));
note("md5 stable", md5(stableState));
note("md5 json", md5(JSON.stringify(state)));
note("sha256 stable", sha256(stableState));
note("digest main", sandbox.digest("main"));
note("md5 main", md5("main"));
note("digest empty", sandbox.digest(""));
note("md5 empty", md5(""));
note("digest hello", sandbox.digest("hello"));
note("md5 hello", md5("hello"));

const salts = state.salts;
for (const key of Object.keys(salts)) {
  const joined = salts[key] + stableState;
  note("md5 salt+stable " + key, md5(joined));
  note("md5 stable+salt " + key, md5(stableState + salts[key]));
  note("digest salt+key", sandbox.digest(salts[key] + key));
}

note("attest type", typeof sandbox.attest("main", state));
try {
  const attested = sandbox.attest("main", state);
  note("attest ctor", attested && attested.constructor && attested.constructor.name);
  note("attest keys", attested && typeof attested === "object" ? Object.keys(attested) : typeof attested);
  note("attest json", JSON.stringify(attested));
} catch (error) {
  note("attest error", error.message);
}

note("derive keys", Object.keys(sandbox.derive() || {}));
try {
  note("derive main", JSON.stringify(sandbox.derive("main")));
  note("derive state", JSON.stringify(sandbox.derive(state)));
  note("derive main state", JSON.stringify(sandbox.derive("main", state)));
} catch (error) {
  note("derive error", error.message);
}

note("onconnect", typeof sandbox.onconnect);
note("INDEX keys", Object.keys(sandbox.INDEX));
const zw = sandbox.ZW;
note("zw", zw.map((ch) => "U+" + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, "0")).join(","));

const encoded = sandbox.encode({ n: 1, s: "a" });
const manual = (value) => {
  const bytes = Buffer.from(JSON.stringify(value), "utf8");
  let out = "";
  for (const byte of bytes) {
    out += zw[(byte >> 6) & 7] + zw[(byte >> 3) & 7] + zw[byte & 7];
  }
  return out;
};
note("manual encode match", manual({ n: 1, s: "a" }) === encoded);

fs.writeFileSync(path.join(__dirname, "_codec_notes.txt"), notes.join("\n"), "utf8");
console.log(notes.join("\n"));
