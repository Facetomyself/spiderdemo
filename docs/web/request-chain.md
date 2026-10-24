# Request Chain

Case: `spiderdemo-register-login`

Ordered calls. Keep the challenge chain separate from the business chain. The machine contracts are `contracts/request-parameter-lineage.v1.json` and `contracts/workflow-artifacts.v1.json`.

## Notes

Homepage load on `rt_20261010022224_c1437434d7`, in observed order. Challenge traffic is separate from the unsent register/login submit.

1. Document: `GET https://www.spiderdemo.cn/` 200 (HTML, 29953 bytes).
2. Same document then fetches `GET /admin_I/api/auth/check` 200 (71 bytes; fields `success`, `logged_in`, `message`) and `GET /admin_I/api/auth/captcha` 200 (37877 bytes; slider image fields under `data`). The captcha response is a payload fetch, not a solved challenge submit.
3. Other same-document calls, not register/login submits: `GET /admin_I/api/challenges`, `GET /admin_I/api/leaderboard`, `GET /tools/api/echo-headers/`, `POST /tools/api/kernel-detect/`, `POST /tools/api/hardware-detect/`, `POST /tools/api/client-events/commit/`.
4. Business submit chain: not observed. The page does not navigate to a register or login document.
5. Local `r56175f00023947f4985b` diverges before item 2: channel `GET /` 200 did not replace `about:blank`, so items 2–4 were not sent. `firstDivergence=environment-gap`. `requestBoundaryAligned=false`.

Login-only chain on `rt_20261010083653_880526e2a7`. This run has no register POST and no `POST /admin_I/api/auth/captcha/verify`.

1. Homepage still fetches `GET /admin_I/api/auth/check` and `GET /admin_I/api/auth/captcha`. That captcha GET is not a solved slider submit.
2. `POST /admin_I/api/auth/login` with JSON `username` and `password`. The first observed attempt was rejected and set no session cookie.
3. A second `POST /admin_I/api/auth/login` was accepted and set `sessionid`.
4. `GET /admin_I/api/user/stats` then returned the logged-in stats object.
5. Client module: `modules/login`. It sends the login body and keeps `sessionid`. Credentials come from the project-root `.env`. It does not mint `cs_stable_gate`.

<!-- generated:request-chain -->
TEMPLATE-UNFILLED
<!-- /generated:request-chain -->
