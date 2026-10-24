"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

let watch = false;
const hexes = [];
const nativeToString = Number.prototype.toString;
Number.prototype.toString = function (radix) {
  const text = nativeToString.call(this, radix);
  if (watch && radix === 16) hexes.push(text);
  return text;
};
const box = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, Math, JSON, Object, Array,
  String, Number, Boolean, RegExp, Date, Error, TypeError, Map, Set, Promise, Symbol,
  parseInt, parseFloat, isNaN, isFinite, crypto: global.crypto,
};
box.self = box;
box.globalThis = box;
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });
watch = true;
const digest = box.digest("ab");
console.log("digest", digest);
console.log("hex calls", hexes.length);
console.log(hexes.join(" "));
