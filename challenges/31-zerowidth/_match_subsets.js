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
const targets = new Map([
  [mainReq.mainSeal, "mainSeal"],
  [mainReq.proof, "proof"],
  [workerReq.workerSeal, "workerSeal"],
  [pageReq.gate, "gate"],
  [pageReq.pulseSeal, "pulseSeal"],
  [pageReq.proof, "pageProof"],
]);
const notes = [];
function consider(label, value) {
  if (typeof value === "string" && targets.has(value)) notes.push("MATCH " + targets.get(value) + " = " + label);
}

function subsets(keys, size) {
  const out = [];
  const pick = (start, chosen) => {
    if (chosen.length === size) { out.push(chosen.slice()); return; }
    for (let i = start; i < keys.length; i++) { chosen.push(keys[i]); pick(i + 1, chosen); chosen.pop(); }
  };
  pick(0, []);
  return out;
}

const fields = {
  cn,
  ticket: init.ticket,
  sid: init.sid,
  main: init.salts.main,
  pageSalt: init.salts.page,
  submit: init.salts.submit,
  worker: init.salts.worker,
  env: mainReq.env.digest,
  media: mainReq.media.digest,
  report: workerReq.report.digest,
  page: "1",
  ring: worker.RING,
};
const keys = Object.keys(fields);

for (const size of [1, 2, 3]) {
  for (const chosen of subsets(keys, size)) {
    const obj = {};
    const parts = [];
    for (const key of chosen) {
      obj[key] = fields[key];
      parts.push(fields[key]);
    }
    consider("obj " + chosen.join(","), worker.digest(obj));
    consider("cat " + chosen.join("+"), worker.digest(parts.join("")));
    consider("pipe " + chosen.join("|"), worker.digest(parts.join("|")));
  }
}
consider("env body", worker.digest(mainReq.env));
consider("media obj", worker.digest(mainReq.media));
consider("report obj", worker.digest(workerReq.report));
consider("no seals", worker.digest({
  env: mainReq.env,
  media: mainReq.media,
  sid: init.sid,
  ticket: init.ticket,
}));
consider("pulse cat", worker.digest(pageReq.pulse.envDigest + pageReq.pulse.mediaDigest + init.salts.page + "1"));
fs.writeFileSync(path.join(__dirname, "_seal_matches.txt"), notes.join("\n"), "utf8");
console.log(notes.join("\n") || "no matches");
console.log("checked subsets", keys.length);
