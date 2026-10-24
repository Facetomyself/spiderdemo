# s8-rerun-document-write

## Runner

- 同一条 `landing/env-patch/ruyidom/code.js`，未改代码
- 安装方式是当前 main 文档的 `document.open` / `document.write` / `document.close`，不是 `new RuyiDOM`
- `allowNetwork=true`，`timeoutSeconds=180`
- 未调用 `login()` / `showRegister()` / `toRegister()`
- 不是 browser fact，也不是 `serverAccepted`。未降级 patched Node

## Run

- `r7429e6a582b7404ea200`
- state `failed`，startedAt `2026-10-10T05:21:11.358Z`，finishedAt `2026-10-10T05:22:00.798Z`，elapsedMs 49440，exitCode -1，timedOut false
- 没有打出 JSON。`result` 为 null
- 证据目录：`evidence/web/ruyidom/r7429e6a582b7404ea200/`

## 观测

location 的 host 和 path 都没有打出。

`GET /admin_I/api/auth/check` 和 `GET /admin_I/api/auth/captcha` 没有出现在 stdout、stderr 或 stderrTail，因此没有 method、status、body 长度或 JSON 字段名。这不是两条都没发出的否定证明。

stderr 结尾是 `Exiting due to channel error.`。页面脚本警告来自 `protobuf_min.js`、`client_signals_collector.js`、`client_signals_autorun.js`、`fingerprint_aggregator.js`，这些不是请求记录。stdout 只有 IndexedDB `console.error`。未记录 Cookie、token、密码、验证码图或字段值。

## 阻塞

去掉嵌套 `new RuyiDOM` 之后，这次仍然在 `print` 前因 channel error 退出。location 和 auth 请求边界都没有打出，不能记成 `boundary-moved` 或 `boundary-unchanged`。未改 `next`、`turnGate`、`goal`、`dispatcher`、`hostProbe`。
