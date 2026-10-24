# 28 fingerprint order

The existing page trace reads `navigator.plugins`, canvas `getContext`, `fillText`, and `toDataURL` on `jsvmp2.js` after the depth-8 cookie write and the first `postMessage`. That first turn also touches `port`, `onmessage`, and `start` immediately before `postMessage`. The canvas calls are a later depth-2 turn. The worker thread posts once, then encodes, then `send`s. No second trace.

Local one-worker runs, with the cleared `SPIDER_*` set, still close `4003`. At the sealed `send`, plugins and canvas stay unread: the page has posted `INIT` (`seed` 32, `wsUrl` 27, `token` 94) and the worker has answered `INIT_OK`. `setTimeout` and `requestAnimationFrame` counts stay 0 through that send, so the canvas turn is not an already-queued macrotask.

Deferring the wire emit until after the worker's `WS_CONNECTED` does run the traced calls before the write: plugins 2, getContext 2, fillText 1, toDataURL 1. The page then posts `FINGERPRINT`. The bytes passed to `send` were copied before that post, and the close stays `4003`. Delivering that post synchronously never reaches `WS_CONNECTED`, because the earlier `send` already closes the process. Both timing edits were removed. Shipped delivery is `queueMicrotask(deliver)` and an immediate `send`.

`document.all` inside the realm stays falsy (`typeof` undefined, loose-equal null). That is not the fork before plugins.
