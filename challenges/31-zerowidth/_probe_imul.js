"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const imuls = [];
const math = Object.create(Math);
math.imul = function imul(left, right) {
  if (imuls.length < 40) imuls.push([left >>> 0, right >>> 0]);
  return Math.imul(left, right);
};
const box = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, math,
  JSON, Object, Array, String, Number, Boolean, RegExp, Date, Error, TypeError,
  Map, Set, Promise, Symbol, parseInt, parseFloat, isNaN, isFinite, crypto: global.crypto,
};
box.Math = math;
box.self = box;
box.globalThis = box;
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });

function show(label, sample) {
  imuls.length = 0;
  const digest = box.digest(sample);
  const triple = imuls.slice(0, 3).map((pair) => pair[0].toString(16)).join(",");
  console.log([label, sample.charCodeAt(0).toString(16), triple, digest].join(" "));
}
for (let code = 0; code <= 16; code += 1) show("b" + code, String.fromCharCode(code));
for (let code = 0x20; code <= 0x70; code += 8) show("s" + code.toString(16), String.fromCharCode(code));
