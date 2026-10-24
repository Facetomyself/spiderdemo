# 请求头检测

## 解题思路

题目页 `/sec1/header_check` 的任务是采集 100 页数字并提交总和。共享脚本 `challenge.js` 把挑战类型默认成 `header_check`：首次进入走 init，其余页走分页接口，答案用 JSON 提交。`anti_automation.js` 只在浏览器里限制翻页点击次数，不参与求和。

服务端会看请求头顺序。`httpx` 会先塞入自己的默认头，再在组包时把 `Host` 提前，`Cookie` 由会话追加到末尾。求解时用一份包含这些默认头的显式列表覆盖客户端头，避免 `Headers.update` 把顺序打乱。100 页用 `collect_pages` 异步拉取，并发 4，遇到 429 就退避重试。全部 `page_data` 都是整数，求和后提交。

## 请求链

1. `GET /sec1/header_check` 拿到页面。脚本顺序是 `anti_automation.js`、`login-alert.js`、`challenge.js`、`jquery.js`，页内再定义 `apiGetPageData`。
2. `GET /sec1/api/challenge/init/?challenge_type=header_check`。成功时返回 `page_data`、`total_pages=100`。
3. `GET /sec1/api/challenge/page/{1..100}/?challenge_type=header_check`。每页 10 个整数。页面本身对第 1 页用 init 的数据，对其余页用 jQuery ajax；求解时 init 之后 100 页都走分页接口，保证是同一轮挑战的数字。
4. `POST /sec1/api/challenge/submit/`，body 为 `{"challenge_type":"header_check","answer":<总和>}`。通过条件是响应里 `is_correct=true` 且文案为答案正确，不是 HTTP 200。

## 重点解决思路

分页接口的 `Accept` 跟 jQuery `dataType: "json"` 一致：`application/json, text/javascript, */*; q=0.01`，并带上 `X-Requested-With: XMLHttpRequest` 和 `Sec-Fetch-*`。显式头顺序是 `Connection`、`Accept`、`Accept-Language`、`Accept-Encoding`、`User-Agent`、`X-Requested-With`、`Origin`、`Referer`、`Sec-Fetch-Site`、`Sec-Fetch-Mode`、`Sec-Fetch-Dest`。这四项 httpx 默认头也写在列表里，这样客户端 setter 会先弹出默认项，再按这份列表接上。线上顺序因此是 `Host`、上述列表、会话 `Cookie`；POST 再在末尾补 `Content-Type` 和 `Content-Length`。

不要把登录态写进脚本或结果。`result.json` 只保留提交接口的公开判定字段。
