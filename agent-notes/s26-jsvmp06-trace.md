# 06-jsvmp 登录态实页 trace

run `rt_20261010143356_3e38a94715`。RuyiTrace 3.3.0，interactive，`jscall-detail`，脚本过滤 `/static/js/js`，native detail `btoa`。已 stop，index 93639 条。不记录 cookie、公钥、UA、密文原值。

## 翻页

点击已经发出请求。`page/1` 到 `page/4`，以及再次 `page/2`，共 5 次 POST，全部 HTTP 400，响应只有 `Protobuf鉴权验证失败`。init 是 200：继续现有挑战，`current_page=1`，`total_pages=100`，`page_data` 10 个数。页面停在第 1 页，是因为翻页接口拒绝，不是点击没发生。

发起栈在 `jsvmp_challenge.js`。请求带登录 cookie 名 `sessionid`。`Content-Type: application/grpc-web+proto`，`X-Protobuf-Request: 1`。

## 真实帧

每一页 `Content-Length: 513`。gRPC-Web：flag 0，payload 508，帧长 513，无尾字节。本地复现是 465。公开记录是 512。

顶层：

- 1 页码，与 URL 里的页号一致
- 2 `jsvmp_challenge`
- 3 base64 172 / raw 128
- 4 10 位时间戳
- 5 指纹消息，长 305

指纹：

- 1 base64 172 / raw 128
- 2 ascii 5
- 3 ascii 9，中间有 `x`
- 4 ascii 2
- 5 varint 32
- 6 varint 1
- 7 ascii 98，4 个逗号，14 个空格
- 8 varint 1
- 9 varint 0

305 比本地指纹 257 多 48，等于字段 7 比本地插件串大约 50 多出来的 48。帧长差也是这 48 字节。

## 加密参数

内容进程 `io_errors=0`。每次翻页同一条链：

- `setPublicKey` 两次，PEM 字符数 311 和 291，DER 都是 171，SHA-256 相同，是同一把 1024 位公钥的两种换行
- `btoa` 输入 32 字符，形状是 10 位秒级时间戳加 `_jsvmp_secret_key_2024`
- `encrypt` 的输入就是这次 `btoa` 的返回（base64 44 / raw 32）。返回先有 hex 256（raw 128），真正写入字段 3 的是随后的 base64 172
- 第二次 `encrypt` 的输入是 80 字符、以 Mozilla 开头的 UA。字段 5.1 就是它的 base64 172
- 字段 4 与 btoa 明文里的时间戳相同
- 该 UA 与这一条 POST 的 HTTP User-Agent 相同

五次 POST 都对得上，没有第二套明文。

## 和本地复现的差别

本地沙箱走的是 `_2025`，帧 465。这次页面实际执行的是 `_2024`，帧 513，多出来的是指纹字段 7。只改年份、不把字段 7 写成这 98 字符，对不上这条浏览器请求。

这条浏览器请求本身也被拒绝。UA、时间戳、公钥和密文都自洽，错误仍是鉴权失败。把本地帧改成同样形状，预期还是这句 400，除非服务端校验的是解密后的另一段明文，或帧以外的条件。响应分不开解密失败和明文不匹配。
