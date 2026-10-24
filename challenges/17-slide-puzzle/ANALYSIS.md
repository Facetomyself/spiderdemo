# 滑动拼图

## 解题思路

这题要采集 100 页、每页 10 个数字，求和后提交。`init` 会带出第 1 页；其余页的接口要求先通过滑动拼图，拿到当次验证 token。token 可以复用，不需要每页做一次验证码。

验证码接口只给一张整图和切割行 `y`。图是 300×184，和页面容器一样宽，所以上半段就是被水平错开的拼图条，不是单独的缺口小图。滑块拖动时，前端把同一张图的 `background-position` 设成 `{distance}px 0`。正的位移会让第 `col` 列显示源图的 `(col - distance) mod width`。本地在切割行上下各取 8 行，按这个方向做循环 SAD，最小值就是应提交的 `distance`。

`ddddocr.slide_match` 用来在下半段里找上半段的一块裁片。全宽条带没有独立缺口，模板匹配经常对不齐，所以只有它的位移接缝代价不差于 SAD 最优值时才采用，否则用 SAD。不调用外部打码。

## 请求链

1. `GET /captcha/api/challenge/init/?challenge_type=slide_puzzle_challenge`  
   初始化。返回 `total_pages` 和第一页 `page_data`。
2. `GET /captcha/api/slide_puzzle_challenge/captcha`  
   返回 `data.bg`（PNG data URL）、`data.y`、`data.captchaId`。
3. `POST /captcha/api/slide_puzzle_challenge/verify`  
   JSON：`distance`、`captchaId`。成功时 `data.token` 用于翻页。
4. `GET /captcha/api/slide_puzzle_challenge/page/{n}/?challenge_type=slide_puzzle_challenge&token=...`  
   100 页用 `collect_pages` 并发拉取，并发 4。HTTP 429 或 5xx 指数退避。token 失效时重新做一次验证码，再取失败的页。
5. `POST /captcha/api/challenge/submit/`  
   JSON：`challenge_type=slide_puzzle_challenge`，`answer` 为全部数字之和。页面内联脚本覆盖了 JS 文件里的另一条 submit 路径；若这条没有判定字段，再试 `/captcha/api/slide_puzzle_challenge/submit/`。

## 重点解决思路

对齐只看切割行两侧，不依赖浏览器拖动。图宽等于容器宽，`distance` 就是图像素，不用再按滑轨 270px 缩放。方向必须和 CSS 一致：向右拖是把上半段源列左移，SAD 用 `(col - shift)`，反了会对不齐。

多页数字不能串行干等。一个 token 可以覆盖全部页，所以先验证一次，再用异步并发把 1 到 `total_pages` 取完。单页必须是 10 个数字，缺页或 token 错误会重试，不会把半套数交上去。

通过标准是提交响应里的 `is_correct=true` 和「答案正确」，不是 HTTP 200。Cookie、token 和验证码原图不写进结果。
