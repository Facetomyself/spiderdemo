# Gif动态验证码

## 解题思路

这一题要采集 100 页、每页 10 个整数，求和后提交。第 1 页由 init 直接给出，不需要验证码。第 2 页到第 100 页每次都要先解一张 4 位 GIF 验证码，再把识别结果和页码一起交给 page 接口。

验证码接口返回两段 base64 GIF：`F` 是页面默认展示的假图，只有一帧；`T` 才是点击后出现的真实验证码，约 10 帧。干扰帧里也会出现完整的 4 位字符，不能逐帧投票。有效帧是停留时间最长的那一帧（约 300ms，其余约 100ms）。用 PIL 取出这一帧，交给本机 ddddocr。结果只保留小写字母和数字，长度必须是 4。识别不稳定时放大一倍，或去掉高色差干扰线后再认一次。认不出或站点返回「验证码错误」就重新要图，不沿用旧图。

同一登录会话里只保存最后一张验证码。先取图再取下一张，前一个答案会失效，所以取图、识别、提交必须串成一个临界区。页采集仍走 `collect_pages`，并发上限 4；临界区用锁保证不会同时存在两张未消费的验证码。遇到 429 或「频繁」按指数退避，上限 20 秒。

100 页到齐后把全部整数相加，整数答案提交到 submit。站点返回 `is_correct: true` 且消息含「答案正确」才算通过。

## 请求链

1. `GET /captcha/cap2_challenge?challenge_type=cap2_challenge`  
   页面脚本是 `/static/js/captcha/cap2_challenge.js`。page 调用写在页面内联脚本里。

2. `GET /captcha/api/cap2_challenge/init/?challenge_type=cap2_challenge`  
   成功时给出 `page_data`（第 1 页）、`total_pages`、`current_page`、`message`、`has_passed_before`。只初始化一次，避免把已发出的页数据换成新题。

3. 每一页 `2..total_pages`：  
   `GET /captcha/api/cap2_challenge/captcha_image/?t=<毫秒时间戳>`  
   JSON 只有 `T` 和 `F`。  
   `POST /captcha/api/cap2_challenge/page/`  
   JSON 体：`captcha_input`、`page_num`、`challenge_type`。  
   成功时 `success=true`，`page_data` 为 10 个整数。

4. `POST /captcha/api/cap2_challenge/submit/`  
   JSON 体：`challenge_type`、`answer`（整数和）。  
   判定字段是 `success`、`is_correct`、`message`。

页面上的「先点击图片」只改前端的 `hasClickedCaptcha`，服务端不要求这个点击。`anti_automation.js` 里的 `validatePageNavigation` 也是浏览器侧检查；求和必须覆盖每一页，但验证码槽不要求按页号顺序访问。

## 重点解决思路

真假图不能混用。`F` 也能被 OCR 读成 4 位，但是假码。`T` 里短帧同样能读出 4 位，也是干扰。只认停留最长的帧，并用最暗像素打破并列。

会话只有一个验证码槽。探测里连续取两张图时，只有后一张的识别结果能换到 `page_data`；两张并行时两页都会「验证码错误」。因此锁包住整段「取图 → 本地识别 → POST」，失败就在同一把锁里换新图。并发 4 只限制同时挂起的页任务，不会叠两张未提交的 GIF。

ddddocr 对清晰长帧多数一次命中。长度不是 4 就丢弃这次图片，不把残缺字符串提交。提交后若返回「验证码错误」，同一页换图重试，最多 8 次。429 不换新的并发，在锁内退避后再继续。

答案是 init 的第 1 页加上第 2 到第 100 页 `page_data` 的整数和。`result.json` 只保留提交响应里的公开判定：`success`、`message`、`is_correct`。
