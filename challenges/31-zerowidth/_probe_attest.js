"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const here = __dirname;
const trace = path.join(here, "_trace");
const zw = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"];
const index = new Map(zw.map((ch, pos) => [ch, pos]));
function decodeFile(name) {
  const text = fs.readFileSync(path.join(trace, name), "utf8");
  const raw = Buffer.alloc(text.length / 3);
  for (let offset = 0, at = 0; offset < text.length; offset += 3, at += 1) {
    raw[at] = (index.get(text[offset]) << 6) | (index.get(text[offset + 1]) << 3) | index.get(text[offset + 2]);
  }
  return JSON.parse(raw.toString("utf8"));
}
const names = fs.readdirSync(trace);
const init = decodeFile(names.find((name) => name.includes("init_") && name.includes("_res_")));

const nativeBind = Function.prototype.bind;
Function.prototype.bind = function bound(thisArg, ...args) {
  if (typeof this !== "function") {
    const owner = thisArg && typeof thisArg === "object" ? Object.keys(thisArg).slice(0, 8).join(",") : typeof thisArg;
    console.log("bad bind thisType", typeof this, "thisArg", owner, "args", args.length);
    throw new TypeError("Bind must be called on a function");
  }
  return nativeBind.call(this, thisArg, ...args);
};

const box = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, Math, JSON, Object, Array,
  String, Number, Boolean, RegExp, Date, Error, TypeError, Map, Set, Promise, Symbol,
  parseInt, parseFloat, isNaN, isFinite, crypto: global.crypto,
  navigator: { userAgent: "Mozilla/5.0", webdriver: false },
  devicePixelRatio: 1,
  innerWidth: 1920,
  innerHeight: 1080,
};
box.window = box;
box.self = box;
box.globalThis = box;
box.document = { hidden: false };
vm.runInNewContext(fs.readFileSync(path.join(here, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });

async function main() {
  const calls = [
    () => box.attest("main", init.ticket),
    () => box.attest("main", init),
    () => box.attest.call(box, "main", init.sid),
    () => box.derive.call(box, "main", init.ticket),
  ];
  for (const call of calls) {
    try {
      const value = await call();
      const text = typeof value === "string" ? "str " + value.length : JSON.stringify(Object.keys(value || {}));
      console.log("ok", text);
    } catch (error) {
      console.log("err", error.message);
    }
  }
}
main();
