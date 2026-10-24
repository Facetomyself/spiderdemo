# 第二代验证码（随机滑块）

## 解题思路

这题要采集 100 页、每页 10 个整数，再把全部数字加总提交。第 1 页由 init 直接给出。第 2 页起每次换页都要先过一次随机滑块：缺口的纵坐标 `slider_y` 随图变化，横坐标不给。

背景是 840×540 的 webp，滑块是 143×143 的透明 PNG。缺口像素的 alpha 是 100，滑块不透明像素的 alpha 是 255，两边像素集合一一对应。把滑块不透明像素平移到缺口上，平移量就是蒙版左上角在原图上的坐标；这个纵坐标必须等于接口给的 `slider_y`。

页面容器是 400×240，背景用 `object-fit: cover`。脚本按 `scale = max(400 / bg_width, 240 / bg_height)` 把原图横坐标换成拖动距离，再连同容器宽高提交。`ddddocr.slide_match` 对这块透明拼图的置信度只有约 0.27，纵坐标也对不上 `slider_y`，所以不用它的坐标。

100 页收齐后，把总和 POST 到 submit。站点返回 `is_correct: true` 且文案为「答案正确」才算通过。

## 请求链

1. `GET /captcha/api/cap5_challenge/init/?challenge_type=cap5_challenge`  
   返回 `page_data`（第 1 页）、`total_pages`、`success`。已有挑战时是「继续现有挑战」，不要重复初始化。
2. 对第 2 到第 100 页：`GET /captcha/api/cap5_challenge/captcha_image/`  
   字段是 `masked`、`overlay`、`image_info`、`slider_y`。没有独立验证码 id，答案存在当前会话里。
3. `POST /captcha/api/cap5_challenge/page/`  
   JSON：`distance`、`page_num`、`challenge_type`、`container_width=400`、`container_height=240`。成功时 `page_data` 为 10 个整数。
4. `POST /captcha/api/cap5_challenge/submit/`  
   JSON：`challenge_type`、`answer`（整数总和）。判定看 `success`、`is_correct`、`message`。

页面调度用 `collect_pages`，并发上限 4。验证码槽是会话级的，取图和提交必须串行，否则后一次取图会冲掉前一次答案。遇到 429 就退避后重试。

## 重点解决思路

距离不是缺口内缘，也不是原图像素。滑块图左侧有透明边，接口要的是蒙版画布左边缘在原图上的 x，再按封面缩放四舍五入：

`distance = round(origin_x * max(400 / bg_width, 240 / bg_height))`

`origin_x = min(缺口 x) - min(滑块不透明 x)`。对齐后用像素集合核对，不一致就丢弃这张图重取。`slider_y` 只用来确认纵坐标，不参与提交。直接提交原图 x，或把容器改成原图尺寸，服务器都回「滑块验证失败」。
