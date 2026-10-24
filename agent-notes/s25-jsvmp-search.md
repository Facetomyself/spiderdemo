# s25 JSVMP 公开线索

检索日期：2026-10-10。意图：Tutorial / Resource。未登录、未改挑战代码、未打开文章正文。`jsvmp_secret_key_2025` 在原始摘要里没有出现。客户端一次「jsvmp2 + 403」查询被搜索通道拒绝，不把它当成技术结论。Grok grounded search 全部超时；Exa 有一次超时后再查仍有结果。

本地题面只用来对号：`06-jsvmp` = `jsvmp_challenge`（喵喵盾、自定义 protobuf、css）；`28-jsvmp2` = `jsvmp2_challenge`（Jsvmp + websocket）。

## 06-jsvmp

- 来源：https://www.cnblogs.com/jzssuanfa/p/19255690（2025-11-22）、https://x-humanoid.csdn.net/6aa834436186240f423a2591.html、https://www.kuazhi.com/post/716055133.html
  - 目标：06-jsvmp。后两个是同一篇「T6 / 喵喵盾 / protobuf / css 纯算」的转载，不是独立复现。
  - 请求形态：表单和响应都是 protobuf。抓到的 body 是长度 512 的 `Uint8Array`。用 blackboxprotobuf 反解后，换掉时间戳和两段密文再组包。外层前缀摘要写成 `bytes([0, 0, 0, 1, 251]) + protobuf`；同一句还说这个前缀前要加空格，语义不清，不确定。
  - 明文模板：`{unix秒}_jsvmp_secret_key_2024`，再 base64，再 RSA。另一段 RSA 明文是 UA。摘要里的字段草图是 `2=jsvmp_challenge`，`3` 为 token 密文，`4` 为时间戳，`5` 为指纹（含 UA 密文、`zh-CN`、分辨率、色深、插件列表）。字段号只来自被截断的转载摘要，不确定。
  - WebSocket / 403：未提。
  - TLS：未提。Cookie：转载代码把 `cookies` 随 POST 发出，没有点名额外 cookie。
  - 响应：仍是 protobuf。摘要称前 10 字节为空，从第 10 字节起当十六进制看。字段 6 是缺数字的 html/数值，字段 7 是用于还原的 base64 或逗号分隔数字，外面还有 CSS。奇偶修正的减数在摘要里不一致（-2/-4 与 -50/-52 都出现过），不确定。

- 来源：https://www.52pojie.cn/thread-2076005-1-1.html（帖内日期 2025-11-27）
  - 目标：06-jsvmp。与上面不是同一篇文章。
  - 请求形态：protobuf 之外有两段密文。做法是 AST 改函数名后打日志断点，不跑完整 VM。第一段是 RSA(UA)；另一段先 base64 再 RSA。日志里的明文同样是 `{秒时间戳}_jsvmp_secret_key_2024`。RSA 形态像 JSEncrypt，1024 位、指数 65537。公钥材料不收录。
  - WebSocket / 403、TLS、额外 cookie：摘要都没写。

- `jsvmp_secret_key_2025`：本轮原始摘要没有这条字符串。公开 T6 题解用的是 `_2024`。是否已改成 2025，不确定。

## 28-jsvmp2

- 来源：无可用公开题解。
  - 查过 `spiderdemo jsvmp2 websocket`、`/ws/`、`jsvmp2_challenge`、题面句「你真的能连上websocket」。没有对上 `jsvmp2_challenge` 或 `/ws/` 的文章。
  - WebSocket 403 的原因：不确定。搜到的 403 是 gotify、FastAPI 尾斜杠、Spring Origin、Envoy，与 spiderdemo 无关，不能拿来解释这题。
  - TLS、额外 cookie：公开材料未提，不确定。

## 易混，不要套到 06 / 28

- 「Protobuf鉴权验证失败」没有命中 JSVMP 题解。命中的是 T3 `protobuf_challenge`：https://www.52pojie.cn/thread-2076729-1-1.html、https://www.52pojie.cn/thread-2067423-1-1.html、https://2048ai.net/6917065082fbe0098cab9d13.html。那是标准 `challenge.proto` 的 `ChallengeRequest`（页码、编码后的 challenge 类型、毫秒时间戳、魔改哈希 signature），`Content-Type: application/x-protobuf`。不是 06 的自定义 protobuf，也不是 28。
- GitHub `site:github.com spiderdemo jsvmp_challenge`：没有同名仓库或文件。https://github.com/baishuijianjia/jsvmp 是通用栈式 VM，不是这站题解。
- 客户端合成回答里出现过 `blog.csdn.net/qq_53444631/article/details/153781127`，search.py 没有返回这个 URL，不确定。

## 本地文件名（未读正文）

`article` 下文件名含 jsvmp 的只有这些，没有 spiderdemo / 喵喵：

- `D:\reverse_ENV\article\web-reverse\jsvmp-ast-defense-patterns-reference.md`
- `D:\reverse_ENV\article\web-reverse\jsvmp-custom-isa-interpreter-reference.md`
- `D:\reverse_ENV\article\web-reverse\jsvmp-variant-failure-lineage-procedure.md`
- `D:\reverse_ENV\article\web-reverse\jsvmp-variant-failure-lineage.md`
- `D:\reverse_ENV\article\web-reverse\meituan-mtgsig-jsvmp-source-limits-reference.md`

是否适用于 06 或 28，不确定。未读 `article\INDEX.md`。
