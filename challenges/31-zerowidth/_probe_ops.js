"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ops = [];
let watch = false;
function record(kind, detail) {
  if (watch && ops.length < 80) ops.push(kind + " " + detail);
}
const nativeChar = String.prototype.charCodeAt;
String.prototype.charCodeAt = function (index) {
  const value = nativeChar.call(this, index);
  if (watch && this.length < 80) record("char", this.length + "@" + index + "=" + value);
  return value;
};
const nativeCodePoint = String.prototype.codePointAt;
String.prototype.codePointAt = function (index) {
  const value = nativeCodePoint.call(this, index);
  if (watch && this.length < 80) record("cp", this.length + "@" + index + "=" + value);
  return value;
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
console.log("digest", box.digest("ab"));
console.log(ops.join("\n") || "no ops");
