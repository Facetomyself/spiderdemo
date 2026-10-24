# 28 目标 WebSocket 请求绑定

阶段仍是 `interpreter-structure` 的 `request-dispatcher` 分支。不重做分型，不改 `jsvmBlocker`，不填 opcode。脚本哈希沿用 s29 / 技术审计：`jsvmp2.js` 与 `sdk.min.js` 和捕获响应一致。`solve.py` 与这两份资源的当前哈希仍等于审计现场样本。`_sandbox.js` 与 `result.json` 在审计取样之后有过写入；本轮把多出来的 fetch 参数长度日志加过又撤掉，没有把沙箱改回审计字节，也没有把 `result.json` 改回旧哈希。当前公开判断仍是连接之后、ready 之前的 `send closed 4003`，不是站点接受。

## 时间线

1. 父进程 pid 58576 依次拿到页面、`anti_automation.js`、`login-alert.js`、`jsvmp2.js`、init GET 200、`sdk.min.js`。两份 VM 脚本哈希与本地资源相同。
2. 页面 DOM / JSCall 在内容进程 pid 52720。Worker 脚本是后加载的 `sdk.min.js`。本地对应关系是页面 realm 跑 `jsvmp2.js`，`WorkerStub` 另开 realm 跑 `sdk.min.js`。
3. 页面把 `INIT` 交给 Worker。本地这条消息带字符串 token。浏览器侧没有一条记录把 52720 的 INIT 和 58576 的目标帧用同一个 id 接上。这是缺口。
4. 目标套接字只计 `url` 为站点主机的帧。第一帧是发送、opcode 2、`payload_len` 108、`rsv1` true、未截断。下一帧是接收、opcode 1、`payload_len` 24、`rsv1` true。其后是发送 89，以及成对的发送 8 / 接收 15，夹着 ping/pong。这条目标连接上没有 close 帧。
5. opcode 8 且长度为 0 的 close 只出现在另一条空 url 连接上，各一发一收。那是控制连接，不计入本题应用帧。
6. 本地既有 stderr（不是本轮新跑）里，过桥的第一发是 `kind=bin`、长度 108、首字节 130。`FakeWS.send` 走了二进制分支。合成实验里跨 realm `ArrayBuffer` 落到字符串分支时，序列化长度是 20。当前这帧不是那条分支。实参的构造器名字仍然没有记下，这是缺口。浏览器 `WebSocket.send` 的 JS 品牌也不在已查看的 JSCall 字典里，这是缺口。
7. 本地失败阶段：升级已经打开，随后发送观察到关闭码 4003，`ready` 没有置位，`is_correct` 仍空。结果文案里的 upgrade-rejected 是旧标签，不表示停在握手。

## 第一处分叉

脚本哈希、init 路径长度不是这处分叉。审计之后的一次单工人测量里，VM 传给 fetch 的参数长度是 74，问号前有斜杠，与已索引的浏览器参数长度相同。不为此做对照实验。

已证实的协议分叉在第一帧之后：浏览器目标连接收到 24 字节的文本帧，并且这次捕获里没有在该连接上关闭；本地在这一次发送上得到 4003，业务 ready 没有出现。两份 108 字节正文是否相同，没有证明。`rsv1` 只说明线上帧压过；不拿压缩线长和明文比，也不凭 4003 断言 token 算法错误。

没有同时具备「浏览器值」和「本地值」的宿主差异可供本轮改一处。跨 realm 字符串化保持为条件性缺陷，不是这次 4003 的已观测转换。

## dispatch_evidence

```json
{
  "request_anchor": {"method": "UPGRADE", "path": "/ws/", "field": "first-binary-frame"},
  "script_sha256": {
    "jsvmp2.js": "0bf700f338edcc3aa8addc45d86be0240efa3f1746cea2f792d00fb4fec70775",
    "sdk.min.js": "bbce993e05762e6c01b032f5203deba96ecdb94a3a7b964343aa143fdc7770a9"
  },
  "callsite": "page jsvmp2.js INIT -> worker sdk.min.js WebSocket; join id between pid 52720 and pid 58576 is absent",
  "vm_boundary": {
    "fetch": "unchanged from s29; opcode table not re-derived",
    "dispatch": "unchanged from s29",
    "state": "unchanged from s29"
  },
  "shape": "table",
  "basis": "runtime-observation",
  "limits": [
    "未把 INIT 与目标帧用同一 id 接上",
    "未记录 send 实参构造器名",
    "未证明两份 108 字节正文相同",
    "未确认 opcode 语义",
    "4003 不是 token 算法错误的证明"
  ]
}
```
