# 验收探针上游改记

`acceptanceProbe=failed` 的那一轮没有打到站点。项目根没有 `test.py`，进程在脚本启动前退出。见 `agent-notes/20261023-test-py-missing.md`。这不是请求边界失败，也不是把 `serverAccepted` 写成假通过。

保持不动：

- `requestBoundaryAligned=true`。登录回放边界没有新的反证。
- `hostProbe=boundary-moved`。这个字段由宿主工具记账，不改。
- `purecalcStage` 与 `v8rpcStage` 仍是未跑。06 / 28 还没有冻结的纯算或 RPC 基线。

改记的上游是当前未完成步骤的形态。06 的登录态实页 trace（`agent-notes/s26-jsvmp06-trace.md`，run `rt_20261010143356_3e38a94715`）显示页面在 `jsvmp_challenge.js` 里组包，浏览器自己的 protobuf POST 被拒绝。这次 capture 没有带操作数或栈值的 opcode trace。因此：

- `boundaryKind=js-vm`
- `obfuscationBlocking=true`
- `jsvmBlocker=interpreter-structure`

然后把 `acceptanceProbe` 清空。不重跑缺失的 `test.py`，不改它的输入。
