const fs = require("fs");
const path = require("path");
const readline = require("readline");
const vm = require("vm");

const sdk = fs.readFileSync(path.join(__dirname, "assets", "sdk.min.js"), "utf8");
const realm = {
  console: { log() {}, error() {}, warn() {}, info() {}, debug() {} },
  setTimeout() { return 0; },
  clearTimeout() {},
  setInterval() { return 0; },
  clearInterval() {},
  TextEncoder,
  TextDecoder,
  URL,
  URLSearchParams,
  crypto: globalThis.crypto,
  postMessage() {},
  addEventListener() {},
  removeEventListener() {},
  importScripts() {},
  close() {},
};
realm.self = realm;
realm.globalThis = realm;
realm.window = realm;
vm.createContext(realm);
vm.runInContext(sdk, realm, { timeout: 8000 });

function asBytes(value) {
  if (value instanceof Uint8Array) return value;
  return Uint8Array.from(value);
}

function reply(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}

function handle(message) {
  if (message.op === "token") {
    const seed = String(message.seed);
    const body = realm.spiderEncrypt(seed + "|" + String(message.ts) + "|jsvmp2_challenge", "spiderdemo_ws_jv2");
    const token = seed.slice(0, 8) + "." + body;
    const frame = Buffer.from(asBytes(realm.msgpackEncode({ cmd: 100, token })));
    reply({ op: "token", tokenLen: token.length, frameLen: frame.length, token, frame: frame.toString("base64") });
    return;
  }
  if (message.op === "seal") {
    const packed = asBytes(realm.msgpackEncode(message.value));
    const text = realm.spiderEncryptBytes(packed, String(message.key));
    reply({ op: "seal", text, textLen: String(text).length, plainLen: packed.length });
    return;
  }
  if (message.op === "open") {
    const packed = asBytes(realm.spiderDecryptBytes(String(message.text), String(message.key)));
    reply({ op: "open", value: realm.msgpackDecode(packed), plainLen: packed.length });
    return;
  }
  reply({ op: "error", name: "unknown" });
}

if (process.argv[2] === "--check") {
  const key = "seedseedseedseedseedseedseedseed";
  const fp = Array(22).fill(1).concat([28, 0, 5, 24, 1920, 1080, 100, 1313108922, -1708469978, 1, -1, 0, 0, 1, 0, 1]);
  const sealed = realm.spiderEncryptBytes(asBytes(realm.msgpackEncode({ cmd: 99, fp })), key);
  const opened = realm.msgpackDecode(asBytes(realm.spiderDecryptBytes(sealed, key)));
  const tokenBody = realm.spiderEncrypt("abcdefghijklmnopqrstuvwxyz012345|1710000000000|jsvmp2_challenge", "spiderdemo_ws_jv2");
  const ok = sealed.length === 89 && opened.cmd === 99 && opened.fp.length === 38 && tokenBody.length === 85;
  if (!ok) process.exit(1);
  process.stdout.write("codec-check ok\n");
  process.exit(0);
}

reply({ op: "ready" });
const lines = readline.createInterface({ input: process.stdin });
lines.on("line", (line) => {
  let message;
  try {
    message = JSON.parse(line);
  } catch (err) {
    reply({ op: "error", name: "json" });
    return;
  }
  try {
    handle(message);
  } catch (err) {
    reply({ op: "error", name: err.name, message: String(err.message).split("\n")[0].slice(0, 160) });
  }
});
