"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const code = fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8");
const calls = [];
const sandbox = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, Math, JSON, Object, Array,
  String, Number, Boolean, RegExp, Date, Error, TypeError, Map, Set, Promise, Symbol,
  parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, decodeURIComponent,
  atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
  btoa: (value) => Buffer.from(String(value), "binary").toString("base64"),
  crypto: global.crypto,
};
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
const origStringify = JSON.stringify;
sandbox.JSON = {
  parse: JSON.parse,
  stringify(value) {
    const text = origStringify(value);
    if (text.length < 240) calls.push("stringify " + text);
    else calls.push("stringify len " + text.length);
    return text;
  },
};
vm.runInNewContext(code, sandbox, { filename: "baidu.js", timeout: 8000 });
const origDigest = sandbox.digest;
sandbox.digest = function (value) {
  const text = typeof value === "string" ? value : sandbox.stable(value);
  calls.push("digest " + text.slice(0, 160));
  return origDigest.apply(this, arguments);
};
const origStable = sandbox.stable;
sandbox.stable = function (value) {
  const text = origStable.apply(this, arguments);
  calls.push("stable " + text.slice(0, 160));
  return text;
};

async function main() {
  calls.length = 0;
  const derived = await sandbox.derive("main", "ticket-value");
  console.log("derive type", typeof derived, "len", derived && derived.length);
  console.log(calls.join("\n") || "no inner calls");
  calls.length = 0;
  const attested = await sandbox.attest("page", { page: 1, ticket: "t", sid: "s" }).catch((error) => "ERR " + error.message);
  console.log("attest", typeof attested === "string" ? attested.slice(0, 80) : JSON.stringify(attested).slice(0, 200));
  console.log(calls.join("\n") || "no attest calls");
}

main();
