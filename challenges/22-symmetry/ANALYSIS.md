# 对称加密

## 解题思路

页面任务是把 100 页、每页 10 个数字加总后提交。数字本身是明文 JSON，难点在分页请求的对称加密令牌。`/static/js/obfuscation/symmetry_challenge.js` 用 CryptoJS，明文统一是 `{页码}_symmetry_challenge_{毫秒时间戳}`。

- 请求头 `X-Aes-Token`：AES-128-CTR，密钥 `1234567890123456`，计数器初值 `abcdefghijklmnop`，NoPadding，密文做标准 Base64。
- 请求头 `X-Des-Token`：DES-CBC，密钥 `6f726c64`，IV `01234567`，PKCS7，同样是无 Salted 前缀的 Base64。
- 查询参数 `aes_sign`：同一明文的 AES-256-OFB，密钥 `12345678901234567890123456789012`，IV 仍是 `abcdefghijklmnop`，NoPadding。
- 查询参数 `des_sign`：明文再接 `_param` 后走同一套 DES-CBC。
- 查询参数 `t` 必须和密文里的时间戳是同一次 `Date.now()`。

显式传入 WordArray 密钥时，CryptoJS 的默认 formatter 只编码密文字节，不会加 OpenSSL 的 `Salted__` 头。CTR 只递增计数器最后 4 字节，和 PyCryptodome「12 字节 nonce + 4 字节 initial_value」一致。`anti_automation.js` 里的 `validatePageNavigation` 只拦前端翻页，不改请求头。

## 请求链

1. `GET /authentication/symmetry_challenge?challenge_type=symmetry_challenge` 取页面，再取 `/static/js/obfuscation/symmetry_challenge.js`。
2. `GET /authentication/api/symmetry_challenge/init/?challenge_type=symmetry_challenge`。成功响应里的 `page_data` 就是第 1 页的 10 个数，不再对第 1 页重复签名。
3. 第 2 到 100 页：`GET /authentication/api/symmetry_challenge/page/{n}/?challenge_type=symmetry_challenge&aes_sign=...&des_sign=...&t=...`，并带上两个令牌头。`collect_pages` 并发为 4，遇到 429 指数退避。
4. `POST /authentication/api/symmetry_challenge/submit/`，JSON 为 `challenge_type` 与全部数字之和 `answer`。

登录态走 `modules.runtime.SpiderSession`，不把 Cookie 或口令写入产物。

## 重点解决思路

算法全部在页面脚本里，不需要补环境，也不需要再开浏览器。PyCryptodome 按上面的模式、密钥和 IV 复现四段密文后，先打第 2 页确认 `success` 且 `page_data` 长度为 10，再采满 100 页求和。通过与否只看提交接口：`result.json` 只保留 `success`、`message`、`is_correct` 这几个站点返回的公开字段，其中 `is_correct` 为真。
