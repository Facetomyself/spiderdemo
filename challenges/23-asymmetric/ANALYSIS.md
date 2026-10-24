# 非对称加密

## 解题思路

题目页是 100 页数字求和。业务脚本是 webpack UMD 包 `FSymmetryChallenge`，入口在 `/static/js/obfuscation/fsymmetry_challenge.js`，页面加载后自己拉第 1 页，不依赖首页 `main.js` 里少一个 t 的 `starFsymmetryChallenge`。包内没有 `debugger` 语句；提示里的 debugger 只说明原先可以在本地断点上看 axios 拦截器，静态还原同一段拦截器即可，不必开浏览器。

分页请求走 axios，拦截器在 `/page/{n}/` 上现签。明文是 `{页码}_fsymmetry_challenge_{毫秒时间戳}`。`X-Auth-Key` 是 JSEncrypt 公钥 PKCS#1 v1.5 加密该明文后的 Base64；`X-Signature` 是同一份私钥对明文做 SHA-256 的 PKCS#1 v1.5 签名。查询参数 `data` 是明文加后缀 `_param` 后再做一次公钥加密，`verify` 是密钥 `dsa_secret_key_2025` 的 HMAC-SHA256 十六进制，`t` 是同一个时间戳。名字叫 Dsa，实际不是 DSA 签名。公钥和私钥都在包里，模数一致，本地 `cryptography` 可直接加密和签名。

第 1 页不走这套签名，而是 `GET /init/`，响应里的 `page_data` 就是第 1 页 10 个数。第 2 到第 100 页走签名接口。`anti_automation.js` 里的 `validatePageNavigation` 只拦页面上的快速翻页，不参与接口校验。

## 请求链

1. 登录态由 `SpiderSession` 携带，不把 Cookie 写入结果。
2. `GET /authentication/api/fsymmetry_challenge/init/?challenge_type=fsymmetry_challenge`。成功后读取 `page_data` 与 `total_pages`。
3. 对每一页构造上述 RSA / HMAC 材料，`GET /authentication/api/fsymmetry_challenge/page/{n}/?challenge_type=fsymmetry_challenge&data=&verify=&t=`，并带 `X-Auth-Key`、`X-Signature`。页 2 到页 100 用 `collect_pages`，并发 4；遇到 429 则指数退避。签名接口返回 `encryption_verified` 且 `page_data` 长度为 10 才收下。
4. 第 1 页用 init 的数组。另发一次第 1 页签名请求只做一致性对照，不重复加总。
5. 把 100 页共 1000 个数相加，`POST /authentication/api/fsymmetry_challenge/submit/`，JSON 为 `challenge_type` 与整数 `answer`。以站点返回的 `is_correct` 或「答案正确」为准。

## 重点解决思路

先静态展开 webpack 运行时，定位 axios 请求拦截器，而不是补浏览器环境。JSEncrypt 的 `encrypt` 与 `sign(..., CryptoJS.SHA256, "sha256")` 分别对应 PKCS#1 v1.5 加密和 SHA-256 签名，明文是 ASCII，1024 位密钥够用。HMAC 用 CryptoJS 默认十六进制。init 与分页的分工必须按脚本来：只签第 1 页会丢掉 init 下发的那组数，只靠 init 又拿不到其余 99 页。页级签名各自带当前毫秒时间戳，不能复用同一份密文。
