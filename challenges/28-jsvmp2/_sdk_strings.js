const fs = require("fs");
const path = require("path");
const vm = require("vm");
const source = fs.readFileSync(path.join(__dirname, "assets", "sdk.min.js"), "utf8");
const sandbox = {
  version: "Concurrency V2026 WX:Jsvmp6",
  console: { log() {}, error() {}, warn() {}, info() {} },
  WebSocket: function () {},
  postMessage() {},
  self: {},
  window: {},
  location: { hostname: "www.spiderdemo.cn", host: "www.spiderdemo.cn" },
  navigator: { userAgent: "Mozilla" },
  document: { getElementById() { return null; }, addEventListener() {} },
};
sandbox.self = sandbox;
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(
  `(() => {
    const orig = String.prototype.split;
    String.prototype.split = function (sep, limit) {
      const result = orig.call(this, sep, limit);
      if (sep === "|" && this.length > 1000 && result.length > 500) globalThis.__captured = result;
      return result;
    };
  })();`,
  sandbox
);
try { vm.runInContext(source, sandbox, { timeout: 8000 }); } catch (err) {}
const captured = sandbox.__captured;
if (!captured) {
  fs.writeFileSync(path.join(__dirname, "_sdk_strings_meta.txt"), "none\n");
  process.exit(0);
}
const interesting = [];
const needles = ["aes", "hmac", "sha", "md5", "encrypt", "decrypt", "websocket", "page", "token", "seed", "fingerprint", "opcode", "xor", "base64", "utf", "json", "send", "buffer"];
captured.forEach((item, index) => {
  const low = item.toLowerCase();
  if (needles.some((needle) => low.includes(needle)) && item.length < 80) interesting.push(index + "\t" + item);
});
fs.writeFileSync(path.join(__dirname, "_sdk_hits.txt"), interesting.join("\n"), "utf8");
fs.writeFileSync(path.join(__dirname, "_sdk_strings_meta.txt"), "parts " + captured.length + "\n", "utf8");
