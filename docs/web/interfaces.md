# Interfaces

Case: `spiderdemo-register-login`

Endpoint catalog. The machine contract is `contracts/request-parameter-lineage.v1.json`. Do not paste raw request bodies.

## Notes

Observed on `rt_20261010022224_c1437434d7` (homepage only; no credential submit):

- `GET https://www.spiderdemo.cn/` → 200, HTML response 29953 bytes. This document has no same-origin register or login href. Login and register are in-page controls: `login()`, `showRegister()`, `toRegister()`.
- `GET https://www.spiderdemo.cn/admin_I/api/auth/check` → 200, response 71 bytes. JSON fields: `success`, `logged_in`, `message`. `logged_in` was false. Initiator: `checkLoginStatus` in `/static/js/main.js`.
- `GET https://www.spiderdemo.cn/admin_I/api/auth/captcha` → 200, response 37877 bytes. JSON fields: `success`, `message`, `data.y`, `data.captchaId`, `data.sliderImage`, `data.bgImage`.
- No register or login POST was sent. `login()` contains an obfuscated POST fetch URL; that URL is not an observed request.
- Local `r56175f00023947f4985b` left the document on `about:blank`, so the two auth GETs above were not sent. `firstDivergence=environment-gap`. `requestBoundaryAligned=false`.

Login submit on `rt_20261010083653_880526e2a7`. Field names only:

- `POST https://www.spiderdemo.cn/admin_I/api/auth/login` with `Content-Type: application/json`. Body fields: `username`, `password`. No captcha field.
- Rejected attempt: HTTP 200, JSON fields `success=false`, `message`. No `Set-Cookie`.
- Accepted attempt: HTTP 200, JSON fields `success=true`, `message`, `user` (`user_id`, `username`, `nickname`, `email`, `total_score`, `completed_challenges`, `avatar`, `is_admin`). `Set-Cookie` name `sessionid` (HttpOnly, Path `/`, SameSite Lax, Max-Age 86400).
- `GET https://www.spiderdemo.cn/admin_I/api/user/stats` after the accepted login. Request cookies: `cs_stable_gate`, `sessionid`. Response fields: `success`, `stats` (`total_score`, `completed_challenges`, `user_rank`, `login_count`, `nickname`).
- `cs_stable_gate` was already on the login request. This capture has no `Set-Cookie` that creates it. The login module does not mint that cookie.

<!-- generated:interfaces -->
TEMPLATE-UNFILLED
<!-- /generated:interfaces -->
