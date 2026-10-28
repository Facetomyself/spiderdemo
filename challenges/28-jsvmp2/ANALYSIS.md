# jsvmp2_challenge

## 解题思路

这一题要采集 100 页、每页 10 个整数，再把总和交给站点提交接口。第 1 页在初始化 JSON 的 `page_data` 里。后面的页不走普通分页 HTTP。页面 JSVMP 把 `seed` 交给 `/static/js/authentication/sdk.min.js`，由 Worker 走 `WebSocket` 取数。

`solve.py` 不改 opcode。Node 只跑 `_sdk_codec.js`，负责发 token、开二进制帧、解密回包和封装页命令。Python 握有登录会话、套接字和翻页调度。加解密不在 Python 里重写。

## 请求链

1. 登录态只留在内存里的 `SpiderSession`。
2. `GET /authentication/api/jsvmp2_challenge/init/?challenge_type=jsvmp2_challenge`。这里拿到总页数、第 1 页数字和 `seed`。HTTP 429 退避后重试。
3. codec 用 `seed` 和毫秒时间戳发出 `token`。然后连接 `wss://www.spiderdemo.cn/ws/`。客户端是 `websockets`，UA 用 Firefox 155，开启 permessage-deflate，地址上没有查询串。第一次把 cookie 名 `ads-baidu` 设成这次 token；升级不是 403 时再去掉这个名字重试。
4. 升级成功后先发送 codec 给出的二进制帧，收回的文本用 `seed` 解开，再发送 `{cmd:99, fp}` 的密封文本。这一步完成之前不去要页数据。
5. 每一页在同一条套接字上发送 `{cmd:4, page, ts}`。回包仍由 codec 解开，按 `page-N` 对上等待中的页。`collect_pages` 默认 4 路并发，可用 `SPIDER_WORKERS` 调到 1 到 8。单页等待 20 秒。
6. 全部页求和后，`POST /authentication/api/jsvmp2_challenge/submit/`，JSON 体是 `challenge_type` 和十进制 `answer`。

## 重点解决思路

只拿构造器里的 `wss://www.spiderdemo.cn/ws/` 去升级，不带 codec 帧，服务端直接 403，响应体长度为 0，帧发不出去。补 `Sec-Fetch-*`、改 `curl_cffi` 的 HTTP/1.1 或 HTTP/2，结果仍是 403。所以入口不再停在这条裸升级上。

现在的升级带 permessage-deflate，并且先发出 codec 的二进制帧，再发指纹命令。握手在 ready 之前被关掉时，错误写成 `send closed` 加关闭码，不再记成 HTTP 403。页命令的密文只经过 SDK codec。Python 只检查解出来的页号和 10 个整数。

`result.json` 只留站点对提交的公开判定：`success=true`，`is_correct=true`，文案是已经提交过该答案。本地凑出一个和，或者升级返回 101，都不单独算通过。
