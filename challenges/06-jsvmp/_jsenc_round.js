const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

globalThis.navigator = { appName: "Netscape", userAgent: "Mozilla/5.0" };
globalThis.window = globalThis;
globalThis.crypto = {
  getRandomValues(buffer) {
    for (let i = 0; i < buffer.length; i += 1) buffer[i] = (i * 17 + 3) & 255;
    return buffer;
  },
};
eval(fs.readFileSync(path.join(__dirname, "assets", "jsencrypt1.js"), "utf8"));

const vm = JSON.parse(fs.readFileSync(path.join(__dirname, "vm-strings.json"), "utf8"));
const sitePem = vm.unique.find((item) => String(item).startsWith("-----BEGIN PUBLIC KEY-----"));
const site = new globalThis.JSEncrypt();
site.setPublicKey(sitePem);
const siteHex = site.getKey().n.toString(16);
console.log("site bits", site.getKey().n.bitLength(), "head", siteHex.slice(0, 8), "tail", siteHex.slice(-8));
const siteToken = site.encrypt(Buffer.from("1791636536_jsvmp_secret_key_2025", "utf8").toString("base64"));
const raw = Buffer.from(siteToken, "base64");
const modulus = Buffer.from(siteHex.length % 2 ? "0" + siteHex : siteHex, "hex");
console.log("siteTokenLen", siteToken ? siteToken.length : 0, "clen", raw.length, "cmp", raw.compare(modulus));

const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 1024 });
const pem = publicKey.export({ type: "spki", format: "pem" });
const engine = new globalThis.JSEncrypt();
engine.setPublicKey(pem);
const plain = "1791635170_jsvmp_secret_key_2025";
const wrapped = Buffer.from(plain, "utf8").toString("base64");
for (const sample of [plain, wrapped]) {
  const token = engine.encrypt(sample);
  let ok = false;
  let error = "";
  try {
    const buf = Buffer.from(token, "base64");
    const back = crypto.privateDecrypt({ key: privateKey, padding: crypto.constants.RSA_PKCS1_PADDING }, buf);
    ok = back.toString("utf8") === sample;
  } catch (err) {
    error = err.message.split("\n")[0];
  }
  console.log("round", sample.length, "token", token ? token.length : 0, "ok", ok, error);
}
