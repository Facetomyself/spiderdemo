# JSVMP 卡点审计的方法参考

日期：2026-10-24。范围：仅检索方法边界；未读取 `challenges/28-jsvmp2` 业务文件、运行脚本、浏览器或目标网络。这里不对该 case 的真实 VM 语义、首帧内容或关闭原因作独立事实认定。

## 可供父审计使用的结论

1. **分型解决后不应自动继续分型。** 本地 `jsvmp-analysis-triage-procedure.md` S4/S7 明确要求先判断算法在宿主、里层还是当前 opcode；宿主/里层已能闭合就停止拆外层 opcode。`ai-assisted-20260810-01-procedure.md` S3 与 outputs 则要求用反混淆后实际结构决定是否逐 op。适用判断：若父审计确认 s29 已完成解释器结构判定，则继续重复结构判定必须指出新反例或具体未知指令，否则没有直接回答后续应用链卡点。
2. **VM 产值、浏览器语义一致、业务接受须分账。** `jsvmp-variant-failure-lineage-procedure.md` S4/S5、F4/F5/F6 将解析兼容、本地语义一致和下游业务结果分开。若父审计所报 connect 后关闭属实，不能据此倒推 VM 分型失败，也不能仅凭连接建立认定应用鉴权通过。关闭是否由鉴权、状态、时序或输入错误引起，必须由本 case 原始运行证据判定。
3. **Worker → 应用 WS 的证据缺口不能靠猜队列弥补。** `browser-env-objects.md` 的“补环境纪律”要求当前目标 browser fact 对齐对象外观、内容、行为、身份和时序；明令 Worker / MessagePort 的派发、source/ports、transferable 和顺序没有证据时保持缺口。若现有 VM 结果已经可产出，应优先在同一有效会话比较真实浏览器从 Worker 产物到 WebSocket 构造及首帧的输入输出、转换与时序，而不是继续补邻近环境面。此为方法建议，不是本次已执行或获准绕过 dispatcher 的动作。
4. **“本地没异常/产出了 token”不是环境正确的证据。** `ai-assisted-20260810-01-procedure.md` F5 记载环境探测错误仍可能产出值；必须有真实浏览器同输入样本才能把偏差收敛到首处分叉。这张卡是其他样本的来源流程，不证明 28-jsvmp2 使用相同算法或检测。
5. **外部工具说明只能证明工具自述能力。** jsdom 官方 README 确认其实现浏览器子集，不执行布局/渲染，navigation 有未实现部分；这解释“假对象齐全”不等于真实浏览器，但无法指认当前 case 缺的属性。外部 firefox-reverse README 自述引擎级 JSVMP/WebAPI 观测，未检验其二进制或当前 case 适配，不建议为此次审计更换项目既定 RuyiTrace/runtime。

## 检索与证据账本

- 已按 `search-layer` 使用公开且不带本地资料的两组查询，结果见 `search.json`：Exa + Tavily 有返回，Grok 两次 timeout（35 秒），不视为有 grounded 结果。当前可发现工具没有 client-native web-search lane，因此未伪造第四源覆盖。
- 先执行 `article/scripts/kb_catalog.py query --tag jsvmp --limit 12`，命中 27 个 module 条目、返回 12，见 `kb-jsvmp.json`；不是 27 篇相互独立文章。补充 `--target JavaScript` 仅属同义词探查，见 `kb-javascript.json`。随后对 INDEX 做了关键词定向定位，未读取 INDEX/CATALOG 全文。
- GitHub 命中后读取 `pavedpath-code`，使用 `gh search repos`、`gh repo view`、`gh api repos/.../readme` 定向核查。此切片已是父任务的独立资料子代理，未再次拆分，避免重复检索和无关生态扩张。
- 不采用公开题解，未检索站点题号、不运行参考实现、不复制他站算法、设备字段或请求样值。

### 本地参考（全部为来源流程/参考，不是当前 case 验收）

| 文件 | 关键位置 | 适用边界 |
|---|---|---|
| `D:/reverse_ENV/article/web-reverse/jsvmp-analysis-triage-procedure.md` | S2–S7 / acceptance / failure-exits | VM 分型、算法所在层、何时停止逐 op；source-report |
| `D:/reverse_ENV/article/web-reverse/ai-assisted-web-reverse-compilation/ai-assisted-20260810-01-procedure.md` | S3/S4、outputs、F5 | 结构判据、环境补错仍出值；来源为其他样本 |
| `D:/reverse_ENV/article/web-reverse/jsvmp-variant-failure-lineage-procedure.md` | S4/S5、F4/F5/F6 | 首处分叉、同资源回归与业务层分账；source-report |
| `D:/reverse_ENV/article/web-reverse/browser-env-objects.md` | “补环境纪律” | 当前目标真值、身份与异步时序；未有当前 case 对拍 |

### 外部 primary-source 核查

| 来源 | 核查面 | 当次元数据 / 限制 |
|---|---|---|
| https://github.com/jsdom/jsdom | 官方 README 行 6、120–138、394、539–542；GitHub API 元数据 | MIT；21,730 stars / 1,820 forks；pushedAt 2026-10-23；仅用于浏览器子集边界，不推荐替换项目运行时 |
| https://github.com/WhiteNightShadow/firefox-reverse | 仓库 README 行 38、147、201–202；GitHub API 元数据 | 940 stars / 199 forks；licenseInfo=null；pushedAt 2026-10-23；README 自述观测能力，未做可运行验证、未推荐引入 |

拒绝把高 star、README 宣称或第三方博客当成当前问题已解决；搜索中的泛 JSVMP 教程、Native VM workshop 和未核验商业文章均未用作当前 case 事实证据。确切关闭原因和旧 blocker 是否失效仍由父审计的本地证据决定。

## 建议父审计的判定问题

- s29 的结构成果具体回答了什么，还未回答什么？后续 slice 是否承认这份成果？
- VM/Worker 产物到 WS 首帧中间有哪些可定位的转换、状态依赖与异步事件？每条有没有当前 browser fact？
- 产物对拍失败发生在 VM、Worker 消息、WS 构造、首帧编码，还是服务端接受之后？每次试验是否改变一个可证假设？
- 现行 blocker 是否仍对应眼前失败？若实际剩余是应用鉴权，旧 interpreter-structure 的标签不应替代当前未知边界。

限制：这里的建议不替代父 `web_case.py next`、实际 runtime 取证和共享 validator；没有证明任何本地候选已可通关。
