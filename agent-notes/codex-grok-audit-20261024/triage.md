# 28-jsvmp2 审计交接

状态：审计完成；题目尚未通过；Grok 仍可能在运行。不是通关成功回执。

## 已确认
- 当前失败在 connect/opened 后、ready 前发现关闭 4003；旧 403 及 upgrade-rejected 总标签已经滞后。
- s29 已做静态分型；缺的是请求/参数到 VM、Worker、WS 首帧的绑定及 browser/local 首差。
- 捕获的两个脚本与本地 hash 相同，不支持凭空切变体/动态解释器/opcode 路线。
- Grok 读过三份相关 reference；偏差是产物未闭合下继续宿主枚举，且登录/06/28 的事实 scope 混用。

## 下一份最小产物
沿现有 interpreter-structure → request-dispatcher，交付仅针对目标 WS 连接的时间线：脚本 hash、page/Worker 归属、INIT、send 实参品牌与字节转换、首帧、关闭阶段/原因。先利用现有证据；证据不存在时明确记缺口。

在同一冻结输入上定位 browser/local 第一处分叉，然后仅验证一个有双条件证据的宿主差异。token 改变不是通过条件，业务 ready 和答案接受分别验收。

## 条件性缺陷
跨 realm ArrayBuffer 可被 bridge 字符串化，合成 fixture 已复现；先观测实际 send 类型再决定是否是当前故障。不直接当成 4003 根因。

## 不应继续
不重做分型；不把控制 WS 帧当应用帧；不拿压缩长度比明文；不凭 4003 断言 token 算法错误；不换 blocker 过门；不在无 opcode trace 时拆完整指令集。

## 本轮边界
日志截止 2026-10-24 14:26:13，技术取样至 14:28:20（北京时间）。未改解题代码，未停止 Grok；后续文件变化须按技术报告 hash 重新核验。事实更新应走既有 fact record，避免覆盖正在运行的 Grok 写入。
