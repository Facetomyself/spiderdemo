# web-jsvmp skill 在 28-jsvmp2 的使用评估

评估日期：2026-10-24。范围：skill 在本 case 中的阶段选择、产物质量、暴露的缺口与改进建议。不改变已通关的事实。

## 1. 阶段走位（按时间）

| 阶段 | 用到的 slices | 结果 |
|---|---|---|
| interpreter-structure | s29 | 静态分型完成，两台栈 VM 识别清楚 |
| interpreter-structure → request-dispatcher | s32 | 请求锚（`/ws/` 首帧）定位，但 108 字节正文没解开 |
| host-primitive | s33–s36 | 多轮宿主 A/B（document.all、SharedWorker、TextEncoder、documentElement），单点未命中 |
| variant-failure | 未真正启用 | 只在 s37 前读过 reference |
| opcode-recovery | 未进入 | 缺带 operands/stack 的 runtime trace |
| chaos-vm-instrument | 未进入 | 无动态字节码证据 |

skill 的按阻碍选阶段原则确实被执行了：Grok 没有按表顺序走，而是依据「请求绑定没闭合」「宿主面有差异」这类判断在 interpreter-structure 和 host-primitive 之间反复。问题不在阶段选择本身，在于缺一个能提前把注意力切到「协议/导出层」的分支。

## 2. skill 的正面作用

- **interpreter-structure 的停止条件清晰**：s29/s32 没有硬填 opcode 表，明确写「不能做 opcode 验收」。避免了把结构分型误当语义恢复。
- **host-primitive 的单变量原则**：s33–s36 每轮只改一个 host 面，实验可回溯，没有混变量。
- **dispatch_evidence 结构化**：s32 输出符合 request-dispatcher.md 规定的 JSON 形态，request_anchor / script_sha256 / callsite / limits 都齐。
- **variant-failure 三分账**：s37 明确把「解析兼容 / 本地语义一致 / 业务接受」分开记账。
- **request-dispatcher S1（从请求反查入口）**：确实定位到目标 WS 连接的首帧。

## 3. skill 的缺口（按影响排序）

### 3.1 没有「全局导出侦察」步骤（影响最大）

`interpreter-structure.md` 只讲取指/分发/状态三边界，不讲「加载完先枚举 window / self / worker global 上的可疑函数名」。`sdk.min.js` 全局暴露了 `spiderEncrypt` / `spiderEncryptBytes` / `spiderDecryptBytes` / `msgpackEncode` / `msgpackDecode`，如果 s29 或 s32 就扫一遍全局，s37 才需要做的事能提前半天。这不是运气问题，是侦察面缺失——分型完成不等于边界闭合，但 skill 没有一句「再扫全局」。

**建议**：interpreter-structure 末尾加一个固定子步骤：列举所有可达 realm 的全局符号（非内建、非混淆器样板），记录名字、参数个数、行为摘要。哪怕全部是空，也记一次「已查无全局导出」。

### 3.2 没有「握手凭据闭环」检查

`request-dispatcher.md` 的 S1 从请求反查签名函数，但只看应用层的参数名和 body 字段，没有明确说「Cookie / Authorization / 自定义头到 upgrade 请求的传递链是否闭合」。本 case 里 `ads-baidu=<sealed token>` 是页面 `document.cookie` 写进来的，但一直停留在 `_sandbox.js` 的 `cookie-set` 日志层面，没提升到 Python 端 upgrade 请求头。如果 s32 在 request-dispatcher 的最小证据里多一项「upgrade 头 vs 宿主写入凭据」对照，握手 cookie 缺失能早 5 轮发现。

**建议**：request-dispatcher S1 加一条：列出 target 请求的全部凭据来源（cookie / header / URL 参数），并对照宿主 runtime 里实际写/读的地方。缺一个来源就记一个缺口，不缺就不标。

### 3.3 没有 WebSocket / 二进制帧分析分支

五个 jsvmBlocker 和所有 reference 都按 HTTP API 思维写：URL / 参数 / body。本 case 真正的边界是 WebSocket 帧上的 cmd 协议（首帧 cmd 100，回帧 18 字节 challenge，回复 cmd 99 + 38 个数，后续 cmd 4 分页）。`request-dispatcher.md` 和 `variant-failure.md` 都没有「frame → cmd/opcode → codec → key 来源」的流程模板。s37 是靠参考点拨才拆出协议结构，不是 skill 里已有的方法。

**建议**：新增分支 `ws-frame-protocol.md`（或并入 request-dispatcher）：把「首帧方向/opcode/长度、帧间 cmd 编号、消息 codec（msgpack / protobuf / 自定义 XOR+base62）与 key 来源」列为标准记录项。明确这个分支不等于 opcode-recovery，产物归 interpreter-structure 或独立的 `ws-protocol` 附件。

### 3.4 `jsvmBlocker` 语义不够用

五个合法值（host-primitive / interpreter-structure / chaos-vm-instrument / opcode-recovery / variant-failure）都是「VM 拆解进度」，没有一个是「**边界已过、应用层未对齐**」。本 case 在 upgrade 成功、发送阶段 4003 期间，facts 只能继续填 interpreter-structure，调度器反复给同一 readRef，而真实缺口在协议/凭据层。这不是 skill 一处的问题，是宿主 facts 字段设计的问题，但 skill 文档里也没有明确说「如果真实失败不在 VM 层，这个字段就不适用」。

**建议**：facts 增加 `phase`（handshake / app_ready / answer_accepted）或在 blocker 值集加 `ws-app-protocol`，让「已经连上了、帧还没对」能表达出来。skill 层面在 SKILL.md「阶段」表后加一句：如果失败边界不在 VM 取指/分发/状态三者中，blocker 字段可能不适用，先回父 next 重判边界。

### 3.5 host-primitive 缺少自动停下来的条件

host-primitive.md 说「一次只换一个变量」，但没说「换了 N 轮还没让 token/目标边界动，就该回父 next」。s33–s36 连做 4 轮宿主 A/B，每轮 token id 都没动、close 都是 4003，但循环没停——因为没写停下来。

**建议**：host-primitive 加一条：同一输入 fixture、连续 3 次 host 差异实验仍未改变 `token id` 或任何目标边界字段，回到父 `web_case.py next`，由父判断是否切阶段。已排除项存入失败谱系，不重复。

### 3.6 opcode-recovery 前置重

opcode-recovery 要求带 operands / stack 的 trace + fixture 才能进入。这个门是对的，但本 case 真正的缺口在协议层不是 opcode 层——没 gate 指向就该回父 next，但父 next 因为 blocker 还是 interpreter-structure 又给回同一个 readRef。形成闭环空转。

**建议**：配合 3.4 的 `phase` 字段，让「真实失败不在 opcode 层」可以显式表达，父 next 能跳出 VM 循环去派 ws-protocol / 协议侦察切片。

## 4. 总体评价

**正面**：skill 的分阶段设计、停止条件、单变量原则、三分账原则都在本 case 起了实际作用，产物（dispatch_evidence、trace 笔记）质量高，可回溯。

**负面**：skill 的阶段是为「拆 VM」设计的，对「VM 是黑盒工具箱 + 应用层协议在 WebSocket」这种场景没有侦察分支。Grok 在 s29–s36 期间没跑偏 skill 的字面流程，而是被 skill 的覆盖面限制住了——真正需要的是「边界外侦察」（全局导出、握手凭据、WS 帧协议），skill 没有对应入口，这些工作只能在 s37 用参考点拨的方式一次性补上。

**一句话**：skill 把「拆 VM 的内功」写得很细，但「边界在哪、协议长什么样」的外功没写，这个 case 8 小时里 7 小时卡的就是这个。

## 5. 建议落地顺序

1. **低成本高收益**（改动 < 20 行）：全局导出侦察、握手凭据闭环、host-primitive 自动停。
2. **中等成本**：新增 `ws-frame-protocol.md` 分支、facts 加 `phase` 字段。
3. **长期**：把「协议层 vs VM 层」的分界显式写进 interpreter-structure / request-dispatcher 的入口判断，避免同类 case 再跑偏。

产物：`agent-notes/codex-grok-audit-20261024/skill-eval.json`（结构化评估）。
