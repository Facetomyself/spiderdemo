const fs = require("fs");
const s = fs.readFileSync(__dirname + "/assets/sdk.min.js", "utf8");
const re = /wss?:[^'"\s]{0,80}|\/ws[^'"\s]{0,40}/g;
const hits = s.match(re) || [];
console.log("hits", hits.length);
console.log(hits.slice(0, 30).join("\n"));
