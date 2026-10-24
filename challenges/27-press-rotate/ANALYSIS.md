# 按压旋转验证码

## 解题思路

这题采集 30 页、每页 10 个整数，总和交给站点提交接口。第 1 页不需要验证码。第 2 页到第 30 页先取一张圆形图，本地算出把它转正的顺时针角度，再用页面同款 WASM 按这个角度生成按压证明，验证通过后立刻用返回的 token 取该页。30 页用 `collect_pages` 异步采集，并发 4；HTTP 429 按 0.8 秒起指数退避。角度只在本机用 ONNX 朝向分类和线段方向计算，验证码原图、证明和 token 不落盘。

## 请求链

1. `GET /captcha/api/press_rotate_challenge/init/?challenge_type=press_rotate_challenge` 开启本轮，确认 30 页。
2. `GET /captcha/api/press_rotate_challenge/page/1/?challenge_type=press_rotate_challenge` 直接拿第 1 页的 10 个整数。
3. `GET /captcha/api/press_rotate_challenge/captcha` 取 `captchaId`、圆形 PNG 和一段给 WASM `check_data` 的十六进制参数。
4. `POST /captcha/api/press_rotate_challenge/verify`，JSON 为 `timestamp`、`angle`、`captchaId`、`data`。`data` 是 WASM `getResult(User-Agent)` 的十六进制。成功后马上请求对应页。
5. `GET /captcha/api/press_rotate_challenge/page/{n}/?challenge_type=press_rotate_challenge&token=...`。token 只用于刚解开的那一页，失败就换一张新验证码。
6. `POST /captcha/api/press_rotate_challenge/submit/`，JSON 为 `challenge_type` 与 30 页总和 `answer`。

## 重点解决思路

页面把 CSS `rotate(angle deg)` 交给 WASM：`set_t` 记下按下时的毫秒，`tick(dt)` 按服务端下发的加速再匀速模型积分，松手时的 `angle` 和 `getResult` 一起提交。`timestamp` 必须等于按下时刻加上按住毫秒，并且接近提交瞬间的本地时钟，所以积分在本地瞬间算完，再把提交时刻对齐到这个时间戳之后几十毫秒。请求头里的 User-Agent 和传给 `getResult` 的字符串是同一个。

转正角度不是 `duration` 时刻的积分角。圆形图先过本机四分类朝向网络，得到大约 90 度一档的正立象限。圆内长线段足够强时，用线段方向的四重轴把角度收到该象限里，地平线和桥面这类图能收到 1 度左右。线段很弱的人像或插画，则顺时针扫一圈，取分类器认为正立的那一段角度的中心；峰很窄时直接取峰值。PIL 的正角度是逆时针，搜索和提交都用顺时针，与 CSS 一致。站点判定 `is_correct` 为真才算通过。
