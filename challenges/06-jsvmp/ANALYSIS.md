# jsvmp_challenge

## 解题思路

这一题要采集 100 页、每页 10 个整数，再把总和交给站点提交接口。初始化接口只给第 1 页的明文数组。第 2 页起走 gRPC-Web protobuf，响应里的数字被拆进一段 CSS 混合 HTML。

`solve.py` 不跑页面 VM。鉴权帧、CSS 还原、翻页和提交都在 Python 里完成。鉴权明文是 `{秒级时间戳}_jsvmp_secret_key_2024`。先做标准 Base64，再用题目页里的 1024 位公钥做 PKCS#1 v1.5，密文再 Base64，放进 protobuf 字段 3。指纹里的 UA 只取前 80 个字符，用同一把公钥加密。时区按页面 `writeInt32` 不循环的写法写成 varint `32`，对应 `-480`。

早先按 VM 分支试过 `2022`、`2023`、`2025`，服务端都回 `Protobuf鉴权验证失败`。现在的入口固定用 `2024`，不再回放 VM 自己发出的那一帧。

## 请求链

1. `GET /authentication/api/jsvmp_challenge/init/?challenge_type=jsvmp_challenge` 返回 JSON。`total_pages=100`，`page_data` 只有第 1 页的 10 个整数。
2. `POST /authentication/api/jsvmp_challenge/page/{n}/?challenge_type=jsvmp_challenge`。头是 `Content-Type: application/grpc-web+proto` 和 `X-Protobuf-Request: 1`。体是 `0x00` + 4 字节大端长度 + protobuf。
3. 顶层字段：1 页码，2 `jsvmp_challenge`，3 鉴权字符串，4 与明文相同的秒级时间戳，5 嵌套指纹。指纹顺序是 UA 密文、`zh-CN`、`1920x1080`、`24`、时区 varint `32`、`cookiesEnabled=1`、插件名、`sessionStorage=1`、`javaEnabled=0`。
4. 响应仍是一条 gRPC-Web 帧。其中一个字符串字段是带空 `context_kw` span 的 HTML，另一个是 10 个两位整数的 Base64。偶数减 50，奇数减 52，得到 0 到 9 的隐藏数字，按 span 出现的顺序填回 HTML，再拆成 10 个整数。
5. 第 1 页必须和第 1 步的 `page_data` 相同。`collect_pages` 以 4 路并发拉完全部 100 页。HTTP 429 从 0.4 秒起指数退避，上限 8 秒，最多 6 次。
6. `POST /authentication/api/jsvmp_challenge/submit/?challenge_type=jsvmp_challenge`，JSON 体是 `challenge_type` 和全部整数之和 `answer`。

## 重点解决思路

缺帧或长度不对时，错误是 `Protobuf解析失败`。字段 3 不是合法字符串时，错误会变成页面请求解析失败。这两种都说明帧格式先被读到了。年份分支和 VM 原帧过不了鉴权，不代表字段布局是错的。

数字不在 protobuf 的整数域里。响应给出的 10 个两位整数是 CSS 隐藏位，不是页上的数。还原公式是 `value - 50 - 2 * (value % 2)`。位数不对或还原后不在 0 到 9，就直接失败，不拿局部和去提交。

`result.json` 只留站点对提交的公开判定：`success=true`，`is_correct=true`，文案是已经提交过该答案。这不是本地算出一个数就算通过。
