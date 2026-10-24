# s17 capture stop

- `ruyitrace_capture_stop` 已发出。project `spiderdemo`，caseId `spiderdemo-register-login`，runId `rt_20261010073916_6f589cbd54`。回执 status 为 requested。未导航，未清 cookie，未点击。
- 最终 `state.json`：state `stopped`，phase `stopped`。不是 `completed`，也不是 `failed`。
- gates：`runtime-hash` pass，`evidence-index` pass，`evidence-receipt` pending。`integrityReceipt` 不存在，`receipt.json` 不存在。
- 三个 gate 未齐，未调用 `web_case.py run`。`web-case.json` 的 `activeRuns.ruyitrace` 仍是这个 runId（本刀没有改它）。
- 未调用 `ruyitrace_query`、`ruyitrace_get`、`ruyitrace_index`，也未用 `capture_status` 列 artifacts。未读请求包。

## 阻塞

graceful stop 落成 `stopped`，`evidence-receipt` 未 pass，没有 `integrityReceipt`。本刀不为补 gate 去 query，也不再开 capture。

## receipt 门禁

`mcp/ruyitrace-mcp/docs/mcp-tools.md`：`ruyitrace_receipt`「完成的采集会自动生成该 receipt。再次调用本工具只用于在显式完整性调查后复核先前已完成的 run。」`ruyitrace_capture_stop` 也只对「完成的采集」生成完整性 receipt。

本 run 的 state 是 `stopped`，不是 `completed`。未调用 `ruyitrace_index`，未调用 `ruyitrace_receipt`。
