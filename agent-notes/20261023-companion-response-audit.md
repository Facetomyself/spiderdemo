# 2026-10-23 companion response audit

## Scope

Dispatcher action: `companion_response_audit` / `blocked`. Reviewed only existing RuyiTrace run `rt_20261010022224_c1437434d7`, receipt integrity=`pass`, HTTP packet index under the same run, and its contemporaneous summary `agent-notes/s1-capture-start.md`. No target run, browser capture, credential replay, or network request was performed.

## Same-window evidence

- HTTP packet index: 76 indexed records, 26 HTTP packet artifacts, 23 status-200 rows; receipt root SHA-256 `0f2fc75b304fc6b8b32f25960b2daf4c6d8db17a75ac9bcb02da87cbeb26f2f0`.
- The window navigated only `https://www.spiderdemo.cn/`. The observed 200 set includes document/script resources; `/admin_I/api/auth/check` (logged-in=false), `/admin_I/api/auth/captcha`, `/admin_I/api/challenges`, `/admin_I/api/leaderboard`, `/tools/api/echo-headers/`, `/tools/api/kernel-detect/`, `/tools/api/hardware-detect/`, `/static/protos/client_signals.proto`, and `/tools/api/client-events/commit/`. Body values are not copied here. Contemporaneous notes record only response schema/lengths for the listed APIs.
- There is no same-window registration/login POST, `jsvmp_challenge` init/page POST, `jsvmp2_challenge` init, or `/ws/` upgrade in this run. Therefore neither failed challenge response belongs to this window and no causal response-body-to-challenge-request consumption can be established from it.
- The `challenges` response advertises challenge entries, but the observed trace does not navigate a challenge route or issue either challenge protocol. It cannot be treated as an auth ticket consumed by 06/28.
- Existing challenge records are separate: 06 has page POST HTTP 400 `Protobuf鉴权验证失败`; 28 has WebSocket upgrade HTTP 403 before 101. These are distinct target-boundary results, not companion responses for the homepage capture.

## Finding and limit

For the audited homepage/login capture, no same-window companion-response ticket chain to a failed business submission is present because no such submission occurred in the capture. This closes only the requested audit prerequisite for this capture. It does not prove challenge response completeness, JSVMP semantics, local parity, or server acceptance for challenge 06/28. Challenge validation still requires their own frozen run/fixture and dispatcher action.

## Inputs

- `evidence/web/ruyitrace/rt_20261010022224_c1437434d7/receipt.json`
- `evidence/web/ruyitrace/rt_20261010022224_c1437434d7/raw/http_packet/index.jsonl`
- `agent-notes/s1-capture-start.md`
- `challenges/06-jsvmp/ANALYSIS.md`, `challenges/06-jsvmp/result.json`
- `challenges/28-jsvmp2/ANALYSIS.md`, `challenges/28-jsvmp2/result.json`
