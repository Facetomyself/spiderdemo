## 解题思路

这一题要把 100 页、每页 10 个数字加总，再交给站点提交接口。第 1 页在初始化接口的 `page_data` 里。后面每一页不走普通分页 HTTP。页面里的 JSVMP 把 `seed`、`wsUrl`、`token` 交给 `/static/js/authentication/sdk.min.js`，由 Worker 调用 `WebSocket` 取数。

脚本外层有版权串校验，校验通过后才会注册 `changePage` 和 `submitAnswer` 并发起初始化请求。Worker 与页面之间的消息是 `INIT`、`FINGERPRINT`、`PAGE`。真正握手成功后，Worker 才会发出二进制帧和按页帧，返回帧仍由同一个 Worker 解密，页面把 10 个数字写进 `#numbersGrid`。

这次先记录 Worker 交给 `WebSocket` 构造器的参数，不再在缺少 url 时改用默认地址。构造器实际只收到一个字符串：主机是 `www.spiderdemo.cn`，路径是 `/ws/`，没有查询键，没有 subprotocol，也没有 Worker 自己附加的头。用这个地址升级仍被拒绝，状态 403，响应体长度为 0，帧还没发出。这不是站点判对。

## 请求链

1. 使用项目账号登录，只在内存里保留会话。
2. `GET /authentication/api/jsvmp2_challenge/init/?challenge_type=jsvmp2_challenge`，拿到总页数和第 1 页数字。初始化里的套接字地址只作为 Worker 的输入，不直接拿来升级。
3. Node 补环境执行页面脚本和 Worker 脚本。Python 只在构造器给出 url 时升级，并带上调用里的 subprotocol 和头。这次调用没有这两项。浏览器会自动带上的会话 Cookie、页面 Cookie 和 Origin 仍然附上。
4. 升级成功后，才把 Worker 发出的二进制帧和文本帧原样写进套接字，并把服务器帧交回 Worker。
5. 用 asyncio 按页请求剩余页，同时在途的页不超过 4。遇到 HTTP 429 则退避重试。
6. 全部页的数字求和后，`POST /authentication/api/jsvmp2_challenge/submit/`，JSON 体为 `challenge_type` 与 `answer`。只有站点判定正确才算通过。

## 重点解决思路

JSVMP 不改 opcode，也不在字节码里打补丁。页面和 Worker 都在 Node `vm` 里当黑盒跑。`WebSocket` 构造器被换成记录调用参数的桩：只向外写出路径、查询键名、参数个数和头名，不把 cookie、token、seed 原值写入文件。`onopen` 仍在当前调用栈退出后触发，这样能看全同步写上的属性。

对照结果是 `argc=1`，唯一参数类型为字符串，`queryKeys=[]`，`protocolCount=0`，`headerKeys=[]`，实例上也没有额外字段。浏览器的升级头和子协议只能来自构造参数，调用之后再赋值改变不了这次握手。因此不再拼接查询串。

站点对这条真实地址的升级直接返回 403。初始化接口和提交接口是通的，提交缺答案时会返回「缺少答案参数」。第 2 页及以后的数字还没有取到，总和也还没有被站点接受。

同一地址又补了浏览器在构造器之外会自动带上的升级头：`Sec-Fetch-Dest: websocket`、`Sec-Fetch-Mode: websocket`、`Sec-Fetch-Site: same-origin`、`Cache-Control: no-cache`、`Pragma: no-cache`、`Accept-Language: zh-CN,zh;q=0.9`。Origin、Referer 和登录会话 Cookie 保持原样，url 和查询串没有改。这次升级状态码仍是 403，body 长度为 0。帧没有发出，站点也没有判定答案。

传输层再换了一次客户端：`curl_cffi`，`impersonate=chrome`，HTTP/1.1。地址仍是 `wss://www.spiderdemo.cn/ws/`，Cookie、Origin、Referer 用登录会话。状态码 403，body 长度为 0。响应头名字是 `server`、`date`、`x-content-type-options`、`connection`、`content-length`。没有进入 101，页数据没有继续采集。

同一条 `curl_cffi` chrome 会话先请求了题目页和 init。题目页没有 `Set-Cookie`。init 的 `Set-Cookie` 名字只有 `sessionid`，登录 jar 里本来就有这个名字，jar 没有新增 Cookie 名。随后用这个 jar 升级，Referer 是题目页完整 URL。状态码仍是 403，body 长度为 0，`server` 值为 `istio-envoy`。没有进入 101。

现有补环境在 `new WebSocket` 之前通过 `document.cookie` 写出的名字只有 `ads-baidu`。这个值只放在内存里，和登录会话一起用 `curl_cffi` chrome 再升级了一次，地址未改。状态码 403，body 长度为 0。没有进入 101。

同一地址再用 `curl_cffi` chrome 的 `http_version=v2` 做了一次 HTTP/2 升级。状态码 403，body 长度为 0，`server` 为 `istio-envoy`。没有进入 101。
