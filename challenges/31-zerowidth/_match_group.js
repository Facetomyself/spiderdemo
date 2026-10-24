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
const main = decodeFile(names.find((name) => name.includes("POST_req") && name.includes("attest_main")));
const worker = decodeFile(names.find((name) => name.includes("POST_req") && name.includes("attest_worker")));
const page = decodeFile(names.find((name) => name.includes("POST_req") && name.includes("_page_")));

const box = {
  console: { log() {}, info() {}, warn() {}, error() {}, debug() {} },
  TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, DataView, Math, JSON, Object, Array,
  String, Number, Boolean, RegExp, Date, Error, TypeError, Map, Set, Promise, Symbol,
  parseInt, parseFloat, isNaN, isFinite, crypto: global.crypto,
};
box.self = box;
box.globalThis = box;
vm.runInNewContext(fs.readFileSync(path.join(here, "baidu.js"), "utf8"), box, { filename: "baidu.js", timeout: 8000 });

const RING = "spiderdemo-spiderking/v1";
const targets = {
  mainSeal: main.mainSeal,
  proof: main.proof,
  workerSeal: worker.workerSeal,
  gate: page.gate,
  pulseSeal: page.pulseSeal,
};
const named = {
  ticket: init.ticket,
  sid: init.sid,
  mainSalt: init.salts.main,
  pageSalt: init.salts.page,
  workerSalt: init.salts.worker,
  submitSalt: init.salts.submit,
  envDigest: main.env.digest,
  mediaDigest: main.media.digest,
  reportDigest: worker.report.digest,
  mainSeal: main.mainSeal,
  proof: main.proof,
  workerSeal: worker.workerSeal,
};

function check(label, material) {
  const digest = box.digest(material);
  for (const [name, value] of Object.entries(targets)) {
    if (digest === value) console.log("MATCH", name, label);
  }
}

const mainObj = JSON.stringify({
  env: main.env.digest,
  media: main.media.digest,
  salt: init.salts.main,
  sid: init.sid,
});
const workerObj = JSON.stringify({
  main: main.mainSeal,
  salt: init.salts.worker,
  sid: init.sid,
  worker: worker.report.digest,
});
const pageObj = JSON.stringify({
  envDigest: main.env.digest,
  mainSeal: main.mainSeal,
  mediaDigest: main.media.digest,
  page: page.page,
  salt: init.salts.page,
  sid: init.sid,
  workerSeal: worker.workerSeal,
});
const pulseObj = JSON.stringify({
  page: page.page,
  pulse: page.pulseSeal,
  salt: init.salts.page,
  sid: init.sid,
});

const hex32 = ["ticket", "envDigest", "mediaDigest", "reportDigest", "mainSeal", "proof", "workerSeal"];
for (const left of hex32) {
  for (const right of hex32) {
    const pipe = [RING, "main", init.sid, named[left], init.salts.main, named[right]].join("|");
    check("mainpipe " + left + " " + right, pipe);
    check("maincat " + left + " " + right, mainObj + init.salts.main + pipe);
    check("maincat2 " + left + " " + right, mainObj + pipe);
  }
}
for (const left of hex32) {
  for (const right of hex32) {
    const pipe = [RING, "worker", init.sid, init.salts.worker, named[left], named[right]].join("|");
    check("workerpipe " + left + " " + right, pipe);
    check("workercat " + left + " " + right, workerObj + init.salts.worker + pipe);
  }
}
const hexPage = hex32.concat(["gate"]);
named.gate = page.gate;
for (const a of hexPage) {
  for (const b of hexPage) {
    for (const c of hexPage) {
      const pipe = [RING, "page", init.sid, init.salts.page, named[a], named[b], named[c]].join("|");
      check("pagepipe " + [a, b, c].join(","), pageObj + init.salts.page + pulseObj + init.salts.page + pipe);
    }
  }
}
console.log("done");
