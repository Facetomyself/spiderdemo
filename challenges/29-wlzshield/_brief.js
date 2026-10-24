function isErrorText(value) {
  return /not implemented|undefined|unsupported|TypeError|is not a function|failed|missing|jsdom/i.test(value);
}

function brief(value, depth) {
  if (value == null) return String(value);
  if (typeof value === "boolean" || typeof value === "number") return String(value);
  if (typeof value === "string") return "s" + value.length;
  if (Array.isArray(value)) return "arr" + value.length;
  if (typeof value === "object") {
    if (depth >= 1) return "obj" + Object.keys(value).length;
    return Object.keys(value).slice(0, 24).map((key) => {
      const item = value[key];
      if (typeof item === "boolean" || typeof item === "number" || item == null) return key + "=" + item;
      if (typeof item === "string") {
        if (/^[A-Za-z_-]{1,24}$/.test(item)) return key + "=" + item;
        if (item.length <= 300 && isErrorText(item)) return key + "=" + JSON.stringify(item);
        if (item.length > 40 && (item.includes(" at ") || item.includes("\n"))) return key + "=trace" + item.length;
        return key + ":s" + item.length;
      }
      if (Array.isArray(item)) return key + ":arr" + item.length;
      return key + ":" + typeof item;
    }).join(",");
  }
  return typeof value;
}
module.exports = { brief };
