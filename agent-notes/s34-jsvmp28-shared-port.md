# 28 SharedWorker port

The page trace's `port` / `onmessage` / `start` / `postMessage` sequence is `SharedWorker.port`, after `document.cookie` is set. DOM operations from the start of that turn through the cookie write are `createElement`, `setAttribute`, `documentElement`, `appendChild`, `removeChild`, anchor `href`, `document.all`, `navigator.webdriver`, `TextEncoder.encode`, and the cookie write. No second trace.

A frozen clock and a replayed init keep the sealed token id still. Adding `SharedWorker` with an entangled port, `start`, and `onconnect` makes the page construct the shared worker (`worker-ok` kind `shared`). The token id does not move, and the cleared one-worker close stays `4003`. That host was removed again. Shipped code still deletes `SharedWorker` and delivers with `queueMicrotask`.
