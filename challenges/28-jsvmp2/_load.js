const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const parts = src.split(/\r?\n/);
const expr = parts.slice(2).join("\n");
const out = [];
out.push("parts " + parts.length);
out.push("exprLen " + expr.length);
out.push("exprHead " + JSON.stringify(expr.slice(0, 120)));
out.push("exprTail " + JSON.stringify(expr.slice(-120)));
out.push("tiny " + typeof eval('Function("a","return a+1")'));
let fn;
try {
  fn = eval(expr);
  out.push("evalType " + typeof fn);
  out.push("evalStr " + String(fn).slice(0, 80));
} catch (err) {
  out.push("evalError " + err.name + " " + err.message);
}
try {
  const wrapped = "(" + expr.replace(/;\s*$/, "") + ")";
  const fn2 = eval(wrapped);
  out.push("wrapType " + typeof fn2);
  out.push("wrapLen " + (fn2 && fn2.length));
  out.push("wrapName " + (fn2 && fn2.name));
} catch (err) {
  out.push("wrapError " + err.name + " " + err.message.slice(0, 300));
}
fs.writeFileSync(path.join(__dirname, "_load.txt"), out.join("\n"), "utf8");
