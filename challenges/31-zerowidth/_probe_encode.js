"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const calls = [];
function TracingEncoder() {}
TracingEncoder.prototype.encode = function (input) {
  calls.push(String(input).slice(0, 120));
  return new TextEncoder().encode(String(input));
};
const box = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder: TracingEncoder,
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
  crypto: global.crypto,
};
box.self = box;
box.globalThis = box;
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });
calls.length = 0;
const hex = box.digest("abc");
console.log("digest abc", hex, "encodes", calls.length, calls.map((item) => item.length).join(","));
calls.length = 0;
const obj = box.digest({ b: 1, a: 2 });
console.log("digest obj", obj, "encodes", calls.length);
calls.forEach((item) => console.log(" ENC", JSON.stringify(item), [...item].map((ch) => ch.charCodeAt(0).toString(16)).join(" ")));
calls.length = 0;
Promise.resolve(box.derive("page", "1")).then((value) => {
  console.log("derive", value, "encodes", calls.length);
  calls.forEach((item) => console.log(" ENC", JSON.stringify(item), [...item].map((ch) => ch.charCodeAt(0).toString(16)).join(" ")));
});
