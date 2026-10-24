const fs = require("fs");
const path = require("path");

function decompress(length, resetValue, getNextValue) {
  const dictionary = [];
  let enlargeIn = 4;
  let dictSize = 4;
  let numBits = 3;
  let entry = "";
  const result = [];
  let w;
  let bits, resb, maxpower, power, c;
  const data = { val: getNextValue(0), position: resetValue, index: 1 };
  for (let i = 0; i < 3; i += 1) dictionary[i] = i;
  const readBits = (n) => {
    let bits = 0;
    let maxpower = 2 ** n;
    let power = 1;
    while (power !== maxpower) {
      const resb = data.val & data.position;
      data.position >>= 1;
      if (data.position === 0) {
        data.position = resetValue;
        data.val = getNextValue(data.index++);
      }
      bits |= (resb > 0 ? 1 : 0) * power;
      power <<= 1;
    }
    return bits;
  };
  switch ((c = readBits(2))) {
    case 0:
      c = String.fromCharCode(readBits(8));
      break;
    case 1:
      c = String.fromCharCode(readBits(16));
      break;
    case 2:
      return "";
  }
  dictionary[3] = c;
  w = c;
  result.push(c);
  while (true) {
    if (data.index > length) return "";
    switch ((c = readBits(numBits))) {
      case 0:
        dictionary[dictSize++] = String.fromCharCode(readBits(8));
        c = dictSize - 1;
        enlargeIn--;
        break;
      case 1:
        dictionary[dictSize++] = String.fromCharCode(readBits(16));
        c = dictSize - 1;
        enlargeIn--;
        break;
      case 2:
        return result.join("");
    }
    if (enlargeIn === 0) {
      enlargeIn = 2 ** numBits;
      numBits++;
    }
    if (dictionary[c]) entry = dictionary[c];
    else if (c === dictSize) entry = w + w.charAt(0);
    else return null;
    result.push(entry);
    dictionary[dictSize++] = w + entry.charAt(0);
    enlargeIn--;
    w = entry;
    if (enlargeIn === 0) {
      enlargeIn = 2 ** numBits;
      numBits++;
    }
  }
}

function decompressFromUTF16(compressed) {
  if (compressed == null) return "";
  if (compressed === "") return null;
  return decompress(compressed.length, 16384, (index) => compressed.charCodeAt(index) - 32);
}

const inner = fs.readFileSync(path.join(__dirname, "assets", "inner.js"), "utf8");
const payload = inner.slice(13227, 333517);
const text = decompressFromUTF16(payload);
const out = path.join(__dirname, "assets", "strings.txt");
fs.writeFileSync(out, text == null ? "NULL" : text, "utf8");
const parts = text ? text.split("|") : [];
fs.writeFileSync(
  path.join(__dirname, "_decompress.txt"),
  [
    "payload " + payload.length,
    "textType " + typeof text,
    "textLen " + (text ? text.length : 0),
    "parts " + parts.length,
    "head " + (text ? JSON.stringify(text.slice(0, 200)) : ""),
  ].join("\n"),
  "utf8"
);
