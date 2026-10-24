# s15 capture restart

## Runtime

- appVersion `3.3.0`，verification `verified`。未做 runtime_sync。
- 旧 run `rt_20261010071226_f62dc0d172` 已是 completed。磁盘上没有别的 capture 处于 running。

## Capture

- runId: `rt_20261010073916_6f589cbd54`
- state `running`，phase `capturing`，gateEnabled true
- mode `interactive`，profile `dom-observe`，fingerprintMode `baseline`，durationSeconds `600`
- 未开 JSCall，未使用 Chrome UA
- 首页 URL: `https://www.spiderdemo.cn/`
- 浏览器停在首页。未再导航，未点击注册或登录，未填写任何账号。
- 未调用 capture_stop。capture 保持 running，留给用户自己注册和登录。
- `web_case.py run --plane ruyitrace` 已把 `activeRuns.ruyitrace` 指向本 run。未调用 `web_case.py next`。
