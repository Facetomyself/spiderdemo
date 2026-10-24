# s5-rerun-host-baseline

## Runner

- 同一条 `landing/env-patch/ruyidom/code.js`，未改代码，未新增宿主字段
- `allowNetwork=true`，`timeoutSeconds=180`
- 未调用 `login()` / `showRegister()` / `toRegister()`，未提交注册或登录
- 未降级 patched Node。不是 browser fact，也不是 `serverAccepted`

## Run

- `r656200b927284d80866d`
- state `failed`，startedAt `2026-10-10T03:14:11.105Z`，finishedAt `2026-10-10T03:15:02.493Z`，elapsedMs 51388，exitCode -1，timedOut false
- `result` 为 null。stdout 没有可解析 JSON
- 证据目录：`evidence/web/ruyidom/r656200b927284d80866d/`
- 不重用上一轮 `r56175f00023947f4985b`

## 观测

location 没有打出。不能说它仍是 `about:blank`，也不能说它已经离开。`document.host` / `path`、navigation timing、`login` / `showRegister` / `toRegister` 都没有本次字段。

`GET /admin_I/api/auth/check` 和 `GET /admin_I/api/auth/captcha` 没有出现在 stdout、stderr 或 `run.json` 的 stderrTail。结构化请求表也没有打出，所以这不是「两条都没发出」的否定证明，只是本次没有 method/url/status/body 长度或 JSON 字段名。

stderr 里新出现的是页面脚本警告，不是请求记录，没有 status，也没有 body 长度：

- `https://www.spiderdemo.cn/static/js/protobuf_min.js`
- `https://www.spiderdemo.cn/static/js/client_signals_collector.js`
- `https://www.spiderdemo.cn/static/js/client_signals_autorun.js`
- `https://www.spiderdemo.cn/static/js/fingerprint_aggregator.js`

另外有两次 worker 调度诊断，没有脚本 URL。结尾是 `Exiting due to channel error.`。stdout 只有两条 IndexedDB `console.error`，没有页面 JSON。未记录 Cookie、token、密码、验证码图或字段值。

## 和上一轮结构化结果

上一轮 `r56175f00023947f4985b` 打出了 JSON：通道只有 `GET /` 200，location 停在 `about:blank`，两条 auth 都缺。这一轮没有可对照的 JSON。`SessionStoreFunctions.sys.mjs` 这次没有出现在 stderrTail。页面脚本警告说明文档至少解析并执行到这些脚本，但不能代替 location 或请求边界。

## 阻塞

重跑已经结束，但 location 和 auth 请求边界都没有打出。不能把这次记成 `boundary-moved` 或 `boundary-unchanged`。未改 `next`、`turnGate`、`goal`、`dispatcher`、`hostProbe`。
