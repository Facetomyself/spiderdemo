const fs = require("fs");
const path = require("path");
global.window = global;
global.self = global;
global.navigator = { appName: "Netscape", userAgent: "Mozilla/5.0", appVersion: "5.0" };
global.crypto = {
  getRandomValues(buffer) {
    require("crypto").randomFillSync(buffer);
    return buffer;
  },
};
global.addEventListener = () => {};
global.removeEventListener = () => {};
eval(fs.readFileSync(path.join(__dirname, "assets", "jsencrypt1.js"), "utf8"));
const pem = `-----BEGIN PUBLIC KEY-----
        MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCHshK1NixnImx08tq3V6Vjvfwk
        ARCOJbnPMZr4Ogh16ORkC45CFUB+2gu+IN2vjH3oJaY2e/6y0shD2fURMB3urxKE
        3gewRZMm5/T7noAXs4DJTOxJGwAJFHFfd9Zp73vXEcac4DKrvItOkjLx9P5JkA39
        47brgsMObYGdG3HOdwIDAQAB
        -----END PUBLIC KEY-----`;
const stamp = process.argv[2];
const plain = Buffer.from(`${stamp}_jsvmp_secret_key_2023`).toString("base64");
const rsa = new window.JSEncrypt();
rsa.setPublicKey(pem);
const token = rsa.encrypt(plain);
const modulus = rsa.getKey().n.toString(16);
console.error("modlen", modulus.length, "modhead", modulus.slice(0, 8), "modtail", modulus.slice(-8), "tokenlen", token ? token.length : 0);
if (!token) process.exit(2);
process.stdout.write(token);
