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
const api = worker.API;
const notes = [];
const targets = {
  mainSeal: mainReq.mainSeal,
  proof: mainReq.proof,
  workerSeal: workerReq.workerSeal,
  gate: pageReq.gate,
  pulseSeal: pageReq.pulseSeal,
  pageProof: pageReq.proof,
};
function consider(label, value) {
  if (typeof value !== "string") return;
  for (const [name, target] of Object.entries(targets)) if (value === target) notes.push("MATCH " + name + " = " + label);
}

async function main() {
  const salts = init.salts;
  const mats = {
    init: worker.stable(init),
    env: worker.stable(mainReq.env.body),
    media: worker.stable(mainReq.media.body),
    report: worker.stable(workerReq.report.body),
    pulse: worker.stable(pageReq.pulse),
    page: "1",
    cn,
    ticket: init.ticket,
    sid: init.sid,
    ring,
    api,
  };
  for (const [role, salt] of Object.entries(salts)) {
    for (const [label, text] of Object.entries(mats)) {
      consider(`d ${role}+${label}`, worker.digest(salt + text));
      consider(`d ${label}+${role}`, worker.digest(text + salt));
      consider(`d ring+${role}+${label}`, worker.digest(ring + salt + text));
      consider(`d ${role}+ring+${label}`, worker.digest(salt + ring + text));
    }
    consider("derive " + role, await worker.derive(role, init));
  }
  consider("d ring+ticket", worker.digest(ring + init.ticket));
  consider("d ring+cn", worker.digest(ring + cn));
  consider("d api+ticket", worker.digest(api + init.ticket));
  consider("d ring+env", worker.digest(ring + mats.env));
  consider("d main+ring+cn", worker.digest(salts.main + ring + cn));
  consider("d cn+ring+main", worker.digest(cn + ring + salts.main));
  const joined = [ring, init.sid, init.ticket, cn, salts.main].join("|");
  consider("d joined", worker.digest(joined));
  consider("d stable mainReq", worker.digest(mainReq));
  consider("d stable pageReq", worker.digest(pageReq));
  fs.writeFileSync(path.join(__dirname, "_seal_matches.txt"), notes.join("\n"), "utf8");
  console.log(notes.join("\n") || "no matches");
}

main();
