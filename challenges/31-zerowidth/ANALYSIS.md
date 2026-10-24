## 解题思路

ZeroWidth 的页面脚本 `spiderking_challenge.js` 是一段 JSVMP，Worker 脚本是 `/static/js/baidu.js`。协议不在明文里，补环境把 init、主页面证明、Worker 证明和每一页的请求体跑出来，再用登录态把 100 页真正打到站点。页上的数字不在 HTML 里，而在接口返回的零宽字符串里。

零宽字符是一套八进制字节编码，不是一位数字一个字符。字母表按这个顺序对应 0 到 7：U+200B、U+200C、U+200D、U+2060、U+2061、U+2062、U+2063、U+2064。每 3 个字符还原 1 个字节，`byte = (d0 << 6) | (d1 << 3) | d2`。字节序列是 UTF-8，解出来再 `JSON.parse`。编码是这条路径的逆操作：`JSON.stringify` 的 UTF-8 字节，每个字节拆成 3 个零宽字符。

页响应解出来之后，数字在 `values`，固定 10 个整数。`page` 是当前页号。100 页的答案是全部 `values` 相加。提交体同样是零宽 JSON，字段只有 `answer` 和 `proof`：`answer` 是这个总和的十进制字符串。

分页参数有两处。路径是 `POST /authentication/api/spiderking_challenge/page/<sid>/`，`<sid>` 来自 init。请求体里的整数 `page` 才是页号，从 1 到 100，不在查询串上。init 给出 `perPage = 10`、`totalPages = 100`。

异步采集在 `solve.py`。`collect_pages(fetch_page, range(1, 101), concurrency=4)` 用 `asyncio.Semaphore(4)` 包住全部页任务，再 `asyncio.gather` 一起跑，不是按页顺序一个一个等。单页 POST 若返回 429，从 0.5 秒起指数退避，上限 8 秒，最多 8 次。汇总之后才把总和交给还活着的补环境去提交。

## 请求链

同一登录态、同一个 `sid` 走完下面五步。除 init 外，正文都是 `Content-Type: text/plain;charset=utf-8` 的零宽 JSON。

1. `GET /authentication/api/spiderking_challenge/init/?cn=<32位十六进制>`。`cn` 是 16 字节随机数。响应给出 `sid`、`ticket`、四种 salt、`perPage` 和 `totalPages`。不带 `cn` 会 400。
2. `POST /authentication/api/spiderking_challenge/attest/main/<sid>/`。正文带环境摘要、`mainSeal`、`proof`、`sid`、`ticket`。环境摘要的 `digest` 覆盖视口、UA 和 `webdriver` 等字段。
3. 页面把状态交给 `/static/js/baidu.js` 这个 SharedWorker。Worker 再 `POST /authentication/api/spiderking_challenge/attest/worker/<sid>/`，正文带 `workerSeal` 和 Worker 作用域报告。这个作用域不能挂 `window`，否则站点直接拒绝。
4. 对 `page = 1..100` 分别 `POST /authentication/api/spiderking_challenge/page/<sid>/`。正文字段是 `page`、`gate`、`mainSeal`、`proof`、`pulse`、`pulseSeal`、`workerSeal`、`sid`、`ticket`。成功时响应解出来是 `{page, success, values:[10个整数]}`。
5. 100 页都回来之后，`POST /authentication/api/spiderking_challenge/submit/<sid>/`。正文解出来是 `{answer, proof}`。站点返回 `success: true`，并且 `message` 写明答案正确，这一题才算过。

## 重点解决思路

页印章和提交 `proof` 都在 VMP 里现算，Python 不重写哈希。`solve.py` 拉起 `_run_vm.js`：Node 的 `vm` 执行页面脚本，并按 SharedWorker 把 `baidu.js` 跑在没有 `window` 的盒子里。页面定时器会反复构造错误的 `Uint8Array` 把进程打满，所以沙箱里的 `setTimeout` / `setInterval` 置空；init 和两段 attest 走的是 Promise，不受这个影响。

翻页函数 `changePage(n)` 会组出该页的零宽正文。铸页阶段不把这 100 个 POST 发给站点，只把正文落到本地，并回一个空的 `values`，让脚本继续翻到下一页。100 份正文齐了以后，脚本停住等答案。

真正取数用的是同一次 `SpiderSession`。`collect_pages` 以 4 路并发回放这 100 份正文，解零宽 JSON，把每页 `values` 相加。429 在 `fetch_page` 里退避。总和写成答案文件后，补环境把它填进 `#answerInput` 并触发提交。这一下提交是真实请求。`result.json` 只保留站点返回里的 `success` 和 `message`。
