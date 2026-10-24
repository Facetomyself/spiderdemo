const fs = require("fs");
const path = require("path");

let captured = null;
const orig = String.prototype.split;
String.prototype.split = function (sep, limit) {
  const result = orig.call(this, sep, limit);
  if (sep === "|" && this.length > 1000) captured = result;
  return result;
};

const src = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const expr = src.split(/\r?\n/).slice(2).join("\n");
try {
  eval(expr);
} catch (err) {
  fs.writeFileSync(path.join(__dirname, "_dump_meta.txt"), "ERR " + err.message, "utf8");
}
if (captured) {
  fs.writeFileSync(path.join(__dirname, "assets", "strings.json"), JSON.stringify(captured), "utf8");
  fs.writeFileSync(
    path.join(__dirname, "_dump_meta.txt"),
    "parts " + captured.length + "\nfirst " + JSON.stringify(captured.slice(0, 5)) + "\n",
    "utf8"
  );
}
