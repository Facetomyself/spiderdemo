const fs = require("fs");
const path = require("path");

const NativeFunction = Function;
let n = 0;
function dump(label, text) {
  n += 1;
  const file = path.join(__dirname, "assets", label + "-" + n + ".js");
  fs.writeFileSync(file, text, "utf8");
  return file;
}

const Wrapped = function (...args) {
  const body = args.length ? String(args[args.length - 1]) : "";
  if (body.length > 200) dump("fn", body);
  return NativeFunction.apply(this, args);
};
Wrapped.prototype = NativeFunction.prototype;
Object.defineProperty(Wrapped, "name", { value: "Function" });
// Keep original toString so integrity checks still see native-looking source if they check Function.
global.Function = new Proxy(NativeFunction, {
  apply(target, thisArg, args) {
    const body = args.length ? String(args[args.length - 1]) : "";
    if (body.length > 80) {
      const file = dump("fn", body);
      fs.appendFileSync(path.join(__dirname, "_hook.txt"), "apply " + body.length + " " + file + "\n");
    }
    return Reflect.apply(target, thisArg, args);
  },
  construct(target, args) {
    const body = args.length ? String(args[args.length - 1]) : "";
    if (body.length > 80) {
      const file = dump("newfn", body);
      fs.appendFileSync(path.join(__dirname, "_hook.txt"), "new " + body.length + " " + file + "\n");
    }
    return Reflect.construct(target, args);
  },
});

const origEval = global.eval;
global.eval = function (code) {
  const text = String(code);
  if (text.length > 80) {
    const file = dump("eval", text);
    fs.appendFileSync(path.join(__dirname, "_hook.txt"), "eval " + text.length + " " + file + "\n");
  }
  return origEval(code);
};

const src = fs.readFileSync(path.join(__dirname, "assets", "jsvmp2.js"), "utf8");
const expr = src.split(/\r?\n/).slice(2).join("\n");
try {
  const result = origEval(expr);
  fs.appendFileSync(path.join(__dirname, "_hook.txt"), "result " + typeof result + "\n");
} catch (err) {
  fs.appendFileSync(path.join(__dirname, "_hook.txt"), "ERR " + err.name + " " + err.message.split("\n")[0] + "\n");
}
