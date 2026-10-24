const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const expr = src.split(/\r?\n/).slice(2).join("\n");
const marker = 'Function("_0xB1D0483","';
if (!expr.startsWith(marker)) throw new Error("marker missing");
const closeAt = expr.lastIndexOf('")({');
if (closeAt < 0) throw new Error("close missing");
let raw = expr.slice(marker.length, closeAt);
// The argument is a JS string literal body with escapes.
const inner = JSON.parse('"' + raw + '"');
const dir = path.join(__dirname, "assets");
fs.writeFileSync(path.join(dir, "inner.js"), inner);
const slices = [
  ["inner_head.js", inner.slice(0, 4000)],
  ["inner_mid.js", inner.slice(500000, 506000)],
  ["inner_tail.js", inner.slice(-4000)],
];
// find shuffle anchor
const anchor = inner.indexOf("new Function(");
fs.writeFileSync(
  path.join(dir, "inner_shuffle.js"),
  inner.slice(Math.max(0, anchor - 1500), anchor + 1500)
);
fs.writeFileSync(
  path.join(__dirname, "_extract.txt"),
  [
    "raw " + raw.length,
    "inner " + inner.length,
    "anchor " + anchor,
    "closeAt " + closeAt,
  ].join("\n")
);
