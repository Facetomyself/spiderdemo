# 点选验证码（cap8_challenge）

## 解题思路

题目要采集 100 页、每页 10 个整数并提交总和。第 1 页由初始化接口直接给出。第 2 页到第 100 页每次都要先过一张点选图：图上方是「请依次点击」和 4 个目标字，画面里同一套卡通背景上散落 4 个旋转、变色的字。

点选顺序用本机 `ddddocr` 检测。检测框按纵坐标拆开：横幅里最靠右的 4 个框就是要点的字序。画面里的字有时贴在羊毛或深色被子上，检测框会缺一个，所以另外取 8 张图做像素中值，得到不含字的静态背景。当前图和这张背景做差分，膨胀后恰好得到 4 个笔画连通域。把目标字和这 4 个笔画做成二值图，按 12 度旋转做归一化互相关，4 的全排列里取得分最高的对应关系。若某个差分框里落着 `ddddocr` 检出的字心，点击坐标用检测框中心，否则用笔画质心。

页数据用 `collect_pages` 异步拉取，并发 4。单页验证失败或框数不是 4 就换一张，最多 8 次。遇到 HTTP 429 就指数退避。全部页求和后提交，站点返回 `is_correct=true` 且文案为答案正确。

## 请求链

1. `GET /captcha/api/cap8_challenge/init/?challenge_type=cap8_challenge`  
   初始化挑战。成功时带 `page_data`（第 1 页 10 个数）、`total_pages=100`。
2. `GET /captcha/api/cap8_challenge/click_captcha_image/`  
   返回 `captcha_id`、`background_pic`（PNG 的 base64）和 `image_size`（400×280）。先取 8 张只用来估计背景，不拿去提交。
3. `POST /captcha/api/cap8_challenge/click_page/`  
   JSON 字段：`click_positions_encoded`、`page_num`、`challenge_type`、`captcha_id`。坐标是原图像素上的 4 个 `[x, y]`，`JSON.stringify` 后再做 UTF-8 Base64，与页面脚本里 `btoa(unescape(encodeURIComponent(...)))` 一致。成功时 `page_data` 为该页 10 个数。
4. `POST /captcha/api/cap8_challenge/submit/`  
   JSON 字段：`challenge_type`、`answer`（100 页整数之和）。通过判定看 `success`、`is_correct` 和 `message`。

页面脚本在 `static/js/captcha/cap8_challenge.js`。提示字在图里，接口不另给字符列表，页面还会把提示节点藏起来。

## 重点解决思路

难点不在请求签名，而在点哪四个点。`ddddocr` 检测负责两件事：切开横幅上的目标字，以及在差分框内提供可对齐的点击中心。只靠检测框不够，羊毛和深色区域上的字经常漏检，漏一个就无法和 4 个目标字做一一对应。

背景是同一张卡通，字的位置每次都变。8 张图的中值能把字抹掉，差分阈值大约 30、核大小 7 到 9 时，四个字会收成四个连通域。字是旋转的，所以不能直接比外接框；把横幅黑字和差分笔画都裁成内容、铺成方图再旋转匹配，复杂字也能对上。服务器认的是字心附近的整数坐标，质心或检测框中心都在容差内。

旧的验证码编号在继续拉新图之后仍然有效，所以 4 路并发不会把前一张作废。匹配失败只丢弃这一张并重试，不把验证码图片落盘。
