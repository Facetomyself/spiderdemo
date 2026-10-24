const fs = require("fs");
const path = require("path");
const vm = require("vm");

const dir = __dirname;
const sample = JSON.parse(fs.readFileSync(path.join(dir, "_sample.json"), "utf8"));
const sandbox = { exports: {}, module: { exports: {} }, window: {}, self: {}, console };
vm.runInNewContext(fs.readFileSync(path.join(dir, "crypto-js.min.js"), "utf8"), sandbox);
const CryptoJS = sandbox.module.exports;

function* perms(items) {
  if (items.length <= 1) {
    yield items.slice();
    return;
  }
  for (let i = 0; i < items.length; i++) {
    const rest = items.slice(0, i).concat(items.slice(i + 1));
    for (const tail of perms(rest)) yield [items[i]].concat(tail);
  }
}

const target = sample.order;
let found = 0;
for (const perm of perms([0, 1, 2, 3, 4, 5, 6, 7])) {
  const candidates = {
    joinComma: perm.join(","),
    json: JSON.stringify(perm),
    joinEmpty: perm.join(""),
    array: perm,
  };
  for (const [name, value] of Object.entries(candidates)) {
    let digest;
    try {
      digest = CryptoJS.MD5(value).toString();
    } catch (error) {
      continue;
    }
    if (digest === target) {
      console.log("match", name, perm.join(","));
      found += 1;
    }
  }
  if (found) break;
}
if (!found) console.log("no match");
console.log("target", target);
