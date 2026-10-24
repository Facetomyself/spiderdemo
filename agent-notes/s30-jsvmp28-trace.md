# 28 登录态交互 trace

run `rt_20261024005551_a5cd2fe0e2`。RuyiTrace 3.3.0，interactive，preset `jscall-detail`，脚本过滤 `/static/js/`，native detail 名 `WebSocket`。另开 WebSocket 帧日志。没有开 opcode，没有开 WASM 指令。已停止并索引，315753 条。不记录 cookie、token、页面数字或帧明文。

## 页面加载

- `GET /authentication/jsvmp2_challenge` 先 301 再 200
- `GET /static/js/jsvmp2.js` 200
- `GET /authentication/api/jsvmp2_challenge/init/` 200，请求体为空，ALPN 是 h2
- `GET /static/js/authentication/sdk.min.js` 200

内容进程拉过页面脚本。JSCall 按 `WebSocket` 这个名字没有命中构造器记录。

## 套接字

升级路径是 `/ws/`。状态 101，`server=istio-envoy`，响应扩展是 `permessage-deflate`。请求头名有 Origin、Cookie、Sec-WebSocket-Extensions、Sec-Fetch-Dest、Sec-Fetch-Mode、Sec-Fetch-Site、Pragma、Cache-Control。没有 Referer。Cookie 只有两个名字：`sessionid` 和 `ads-baidu`。User-Agent 是 Firefox 155 的公开产品串。

同一会话的帧：文本发送 10、文本接收 10，其中压缩短帧是发送长度 8 共 7 条、接收长度 15 共 7 条，另有压缩文本发送 89、接收 24，压缩二进制发送 108。ping/pong 各 11，close 各 1。没有操作数或栈值。

未压缩 JSON 里能看到方法名 `browsingContext.navigate` 和 `browser.close`。这几条不像分页取数，不拿来当页数据。

## 和本地客户端的差

先前非浏览器客户端在帧之前收到 403。这次浏览器握手已经进入 101。本地 `websockets` 调用把压缩关掉，并且加了这次 101 请求里没有的 Referer。这条 trace 只说明握手边界，不作为提交路径。
