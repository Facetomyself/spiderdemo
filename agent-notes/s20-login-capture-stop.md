# s20 login capture stop

- `ruyitrace_capture_stop` 已发出。project `spiderdemo`，caseId `spiderdemo-register-login`，runId `rt_20261010083653_880526e2a7`。回执 status 为 requested。未导航，未清 cookie，未点击。
- workerPid `75888` 与 browserPid `39948` 在 stop 发出时仍在。本地 `2026-10-10 16:43:48` 复查时两者都已退出。`state.json` `updatedAt` 为 `2026-10-10T08:43:45.839Z`。没有再等满 3 分钟。
- 最终 `state.json` 与 `evidence-run.json` 顶层：state `stopped`，phase `stopped`。不是 `completed`。
- gates：`runtime-hash` pass，`evidence-index` pass，`evidence-receipt` pending。`integrityReceipt` 不存在，`receipt.json` 不存在。
- 未调用 `web_case.py run`。未调用 `ruyitrace_query`、`ruyitrace_get`、`ruyitrace_index`、`ruyitrace_receipt`。未再 `capture_stop` 或 `capture_start`。未读请求包。

## 阻塞

graceful stop 落成 `stopped`，`evidence-receipt` 未 pass，没有 `integrityReceipt`。不能登记为 browser fact。本刀不为补 gate 去 query 或再开 capture。
