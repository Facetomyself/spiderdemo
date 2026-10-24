# 控制台检测

## 解题思路

页面模板仍是 100 页、每页 10 个整数再求和，但站点不收纯数字。提交接口要求「控制台拿到的 key」拼成 `key-数字`，数字必须全是十进制。`key-1` 这种字面量会被格式拒绝；把控制台印出的密钥原样接上 `-` 和数字后，格式才会通过。

`check_devtools_jsvmp.js` 是一层 JSVMP。它用 iframe 的 `srcdoc` 跑第二段同样结构的字节码，轮询尺寸差、`debugger` 耗时、`console.log` 元素 `id` getter、`console.error` 属性 getter、`console.dir`、大数组 `console.log` 耗时和 Promise 错误 getter。这些检测命中后，父脚本打印的不是跳转地址，而是一行固定文本：`SecretKey: ` 加上密钥。只替换 `console.log`、不去读 DevTools 才会读的属性，getter 不触发，这行就不会出现。密钥本身不依赖打开控制台的时刻，它在外层字符串表里。

字符串还原式是 `char = value - index - key`。用首字符 `S` 反推 key，表项解出整行 `SecretKey: wlzshield-check-devtools-v8-spiderdemo-2026-02-09`。冒号后的密钥作为前缀。数字部分按页面脚本，把 init 之后 1 到 `total_pages` 的 `page_data` 全部相加。最终答案是 `密钥-总和`。

## 请求链

1. `GET /authentication/panel_challenge/?challenge_type=panel_challenge` 取页面，脚本为 `/static/js/check_devtools_jsvmp.js` 和 `/static/js/panel_challenge.js`。
2. `GET /authentication/api/panel_challenge/init/?challenge_type=panel_challenge` 建立本次挑战，读 `total_pages`。
3. `GET /authentication/api/panel_challenge/page/{n}/?challenge_type=panel_challenge` 取每一页的 `page_data`。页请求用 `collect_pages` 并发，上限 4；遇到 429 就指数退避。
4. `POST /authentication/api/panel_challenge/submit/`，JSON 只有 `challenge_type=panel_challenge` 和 `answer=密钥-总和`。以返回里的 `is_correct` 或「答案正确」为准。

## 重点解决思路

不要用浏览器自动化去开开发者工具。控制台那一行是字符串表常量，检测逻辑只决定它会不会被打印。本地把 `value - index - key` 解出来即可，密钥前缀是 `SecretKey: `。

页面接口没有额外签名，数字是会话里的明文整数。格式校验把「key」当成控制台密钥本身，不是单词 `key`。所以答案形态是 `wlzshield-check-devtools-v8-spiderdemo-2026-02-09-<全部页数字之和>`。`result.json` 只留站点返回的公开判定字段。
