# Grok 在 28-jsvmp2 的卡点与偏差审计

审计日期：2026-10-24。日志冻结截止北京时间 14:26:13；技术文件最后取样为 14:28:20。Grok 在此期间仍运行并修改文件，因此本报告是带时间界限的顺序取样，不能代表其后续状态。

## 核心判断

**存在使问题长期不收敛的路线偏差，但尚未证明关闭 4003 的唯一技术根因。** 实际失败已经从早期握手 403 前移到连接建立、桥接 opened 后、ready 前的发送/关闭阶段。解释器静态结构也已识别；眼前缺的是目标请求、页面 VM、Worker INIT、WebSocket 首帧之间可核对的因果链，以及 browser/local 的第一处分歧。

Grok 确实读过 interpreter-structure、request-dispatcher、variant-failure，也做过有效的冻结种子 A/B、传输修复及无效补丁撤回。不能说它完全没按技能走、一直误追 403，或所有操作都为空转。偏差出在读取方法后，未完成请求绑定就持续选择相邻宿主差异实验，实际实验与全局调度事实逐渐脱钩。

## 1. 当前到底卡在哪里

- `solve.py:249-250` 在 connect 成功后才保存连接；`:404-416` 在连接存在且 opened 后发送并产生 `send closed 4003`。因此不能再把当前结果称为升级握手前的 403。
- `solve.py:427-434` 把 ready 前所有失败都包装成 `websocket upgrade rejected`；`ANALYSIS.md:7,24-34` 仍记旧 403。这是失败层分类和交接文档的问题；Grok 当前会话已知道握手修复，不能由旧文档反推它的当前认知。
- `agent-notes/s29-jsvmp28-interpreter.md:7-60` 已有页面和 Worker 两台栈 VM 的取指、滚动解码、映射与状态描述；`:64,102` 明确承认目标请求/参数入口尚未定位。
- 浏览器 s30 真实捕获目标 `/ws/` 的 101。冻结响应里的两份 JS hash 与本地和 s29 完全一致；没有足够证据切到资产变体失败、动态解释器差异或 opcode 恢复。
- 4003 是观测到的关闭码，现有材料不足以区分 token、会话、时序、帧编码或其他应用条件，不能把其中任一项直接认作定论。

## 2. 哪些偏差会让它持续卡住

### A. 用 token 变化代替与浏览器一致的证据（高置信度）

请求入口尚未绑定时，持续试 document.all、Window prototype、反射、stack、function name、version 等宿主面。部分改动会改变 token，但改变并不等于更接近浏览器；有些冻结种子下改动不改变标识、两臂均 4003，仍继续转下一个相邻面。缺少“哪个页面/Worker 调用，读取哪个 receiver，在何处改变首帧”的首差定位，排除实验难以形成稳定的故障谱系。

日志冻结时间链中，13:58:02 的 stack、14:00:54 的 function name、14:17:09 的 version 三组 A/B 都没有改变相应冻结样本的 token 标识，且均 4003。它们能排除这些样本中的候选，不能证明对应字段永远无关。详见 `process/timeline.json` 和 `process/process.md`。

### B. 登录、06 和 28 的事实作用域混用（高置信度）

`web-case.json:3` 仍是注册登录 case；`s27-acceptance-upstream.md:7` 解释 `requestBoundaryAligned=true` 来自登录回放，`:11-15` 的 VM 分类来自 06。题 28 的请求/应用鉴权边界未闭合，却沿用这份全局事实。

Grok 压缩摘要承认：清掉 obfuscation 会落到缺失的根 `test.py`，因此保留 JSVM interrupt 继续 host work。多次 next 给同一个阶段，实际工作则继续 Node 宿主实验。**问题不在 interpreter-structure 这个字段没改名，而在该阶段内部的请求绑定产物没闭合、工作与事实没有对齐。** 不能为换路由凭空改 blocker。

### C. 成功信号与通道没有充分分账（高置信度）

s30 的 WS 帧文件同时包含目标业务连接和 url 为空的 BiDi 控制帧；全文件 close 及发送统计不能全部归给目标业务。压缩帧长度也不能直接与本地明文长度比较。应按连接与目标 URL 过滤后，分别记录 upgrade、token send、application ready、分页返回、答案接受。

### D. 状态文档与执行面不同步（高置信度）

facts 仍有 noOfflineFallback/live RuyiDOM/diverged，实际长期使用 Node vm；ANALYSIS 仍写 403，result 已为 4003。这里首先是合同、证据范围和恢复信息不一致，不能仅凭字段认定用户授权违规。Node 产物也不等于浏览器事实。

## 3. 额外发现，但不是已定根因

`_sandbox.js:295-303` 的 FakeWS.send 对跨 realm ArrayBuffer 使用外部 `instanceof`，失败后可落到 String fallback。独立、不含目标代码的合成 fixture 已复现 4 字节变为 20 字节；跨 realm typed array 不触发同一分支。**尚未观测 SDK 实际 send 参数的类型，因此只能认定条件性 bridge 缺陷，不能宣布它导致本题 4003。** 复现与限制见 `technical/cross-realm-result.json`、`technical/technical.md` F5。

06 与 28 的编码/分发结构也有实质差别；同站点、同为栈 VM 不证明同一 ISA 或鉴权根因，不能互抄补丁。

## 4. 纠偏顺序

1. 固定题 28 自己的证据 scope 和当前阶段，记录“结构已识别、请求绑定未完成”。保留已完成结构成果，不再重做分型；事实必须按原有记录流程更新，不能为了调度过门直接改布尔值。
2. 在当前 interpreter-structure 下落实已读过的 request-dispatcher 分支：按目标连接关联 page VM → INIT → Worker → 首次 token send，并观测 send 实参品牌、字节转换和顺序。现有证据缺什么就标什么，不猜浏览器值。
3. 建立同一冻结输入的 browser/local 边界对照，先找最早分歧；只有浏览器实际读取与本地确有缺失/错误同时成立，才做一个有明确验收条件的宿主实验。
4. 将关闭阶段、close reason、应用 ready、页数据及最终答案接受分开记账。同步 ANALYSIS 和错误标签，避免下个会话退回旧握手叙事。
5. 无 operands/stack trace 与 fixture 不进 opcode 恢复；资产 hash 相同不构成 variant-failure；不要用新的泛化 blocker 名称代替缺失证据。

这套顺序有明确门槛：第一份应交付的是连接级/调用级请求绑定时间线和首差结论，而不是又一组“token 有没有变化”的宿主字段实验。

## 验证与证据范围

- 核查原始代码失败分支、s27/s29 锚点、已停止的 s30 浏览器材料及 Grok 冻结日志时间链；两份题目资产与捕获响应 hash 一致。
- 独立合成 fixture 复现条件性 bridge 类型缺陷；未执行题目 JS、未在线提交答案、未启动或中断浏览器。
- 本轮仅写审计证据、审计状态，并按项目规定运行 next/登记审计 slices；未改解题脚本或技术事实字段，未 commit/push。
- 仍缺服务端可归因原因与同一输入的完整 browser/local 应用链对照，因此不能保证具体补丁即可通关。

## 证据入口

- `process/process.md`：过程发现、逐项原始文件定位及反证。
- `process/timeline.json`：冻结日志中的时间、行号、tool id；`process/snapshot-meta.json` 保存快照元数据。
- `technical/technical.md`：代码级检查、资产 hash、目标/控制 WS 分离、bridge 合成复现和并发取样说明。
- `reference/reference.md`：方法边界与参考；参考不替代本题事实。
- `findings.json`：合并结构化发现；`triage.md`：可交接的下一步与停止条件。
