# s18 login capture intent

用户要求再开一轮 trace，范围只做登录。登录不一定带滑块。不要注册，不要代填。

上一轮 `rt_20261010073916_6f589cbd54` 的 `captureWindow=ended` 还在。新的 capture 变成 running 后，这个值会让 `next` 立刻 `ruyitrace_capture_stop`。先清掉。登录仍要人手提交，所以 `humanActionPending` 改回 true。

本轮开启选项按 `references/ruyitrace-capture.md` 的补环境默认，不升级纯算：

- mode `interactive`，profile `dom-observe`，fingerprintMode `baseline`，sensitivity `private-redacted`
- gated true，bootstrap 后再开 gate
- switches 只留 `MOZ_DOM_HTTP_PACKET_TRACE=1` 与 `MOZ_DOM_TRACE_ASYNC=1`
- 不开 JSCall、Opcode、全量事件、WebSocket、`MOZ_DOM_TRACE_BUILTIN_ERROR`、IndexedDB 值捕获、env-probe
- 不用 Chrome UA，不设 `fingerprintMode=none`
- durationSeconds 600，因为这是 wait_human
