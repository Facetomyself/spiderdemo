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
  for (const [name, target] of Object.entries(targets)) {
    if (value === target) notes.push("MATCH " + name + " = " + label);
  }
}

async function main() {
  const salts = init.salts;
  const base = [cn, init.ticket, init.sid, salts.main, salts.page, salts.submit, salts.worker, "1", "main", "page", "worker", "submit", mainReq.env.digest, mainReq.media.digest, workerReq.report.digest, mainReq.mainSeal, mainReq.proof, workerReq.workerSeal];
  const labels = ["cn", "ticket", "sid", "main", "page", "submit", "worker", "p1", "roleMain", "rolePage", "roleWorker", "roleSubmit", "envD", "mediaD", "reportD", "mainSeal", "proof", "workerSeal"];
  for (let i = 0; i < base.length; i++) consider("d " + labels[i], worker.digest(base[i]));
  for (let i = 0; i < base.length; i++) {
    for (let j = 0; j < base.length; j++) {
      if (i === j) continue;
      consider("d " + labels[i] + "+" + labels[j], worker.digest(base[i] + base[j]));
      consider("d " + labels[i] + "|" + labels[j], worker.digest(base[i] + "|" + base[j]));
      consider("d " + labels[i] + ":" + labels[j], worker.digest(base[i] + ":" + base[j]));
    }
  }
  const objs = [];
  objs.push(["nonce ticket", { clientNonce: cn, ticket: init.ticket }]);
  objs.push(["sid ticket", { sid: init.sid, ticket: init.ticket }]);
  objs.push(["page pulse", { page: 1, ticket: init.ticket, sid: init.sid }]);
  objs.push(["env features", mainReq.env.features]);
  objs.push(["media coherent", { coherent: mainReq.media.coherent, digest: mainReq.media.digest }]);
  objs.push(["seals", { mainSeal: mainReq.mainSeal, proof: mainReq.proof, workerSeal: workerReq.workerSeal }]);
  for (const [label, value] of objs) consider("obj " + label, worker.digest(value));
  for (const role of ["main", "page", "submit", "worker"]) {
    consider("derive " + role + " init", await worker.derive(role, init));
    consider("derive " + role + " cn", await worker.derive(role, cn));
    consider("derive " + role + " ticket", await worker.derive(role, init.ticket));
    consider("derive salt role", await worker.derive(salts[role], init.ticket));
  }
  consider("d main+cn+ticket", worker.digest(salts.main + cn + init.ticket));
  consider("d cn+ticket+main", worker.digest(cn + init.ticket + salts.main));
  consider("d ticket+cn+main", worker.digest(init.ticket + cn + salts.main));
  consider("d main+ticket+cn", worker.digest(salts.main + init.ticket + cn));
  consider("d page+ticket+1", worker.digest(salts.page + init.ticket + "1"));
  consider("d page+1+ticket", worker.digest(salts.page + "1" + init.ticket));
  consider("d 1+page+ticket", worker.digest("1" + salts.page + init.ticket));
  consider("d worker+report", worker.digest(salts.worker + workerReq.report.digest));
  consider("d report+worker", worker.digest(workerReq.report.digest + salts.worker));
  consider("d env+media+main", worker.digest(mainReq.env.digest + mainReq.media.digest + salts.main));
  consider("d main+env+media", worker.digest(salts.main + mainReq.env.digest + mainReq.media.digest));
  consider("d proof pieces", worker.digest(mainReq.mainSeal + workerReq.workerSeal));
  fs.writeFileSync(path.join(__dirname, "_seal_matches.txt"), notes.join("\n"), "utf8");
  console.log("matches", notes.length);
  console.log(notes.join("\n"));
}

main();
