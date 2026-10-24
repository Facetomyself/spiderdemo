# 字体反爬

## 解题思路

页面要求把 100 页、每页 10 个数字加总后提交。`init` 只给出第 1 页的明文整数，用来对答案做校验。第 1 页到第 100 页的分页接口返回 10 个四位字符串，外加一份 `b64Font`（woff2）。字符串本身是 ASCII `0-9`，但字体的 cmap 把这些码位画成另一套数字轮廓，所以页面上看到的才是真实数字。

十个轮廓在各页之间不变，变的只是码位到轮廓的置换。本地用 fontTools 取出 glyf 轮廓，做稳定哈希，再对照一次光栅化结果把哈希钉到 `0-9`。之后每一页都按当页字体查表，把字符串还原成整数再求和。

## 请求链

1. `SpiderSession` 带登录态发请求，Cookie 不落盘。
2. `GET /font_anti/api/challenge/init/?challenge_type=font_anti_challenge` 初始化，响应里的 `page_data` 是第 1 页明文。
3. `GET /font_anti/api/font_anti_challenge/page/{n}/?challenge_type=font_anti_challenge` 取第 n 页。响应字段是 `page_data`、`b64Font`、`current_page`、`total_pages`。100 页用 `collect_pages` 并发拉取，并发数 4；遇到 429 或 5xx 按 `Retry-After` 或指数退避重试。
4. `POST /font_anti/api/challenge/submit/`，JSON 正文只有 `challenge_type` 和 `answer`（整数和）。通过条件是响应里的 `is_correct` 为真，而不是 HTTP 200。

## 重点解决思路

字形名（`zero`、`one` 这类）跟着码位走，不能当成视觉数字。`RecordingPen` 记录的轮廓坐标在不同页上完全一致，所以哈希可以跨页复用。人工只核对过一次渲染：例如某个轮廓画出来是 `8`，以后凡是这个哈希都读成 `8`。

第 1 页的字体解码必须和第 1 步 init 的明文数组一致，不一致就不提交。分页字符串里的前导零按整数解释。`anti_automation.js` 里的点击计数是浏览器本地限制，请求本身不带签名。
