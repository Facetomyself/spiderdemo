const fs = require("fs");
const path = require("path");

const logPath = path.join(__dirname, "_run_restore.log");
fs.writeFileSync(logPath, "start\n");

let code = fs.readFileSync(path.join(__dirname, "restore.js"), "utf8");
const replaced = code.replace("new _0x42d47f(_0x5bea)['FTHhhD']()", "0");
fs.appendFileSync(logPath, "replaced " + (replaced !== code) + "\n");
code = replaced.replace(
  "while(!![]){try{const _0x4a6a03=",
  "while(!![]){try{if(!global.__n)global.__n=0;global.__n++;if(global.__n===1||global.__n%50===0)require('fs').appendFileSync(" +
    JSON.stringify(logPath) +
    ", 'rot '+global.__n+'\\n'); if(global.__n>800){require('fs').appendFileSync(" +
    JSON.stringify(logPath) +
    ", 'giveup\\n'); break;} const _0x4a6a03="
);

global.window = global;
global.document = { createElement() { return { style: {}, getContext() { return {}; } }; } };
global.self = global;

const started = Date.now();
try {
  eval(code);
  fs.appendFileSync(logPath, "eval ok " + (Date.now() - started) + " typeof " + typeof global.aaaa + "\n");
} catch (error) {
  fs.appendFileSync(logPath, "eval error " + (error && error.stack ? error.stack.split("\n").slice(0, 6).join(" | ") : error) + "\n");
}
console.log("done");
