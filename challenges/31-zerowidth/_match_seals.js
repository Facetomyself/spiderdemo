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
  const name = files.find((item) => item.includes(part));
  return decode(fs.readFileSync(path.join(trace, name), "utf8"));
}

const init = read("1_200_res");
const mainReq = read("POST_req__authentication_api_spiderking_challenge_attest_main");
const workerReq = read("POST_req__authentication_api_spiderking_challenge_attest_worker");
const pageReq = read("POST_req__authentication_api_spiderking_challenge_page");

const notes = [];
const targets = {
  mainSeal: pageReq.mainSeal,
  proof: pageReq.proof,
  workerSeal: pageReq.workerSeal,
  gate: pageReq.gate,
  pulseSeal: pageReq.pulseSeal,
  envDigest: pageReq.pulse.envDigest,
  mediaDigest: pageReq.pulse.mediaDigest,
  mainEnvDigest: mainReq.env.digest,
  mainMediaDigest: mainReq.media.digest,
  mainProof: mainReq.proof,
  mainMainSeal: mainReq.mainSeal,
  workerProof: workerReq.proof,
  workerWorkerSeal: workerReq.workerSeal,
  reportDigest: workerReq.report.digest,
};

function consider(label, value) {
  if (typeof value !== "string" || !/^[0-9a-f]{32}$/.test(value)) return;
  for (const [name, target] of Object.entries(targets)) {
    if (value === target) notes.push("MATCH " + name + " = " + label);
  }
}

async function main() {
  const salts = init.salts;
  const pieces = {
    ticket: init.ticket,
    sid: init.sid,
    page: "1",
    mainSalt: salts.main,
    pageSalt: salts.page,
    submitSalt: salts.submit,
    workerSalt: salts.worker,
    mainSeal: pageReq.mainSeal,
    workerSeal: pageReq.workerSeal,
    proof: pageReq.proof,
    envDigest: mainReq.env.digest,
    mediaDigest: mainReq.media.digest,
  };
  const names = Object.keys(pieces);
  for (const name of names) consider("digest " + name, worker.digest(pieces[name]));
  for (const left of names) {
    for (const right of names) {
      if (left === right) continue;
      const text = pieces[left] + pieces[right];
      consider("digest " + left + "+" + right, worker.digest(text));
    }
  }
  const objects = {
    "env.body": mainReq.env.body,
    "media.body": mainReq.media.body,
    "report.body": workerReq.report.body,
    "pulse": pageReq.pulse,
    "page obj": { page: 1, sid: init.sid, ticket: init.ticket },
    "page only": { page: 1 },
    "gate obj": { page: 1, ticket: init.ticket, salt: salts.page },
  };
  for (const [label, value] of Object.entries(objects)) consider("digest obj " + label, worker.digest(value));
  for (const role of ["main", "page", "submit", "worker"]) {
    consider("derive " + role, await worker.derive(role, init));
    consider("derive role page", await worker.derive(role, 1));
    consider("derive role pageReq", await worker.derive(role, pageReq));
  }
  consider("digest stable pageReq", worker.digest(worker.stable(pageReq)));
  consider("digest mainSeal+page", worker.digest(pageReq.mainSeal + "1"));
  consider("digest pageSalt+1", worker.digest(salts.page + "1"));
  consider("digest 1+pageSalt", worker.digest("1" + salts.page));
  consider("digest ticket+1+pageSalt", worker.digest(init.ticket + "1" + salts.page));
  consider("digest pageSalt+ticket+1", worker.digest(salts.page + init.ticket + "1"));
  consider("digest pageSalt+1+ticket", worker.digest(salts.page + "1" + init.ticket));
  fs.writeFileSync(path.join(__dirname, "_seal_matches.txt"), notes.join("\n"), "utf8");
  console.log(notes.length ? notes.join("\n") : "no matches");
}

main().catch((error) => {
  console.log("ERR", error && error.message ? error.message : error);
  process.exit(1);
});
