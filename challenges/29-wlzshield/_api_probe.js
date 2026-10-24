const { JSDOM } = require("jsdom");
const dom = new JSDOM("<!doctype html><body></body>", {
  url: "https://www.spiderdemo.cn/captcha/wlzshield_captcha_challenge",
  pretendToBeVisual: true,
  userAgent: "Mozilla/5.0",
});
const window = dom.window;
if (typeof window.fetch !== "function") window.fetch = globalThis.fetch;
const lines = [];
const note = (line) => lines.push(line);
note("fetchRealm " + (window.fetch instanceof window.Function));
note("openSrc " + window.XMLHttpRequest.prototype.open.toString().slice(0, 120).replace(/\s+/g, " "));
note("sendSrc " + window.XMLHttpRequest.prototype.send.toString().slice(0, 120).replace(/\s+/g, " "));
note("xhrSrc " + window.XMLHttpRequest.toString().slice(0, 80).replace(/\s+/g, " "));
note("wsSrc " + window.WebSocket.toString().slice(0, 80).replace(/\s+/g, " "));
note("xhrKeys " + Object.getOwnPropertyNames(window.XMLHttpRequest.prototype).join(","));
try {
  const xhr = new window.XMLHttpRequest();
  note("upload " + typeof xhr.upload);
  note("ready " + xhr.readyState);
  xhr.open("POST", "https://captcha.wangluozhe.com/api/challenge");
  note("afterOpen " + xhr.readyState);
} catch (error) {
  note("xhr " + String(error && error.name) + " " + String(error && error.message).slice(0, 120));
}
try {
  const socket = new window.WebSocket("wss://captcha.wangluozhe.com/ws");
  note("wsState " + socket.readyState);
} catch (error) {
  note("ws " + String(error && error.name) + " " + String(error && error.message).slice(0, 140));
}
try {
  const peer = new window.RTCPeerConnection();
  note("rtc " + typeof peer);
} catch (error) {
  note("rtc " + String(error && error.name) + " " + String(error && error.message).slice(0, 140));
}
const names = ["Request", "Headers", "Response", "AbortController", "ReadableStream", "MessageChannel", "Worker", "Blob", "File", "FormData", "TextEncoder", "TextDecoder", "RTCSessionDescription", "RTCIceCandidate", "MediaStream", "AudioContext", "OfflineAudioContext", "webkitAudioContext", "speechSynthesis", "chrome", "external", "Notification", "Permissions", "WebGLRenderingContext", "CanvasRenderingContext2D"];
note(names.map((name) => name + ":" + typeof window[name]).join(" "));
note("mediaDevices " + typeof (window.navigator.mediaDevices));
require("fs").writeFileSync(require("path").join(__dirname, "_api_probe.txt"), lines.join("\n"));
window.close();
