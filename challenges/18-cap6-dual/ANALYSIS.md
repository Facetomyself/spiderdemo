# 双滑块验证码

## 解题思路

这一题要采集 100 页、每页 10 个整数，再把全部数字加总提交。第 1 页由初始化接口直接给出，不需要滑块。第 2 页到第 100 页每次都会发一张新的双滑块图：背景是带两个压暗缺口的 webp，两块滑块是带透明通道的 png，接口同时给出每块的纵向位置 `y`。

缺口像素是原图对应区域压暗后的结果，形状和滑块 alpha 一致。在给定的 `y` 上，用带 mask 的归一化相关找出每块滑块画布的左边缘 `x`。页面桌面容器是 400×240，背景按 `object-fit: cover` 缩放，提交距离是 `round(x * scale)`，不是原图像素。100 页数字求和后调用提交接口，以站点返回的 `is_correct` 为准。

## 请求链

1. `GET /captcha/api/cap6_challenge/init/?challenge_type=cap6_challenge`  
   返回 `page_data`（第 1 页）、`total_pages`。一次解题只初始化一次，再次初始化会换一组数字。
2. `GET /captcha/api/cap6_challenge/captcha_image/`  
   `mode=dual` 时字段为 `image_info`（背景 840×540，滑块 120×100）、`overlay`、`sliders[].masked`、`sliders[].y`、`captcha_id`。两张验证码可以同时有效。
3. `POST /captcha/api/cap6_challenge/page/`  
   JSON：`distances`（`slider1`、`slider2`）、`page_num`、`challenge_type`、`captcha_id`、`container_width=400`、`container_height=240`。成功时 `page_data` 是 10 个整数。单滑块兼容体使用 `distance`。
4. `POST /captcha/api/cap6_challenge/submit/`  
   JSON：`challenge_type`、`answer`（100 页整数之和）。

第 2 到第 100 页用 `collect_pages` 异步拉取，并发 4。验证失败就换一张验证码重试；HTTP 429 指数退避。

## 重点解决思路

前端把拖动距离写进滑块的 CSS `left`，`marginLeft` 另放 cover 缩放的 `offsetX`。因此服务端要的是显示坐标里的拖动距离，而不是缺口在原图上的 x。容器按样式表的桌面尺寸 400×240 计算：

`scale = max(400 / bg_width, 240 / bg_height)`

在这组尺寸下宽度先触顶，`offsetX` 为 0，`distance = round(x * scale)`。直接提交原图 x，或把容器尺寸改成原图大小，都会返回「双滑块验证失败」。

`ddddocr.slide_match` 会先丢掉 alpha，再在整张背景上找中心点，两个缺口会互相干扰，对不准。这里改为只在服务端给的 `y` 行带上做匹配：滑块 RGB 作模板，alpha 作 mask，`TM_CCOEFF_NORMED` 的峰值就是画布左边缘。压暗不会破坏纹理，相关峰值通常高于 0.95。
