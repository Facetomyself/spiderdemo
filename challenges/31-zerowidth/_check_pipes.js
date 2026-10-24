"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const here = __dirname;
const trace = path.join(here, "_trace");
const zw = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064"];
const index = new Map(zw.map((ch, pos) => [ch, pos]));

function decodeText(text) {
  const raw = Buffer.alloc(text.length / 3);
  for (let offset = 0, at = 0; offset < text.length; offset += 3, at += 1) {
    raw[at] = (index.get(text[offset]) << 6) | (index.get(text[offset + 1]) << 3) | index.get(text[offset + 2]);
  }
  return JSON.parse(raw.toString("utf8"));
}
function decodeFile(name) {
  return decodeText(fs.readFileSync(path.join(trace, name), "utf8"));
}
const names = fs.readdirSync(trace);
const init = decodeFile(names.find((name) => name.includes("init_") && name.includes("_res_")));
const main = decodeFile(names.find((name) => name.includes("POST_req") && name.includes("attest_main")));
const worker = decodeFile(names.find((name) => name.includes("POST_req") && name.includes("attest_worker")));
const page = decodeFile(names.find((name) => name.includes("POST_req") && name.includes("_page_")));
const calls = fs.readFileSync(path.join(here, "_vm_calls.txt"), "utf8");
const cn = (calls.match(/cn=([0-9a-f]{32})/) || [])[1];

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
const targets = [
  ["mainSeal", main.mainSeal],
  ["proof", main.proof],
  ["workerSeal", worker.workerSeal],
  ["workerProof", worker.proof],
  ["gate", page.gate],
  ["pulseSeal", page.pulseSeal],
  ["pageProof", page.proof],
];
function check(label, material) {
  const digest = box.digest(material);
  const hits = targets.filter((entry) => entry[1] === digest).map((entry) => entry[0]);
  if (hits.length) console.log("MATCH", hits.join(","), "<=", label);
}

const mainObj = JSON.stringify({
  env: main.env.digest,
  media: main.media.digest,
  salt: init.salts.main,
  sid: init.sid,
});
const mainPipe = [RING, "main", init.sid, cn, init.salts.main, init.ticket].join("|");
check("mainPipe", mainPipe);
check("mainObj", mainObj);
check("mainCat", mainObj + init.salts.main + mainPipe);
check("mainObjPipe", mainObj + mainPipe);
check("mainSaltPipe", init.salts.main + mainPipe);

const workerObj = JSON.stringify({
  main: main.mainSeal,
  salt: init.salts.worker,
  sid: init.sid,
  worker: worker.report.digest,
});
const workerPipe = [RING, "worker", init.sid, init.salts.worker, init.ticket, main.mainSeal].join("|");
check("workerPipe", workerPipe);
check("workerObj", workerObj);
check("workerCat", workerObj + init.salts.worker + workerPipe);

const pageObj = JSON.stringify({
  envDigest: main.env.digest,
  mainSeal: main.mainSeal,
  mediaDigest: main.media.digest,
  page: 1,
  salt: init.salts.page,
  sid: init.sid,
  workerSeal: worker.workerSeal,
});
const pagePipe = [RING, "page", init.sid, init.salts.page, init.ticket, main.mainSeal, worker.workerSeal].join("|");
check("pagePipe", pagePipe);
check("pageObj", pageObj);
check("pageCat", pageObj + init.salts.page + pagePipe);
const pulseObj = JSON.stringify({ page: 1, pulse: page.pulseSeal, salt: init.salts.page, sid: init.sid });
check("pulseObj", pulseObj);
check("pageAll", pageObj + init.salts.page + pulseObj + init.salts.page + pagePipe);
function xorHex(left, right) {
  const size = Math.max(left.length, right.length);
  let out = "";
  for (let i = 0; i < size; i += 2) {
    const a = parseInt(left.slice(i, i + 2) || "00", 16);
    const b = parseInt(right.slice(i % right.length, (i % right.length) + 2), 16);
    out += (a ^ b).toString(16).padStart(2, "0");
  }
  return out.slice(0, 32);
}
function swapWords(hex) {
  let out = "";
  for (let i = 0; i < hex.length; i += 8) {
    const word = hex.slice(i, i + 8);
    out += word.slice(6, 8) + word.slice(4, 6) + word.slice(2, 4) + word.slice(0, 2);
  }
  return out;
}
function report(label, hex) {
  const hits = targets.filter((entry) => entry[1] === hex).map((entry) => entry[0]);
  if (hits.length) console.log("MATCH", hits.join(","), "<=", label);
}
const mixes = [
  ["mainPipe", mainPipe, init.salts.main],
  ["workerPipe", workerPipe, init.salts.worker],
  ["pagePipe", pagePipe, init.salts.page],
];
for (const [label, material, salt] of mixes) {
  const digest = box.digest(material);
  report(label, digest);
  report(label + " rev", digest.split("").reverse().join(""));
  report(label + " swap", swapWords(digest));
  report(label + " xorSalt", xorHex(digest, salt));
  report(label + " xorTicket", xorHex(digest, init.ticket));
  report(label + " xorCn", xorHex(digest, cn));
  report(label + " xorSid", xorHex(digest, init.sid));
  report(label + " digest2", box.digest(digest));
  report(label + " digestSalt", box.digest(digest + salt));
  report(label + " saltDigest", box.digest(salt + digest));
}
console.log("same proof", main.proof === worker.proof, worker.proof === page.proof, main.proof === page.proof);
console.log("done");
