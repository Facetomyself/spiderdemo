# 圆柱验证码

## 解题思路

这一题要采集 100 页数字再求和。第 1 页由初始化接口直接给出；第 2 页到第 100 页每次都要先过一张圆柱滑块。验证码接口返回打乱的全景 JPEG、初始贴图偏移 `offset`，以及一个 MD5 `order`。响应同时种下 `server_time`。`restore.js` 里的 `aaaa` 在 8 个格子的全排列里找那个排列，使 `MD5(JSON.stringify(perm) + server_time)` 等于 `order`。原图是 1020×370，按 4×2、每块 255×185 切开，`perm[源格] = 目标格`，拼回去就是蜡笔小新全景。

滑块拖动被页面归一化到 0–350，角度是 `x / 350 * 360`。Three.js r155 的 `CylinderGeometry` 把贴图 `u` 绕圆柱展开，正面在 `u = 0`（朝 +Z，相机在 `(0,0,5)`）。正向 `rotation.y` 让正面采样到的 `u` 减小，再加上 `texture.offset.x`。要让图案中心转到画面正中，拖动比例就是 `(offset - 图案中心) mod 1`。图案中心用非背景列的圆周均值，全景被缝切开时也不会把左右两截算成两个物体。

轨迹按这个比例生成约 24 个点，用页面自定义的 base64 字母表编码后，连同 `captcha_id`、页码和容器尺寸 400×240 提交。全部页相加，再交给题目自己的 submit。多页用 `collect_pages`，并发 4；遇到 429 就指数退避。

## 请求链

1. `GET /captcha/api/slide_cylinder_challenge/init/?challenge_type=slide_cylinder_challenge`  
   拿到 `page_data`（第 1 页 10 个整数）和 `total_pages`。
2. 对第 2–100 页，各请求一次  
   `GET /captcha/api/slide_cylinder_challenge/captcha_image/?t=...`  
   读 `bg`、`offset`、`order`，并从该响应的 `server_time` 还原排列。不把这个值写入结果。
3. `POST /captcha/api/slide_cylinder_challenge/page/`  
   JSON 字段：`captcha_id`、`page_num`、`challenge_type`、`track`（自定义 btoa）、`container_width`、`container_height`。成功时 `success=true`，`page_data` 为 10 个整数。
4. `POST /captcha/api/slide_cylinder_challenge/submit/`  
   JSON 字段：`challenge_type`、`answer`（100 页整数之和）。以响应里的 `is_correct` 和消息判定，不以 HTTP 200 为准。

页面脚本顺序是 `slide_cylinder.js`、`restore.js`、`three.min.js`、`crypto-js.min.js`。`validatePageNavigation` 只在浏览器里拦翻页，服务端认的是 init 之后带验证码的 page 接口。

## 重点解决思路

还原排列不能漏掉 `server_time`。哈希原文是 `JSON.stringify` 的紧凑数组直接拼接该值，没有分隔符。8! 可以本地穷举。拼图方向是源格下标映射到目标格，不是反过来。

圆柱正面和拖动方向要一起看。几何上 `u_front = -拖动比例 + offset`。令它等于图案的圆周中心，得到 `拖动比例 = (offset - center) mod 1`。背景是浅黄，按列统计偏离背景的像素，再做圆周平均，避免外包框被零星噪点拉偏，也避免人物骑在全景接缝上时中心被算到图的中间。

`btoa` 的字母表把数字排成 `1-9` 再加 `0`，不是标准 Base64。它的余数字节分支还有越界读。轨迹 JSON 补空格到长度是 3 的倍数，只走三联字节分支，这样和解码端的 `atob` 互逆。轨迹的 `x` 用 0–350 的归一化坐标，最后一点落在目标比例上；容器宽高按样式表里桌面尺寸 400×240 填写。单次验证失败就换一张新图重算，不复用 `captcha_id`。
