# 加解密 ob_challenge1

## 解题思路

题目要采集 100 页、每页 10 个数字并提交总和。页码接口本身不加密数字，门槛在查询签名。页面内联脚本把签名写成 `hex_md5(timestamp + page)`，真正的 `hex_md5` 在 `/static/js/obfuscation/ob_challenge1.js`。

该文件是控制流平坦化后的 MD5。摘要前会把固定盐 `\xa3\xac\xa1\xa3fdjf,jkgfkl` 拼到原文后面，字符按 8 位 `charCode` 送进标准 MD5，输出小写十六进制。混淆轮常量写成浏览器环境分支，正常浏览器里这些分支仍等于标准 T 表；错误盐或未加盐会被接口以 400 拒绝。

第 1 页先 `GET /ob/api/challenge/init/?challenge_type=ob_challenge1`。其余页以及第 1 页的复核走带签名的 page 接口。100 页用 `collect_pages` 异步拉取，并发 4，遇到 429 指数退避。全部数字求和后 `POST /ob/api/challenge/submit/`，只有返回 `is_correct: true` 才算通过。

## 请求链

1. `GET /ob/ob_challenge1?challenge_type=ob_challenge1` 读取页面和脚本。
2. `GET /ob/api/challenge/init/?challenge_type=ob_challenge1` 打开本题会话，响应给出 `total_pages=100` 和当前页数字。
3. `GET /ob/api/ob_challenge1/page/{page}/?challenge_type=ob_challenge1&sign={md5}&timestamp={ms}`。`sign = MD5(str(timestamp) + str(page) + salt)`。
4. `POST /ob/api/challenge/submit/`，JSON 正文只有 `challenge_type` 和整数 `answer`。

## 重点解决思路

不要在浏览器里跑混淆函数。盐是脚本里 `hex_md5` 对入参做的那一次字符串追加：四个 Latin-1 字节 `A3 AC A1 A3` 加 ASCII `fdjf,jkgfkl`。Python `hashlib.md5` 与这个字节序列一致，服务端已用错误签名对照过，只有这条摘要能取回 `page_data`。

数字是明文整数，没有二次解密。签名按页独立，时间戳用本地毫秒即可，因此可以并发，不必按页串行。客户端的 `validatePageNavigation` 只拦前端翻页，不参与服务端校验。
