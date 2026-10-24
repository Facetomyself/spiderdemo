# 28-jsvmp2 技术卡点审计

日期：2026-10-24。范围：只读静态分析与既存采集对照；未执行题目 JS，未发送站点请求，未修改业务脚本、资产或 dispatcher facts。

## 结论

当前可核实的失败已经是 WebSocket 建立后、ready 前的应用层关闭 4003，而非早期的握手 403。代码仍把这个阶段统称为 “upgrade rejected”，旧 ANALYSIS.md 又停留于 403，容易让恢复会话读错失败层。它不能证明 Grok 当前也一直误追 403：流程代理掌握的后续会话摘要需与本报告分开判断。

解释器分型不是空白：既存 s29 已完成两台栈 VM 的取指、映射表和状态识别，本拍重新核对了资产 hash 和对应代码。剩余缺口是目标 Worker 首帧 / 后续页帧与 VM、INIT、宿主读取之间的因果绑定，以及同一冻结输入的 browser/local parity；不是拿更多 switch/case 数来补结构。

不能把 4003 单独解释成 token 错误、指纹错误、压缩错误或 VM opcode 错误；现有关闭结果没有保留可归因的服务端 close reason 和完整首个分歧记录。

## F1：当前错误阶段被包装层误分类（事实，高置信度）

- `challenges/28-jsvmp2/result.json:3-4` 为 `send closed 4003`。
- `solve.py:249-250`：websockets.connect 返回成功后才设置 holder.ws。
- `solve.py:280-287`：建立接收任务并向桥发 opened，然后标记 opened。
- `solve.py:404-416`：只有 ws 存在且 opened=true，才调用发送并取得 send closed 的异常码。
- `solve.py:427-434`：ready 前发生的任何 failed 都被重包装为 websocket upgrade rejected。
- 因此最早可确认失败边界是“已连接、桥已 opened，发送时发现对端已关闭，尚未达到 ready”；不能断言恰是哪一帧导致关闭，更不能用此字符串证明仍未完成 101。
- `ANALYSIS.md:7,24-34` 记录早期 403，没有反映当前 4003，属于历史笔记滞后。

## F2：interpreter-structure 的结构部分已经完成（事实，高置信度）

既存文档：`agent-notes/s29-jsvmp28-interpreter.md:7-60`。该文 `:64,102` 也明确真实缺口是请求 / 参数入口。本拍未另填 opcode 表。

原资产都在第 3 行，以下 offset 为 Python 解码后的 0-based 字符索引，不是 UTF-8 byte offset：

| 资产 | 取指循环 offset | Int16 表 offset | 观察 |
| --- | ---: | ---: | --- |
| assets/jsvmp2.js | 441216 | 511099 | code[pc] → XOR rolling byte → 256 槽 Int16 映射 → 嵌套比较；栈数组与独立 sp |
| assets/sdk.min.js | 320864 | 315562 | 同形取指、滚动量、映射表、栈式分发 |

页面符号：pc=_0xBBE396，栈=_0x0B11B11，sp=_0xCCBD44，rolling=_0x61F90C3；Worker 符号：pc=_0x44D0E3，code=_0xB8C31E6，栈=_0x6FCECA2，sp=_0xF2BA079，rolling=_0x0A9D62A，映射表=_0xEC323A。滚动量更新是 (old XOR decoded)+2*(old AND decoded) 再 &255，即模 256 加法。

映射初始化先建立 256 槽、填 -1，再把排列位置写入内部序号；这个静态初始化上界不代表运行覆盖率。外层和式 switch/with 是混淆包装；内层取指才是 VM。页面和 Worker 各有 generator 包装，未据此推断调用约定。

缺少：参数的 VM entry / pc、确定操作数宽度、逐条语义、操作数 / 栈值 runtime trace、同一次 INIT 与请求 fixture、首个差异的边界。因此不能进入 opcode 验收。

## F3：不是已经证明的资产版本变化（事实，高置信度）

将 RuyiTrace 已停止采集中两个 HTTP 200 的 responseBody.text 逐字节 hash 与本地资产对照：

- jsvmp2.js：`0bf700f338edcc3aa8addc45d86be0240efa3f1746cea2f792d00fb4fec70775`
- sdk.min.js：`bbce993e05762e6c01b032f5203deba96ecdb94a3a7b964343aa143fdc7770a9`

两份都与 s29 的锚完全一致，responseBody.truncated=false。采集路径：
`evidence/web/ruyitrace/rt_20261024005551_a5cd2fe0e2/raw/http_packet/000008_GET_200_www.spiderdemo.cn_static_js_jsvmp2.js_b1a3943b_pid58576_400000015.http_packet.json:1`
`.../000013_GET_200_www.spiderdemo.cn_static_js_authentication_sdk.min.js_427eae38_pid58576_40000001a.http_packet.json:1`

这只证明被冻结响应资产相同，不排除运行时字节码生成或宿主行为差异；但现有材料不能据此改成 variant-failure 或以“源码不同”为由进入 chaos-vm-instrument。

## F4：浏览器成功握手是真实的，但帧日志混有控制通道（事实，高置信度）

`raw/websocket_handshake.jsonl:2`：目标 /ws/，101，协商 permessage-deflate。`s30-jsvmp28-trace.md:16` 对这点记录正确。

同一 raw/websocket_frames.jsonl：
- `:3-4`：url 为空的 BiDi 导航命令及回复。
- `:5-43`：url 标成目标 host 的业务帧，共 send binary 1、send text 8、recv text 8、recv ping 11、send pong 11。
- `:44-47`：url 为空的 browser.close 及回复、close 双向帧。
- 因而全文件的 text send/recv 各 10 和 close 各 1 不都是题目流量；不能据此声称目标握手后主动 close 或已经发生全部分页请求。
- 目标 send 二进制 108、后续文本 89 与短帧的压缩长度都不是解压后业务协议长度，不可直接拿来和本地 emit 中明文长度判断算法相同。
- 本拍离线解压探针没有成功建立明确的 masking/compression 解释，未使用任何试探所得明文，未把原始载荷写入本报告。

## F5：宿主 bridge 存在一个可复现的条件性二进制类型缺陷（缺陷事实；与 4003 关系未证明）

`_sandbox.js:1022-1026` 把 SDK 放在独立 Node vm context；`:295-303` 的 FakeWS.send 在外部 realm 用 `data instanceof ArrayBuffer` 判断 ArrayBuffer，失败后仅检查 ArrayBuffer.isView，最后退化为 String(data)。

本拍自建无目标代码 fixture：跨 realm 的 new ArrayBuffer(4) 不满足外部 instanceof ArrayBuffer，也不是 view，落到 StringFallback，把 4 字节变成 20 字节；跨 realm Uint8Array 仍正确进入 view 分支。结果见 `cross-realm-result.json`，exit 0。

这证明桥接层在该输入类型上错误，不能证明当前 SDK 实际发送的是该类型。如果运行时给 FakeWS 的参数是 typed array，该缺陷不触发。应只记录 “SDK send 实参品牌未观测” 这个证据缺口，不能把它直接宣布为 4003 根因。

其他宿主差异也还没有 parity：Worker 使用主线程 navigator 并暴露 window (`_sandbox.js:993,1021`)，postMessage 同步直传对象而无 structured clone (`:1004-1011`)；这些是模型简化，未经目标读取对照不能各自宣判为本题根因。

## F6：与第 6 题并非可互抄的 VM（事实）

`06-jsvmp/assets/jsvmp_challenge.js:3` 及 `agent-notes/s28-jsvmp06-interpreter.md` 显示不同架构：Unicode 混淆标识符，整数槽 code[pc++]，嵌套大小比较直接状态分发，5 参数解释器含作用域、调用栈、帧；大量代码槽不属于单字节值。SHA256：
`64e6e4698722383fbe24ef2a58c554bc20616c7c32a52694d746cd1895394fa8`。

28 是 XOR + 模 256 rolling 解码、Int16 映射加比较分发。两题同为栈 VM、同站点，不足以断言同一保护器、ISA、鉴权协议或可共用补丁。06 的 protobuf 鉴权失败也不证明 28 WebSocket 首帧具有同根因。更准确结论是“没有已证明的同源性，结构上存在实质差别”。

## 本拍回程建议

本拍完成 interpreter-structure 的静态复核，不改 dispatcher facts。唯一有证据支持的下一步是仍在同一阶段进入已命名子分支 `request-dispatcher.md` 的 S1：冻结并绑定目标 Worker 首次业务发送的 INIT、脚本 hash、时间线、send 实参品牌及 request/frame 边界，先做 browser/local 首差定位。

不要再次分型；也不要把全量拆 opcode 当成关闭 4003 的默认路线。四个替代 blocker 的状态：
- host-primitive：尚未锁定某个被 VM 调用、影响目标首帧的宿主原语边界；
- chaos-vm-instrument：尚未证明动态解释器 / 字节码与静态资产不同或已有 trace 需要插桩补观察；
- opcode-recovery：无带操作数或栈值的 trace 与 fixture，明确不满足；
- variant-failure：两份资产 hash 相同，未形成失败 / 成功变体谱系，不满足。

因此本拍不制造新的 blocker。若上游需要停止重复派发，需明确记录“结构已识别；目标请求入口未绑定”这一进度，而不能继续把同一个未细化阶段当作新工作。

## 限制

没有本次运行 close reason、完整 local 帧 receipt 或同一冻结 fixture，不给出 token / 指纹 / 动态 VM 的确定根因。没有执行目标代码或站点操作；未修改 solve.py、_sandbox.js、原始资产、result.json 或 facts。

## 并发与取样说明

Grok 仍可能写入源文件；本报告是顺序只读观察，绝非停机快照。以下为收口时重新计算的 hash 与 mtime；前述代码行号对应本拍阅读时的内容，如源文件继续变化应据此重验。

取样时间（UTC）：2026-10-24T06:28:20.559827+00:00。

| 文件 | mtime (UTC) | SHA256 |
| --- | --- | --- |
| challenges/28-jsvmp2/solve.py | 2026-10-24T06:00:36.729079+00:00 | 3ae63915650c5a15c2a26db5a10150c77a03e8a0163461f14bda1dd4bf043a29 |
| challenges/28-jsvmp2/_sandbox.js | 2026-10-24T06:28:03.197975+00:00 | 700a3ba05eb87f8a751314ee145af8563e5ba41aa0d5a28915a17b4fdb608c1d |
| challenges/28-jsvmp2/result.json | 2026-10-24T06:27:37.323868+00:00 | 93042689d5e5136f119beb6398219370f1fafcc70384316f35f52827e9fb0875 |
| challenges/28-jsvmp2/assets/jsvmp2.js | 2026-10-10T11:02:48.749260+00:00 | 0bf700f338edcc3aa8addc45d86be0240efa3f1746cea2f792d00fb4fec70775 |
| challenges/28-jsvmp2/assets/sdk.min.js | 2026-10-10T11:32:54.466580+00:00 | bbce993e05762e6c01b032f5203deba96ecdb94a3a7b964343aa143fdc7770a9 |
