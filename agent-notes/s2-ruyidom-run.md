# s2-ruyidom-run

## Runner

- 路径：`landing/env-patch/ruyidom/code.js`
- 只加载 `https://www.spiderdemo.cn/`，`allowNetwork=true`
- 未调用 `login()` / `showRegister()` / `toRegister()`，未写入历史 Cookie，未灌手写响应
- VM/opcode/bytecode/WASM 未打开

## Runs

- 对照用完成的会话：`r56175f00023947f4985b`
- state `completed`，startedAt `2026-10-10T02:48:04.168Z`，finishedAt `2026-10-10T02:48:51.674Z`，elapsedMs 47490，exitCode -1（进程被 `RuyiDOM.exit` 硬结束，stdout JSON 已解析）
- 证据目录：`evidence/web/ruyidom/r56175f00023947f4985b/`
- 更早的 `r33c6ddd673e94518945d` 在导航前因 runner 引用缺失的 `Services.sys.mjs` 失败，已替换实现，不作为目标对照

## localReproduced

不是 browser fact，也不是 serverAccepted。未记录 Cookie、token、密码、验证码图或指纹原值。`credentialSubmit=false`。

| method | url | status | body |
| --- | --- | --- | --- |
| GET | `https://www.spiderdemo.cn/` | 200 | contentLength 不可用；无 JSON 字段。通道只看到这一条目标请求 |

文档侧：`readyState=complete`，location 仍是 `about:blank`（host 空，path `blank`）。navigation timing 的 `responseStatus=0`，`decodedBodySize=0`，`transferSize=0`。`login` / `showRegister` / `toRegister` 都不存在。页面 fetch/XHR 钩子没有装上。无页面 throw。

stderr 有一条运行时模块错误：`Failed to load resource:///modules/sessionstore/SessionStoreFunctions.sys.mjs`。该文件不在这份 runtime 里。另有 4 条内部通道被丢掉，未记入对照。

## 和 browser fact 的差异

browser fact 来自 `rt_20261010022224_c1437434d7`，本刀没有重读 packet body。

- 缺 `GET /admin_I/api/auth/check`（fact：200，71 bytes，字段 `success`, `logged_in`, `message`）
- 缺 `GET /admin_I/api/auth/captcha`（fact：200，37877 bytes，字段 `success`, `message`, `data.y`, `data.captchaId`, `data.sliderImage`, `data.bgImage`）
- 缺首页其余同源 API（challenges、leaderboard、echo-headers、kernel-detect、hardware-detect、client-events）。脚本没跑起来，不是另一次提交
- `GET /` 的 HTTP 200 在通道上出现了，但文档没有换成首页，响应字节长度也没拿到
- 没有多出来的注册或登录 POST

## 阻塞

本刀动作已跑完。认证请求边界未对齐，原因是文档停在 `about:blank`，不是缺账号。未降级 patched Node。
