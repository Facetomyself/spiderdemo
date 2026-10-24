"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const box = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, Math, JSON, Object, Array,
  String, Number, Boolean, RegExp, Date, Error, TypeError, Map, Set, Promise, Symbol,
  parseInt, parseFloat, isNaN, isFinite, crypto: global.crypto,
};
box.self = box;
box.globalThis = box;
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });

const observed = {
  0x61: 0x9a6ae625,
  0x62: 0x9a6ae626,
  0x63: 0x9a6ae627,
  0x41: 0x9a6ae6c5,
  0x30: 0x9a6ae6d4,
  0x00: null,
  0xff: null,
  0x20: null,
};
for (const key of Object.keys(observed)) {
  const sample = String.fromCharCode(Number(key));
  // Capture second imul argument by hooking after the fact is hard; use known set only.
  void sample;
}
const IV = [0x9e3779b9, 0x85ebca6a, 0x1bdcb3d3, 0x24234423];
const C1 = 0x045d9f3b;
const m1 = Math.imul(1, C1) >>> 0;
const rotl = (x, r) => ((x << r) | (x >>> (32 - r))) >>> 0;
const samples = Object.entries(observed).filter((entry) => entry[1] != null).map(([k, x]) => [Number(k), x >>> 0]);

function fits(fn) {
  return samples.every(([k, x]) => fn(k) === x);
}

const ops = [];
for (const word of IV) {
  for (let rot = 0; rot < 32; rot++) {
    ops.push(["rotl(w^k)", word, rot, (k) => rotl((word ^ k) >>> 0, rot)]);
    ops.push(["rotl(w+k)", word, rot, (k) => rotl((word + k) >>> 0, rot)]);
    ops.push(["rotl(w-k)", word, rot, (k) => rotl((word - k) >>> 0, rot)]);
    ops.push(["w+rotl(k)", word, rot, (k) => (word + rotl(k, rot)) >>> 0]);
    ops.push(["w^rotl(k)", word, rot, (k) => (word ^ rotl(k, rot)) >>> 0]);
    ops.push(["rotl(w,r)^k", word, rot, (k) => (rotl(word, rot) ^ k) >>> 0]);
    ops.push(["rotl(w,r)+k", word, rot, (k) => (rotl(word, rot) + k) >>> 0]);
    ops.push(["rotl(w+m1^k)", word, rot, (k) => rotl((word + m1) ^ k, rot)]);
    ops.push(["rotl(w^m1+k)", word, rot, (k) => rotl(((word ^ m1) + k) >>> 0, rot)]);
    ops.push(["rotl(w+m1+k)", word, rot, (k) => rotl((word + m1 + k) >>> 0, rot)]);
    ops.push(["(rotl(w,r)+m1)^k", word, rot, (k) => ((rotl(word, rot) + m1) ^ k) >>> 0]);
    ops.push(["(rotl(w,r)^m1)+k", word, rot, (k) => ((rotl(word, rot) ^ m1) + k) >>> 0]);
  }
}
let hits = 0;
for (const [name, word, rot, fn] of ops) {
  if (!fits(fn)) continue;
  hits += 1;
  console.log("HIT", name, "word", word.toString(16), "rot", rot);
}
console.log("hits", hits, "m1", m1.toString(16));
console.log("oracle a", box.digest("a"));
