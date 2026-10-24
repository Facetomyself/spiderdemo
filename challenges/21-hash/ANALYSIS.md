# 摘要算法

## 解题思路

题目要采集 100 页、每页 10 个数字并提交总和。页面脚本 `hash_challenge.js` 没有混淆业务逻辑：除第 1 页的初始化外，分页请求在 axios 拦截器里用当前毫秒时间戳本地算出四种摘要，再交给服务端校验。材料串是 `{页码}_{challenge_type}_{timestamp}`。HMAC-SHA256 的密钥是 `spiderdemo_hmac_secret_2025`；MD5 的材料是该串再接 `spiderdemo_md5_salt_2025`；SHA256 与 SHA3-256 的材料是该串再接 `spiderdemo_sha_salt_2025`。输出都是小写十六进制，与 CryptoJS `toString()` 和 js-sha3 的 `sha3_256` 一致，本地用 `hashlib` / `hmac` 复现。

## 请求链

1. `GET /authentication/api/hash_challenge/init/?challenge_type=hash_challenge` 建立本轮题目，不带摘要。
2. `GET /authentication/api/hash_challenge/page/{n}/?challenge_type=hash_challenge&sign={SHA256}&code={SHA3-256}&t={毫秒时间戳}`。请求头 `X-Request-Token` 放 HMAC-SHA256，`X-Verify-Code` 放 MD5。时间戳必须与摘要材料里的时间戳相同。
3. 100 页用 `collect_pages` 异步采集，并发 4。遇到 HTTP 429 就指数退避后重试。
4. `POST /authentication/api/hash_challenge/submit/`，JSON 体为 `challenge_type` 与全部数字之和 `answer`。

## 重点解决思路

签名不依赖浏览器。`sign` 与 `code` 走查询参数，HMAC 与 MD5 走两个自定义头，四份摘要共用同一次 `Date.now()`。初始化只负责开题，真正的数字以带签名的分页接口为准，第 1 页也要按同样规则再取一次。通过条件是提交响应里 `is_correct` 为真且文案包含「答案正确」，不是仅仅 HTTP 200。
