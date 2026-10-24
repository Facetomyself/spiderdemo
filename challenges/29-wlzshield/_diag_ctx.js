const vm = require("vm");
const s = {};
vm.createContext(s);
const p = Object.getPrototypeOf(s);
console.log("protoKeys", Object.getOwnPropertyNames(p).join(","));
console.log("inside", vm.runInContext(
  "['Object','Date','JSON','Math','Function','Array'].map(function(n){return n+':'+typeof globalThis[n];}).join(' ')",
  s
));
console.log("chain", vm.runInContext(
  "var o=globalThis,i=0,out=[]; while(o&&i<6){ out.push(String(i)+':'+Object.getOwnPropertyNames(o).length); o=Object.getPrototypeOf(o); i++; } out.join(' | ')",
  s
));
console.log("objectOnProto", vm.runInContext(
  "var d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(globalThis),'Object'); d ? (d.get ? 'getter' : 'data') : 'missing'",
  s
));
console.log("where", vm.runInContext(
  "var o=globalThis,i=0,hit=-1; while(o&&i<6){ if(Object.prototype.hasOwnProperty.call(o,'Object')||Object.getOwnPropertyDescriptor(o,'Object')) hit=i; o=Object.getPrototypeOf(o); i++; } String(hit)",
  s
));
