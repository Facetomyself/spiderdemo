# 柳暗花明又一墙

## 解题思路

这题要采集 100 页、每页 10 个数字并提交总和。第 1 页由 init 直接返回，第 2 页起必须带本地算出的 `signature`。页面脚本是控制流平坦化加字符串表旋转的变种混淆，签名函数是 `O0o0O0O0`。

字符串表 `encode_arr` 先整体左移 16 位，再按索引 `atob`。还原后能看到分页参数 `down/5000/iphone/one/paid`、接口路径、分隔符 `@#`，以及一段写死的假 Cookie。真正参与运算的只有假 Cookie 里的 `syncd=-1530`。画布指纹代码画完并不读取像素，只用来在环境检查通过时选密钥前缀 `xyz517cda96efgh`，再拼一个 0 到 9 的随机位。服务端按这 10 个候选密钥解密，固定用 `xyz517cda96efgh0` 即可。

签名步骤：

1. 参数值按字典序拼接，得到 `5000downiphoneonepaid`，先做一次 base64。
2. 拼明文：`base64@#/authentication/api/ob1_challenge/page@#调整时间戳@#3`。调整时间戳是当前毫秒减去 1530，再减去常量 `1661224081041`。
3. 用密钥按 `(i + 10) % key.length` 做逐字符异或。
4. 异或结果按 UTF-8 再 base64，末尾接上当前毫秒时间戳，最后再 base64 一次，作为 `signature`。

`anti_automation.js` 里的翻页点击上限只拦浏览器里的 `validatePageNavigation`，接口本身不看这个计数。

## 请求链

1. `GET /authentication/api/ob1_challenge/init/?challenge_type=ob1_challenge`  
   取第 1 页的 `page_data` 和 `total_pages`。
2. `GET /authentication/api/ob1_challenge/page/{n}/?challenge_type=ob1_challenge&signature=...`  
   `n` 从 2 到 100。请求头带 `X-Requested-With: XMLHttpRequest`。99 页用 `collect_pages` 并发，上限 4。遇到 429 就退避重试，签名失败也换新时间戳重试。
3. `POST /authentication/api/ob1_challenge/submit/`  
   JSON 体只有 `challenge_type` 和全部数字的 `answer`。

## 重点解决思路

平坦化 switch 的入口状态是 16，按每次加法能走完到 `return`。容易看错的有两处。一是参数拼接之后、追加路径和时间戳之前，已经调用了一次编码函数，所以异或的明文以参数的 base64 开头，不是原文。二是 `url.replace(baseURL, "")` 的两个操作数：`baseURL` 是空串，空串替换不会改路径，路径仍留在明文里。

反调试只检查函数源码前 50 个字符里有没有 `deb`，也就是源码里的 `debugger` 还在。本地还原不必跑页面，也不必开调试器。画布、语言和插件检查都不进入签名明文。
