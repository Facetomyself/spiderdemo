# Experiments

Case: `spiderdemo-register-login`

Append-only experiment and dated notes. Do not read this file unless `docs/web/index.md` names a section.

<!-- generated:experiments -->
TEMPLATE-UNFILLED
<!-- /generated:experiments -->

2026-10-10: restarted interactive capture `rt_20261010073916_6f589cbd54`; left for the user to register and log in; form not filled by the agent.
2026-10-10: stopped capture `rt_20261010073916_6f589cbd54`; the user had already finished registration; request packets were not read.
2026-10-10: login-round capture `rt_20261010083653_880526e2a7` is running; profile `dom-observe`; switches `MOZ_DOM_HTTP_PACKET_TRACE=1` and `MOZ_DOM_TRACE_ASYNC=1`; JSCall not enabled; form not filled by the agent.
2026-10-10: stopped login-round capture `rt_20261010083653_880526e2a7`; request packets were not read; final state `stopped`, phase `stopped`.
2026-10-10: login module `protocol/login.py` follows `rt_20261010083653_880526e2a7`. Login POST body fields are `username` and `password` only. No captcha field. Success sets cookie `sessionid`. The run is still `stopped` and has no integrity receipt.
2026-10-10: live login for account `mengmaa` succeeded without `cs_stable_gate`. `user_stats` readback succeeded. Password and cookie values were not stored.
2026-10-10: login client moved from `protocol/login.py` to `modules/login`. Account keys live in the project-root `.env` (`SPIDERDEMO_USERNAME`, `SPIDERDEMO_PASSWORD`). No crawler test folders.
2026-10-10: challenge catalog has 33 rows. Two starters are missing and the button text is 开发中: `control_challenge`, `slide_sum2_challenge`. The other 31 have folders under `challenges/`. Shared HTTP helper is `modules/runtime.py`.
