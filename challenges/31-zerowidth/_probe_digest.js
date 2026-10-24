"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

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
sandbox.window = sandbox;
vm.runInNewContext(code, sandbox, { filename: "baidu.js", timeout: 8000 });

const ZW = sandbox.ZW;
const index = new Map(ZW.map((ch, pos) => [ch, pos]));
function decode(text) {
  const raw = [];
  for (let i = 0; i < text.length; i += 3) {
    raw.push((index.get(text[i]) << 6) | (index.get(text[i + 1]) << 3) | index.get(text[i + 2]));
  }
  return JSON.parse(Buffer.from(raw).toString("utf8"));
}

const notes = [];
const note = (label, value) => notes.push(label + " " + (typeof value === "string" ? value : JSON.stringify(value)));

const attestPath = fs.readdirSync(path.join(__dirname, "_trace")).find((name) => name.includes("POST_req"));
const attest = decode(fs.readFileSync(path.join(__dirname, "_trace", attestPath), "utf8"));
const samples = ["", "a", "b", "ab", "abc", "0", "00", stableOf(attest.env.body), JSON.stringify(attest.env.body)];
function stableOf(value) { return sandbox.stable(value); }

for (const sample of ["", "a", "b", "ab", "abc", "0"]) {
  note("digest " + JSON.stringify(sample), sandbox.digest(sample));
}
note("env.digest", attest.env.digest);
note("digest env.body", sandbox.digest(attest.env.body));
note("digest stable env.body", sandbox.digest(sandbox.stable(attest.env.body)));
note("media.digest", attest.media.digest);
note("digest media.body", sandbox.digest(attest.media.body));
note("digest stable media.body", sandbox.digest(sandbox.stable(attest.media.body)));
note("mainSeal", attest.mainSeal);
note("proof", attest.proof);
note("digest ticket", sandbox.digest(attest.ticket));
note("digest sid", sandbox.digest(attest.sid));
note("digest mainSeal field", sandbox.digest(attest.mainSeal));

const init = decode(fs.readFileSync(path.join(__dirname, "_trace", "1_200_res__authentication_api_spiderking_challenge_init_.bin"), "utf8"));
for (const [name, salt] of Object.entries(init.salts)) {
  note("digest salt " + name, sandbox.digest(salt));
  note("digest salt+ticket " + name, sandbox.digest(salt + init.ticket));
  note("digest ticket+salt " + name, sandbox.digest(init.ticket + salt));
}
note("digest ticket+main", sandbox.digest(init.ticket + init.salts.main));
note("digest sid+ticket", sandbox.digest(init.sid + init.ticket));
note("match mainSeal digest(ticket+mainSalt)", sandbox.digest(init.ticket + init.salts.main) === attest.mainSeal);
note("match mainSeal digest(mainSalt+ticket)", sandbox.digest(init.salts.main + init.ticket) === attest.mainSeal);
note("match mainSeal digest(stable init)", sandbox.digest(sandbox.stable(init)) === attest.mainSeal);
note("match proof digest(env.digest+media.digest)", sandbox.digest(attest.env.digest + attest.media.digest) === attest.proof);
note("match proof digest(mainSeal+ticket)", sandbox.digest(attest.mainSeal + init.ticket) === attest.proof);

async function run() {
  try {
    const value = await sandbox.attest("main", init);
    note("await attest keys", value && typeof value === "object" ? Object.keys(value) : typeof value);
    if (value && typeof value === "object") {
      note("await attest proof==", value.proof === attest.proof);
      note("await attest mainSeal==", value.mainSeal === attest.mainSeal);
      note("await attest top", Object.keys(value).join(","));
    }
  } catch (error) {
    note("await attest error", error && error.message ? error.message : String(error));
  }
  try {
    const derived = await sandbox.derive("main", init);
    note("await derive", derived && typeof derived === "object" ? Object.keys(derived) : JSON.stringify(derived));
  } catch (error) {
    note("await derive error", error && error.message ? error.message : String(error));
  }
  fs.writeFileSync(path.join(__dirname, "_digest_notes.txt"), notes.join("\n"), "utf8");
  console.log(notes.join("\n"));
}

run();
