# WASM挑战

## 解题思路

题目要求把 100 页、每页 10 个数字加总后提交。页面脚本在请求前调用 WASM 导出的 `encrypt_simple(verifyString, timestamp)`，把结果放进 `wasm_auth`。反调试在混淆后的页面脚本里，不执行那段脚本就不会走到 `debugger` 检测。加密本身可以从 `wasm_anti_bg.wasm` 静态还原：可选密钥为空时，从线性内存 `1048872` 拷 16 字节作为 AES-128 密钥，从 `1049775` 拷 16 字节作为 CBC 的 IV。明文是 `wasm_challenge_page_{页码}` 直接拼接秒级时间戳，再做 PKCS7。本地用同一套 AES 生成校验，不启动浏览器。

## 请求链

1. `GET /sec1/api/challenge/init/?challenge_type=wasm_challenge` 打开本题会话。未初始化时分页接口返回 `need_init`。
2. `GET /sec1/api/wasm_challenge/page/{page}/?challenge_type=wasm_challenge&wasm_auth={hex}`，请求头带 `X-WASM-Timestamp` 和 `X-WASM-Page`。时间戳是当前 Unix 秒，`wasm_auth` 是上面的 AES-CBC 密文十六进制。缺校验时返回「wasm验证失败」。
3. 100 页用 `collect_pages` 异步拉取，并发 4。遇到 429 就指数退避后重试。
4. `POST /sec1/api/challenge/submit/`，JSON 为 `challenge_type=wasm_challenge` 和全部数字之和 `answer`。

## 重点解决思路

默认密钥是 ASCII `0123456789abcdef`，默认 IV 是 ASCII `abcdef9876543210`。这两段不是报错字符串，而是 `encrypt_simple` 在可选参数为哨兵值时用 `i64.load` 装进临时缓冲区的 16 字节常量。用已知页码和时间戳解出的明文正好是页标识加时间戳再补 `0x01`，从而确认拼接顺序和 PKCS7。页面上的 `anti_automation.js` / `wasm_challenge.js` 只负责浏览器侧反调试和按钮，HTTP 客户端按还原出的请求头直接取数即可绕过。通过标准是提交响应里的 `is_correct=true` 且消息包含「答案正确」，不是单独的 HTTP 200。
