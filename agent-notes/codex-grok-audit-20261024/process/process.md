# Grok 题 28 过程审计（只读快照）

## 结论

存在持续卡点的路径偏差，但不是“从没读 JSVMP 文档”或“还在重复解决 403”。当前实际卡点已前移到 WebSocket 建连后的应用认证/消息阶段，`send closed 4003`；它尚不能单独证明 token 算法错误或某一宿主字段缺失。

最有证据的偏差是：解释器静态分型已完成，而“本题请求 → 页面 VM → Worker → send”的绑定和首个浏览器/本地分歧仍未闭合；主线程却持续把“让 token 改变”当下一实验选择器。全局 facts 里的登录边界 `true`、06 的 JS VM 分类和题 28 的真实失败被混在一个 case 中，因此 `next` 反复给同一阶段，而实际工作已在另一条宿主枚举轨道推进。

## 快照与边界

- 审计截止：2026-10-24T06:26:13.845803+00:00；源 updates 日志 `34677207` bytes / `10943` 行，SHA-256 `a127aa8614138f1ea6b495ce1f0a4c5734673261554605263d9f584970c5c212`；mtime `2026-10-24T06:24:33.260126+00:00`。
- Grok 日志在审计时仍有活动；没有停止、中断或修改它。本报告只代表该冻结读快照，后续变化不纳入结论。
- `timeline.json` 保存脱敏时间、原始行号、tool call id 和动作说明。Grok 日志有压缩/重写风险，因此定位以时间 + tool id + 快照 hash 一起使用；不能假设早期读出的行号永远稳定。
- 未复制原始会话、敏感值、frame 明文；未执行目标 JS，未调用浏览器，未修改原项目文件或 facts。
- 父线程审计启动时刚盖的 dispatcher stamp 与 slices 不算 Grok 历史。当前 skill/dispatcher 有工作区修改，其规则只作当前对照；不把文档矛盾自动当成历史技术根因。

## 时间链（北京时间，2026-10-24）

| 时间 | 证据 | 事件与边界 |
|---|---|---|
| 08:35:49 | updates:3731 | 读取 interpreter-structure。 |
| 08:36:26 | updates:3744 | 派发题 28 解释器分型，产物 s29；请求入口依然未绑定。 |
| 08:53:45 | updates:3874 | 读取 request-dispatcher；“完全没走 reference”不成立。 |
| 09:15:45 | updates:4432–4435 | trace 笔记回填后仍 route_web_jsvmp / interpreter-structure。 |
| 11:48:37–12:12:30 | updates:7931, 8034, 8064, 8419 | 冻结种子比较 host shapes / prototype / Date.now / document.all。部分改变 token，但仍未得服务端接受。 |
| 12:43:20 | updates:9004 | 读取 variant-failure；不代表已发生动态资源变体，当前没有哈希变化证据。 |
| 13:05:40、13:37:54、13:40:15 | updates:9507, 10129, 10149 | 多次 next 仍同一 interpreter 阶段；后续继续 host A/B。 |
| 13:30:26 | updates:10057–10060 | WebSocket constructor name A/B；两臂仍 4003。 |
| 13:58:02 | updates:10454–10457 | Node stack 与 Firefox 形状 stack 的冻结种子比较，两臂 token 标识相同、均 4003。 |
| 14:00:54 | updates:10511–10514 | 匿名/命名 host functions，同种子标识相同、均 4003。 |
| 14:17:09 | updates:10845–10848 | version 绑定 A/B，同种子标识相同、均 4003。 |

上述 token 标识相同只说明这些样本下未观察到该改动影响；不能推断字段永远无关，亦不能把不同 seed 下长度不同当作宿主修复效果。

## 真实阻塞和已知事实

1. s29 已有栈机、表驱动映射、滚动解码量和 wrapper 区别等静态分型。没有带 operands/stack 的 opcode trace，所以不得声称 opcode 恢复或共享 gate 通过。
2. s29 的请求入口尚未钉到 VM fetch；s30 只说明浏览器目标 `/ws/` 的 101 和帧观察，不是完整目标应用链的成功 fixture。混有浏览器控制帧时必须按目标 URL/连接过滤，不能把全部 WS frame 统计当页面数据。
3. Grok 已识别当前本地 4003，且通过 permessage-deflate 等传输修改走过旧 403。旧 ANALYSIS 的 403 是历史状态，不能继续当当前根因。
4. 浏览器/本地前 token 的调用顺序差别目前由会话摘要记录，receiver/value 归属及 immediate caller 仍有不确定性。某原生调用在 JIT parent 链中出现，不能直接认作页面读了该宿主属性；没有精确 receiver 的 href 顺序不宜直接补值。
5. 仍无成功的题 28 “INIT → token → 服务端接受 → page data”配对基线；冻结本地 A/B 是候选排除，不替代此基线。

## 发现

### P1 请求归属未闭合时连续枚举宿主，实验目标逐渐变成改变 token

s29 已分型，但目标分页帧/提交答案尚未绑定到 VM 取指；后续进行 document.all、Window prototype、反射、stack、function name、version 等实验。token 改变只证明输入敏感性，不等于更接近浏览器或服务端接受。

证据：`D:\reverse_ENV\workspace\spiderdemo\agent-notes\s29-jsvmp28-interpreter.md:62`；`D:\reverse_ENV\workspace\spiderdemo\agent-notes\s29-jsvmp28-interpreter.md:102`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:7931`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:8419`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10454`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10511`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10845`。

建议：沿 interpreter-structure 的 request-dispatcher 分支，先冻结目标请求、page→Worker INIT→WebSocket send 归属、receiver/value provenance 和首个真实分歧；一个双条件宿主实验后回同一边界，不继续猜字段。

### P2 全站/登录 facts 被沿用到题 28，dispatcher 与实际工作脱钩

caseId 仍为注册登录；requestBoundaryAligned=true 被笔记明确解释为登录回放无反证，jsvmBlocker=interpreter-structure 则由 06 trace 改记。28 多次得到同一 route，但 Grok 明知重派分型无用，继续 Node host 工作；没有按题 28 重建对应 scope 的对照。

证据：`D:\reverse_ENV\workspace\spiderdemo\web-case.json:3`；`D:\reverse_ENV\workspace\spiderdemo\contracts\auto-decision-facts.json:41`；`D:\reverse_ENV\workspace\spiderdemo\contracts\auto-decision-facts.json:55`；`D:\reverse_ENV\workspace\spiderdemo\agent-notes\s27-acceptance-upstream.md:7`；`D:\reverse_ENV\workspace\spiderdemo\agent-notes\s27-acceptance-upstream.md:11`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\chat_history.jsonl:4`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:4432`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:9507`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10149`。

建议：把 28 的阶段、firstDivergence 与 requestBoundaryAligned 绑定到 28 请求锚及实验结果，避免登录边界的 true 代替本题完整边界。无需仅为字面变化改 blocker。

### P3 稳定公开笔记滞后于实际 4003，影响恢复者对卡点判断

ANALYSIS 仍写重复 403；最新 result 与 Grok goal 已说明握手解决、send 后应用关闭 4003。s30 的浏览器 101 不是答案通过。

证据：`D:\reverse_ENV\workspace\spiderdemo\challenges\28-jsvmp2\ANALYSIS.md:7`；`D:\reverse_ENV\workspace\spiderdemo\challenges\28-jsvmp2\result.json:1`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\goal\plan.md:41`；`D:\reverse_ENV\workspace\spiderdemo\agent-notes\s30-jsvmp28-trace.md:16`。

建议：分开记录 upgrade reached / token submitted / application accepted / page collected / answer accepted；同步 ANALYSIS 和当前阶段，不让 ready 前统一异常标签误指回握手。

### P4 noOfflineFallback/live RuyiDOM 状态与长期 Node 执行缺少明确合同对齐

facts 仍 noOfflineFallback=true、ruyidomNetwork=live、ruyidom=diverged；实际已长期使用 Node vm。当前压缩摘要承认 Node 为现有 shipped runtime。用户允许本地补环境，故不能仅凭字段认定用户授权违规；这是运行面/证据面和状态维护不一致。

证据：`D:\reverse_ENV\workspace\spiderdemo\contracts\auto-decision-facts.json:2`；`D:\reverse_ENV\workspace\spiderdemo\contracts\auto-decision-facts.json:3`；`D:\reverse_ENV\workspace\spiderdemo\contracts\auto-decision-facts.json:4`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\chat_history.jsonl:4`。

建议：明确本题所用执行面及其证明范围，按既有事实记录流程对齐合同；Node 出参不得升格 browser fact。

### P5 不能归因于从未读过 JSVMP reference，亦无证据每步都是空转

08:35:49/08:53:34 读 interpreter-structure，08:53:45 读 request-dispatcher，12:43:20 读 variant-failure。s29 静态分型有具体状态/解码证据。冻结种子 A/B 和移除无效 probe 有效缩小候选，但其结论仅适用于该 fixture，非字段永远无关。

证据：`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:3731`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:3862`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:3874`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:9004`；`D:\reverse_ENV\workspace\spiderdemo\agent-notes\s29-jsvmp28-interpreter.md:1`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10457`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10514`；`C:\Users\mengma\.grok\sessions\D%3A%5Creverse_ENV\01a12396-16d9-78d3-8dfd-366ae7667bb6\updates.jsonl:10848`。

建议：保留冻结种子 A/B 和未通过如实标记；将发现沉淀成按请求边界的失败谱系，避免重新枚举已排除项。

## 纠偏下一步

先保留当前工具/页面，不开新 capture、不重做分型、不改 opcode。用现有完整 trace 和脚本 hash，沿 interpreter-structure 中的 request-dispatcher 分支做一份目标 WS 连接级、页脚本/Worker 级时间线；把第一条业务 token send、其上游 INIT、page VM 真实取指/调用点及对应 host receiver 绑定起来。必要信息没有采到时如实记录证据缺口，而不是猜浏览器值。

然后基于本题请求边界更新明确 scope 的事实，再选一个已被浏览器与本地双条件支持的宿主实验。实验必须回到同一 fixture 和同一观测边界；token 变化与服务端接受分开记录。若消息认证问题还没闭合，避免继续四 Worker 全量验收。保留目前有价值的冻结种子对照，系统记录已排除项。

没有进行源码修复、Git 提交或在线解题；技术根因仍需上述请求绑定取证，不能由本过程审计代替。
