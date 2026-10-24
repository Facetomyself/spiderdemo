# 点击拼图验证码

## 解题思路

这题要采集 30 页、每页 10 个数字，再把总和交给站点提交接口。第 1 页由 init 直接给出；第 2 页起页面会挡住数字，先弹出 2×2 点击拼图。拼图图是一张 280×280 的 PNG，四块各 140×140，位置固定，只绕自己的中心顺时针转。每点一次加 90 度，`clickCounts` 就是四块各自的点击次数。本地把图切成四块，枚举每块 0 到 3 次顺时针旋转，用相邻边 4 像素宽的 RGB 差当接缝代价，取得分最低的那组点击。验证通过后响应里有一个可复用的 token，再用它异步把 30 页数字取齐。分页响应里的 `total_pages=100` 是共用字段，实际越界文案是「页面范围错误(1-30)」，以 init 的 `total_pages` 为准。

## 请求链

1. `GET /captcha/api/click_stitch_challenge/init/?challenge_type=click_stitch_challenge` 开启本轮 30 页挑战。
2. `GET /captcha/api/click_stitch_challenge/captcha` 取 `captchaId` 和 `data:image/png;base64` 背景。原图只在内存里解码，不落盘。
3. `POST /captcha/api/click_stitch_challenge/verify`，JSON 体是 `clickCounts` 和 `captchaId`。成功时 `data.token` 用来换分页。
4. `GET /captcha/api/click_stitch_challenge/page/{n}/?challenge_type=click_stitch_challenge&token=...`。30 页用 `collect_pages` 异步采集，并发 4。HTTP 429 指数退避。token 失效就再解一张拼图。
5. `POST /captcha/api/click_stitch_challenge/submit/`，JSON 体为 `challenge_type` 与全部数字之和 `answer`。

## 重点解决思路

方向要跟页面一致：元素上的 `rotate()` 是顺时针，PIL 的 `rotate` 是逆时针，所以点击 `k` 次对应 `rotate(-90*k)`。块序是 DOM 里的左上、右上、左下、右下，和 `background-position` 的四象限一致。接缝只比内部四条边，不依赖外部打码。一次验证发出的 token 不绑死某一页，30 页可以共用；失败再换新验证码。通过条件是提交响应里 `is_correct` 为真或文案包含「答案正确」，不是 HTTP 200。
