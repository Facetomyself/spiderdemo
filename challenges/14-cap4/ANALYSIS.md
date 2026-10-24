# 第二代验证码 cap4_challenge

## 解题思路

这一题要采集 100 页、每页 10 个整数，求和后提交。第 1 页由 init 直接给出。第 2 页到第 100 页每次都要先过一张滑块：背景是带缺口的 webp，滑块是带透明通道的 png。本地用 ddddocr 的 `slide_match` 找缺口，不调用外部打码，也不开浏览器。

容器按桌面样式取 400×240（`border-box`，和脚本里拿不到 DOM 时的默认值一致）。`slide_match` 返回的是拼图中心，而接口要的是滑块 `style.left`，也就是缺口左缘乘上 cover 缩放。算出的距离和 `captcha_id` 一起提交，通过后收下 `page_data`。100 页用 `collect_pages` 异步拉，并发 4。全部加总后提交。

## 请求链

1. `GET /captcha/api/cap4_challenge/init/?challenge_type=cap4_challenge`  
   初始化本题。公开字段里有 `page_data`（第 1 页）、`total_pages=100`、`current_page=1`。
2. `GET /captcha/api/cap4_challenge/captcha_image/`  
   返回 `masked`、`overlay`、`slider_y`、`image_info`（`bg_width`、`bg_height`、`mask_width`、`mask_height`）和一次性 `captcha_id`。原图只留在内存里。
3. `POST /captcha/api/cap4_challenge/page/`  
   JSON 字段：`distance`、`page_num`、`challenge_type`、`captcha_id`、`container_width`、`container_height`。成功时 `page_data` 是 10 个整数。验证失败或验证码失效都必须重新取图，同一个 id 不能再试。
4. `POST /captcha/api/cap4_challenge/submit/`  
   JSON 字段：`challenge_type`、`answer`（100 页整数之和）。站点返回 `is_correct: true` 且文案为答案正确，才算通过。

页面脚本在 `/static/js/captcha/cap4_challenge.js`，容器尺寸在 `/static/css/captcha/cap4_challenge.css`。`anti_automation.js` 里的翻页校验只在浏览器里挡点击，服务端认的是上面这组接口。

## 重点解决思路

缺口对齐发生在原图像素上，提交距离发生在显示像素上。样式是 `object-fit: cover`，脚本用的缩放是 `scale = max(container_w / bg_w, container_h / bg_h)`。本次图是 840×540，容器 400×240，所以 `scale = 400/840`。

ddddocr 边缘匹配给出的 `target_x` / `target_y` 是拼图中心，不是左上角。左缘是 `target_x - mask_width / 2`，拖动距离是 `round(左缘 * scale)`。用纵轴做校验：`target_y` 应接近 `slider_y + mask_height / 2`，偏差超过 12 像素就丢掉这次匹配，改试 `simple_target`，仍不对就换一张图。距离还要落在 `0 .. (bg_width - mask_width) * scale` 里。

验证码 id 一次一用。并发只开到 4，遇到 HTTP 429 就指数退避，不按页顺序空等。`result.json` 只保留提交响应里的公开判定字段。
