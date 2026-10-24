# s24 解题子代理名册

调度停在 `compact_replay_done` / `blocked`。没有升浏览器采集。两道未开放题不派：`control_challenge`、`slide_sum2_challenge`。

通过只认各文件夹 `result.json` 里站点对提交的公开判定。

## 未通过

- 06-jsvmp：`success=false`，`error=Protobuf鉴权验证失败`。`btoa` 输入仍是 32 字节的 `{秒}_jsvmp_secret_key_2025`，JSEncrypt 与 Python PKCS#1 长度都是 172。字段 6 是 `cookiesEnabled` 布尔，不是空 cookie。未重发。`success=false`，`error=Protobuf鉴权验证失败`。init 没有额外键。btoa 仍是 32 字符的 2025 模板。writer 字段 1–9 都在，外层载荷 460，帧总长 465。画布和音频只返回布尔，没有写入。差的 47 字节补不出来，没有重打第 1 页。停在这里。
- 29-wlzshield：`success=false`，`error=验证服务暂时不可用`。magic sign 已本地还原。第 2–100 页需要 `captcha.wangluozhe.com` 签发的 `wsToken`，该主机 challenge/verify 为 502，空 token 与任意非空 token 都不能换到页数据。未交总和。
- 28-jsvmp2：`success=false`。`curl_cffi` chrome 的 HTTP/2 升级仍是 403、空体，`server=istio-envoy`。地址、`Sec-Fetch-*`、题目页前置、Cookie 名 `ads-baidu`、HTTP/1.1 与 HTTP/2 都试过。未进入 101，未提交。停在边缘拒绝，不再改握手参数。

## 已通过

- 01-header-check：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (header_check)`。100 页，`collect_pages` 并发 4。请求头按页面 XHR 顺序显式覆盖，避免 httpx 重排。
- 05-ob1-wall：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (ob1_challenge)`。第 2–100 页，`collect_pages` 并发 4。签名是参数 base64 后拼接路径与时间戳，再异或并双重 base64。
- 03-protobuf：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (protobuf_challenge)`。100 页，`collect_pages` 并发 4。本地魔改 MD4 签时间戳，题型字符 +3，protobuf 按脚本字段组包。
- 04-wasm：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (wasm_challenge)`。100 页，`collect_pages` 并发 4。AES-128-CBC 从 wasm 静态还原，未执行页面反调试脚本。
- 02-ob-encrypt：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (ob_challenge1)`。100 页，`collect_pages` 并发 4。签名是 `timestamp + page` 加固定盐的 MD5。
- 07-css-offset：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (CSS1_challenge)`。100 页，`collect_pages` 并发 4。`left`/`right` 按 15px 槽位还原。
- 13-cap3-math：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap3_challenge)`。第 2–100 页，50 段切片拼回算式。本机 ddddocr 先读，读不出再用本地字体区分运算符。`collect_pages` 并发 4，验证码槽加锁。
- 11-cap1：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap1_challenge)`。第 2–100 页，4 个会话、`collect_pages` 并发 4。点阵模板匹配为主，本机 ddddocr beta 只作补猜。
- 12-cap2-gif：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap2_challenge)`。第 2–100 页，本机 PIL 取 GIF 最长帧后 ddddocr。`collect_pages` 并发 4，验证码槽用同一把锁。
- 20-cap8-click：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap8_challenge)`。100 页，`collect_pages` 并发 4。本机 ddddocr 检测加背景差分和旋转互相关排点击顺序。
- 19-slide-cylinder：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (slide_cylinder_challenge)`。第 2–100 页，`collect_pages` 并发 4。拖动比例是 `(offset - 图案圆周中心) mod 1`，轨迹按页面自定义 base64 提交。
- 18-cap6-dual：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap6_challenge)`。第 2–100 页，`collect_pages` 并发 4。按给定 y 做蒙版匹配，再 `round(x * scale)` 换到 400×240。
- 16-slide-scratch：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (slide_scratch_challenge)`。第 2–100 页，`collect_pages` 并发 4。蒙版模板匹配原图右边界，按 `x * 350 / 750` 换成遮罩位移。
- 17-slide-puzzle：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (slide_puzzle_challenge)`。100 页，`collect_pages` 并发 4。300×184 整图按 y 切开后用接缝 SAD 求水平位移，一个 verify token 复用全部页。
- 15-cap5-slider：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap5_challenge)`。第 2–100 页，透明通道对齐缺口后按封面缩放提交距离。`collect_pages` 并发 4，验证码槽串行。
- 14-cap4：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap4_challenge)`。第 2–100 页本地 ddddocr `slide_match`，`collect_pages` 并发 4。
- 21-hash：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (hash_challenge)`。100 页，`collect_pages` 并发 4。分页摘要为 HMAC-SHA256、MD5、SHA256、SHA3-256。
- 24-cap7-arc：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (cap7_challenge)`。第 2–30 页，`collect_pages` 并发 4。本机 OpenCV 蒙版匹配缺口，轨迹按弧长固定 17 点，`distance` 与 `rotation_angle` 都按 `index/99`。
- 25-panel-console：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (panel_challenge)`。100 页，`collect_pages` 并发 4。控制台密钥是 JSVMP 字符串表常量，按 `value - index - key` 还原，提交格式是密钥加页数字之和。
- 27-press-rotate：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (press_rotate_challenge)`。30 页，`collect_pages` 并发 4。本机 ONNX 朝向加线段方向算角度，WASM 按目标角生成按压证明。
- 26-click-stitch：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (click_stitch_challenge)`。30 页，`collect_pages` 并发 4。2×2 拼图按顺时针接缝本地匹配。
- 31-zerowidth：`success=true`，`答案正确，已记录到平台通关与积分。`。100 页，`collect_pages` 并发 4。U+200B 起的零宽字符当八进制 0–7，每 3 个还原 1 字节，字节是 UTF-8 JSON。
- 30-jsfuck：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (jsfuck_challenge)`。100 页，`collect_pages` 并发 4。AA 位移与 JSFuck 签名本地还原，页数据按位移凯撒解密。
- 23-asymmetric：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (fsymmetry_challenge)`。第 2–100 页，`collect_pages` 并发 4。按 webpack 拦截器做 RSA PKCS#1 与 HMAC-SHA256。
- 22-symmetry：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (symmetry_challenge)`。第 2–100 页，`collect_pages` 并发 4。AES-128-CTR、AES-256-OFB、DES-CBC 按页面 CryptoJS 参数本地复现。
- 09-font-sprites：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (font_sprites_challenge)`。100 页，`collect_pages` 并发 4。第 1 页明文给 10 个字形建模板，下标为 `abs(background-position) // 50`。
- 10-font-svg：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (font_svg_challenge)`。100 页，`collect_pages` 并发 4。SVG 字形聚类成 10 类，本机 ddddocr 多数票加轮廓规则命名。
- 08-font：`is_correct=true`，`答案正确！🎉 恭喜首次通过！ (font_anti_challenge)`。100 页，`collect_pages` 并发 4。字形轮廓哈希对照第 1 页明文还原数字。

## 01–10

- 01-header-check `01a12574-e138-75b1-9214-8d126cd73e46`
- 02-ob-encrypt `01a12574-e138-75b1-9214-8d20baec450f`
- 03-protobuf `01a12574-e138-75b1-9214-8d3295cbe385`
- 04-wasm `01a12574-e138-75b1-9214-8d4ae4f3db73`
- 05-ob1-wall `01a12574-e138-75b1-9214-8d59099a2192`
- 06-jsvmp `01a12574-e138-75b1-9214-8d661964046d`
- 07-css-offset `01a12574-e138-75b1-9214-8d75325130c1`
- 08-font `01a12574-e138-75b1-9214-8d85fe8c22de`
- 09-font-sprites `01a12574-e138-75b1-9214-8d99e90a1e44`
- 10-font-svg `01a12574-e138-75b1-9214-8daceb37ecc5`

## 11–21

- 11-cap1 `01a12575-6944-7501-b2e5-8e3a15c89cf6`
- 12-cap2-gif `01a12575-6944-7501-b2e5-8e4f3057da9f`
- 13-cap3-math `01a12575-6944-7501-b2e5-8e523cfad94f`
- 14-cap4 `01a12575-6944-7501-b2e5-8e60e2e1dc2a`
- 15-cap5-slider `01a12575-6944-7501-b2e5-8e7621ddbeef`
- 16-slide-scratch `01a12575-6944-7501-b2e5-8e819dd0bd84`
- 17-slide-puzzle `01a12575-6944-7501-b2e5-8e9bd00a0903`
- 18-cap6-dual `01a12575-6944-7501-b2e5-8eaf7d9bf3ac`
- 19-slide-cylinder `01a12575-6944-7501-b2e5-8eb80537f7a9`
- 20-cap8-click `01a12575-6944-7501-b2e5-8ece0cf69987`
- 21-hash `01a12575-6944-7501-b2e5-8edad18397a6`

## 22–31

- 22-symmetry `01a12579-6069-7392-b6ae-ad55cd714a23`
- 23-asymmetric `01a12579-6069-7392-b6ae-ad6d437eae06`
- 24-cap7-arc `01a12579-6069-7392-b6ae-ad77157dfdcc`
- 25-panel-console `01a12579-6069-7392-b6ae-ad8e5004107c`
- 26-click-stitch `01a12579-6069-7392-b6ae-ad9f9849c39f`
- 27-press-rotate `01a12579-6069-7392-b6ae-ada9c0aac92a`
- 28-jsvmp2 `01a12579-6069-7392-b6ae-adbc6f09bc24`
- 29-wlzshield `01a12579-6069-7392-b6ae-adc5aede1777`
- 30-jsfuck `01a12579-6069-7392-b6ae-add8453eec75`
- 31-zerowidth `01a12579-6069-7392-b6ae-adeda1fb57fa`
