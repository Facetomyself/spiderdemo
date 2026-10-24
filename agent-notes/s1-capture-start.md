# s1-ruyitrace-capture-start

## Runtime

- `ruyitrace_runtime_status`: appVersion `3.3.0`, firefox `155.0.1`, buildId `20260913011646`, verification `verified`. 未调用 `runtime_sync`.
- runtime_status 未报告其他正在运行的 capture.

## Capture

- runId: `rt_20261010022224_c1437434d7`
- mode `interactive`, profile `dom-observe`, fingerprintMode `baseline`, sensitivity `private-redacted`, gated `true`, durationSeconds `90`
- 未使用 Chrome UA fpfile，未开 JSCall
- `capture_gate` enabled=true 时 phase 为 `waiting-gate`；随后 `capture_status` 为 state `running`, phase `capturing`, gateEnabled true
- 结束：state `completed`, phase `completed`, finishedAt `2026-10-10T02:24:26.964Z`
- artifactCount 56；indexedRecords 516036；partitions: cookie 4, descriptor 74, domtrace 502896, eval 29, event 19, http_packet 76 records / 26 artifacts, storage 12938
- `runtime/fpfile-audit.json`: complete true, missing 空
- HTTP writer stats: dropped_session/dropped_gate/dropped_full/io_errors 均为 0；skipped 29 且 reason 为 background

## Gates

- runtime-hash pass
- evidence-index pass
- evidence-receipt pass
- integrityReceipt 存在：`evidence/web/ruyitrace/rt_20261010022224_c1437434d7/receipt.json`（artifactId `receipt-0f2fc75b304f`）
- `web_case.py run --plane ruyitrace --run-id rt_20261010022224_c1437434d7` 已成功；`web-case.json` 的 `activeRuns.ruyitrace` 指向该 runId

## 打开过的 URL

- 只导航了 `https://www.spiderdemo.cn/`
- 同一条 capture 的 worker 只导航 `capture_start.url` 一次，没有第二个打开页面的 MCP 工具
- 首页文档里没有指向本站注册页或登录页的 href，因此没有第二页可打开，也没有猜路径

## 注册 / 登录入口

- 首页是同一文档上的表单，不是独立文档
- 按钮「登录」`onclick=login()`；按钮「注册」`onclick=showRegister()`；注册弹层提交「注册」`onclick=toRegister()`
- `loginForm` 输入 id：`username`（placeholder 用户名/邮箱）、`password`
- `registerForm` 输入 id：`regUsername`、`regEmail`、`regPassword`、`regConfirmPassword`
- 另有页内「忘记密码」`showForgotPassword()`，本刀未当注册/登录文档
- 未调用 `login()` / `toRegister()`，未提交注册或登录
- `static/js/main.js` 里 `login()` 含 POST fetch，URL 为混淆字符串查找，本刀不把未发出的 URL 记成已观察请求

## 相关请求边界

查询：`partitions=http_packet`，文档用 path `www.spiderdemo.cn_index_`（1 条，rawOmitted）；认证用 url `https://www.spiderdemo.cn/admin_I/api/auth/`（limit 20，hasMore false）。

| method | url | status | body |
| --- | --- | --- | --- |
| GET | `https://www.spiderdemo.cn/` | 200 | response 29953 bytes, `text/html`；packet raw 超过 inline 上限 |
| GET | `https://www.spiderdemo.cn/admin_I/api/auth/check` | 200 | postBytes 0；response 71 bytes；JSON 字段 `success`, `logged_in`, `message`；initiator `checkLoginStatus` |
| GET | `https://www.spiderdemo.cn/admin_I/api/auth/captcha` | 200 | postBytes 0；response 37877 bytes；JSON 字段 `success`, `message`, `data.y`, `data.captchaId`, `data.sliderImage`, `data.bgImage`；raw 未 inline |

`auth/check` 的 `logged_in` 为 false。未观察到注册或登录 POST。

同一文档加载还发出、但不属于注册/登录提交的同源请求：GET `/admin_I/api/challenges` 200 response 15647（字段 `success`, `challenges`）；GET `/admin_I/api/leaderboard` 200 response 2253（字段 `success`, `leaderboard`，出现两次）；GET `/tools/api/echo-headers/` 200 response 917（字段 `headers`, `ip`）；POST `/tools/api/kernel-detect/` 200 postBytes 55448 response 451（请求字段 `computedStyleKeys`, `engine`, `jsFeaturesKeys`, `referrer`, `userAgentParsed`, `uuid`, `vReport`, `windowFeaturesKeys`）；POST `/tools/api/hardware-detect/` 200 postBytes 1492 response 238（请求字段 `browser`, `hardware`）；POST `/tools/api/client-events/commit/` 200 postBytes 177426 response 154（`application/x-protobuf`）。未记录这些 body 的值。

## 阻塞

无。注册/登录提交链尚未出现，是因为本刀不提交，不是采集失败。
