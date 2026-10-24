const vm = require("vm");
const arr = vm.runInNewContext("new ArrayBuffer(4)");
const view = vm.runInNewContext("new Uint8Array([1,2,3,4])");
const branch = x => x instanceof ArrayBuffer ? "ArrayBuffer" : ArrayBuffer.isView(x) ? "view" : "StringFallback";
console.log(JSON.stringify({crossRealmArrayBuffer:{branch:branch(arr),actualLength:arr.byteLength,serializedLength:Buffer.from(String(arr),"utf8").length},crossRealmView:{branch:branch(view),actualLength:view.byteLength}}));
