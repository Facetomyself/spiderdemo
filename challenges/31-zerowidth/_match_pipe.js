"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

function loadWorker() {
  const code = fs.readFileSync(path.join(__dirname, "baidu.js"), "utf8");
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
  vm.runInNewContext(code, sandbox, { filename: "baidu.js", timeout: 8000 });
  return sandbox;
}

const worker = loadWorker();
const ZW = worker.ZW;
const index = new Map(ZW.map((ch, pos) => [ch, pos]));
function decode(text) {
  const raw = [];
  for (let i = 0; i < text.length; i += 3) raw.push((index.get(text[i]) << 6) | (index.get(text[i + 1]) << 3) | index.get(text[i + 2]));
  return JSON.parse(Buffer.from(raw).toString("utf8"));
}
const trace = path.join(__dirname, "_trace");
const files = fs.readdirSync(trace);
function read(part) {
  return decode(fs.readFileSync(path.join(trace, files.find((item) => item.includes(part))), "utf8"));
}
const init = read("1_200_res");
const mainReq = read("POST_req__authentication_api_spiderking_challenge_attest_main");
const workerReq = read("POST_req__authentication_api_spiderking_challenge_attest_worker");
const pageReq = read("POST_req__authentication_api_spiderking_challenge_page");
const cn = "4c2d022487e77c8d82469c1f181c33b5";
const ring = worker.RING;
const targets = new Map([
  [mainReq.mainSeal, "mainSeal"],
  [mainReq.proof, "proof"],
  [workerReq.workerSeal, "workerSeal"],
  [workerReq.proof, "workerProof"],
  [pageReq.gate, "gate"],
  [pageReq.pulseSeal, "pulseSeal"],
  [pageReq.proof, "pageProof"],
  [pageReq.mainSeal, "pageMainSeal"],
  [pageReq.workerSeal, "pageWorkerSeal"],
]);
const notes = [];
function consider(label, value) {
  if (typeof value === "string" && targets.has(value)) notes.push("MATCH " + targets.get(value) + " = " + label);
}

const mats = {
  cn,
  ticket: init.ticket,
  sid: init.sid,
  mainSalt: init.salts.main,
  pageSalt: init.salts.page,
  submitSalt: init.salts.submit,
  workerSalt: init.salts.worker,
  env: worker.stable(mainReq.env.body),
  media: worker.stable(mainReq.media.body),
  report: worker.stable(workerReq.report.body),
  envD: mainReq.env.digest,
  mediaD: mainReq.media.digest,
  reportD: workerReq.report.digest,
  page: "1",
  pulse: worker.stable(pageReq.pulse),
  envFull: worker.stable(mainReq.env),
  mediaFull: worker.stable(mainReq.media),
  reportFull: worker.stable(workerReq.report),
};
const roles = ["main", "page", "worker", "submit", "proof", "gate", "pulse", "seal", "attest"];
for (const role of roles) {
  for (const [label, text] of Object.entries(mats)) {
    consider(`${role}|${label}`, worker.digest(`${ring}|${role}|${text}`));
  }
}
const pairs = [
  ["cn", "ticket"],
  ["ticket", "cn"],
  ["sid", "ticket"],
  ["ticket", "sid"],
  ["envD", "mediaD"],
  ["mediaD", "envD"],
  ["env", "media"],
  ["ticket", "page"],
  ["page", "ticket"],
  ["sid", "page"],
  ["cn", "sid"],
  ["envD", "ticket"],
  ["ticket", "envD"],
];
for (const role of roles) {
  for (const [a, b] of pairs) {
    consider(`${role}|${a}|${b}`, worker.digest(`${ring}|${role}|${mats[a]}|${mats[b]}`));
  }
}
consider("derive main ticket", worker.digest(`${ring}|main|${init.ticket}`));
fs.writeFileSync(path.join(__dirname, "_seal_matches.txt"), notes.join("\n"), "utf8");
console.log(notes.join("\n") || "no matches");
