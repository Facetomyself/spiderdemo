"use strict";

const C2 = 0x27d4eb2d;
const samples = [
  [0x9a6ae684, 0x7358177a],
  [0x9a6ae685, 0x6892e2c5],
  [0x9a6ae686, 0x5dcdae10],
  [0x9a6ae687, 0x53087957],
  [0x9a6ae6f8, 0x91fc307a],
  [0x9a6ae624, 0x7d4bdfde],
  [0x9a6ae625, 0x7286aaa9],
  [0x9a6ae6c5, 0xb745b283],
];
const rotl = (x, r) => ((x << r) | (x >>> ((32 - r) & 31))) >>> 0;
const m1 = Math.imul(1, 0x045d9f3b) >>> 0;

function same(values) {
  return values.every((item) => item === values[0]);
}

for (let r = 0; r < 32; r++) {
  const m2s = samples.map(([x]) => rotl(Math.imul(x, C2) >>> 0, r));
  const ys = samples.map((pair) => pair[1] >>> 0);
  if (same(ys.map((y, i) => (y ^ m2s[i]) >>> 0))) console.log("Y xor rotl(m2)", r);
  if (same(ys.map((y, i) => (y - m2s[i]) >>> 0))) console.log("Y sub rotl(m2)", r);
  if (same(ys.map((y, i) => (m2s[i] - y) >>> 0))) console.log("m2 sub Y", r);
  const mixed = samples.map(([x]) => rotl(((Math.imul(x, C2) >>> 0) ^ m1) >>> 0, r));
  if (same(ys.map((y, i) => (y ^ mixed[i]) >>> 0))) console.log("Y xor rotl(m2^m1)", r);
  const mixedAdd = samples.map(([x]) => rotl(((Math.imul(x, C2) >>> 0) + m1) >>> 0, r));
  if (same(ys.map((y, i) => (y ^ mixedAdd[i]) >>> 0))) console.log("Y xor rotl(m2+m1)", r);
  if (same(ys.map((y, i) => (y - mixedAdd[i]) >>> 0))) console.log("Y sub rotl(m2+m1)", r);
  const withX = samples.map(([x]) => rotl(((Math.imul(x, C2) >>> 0) ^ x) >>> 0, r));
  if (same(ys.map((y, i) => (y ^ withX[i]) >>> 0))) console.log("Y xor rotl(m2^x)", r);
}
for (let s = 1; s < 32; s++) {
  for (let r = 0; r < 32; r++) {
    const vals = samples.map(([x, y]) => {
      const m2 = Math.imul(x, C2) >>> 0;
      const folded = (m2 ^ (m2 >>> s)) >>> 0;
      return (y ^ rotl(folded, r)) >>> 0;
    });
    if (same(vals)) console.log("Y xor rotl(m2^m2>>>s)", s, r, vals[0].toString(16));
    const vals2 = samples.map(([x, y]) => {
      const m2 = Math.imul(x, C2) >>> 0;
      return (y ^ (rotl(m2, r) ^ (x >>> s))) >>> 0;
    });
    if (same(vals2)) console.log("Y xor rotl(m2)^x>>>s", s, r, vals2[0].toString(16));
  }
}
let best = 99;
for (let r = 0; r < 32; r++) {
  const vals = samples.map(([x, y]) => {
    const m2 = Math.imul(x, C2) >>> 0;
    return (y ^ rotl(m2, r)) >>> 0;
  });
  const uniq = new Set(vals).size;
  if (uniq < best) best = uniq;
  if (uniq <= 3) console.log("uniq", uniq, "rot", r, vals.map((item) => item.toString(16)).join(" "));
}
console.log("best uniq", best);
