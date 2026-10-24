# protobuf加密

## 解题思路

这一题要采集 100 页、每页 10 个数字，求和后提交。页面脚本不走 JSON 分页，而是把页码、挑战类型、时间戳和签名打成 protobuf，再用魔改 MD4 给时间戳签名。

公开的 `/static/protos/challenge.proto` 把 `challengetype` 放在 2 号字段、`signature` 放在 4 号字段。页面实际加载的 `protobuf_min.js` 把非二进制拉取换成了另一份 schema：2 号字段名叫 `signature`，4 号字段名叫 `challengetype`。脚本又把凯撒后的挑战类型写进 2 号字段，把摘要写进 4 号字段。线上字节仍然是：1 页码、2 加密后的类型、3 毫秒时间戳、4 小写十六进制摘要。响应沿用 `NumberData.value` 列表，不需要再验响应签名。

类型加密是每个字符码点加 3。`protobuf_challenge` 变成 `surwrexibfkdoohqjh`。摘要只覆盖时间戳的十进制字符串，不包含页码。

## 请求链

1. `GET /authentication/api/protobuf_challenge/init/?challenge_type=protobuf_challenge`。只有 `success` 为真才继续。
2. 对页码 1 到 100 并发 `POST /authentication/api/protobuf_challenge/page/{page}/`，`Content-Type: application/x-protobuf`。并发上限 4；遇到 429 就退避重试。每页必须解出 10 个 `value`。
3. 把 100 页的数字相加，`POST /authentication/api/protobuf_challenge/submit/`，JSON 字段是 `challenge_type` 和 `answer`。

通过判据是提交响应里的 `is_correct=true` 和“答案正确”，不是 HTTP 200。

## 重点解决思路

魔改 MD4 仍用 MD4 的初值、F/G/H、三轮移位和字序，但有两处不能按标准 MD4 算：

- 输入不是字符的 ASCII。按位运算会先做 `ToNumber`，所以数字字符变成 0 到 9，非数字变成 0。时间戳全是数字，每个字符就是它的数值。
- 填充末尾 8 字节用 `bits >>> (i * 8)`。JavaScript 的移位次数只保留低 5 位，所以第 4 到 7 个长度字节重复了低 32 位长度，而不是标准 MD4 的高 32 位 0。13 位时间戳的比特长度是 104，于是最后两个字都是 104。

空串的长度是 0，这两处都看不出来，标准 MD4 测试向量仍会通过。用页面同一次请求里的时间戳和摘要对过本地实现后，再按上面的字段顺序组包。分页在 `collect_pages` 里并发拉取，求和后一次提交。
