# jsvmp_challenge

## 解题思路

题目页脚本是喵喵盾 JSVMP。静态脚本配上补齐的浏览器对象后，页面自己会组出翻页请求。100 页、每页 10 个数。初始化接口只回第 1 页的明文数组，第 2 页起必须走 protobuf。数字外还有一层 CSS 混合内容，响应类上能看到 `getCssMixedContent` 和 `getCssEncryptedData`，本地解密器要同时拿到混合 HTML 和解密后的字符才能还原。这一步还没有样本，因为翻页接口没有返回 200。

鉴权明文由环境分支决定，不是写死的年份。画布和音频检查都失败时用 `jsvmp_secret_key_2023`，只有画布通过时用 `2022`，两者都通过时用 `2025`。当前补环境走到 2025。明文是 `btoa("{秒级时间戳}_jsvmp_secret_key_2025")`，再用页面里的 1024 位公钥做 PKCS#1 v1.5，结果以 base64 字符串写入请求。指纹里的 UA 另用同一把公钥加密前 80 个字符。

## 请求链

1. `GET /authentication/api/jsvmp_challenge/init/?challenge_type=jsvmp_challenge` 返回 JSON，`total_pages=100`，只带当前页的 `page_data`。
2. `POST /authentication/api/jsvmp_challenge/page/{n}/?challenge_type=jsvmp_challenge`。头是 `Content-Type: application/grpc-web+proto` 和 `X-Protobuf-Request: 1`。体是 gRPC-Web 帧：`0x00` + 4 字节大端长度 + protobuf。
3. protobuf 顶层：1 页码，2 `jsvmp_challenge`，3 鉴权字符串，4 与明文里同一个秒级时间戳，5 嵌套指纹。指纹的 writer 顺序是 UA 密文、语言、分辨率、色深、时区、`cookiesEnabled` 布尔、插件名、`sessionStorage` 布尔、`javaEnabled` 布尔。字段 6 是 `writeBool`，不是空 cookie 字符串。
4. 自定义 `writeInt32` 对负数不循环，`-480` 会写成 varint `32`。页面自己发出的帧就是这个值，时间戳字段和密文里的秒级时间一致。
5. 计划中的提交是 `POST /authentication/api/jsvmp_challenge/submit/?challenge_type=jsvmp_challenge`，JSON 体为 `challenge_type` 和 `answer`。页数据没有拿到，所以没有提交求和。

## 重点解决思路

帧格式已经被服务端接受。缺帧或长度不对时，错误是 `Protobuf解析失败: Failed to parse gRPC-Web request`。字段 3 放进非 UTF-8 时，错误变成 `Failed to parse challenge page request` 的 utf-8 解码失败，说明服务端把字段 3 当字符串读。合法 base64、十六进制、原文 RSA、2022/2023/2025、标准时区 `-480`、以及页面 VM 自己发出的 460 字节帧，都得到同一个 `Protobuf鉴权验证失败`。JSEncrypt 对临时密钥可以解回原文，站点公钥的模数也和 Python 读到的一致，密文小于模数。

因此阻塞点不是帧，也不是年份分支。服务端在 protobuf 解析成功之后拒绝了这枚按页面算法生成的 PKCS#1 令牌，解密失败和明文不匹配共用同一句错误，没法从响应里分开。CSS 还原要等第一页 200 的 `css_mixed_content` 与加密字段。多页采集在 `solve.py` 里走 `collect_pages`，并发 4，遇 429 退避。

对齐只做了一次，帧和年份都没有改。字段 5 的 UA 密文对应明文长度 80，这次 POST 的 User-Agent 长度 111，不相同。cookie 字段不是字符串，长度按字符串计为 0，Cookie 头长度 42，不相同；指纹里没有和 Cookie 头相同的字符串，所以 Cookie 不能改成指纹里的另一套值。重试第 1 页只把 User-Agent 换成指纹里的那一串，换完后长度 80，和明文相同，Cookie 长度仍是 42。对齐后的响应还是 `Protobuf鉴权验证失败`。按这个结果停止，没有采集其余页，也没有提交。

随后只补了 VM 能读到的 cookie，让它和这次 POST 已经带上的会话 Cookie 是同一份。补上之后这份 cookie 非空，长度 42，和 Cookie 头长度相同，两者相同。组包时 VM 没有读取它。字段 5 的 cookie 字段补上之后仍不是字符串，长度仍是 0，非空为 false，指纹里也没有相同字符串。帧格式和年份都没有改。第 1 页状态码仍是 400，错误仍是 `Protobuf鉴权验证失败`。没有采集其余页，也没有提交。

这次只钩了 `btoa` 和页面 `JSEncrypt.encrypt`，并按 writer 调用重标字段，没有改帧，也没有重发。`btoa` 输入长度 32，形态是 `{秒}_jsvmp_secret_key_年份`，年份 2025。加密入口拿到的是这段 btoa 结果，长度 44，时间戳与字段 4 相同。另一路加密输入长度 80，不是 btoa。同一段鉴权明文分别用页面 JSEncrypt 和 Python PKCS#1 v1.5 加密，base64 长度都是 172，原始长度都是 128，两者一致；临时密钥上的解密回环两边都成功。页面函数就是标准 PKCS#1，所以没有改签名实现。上次量到长度 0 的位置是字段 6 的 `writeBool(true)`，名字是 `cookiesEnabled`，不是空 cookie，因此没有把 Cookie 填进去。模板和已失败的页面帧相同，所以没有再打第 1 页。`result.json` 仍是 `success=false`，`error` 为 `Protobuf鉴权验证失败`。

这次只查了一次真实 `GET init`。响应键是 `success`（bool，长度 1）、`message`（str，长度 24）、`challenge_type`（str，长度 15）、`page_data`（10 个 int）、`total_pages`（int，长度 3）、`current_page`（int，长度 1）、`has_passed_before`（bool，长度 1）。没有多出来的键。和 btoa 输入比，`current_page` 的一位数字文本出现在 32 字符模板里，其余键不包含。脚本读了 `success`、`message`、`has_passed_before`、`page_data`，另外还读了响应里没有的 `css_mixed_content`。这些读发生在 btoa 之后，明文仍是原来的 32 字符模板，所以没有把 init 值另写进明文，也没有重打第 1 页。

这次只数了 writer 的字段号、wire 和长度。外层载荷 460，加 5 字节 gRPC 头后总长 465，离 507 还差 47。顶层：1 号 wire 0 长度 1，2 号 wire 2 长度 15，3 号 wire 2 长度 172，4 号 wire 0 长度 5，5 号 wire 2 长度 257。指纹：1 号 172、2 号 5、3 号 9、4 号 2，5 到 6 和 8 到 9 号都是 wire 0 长度 1，7 号 wire 2 长度 50。字段号 1 到 9 没有空号。画布和音频函数返回的是布尔，长度 0，没有进入 writer。插件只读了 `name`，写出的就是这 50 字节，不是被截短的半段。环境补不出新的写入，载荷不会变，所以没有重打第 1 页。状态码仍是之前的 400，`Protobuf鉴权验证失败`。
