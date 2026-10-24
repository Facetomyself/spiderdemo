# s21 login module

Source run: `rt_20261010083653_880526e2a7`. State is still `stopped`. `evidence-receipt` is pending. No integrityReceipt. Packet bodies were not copied into this note.

Login wire, field names only:

- `POST /admin_I/api/auth/login`, `Content-Type: application/json`
- Body fields: `username`, `password`. No captcha field.
- Rejected: `success=false`, message `用户名或密码错误`, no `Set-Cookie`
- Accepted: `success=true`, message `登录成功`, `Set-Cookie` `sessionid` (HttpOnly, Path `/`, SameSite Lax, Max-Age 86400)
- Next call: `GET /admin_I/api/user/stats` carrying `sessionid`

`cs_stable_gate` was already on the login request. This capture does not show a `Set-Cookie` that creates it. The module does not mint it.

Client: `workspace/spiderdemo/protocol/login.py`
Unit check: `protocol/test_login.py`, 3 tests passed, no live login.
