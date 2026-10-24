"""Execute anti_automation.js and list the globals it installs."""

from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
source = (root / "static__js__anti_automation.js").read_text(encoding="utf-8")
script = r"""
const calls = [];
function wrap(name) {
  return new Proxy(function () {}, {
    get(target, prop) {
      if (prop === 'prototype') return {};
      return (...args) => { calls.push(name + '.' + String(prop)); return wrap(name); };
    },
    apply(target, thisArg, args) {
      calls.push(name + '()');
      return wrap(name);
    }
  });
}
const windowProxy = new Proxy(global, {
  get(target, prop) {
    if (typeof prop === 'symbol') return target[prop];
    if (prop in target) return target[prop];
    console.log('NEED', String(prop));
    const fn = function () { console.log('CALL', String(prop)); return windowProxy; };
    target[prop] = fn;
    return fn;
  }
});
global.window = windowProxy;
global.document = {
  addEventListener(type) { console.log('DOC', type); },
  cookie: '',
  createElement() { return { style: {}, setAttribute() {}, appendChild() {} }; },
  getElementById() { return null; },
  querySelector() { return null; }
};
global.navigator = { userAgent: 'Mozilla/5.0', webdriver: false };
global.XMLHttpRequest = function () {
  console.log('XHR');
  return { open() {}, setRequestHeader(k, v) { console.log('HDR', k); }, send() {} };
};
global.fetch = () => { console.log('FETCH'); return Promise.resolve({ text: async () => '' }); };
global.jQuery = wrap('jQuery');
global.$ = global.jQuery;
""" + source + r"""
console.log('KEYS', Object.keys(global).filter(k => !['global','console','process','Buffer','URL','URLSearchParams'].includes(k) && !k.startsWith('_')).slice(0, 40).join(','));
console.log('CALLS', calls.slice(0, 30).join(' | '));
"""
out = root / "_sim_anti.js"
out.write_text(script, encoding="utf-8")
node = Path(r"D:\reverse_ENV\tools\node\node.exe")
proc = subprocess.run([str(node), str(out)], cwd=root, capture_output=True, text=True)
print(proc.stdout[-2500:])
print(proc.stderr[-1200:])
print("exit", proc.returncode)
