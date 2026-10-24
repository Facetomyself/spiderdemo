# s11-rerun-flush

## Run

- `r26a50520ee3b4e1da3fb`
- state `failed`，startedAt `2026-10-10T05:31:06.482Z`，finishedAt `2026-10-10T05:31:49.535Z`，elapsedMs 43053，exitCode -1，timedOut false
- 有 channel error。stderr 结尾是 `Exiting due to channel error.`
- stdout.log 477 字节，没有一行 JSON。`result` 为 null
- 同一条 `code.js`，未改代码，未调用 `login` / `showRegister` / `toRegister`
- 不是 browser fact，也不是 `serverAccepted`

## auth

`GET /admin_I/api/auth/check` 和 `GET /admin_I/api/auth/captcha` 都没有出现在 `landing/env-patch/ruyidom/channel-log.jsonl`。因此没有 method、status、responseBytes。这不是进程若继续就一定不会发的证明。

## channel-log

文件在本次启动时创建（`2026-10-10T05:31:06.871Z`），最后写入 `2026-10-10T05:31:19.422Z`，29 行。全部是 `GET`，status 都是 200。其它 path 只记 path 和 status：

- `/`
- `/static/js/main.js`
- `/static/js/register_captcha.js`
- `/static/js/redirect-www.js`
- `/static/js/email_sign.js`
- `/static/js/client_signals_autorun.js`
- `/static/js/client_signals_collector.js`
- `/static/css/register_captcha.css`
- `/static/css/main.css`
- `/static/js/fingerprint_pages/fingerprint_worker_scope.js`
- `/static/js/protobuf_min.js`
- `/static/js/fingerprint_aggregator.js`
- `/static/images/logo-64.png`
- `/static/images/%E9%BB%91%E6%A1%83.png`
- `/static/images/bestproxy.gif`
- `/static/images/spiderbox.png`
- `/static/images/%E5%8F%8D%E5%90%91%E6%8E%A8%E7%90%86.jpg`
- `/static/images/antidebugger.png`
- `/static/images/first.png`
- `/static/images/wechat.jpg`
- `/static/images/%E8%B5%9E%E5%8A%A9%E5%95%861.png`
- `/blog/api/images/wechat_qr_7e04b123.png`
- `/tools/api/echo-headers/`
- `/static/js/fingerprint_scope_sw.js`
- `cdnjs.cloudflare.com` `/ajax/libs/font-awesome/6.0.0/css/all.min.css`
- `cdnjs.cloudflare.com` `/ajax/libs/crypto-js/4.2.0/crypto-js.min.js`
- `cdnjs.cloudflare.com` `/ajax/libs/font-awesome/6.0.0/webfonts/fa-solid-900.woff2`
- `cdnjs.cloudflare.com` `/ajax/libs/font-awesome/6.0.0/webfonts/fa-brands-400.woff2`
- `api.ip.sb` `/geoip`

未记录 Cookie、token、密码、验证码图或字段值。未改 `next`、`turnGate`、`goal`、`dispatcher`、`hostProbe`。
